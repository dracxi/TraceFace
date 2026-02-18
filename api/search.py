"""Face search API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import time
import logging
import uuid

from database.connection import get_db
from database.models import MissingPerson as DBMissingPerson, PersonPhoto
from models.schemas import SearchResponse, SearchMatch
from services.image_processing import preprocess_image
from services.face_pipeline import face_pipeline
from services.vector_database import vector_db
from services.audit_logging import log_search
from config import settings

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SearchResponse)
async def search_missing_person(
    image: UploadFile = File(...),
    threshold: Optional[float] = Form(None),
    max_results: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Search for missing persons by face image.
    
    Public endpoint - no authentication required.
    """
    start_time = time.time()
    
    try:
        # Set defaults
        if threshold is None:
            threshold = settings.DEFAULT_MATCH_THRESHOLD
        if max_results is None:
            max_results = settings.DEFAULT_MAX_RESULTS
        
        # Validate parameters
        if not 0.0 <= threshold <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Threshold must be between 0.0 and 1.0"
            )
        
        if not 1 <= max_results <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_results must be between 1 and 100"
            )
        
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image (JPEG, PNG, WebP)"
            )
        
        # Read and preprocess image
        image_bytes = await image.read()
        
        # Check file size
        if len(image_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        try:
            image_array = preprocess_image(image_bytes)
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to process image. Please upload a valid image file."
            )
        
        # Detect faces and generate embeddings
        try:
            results = face_pipeline.process_image(image_array)
            
            if not results:
                # No face detected
                processing_time = int((time.time() - start_time) * 1000)
                
                # Log search
                log_search(db, None, 0)
                
                return SearchResponse(
                    matches=[],
                    query_face_detected=False,
                    processing_time_ms=processing_time
                )
            
            # Use first detected face for search
            query_embedding = results[0]['embedding']
            
        except Exception as e:
            logger.error(f"Face processing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to detect face in image. Please upload a clear photo containing a face."
            )
        
        # Search vector database
        try:
            search_results = vector_db.search(
                query_embedding,
                k=max_results,
                threshold=threshold
            )
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed. Please try again."
            )
        
        # Retrieve person details from database
        matches = []
        seen_persons = set()
        
        for person_id_str, photo_id_str, similarity_score in search_results:
            # Skip if we already have this person (multiple photos)
            if person_id_str in seen_persons:
                continue
            seen_persons.add(person_id_str)
            
            # Convert string to UUID object
            try:
                person_uuid = uuid.UUID(person_id_str)
            except ValueError:
                logger.error(f"Invalid UUID format: {person_id_str}")
                continue
            
            # Get person from database
            person = db.query(DBMissingPerson).filter(
                DBMissingPerson.person_id == person_uuid
            ).first()
            
            if not person:
                continue
            
            # Get photo URL
            photo = db.query(PersonPhoto).filter(
                PersonPhoto.person_id == person_uuid
            ).first()
            
            photo_url = photo.photo_url if photo else ""
            
            # Create match
            match = SearchMatch(
                person_id=person.person_id,
                name=person.name,
                similarity_score=similarity_score,
                photo_url=photo_url,
                last_seen_location=person.last_seen_location,
                date_reported=person.date_reported,
                contact_info=person.contact_info
            )
            matches.append(match)
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log search
        log_search(db, None, len(matches))
        
        return SearchResponse(
            matches=matches,
            query_face_detected=True,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
