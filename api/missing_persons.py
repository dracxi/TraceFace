"""Missing persons API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import os
import aiofiles
import logging

from database.connection import get_db
from database.models import MissingPerson as DBMissingPerson, PersonPhoto, AdminUser
from models.schemas import UploadResponse, MissingPerson
from api.dependencies import require_admin
from services.image_processing import preprocess_image
from services.face_pipeline import face_pipeline
from services.vector_database import vector_db
from services.audit_logging import log_upload, log_deletion
from config import settings

router = APIRouter(prefix="/admin/missing-persons", tags=["missing-persons"])
logger = logging.getLogger(__name__)


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_missing_person(
    name: str = Form(...),
    date_reported: str = Form(...),
    contact_info: str = Form(...),
    description: Optional[str] = Form(None),
    last_seen_location: Optional[str] = Form(None),
    photos: List[UploadFile] = File(...),
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Upload a new missing person record with photos.
    
    Requires admin authentication.
    """
    try:
        # Validate photos
        if not photos or len(photos) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one photo is required"
            )
        
        if len(photos) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 photos allowed"
            )
        
        # Parse date
        try:
            date_reported_dt = datetime.fromisoformat(date_reported.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO 8601 format."
            )
        
        # Create person record
        person_id = uuid.uuid4()
        db_person = DBMissingPerson(
            person_id=person_id,
            name=name,
            description=description,
            last_seen_location=last_seen_location,
            date_reported=date_reported_dt,
            contact_info=contact_info
        )
        db.add(db_person)
        
        # Process photos
        total_faces = 0
        photo_records = []
        
        # Create upload directory
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        person_dir = os.path.join(settings.UPLOAD_DIR, str(person_id))
        os.makedirs(person_dir, exist_ok=True)
        
        for idx, photo in enumerate(photos):
            # Validate file type
            if not photo.content_type or not photo.content_type.startswith('image/'):
                continue
            
            # Read photo
            photo_bytes = await photo.read()
            
            # Check file size
            if len(photo_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Photo {photo.filename} exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                )
            
            # Preprocess image
            try:
                image = preprocess_image(photo_bytes)
            except Exception as e:
                logger.error(f"Failed to preprocess image: {e}")
                continue
            
            # Process through face pipeline
            try:
                results = face_pipeline.process_image(image)
                
                if not results:
                    logger.warning(f"No faces detected in photo {photo.filename}")
                    continue
                
                # Save photo file
                photo_id = uuid.uuid4()
                file_ext = os.path.splitext(photo.filename)[1] or '.jpg'
                file_path = os.path.join(person_dir, f"{photo_id}{file_ext}")
                
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(photo_bytes)
                
                photo_url = f"/uploads/{person_id}/{photo_id}{file_ext}"
                
                # Store embeddings in vector database
                for result in results:
                    embedding = result['embedding']
                    
                    # Add to FAISS index using photo_id
                    vector_db.add_embedding(str(person_id), str(photo_id), embedding)
                    
                    # Create photo record
                    photo_record = PersonPhoto(
                        photo_id=photo_id,
                        person_id=person_id,
                        photo_url=photo_url,
                        embedding_id=str(photo_id)  # Use photo_id as embedding_id
                    )
                    photo_records.append(photo_record)
                    total_faces += 1
                
            except Exception as e:
                logger.error(f"Failed to process photo {photo.filename}: {e}")
                continue
        
        # Check if any faces were detected
        if total_faces == 0:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No faces detected in any of the uploaded photos. Please upload clear photos containing faces."
            )
        
        # Add photo records to database
        for photo_record in photo_records:
            db.add(photo_record)
        
        # Commit transaction
        db.commit()
        
        # Save vector database
        vector_db.save_index()
        
        # Log upload event
        log_upload(db, current_user.user_id, person_id, total_faces)
        
        return UploadResponse(
            person_id=person_id,
            faces_detected=total_faces,
            embeddings_stored=total_faces,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.delete("/{person_id}", status_code=status.HTTP_200_OK)
async def delete_missing_person(
    person_id: uuid.UUID,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a missing person record.
    
    Requires admin authentication.
    """
    try:
        # Find person
        person = db.query(DBMissingPerson).filter(
            DBMissingPerson.person_id == person_id
        ).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Delete from vector database
        vector_db.delete_embeddings(str(person_id))
        
        # Delete photo files
        person_dir = os.path.join(settings.UPLOAD_DIR, str(person_id))
        if os.path.exists(person_dir):
            import shutil
            shutil.rmtree(person_dir)
        
        # Delete from database (cascades to photos)
        db.delete(person)
        db.commit()
        
        # Save vector database
        vector_db.save_index()
        
        # Log deletion
        log_deletion(db, current_user.user_id, person_id)
        
        return {"status": "success", "message": "Person deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("", response_model=List[MissingPerson])
async def list_missing_persons(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all missing persons.
    
    Requires admin authentication.
    """
    persons = db.query(DBMissingPerson).offset(skip).limit(limit).all()
    
    result = []
    for person in persons:
        photo_urls = [photo.photo_url for photo in person.photos]
        result.append(MissingPerson(
            person_id=person.person_id,
            name=person.name,
            description=person.description,
            last_seen_location=person.last_seen_location,
            date_reported=person.date_reported,
            contact_info=person.contact_info,
            photo_urls=photo_urls,
            created_at=person.created_at,
            updated_at=person.updated_at
        ))
    
    return result
