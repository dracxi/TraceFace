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
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
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
            age=age,
            gender=gender,
            last_seen_location=last_seen_location,
            date_reported=date_reported_dt,
            contact_info=contact_info,
            status='missing',
            created_by=current_user.user_id,
            updated_by=current_user.user_id
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
            age=person.age,
            gender=person.gender,
            last_seen_location=person.last_seen_location,
            date_reported=person.date_reported,
            contact_info=person.contact_info,
            status=person.status,
            traced_date=person.traced_date,
            traced_notes=person.traced_notes,
            photo_urls=photo_urls,
            created_at=person.created_at,
            updated_at=person.updated_at,
            created_by=person.created_by,
            updated_by=person.updated_by
        ))
    
    return result



@router.get("/dashboard/stats", response_model=dict)
async def get_dashboard_stats(
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics.
    
    Requires admin authentication.
    """
    try:
        from database.models import AuditLog
        from sqlalchemy import func
        from datetime import date
        
        # Get total records
        total_records = db.query(DBMissingPerson).count()
        
        # Get missing count
        missing_count = db.query(DBMissingPerson).filter(
            DBMissingPerson.status == 'missing'
        ).count()
        
        # Get traced count
        traced_count = db.query(DBMissingPerson).filter(
            DBMissingPerson.status == 'traced'
        ).count()
        
        # Get searches today
        today = date.today()
        searches_today = db.query(AuditLog).filter(
            AuditLog.event_type == 'search',
            func.date(AuditLog.timestamp) == today
        ).count()
        
        # Get recent uploads (last 10)
        recent_uploads_query = db.query(DBMissingPerson).order_by(
            DBMissingPerson.created_at.desc()
        ).limit(10).all()
        
        recent_uploads = []
        for person in recent_uploads_query:
            # Get creator name
            creator_name = None
            if person.created_by:
                creator = db.query(AdminUser).filter(
                    AdminUser.user_id == person.created_by
                ).first()
                if creator:
                    creator_name = creator.username
            
            recent_uploads.append({
                "person_id": str(person.person_id),
                "name": person.name,
                "date_reported": person.date_reported.isoformat(),
                "uploaded_at": person.created_at.isoformat(),
                "uploaded_by": creator_name
            })
        
        return {
            "total_records": total_records,
            "missing_count": missing_count,
            "traced_count": traced_count,
            "searches_today": searches_today,
            "recent_uploads": recent_uploads
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.patch("/{person_id}/status", response_model=dict)
async def update_person_status(
    person_id: uuid.UUID,
    status_update: dict,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update person status (mark as traced/found).
    
    Requires admin authentication.
    """
    try:
        from database.models import AuditLog
        
        # Find person
        person = db.query(DBMissingPerson).filter(
            DBMissingPerson.person_id == person_id
        ).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Store old status for audit
        old_status = person.status
        
        # Update status
        new_status = status_update.get('status')
        if new_status not in ['missing', 'traced']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'missing' or 'traced'"
            )
        
        person.status = new_status
        person.updated_by = current_user.user_id
        
        # Update traced fields if status is traced
        if new_status == 'traced':
            traced_date_str = status_update.get('traced_date')
            if traced_date_str:
                try:
                    person.traced_date = datetime.fromisoformat(traced_date_str.replace('Z', '+00:00'))
                except ValueError:
                    person.traced_date = datetime.now()
            else:
                person.traced_date = datetime.now()
            
            person.traced_notes = status_update.get('traced_notes')
        else:
            # Clear traced fields if status changed back to missing
            person.traced_date = None
            person.traced_notes = None
        
        db.commit()
        
        # Create audit log entry
        audit_log = AuditLog(
            event_type='status_change',
            action='update_status',
            user_id=current_user.user_id,
            person_id=person_id,
            admin_name=current_user.username,
            person_name=person.name,
            changes={
                "status": {"old": old_status, "new": new_status},
                "traced_date": person.traced_date.isoformat() if person.traced_date else None,
                "traced_notes": person.traced_notes
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "person_id": str(person_id),
            "status": person.status,
            "traced_date": person.traced_date.isoformat() if person.traced_date else None,
            "updated_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )


@router.put("/{person_id}", response_model=dict)
async def update_person_details(
    person_id: uuid.UUID,
    update_data: dict,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update person details.
    
    Requires admin authentication.
    """
    try:
        from database.models import AuditLog
        
        # Find person
        person = db.query(DBMissingPerson).filter(
            DBMissingPerson.person_id == person_id
        ).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        # Track changes for audit
        changes = {}
        
        # Update fields
        if 'name' in update_data and update_data['name']:
            if person.name != update_data['name']:
                changes['name'] = {"old": person.name, "new": update_data['name']}
                person.name = update_data['name']
        
        if 'age' in update_data:
            if person.age != update_data['age']:
                changes['age'] = {"old": person.age, "new": update_data['age']}
                person.age = update_data['age']
        
        if 'gender' in update_data:
            if person.gender != update_data['gender']:
                changes['gender'] = {"old": person.gender, "new": update_data['gender']}
                person.gender = update_data['gender']
        
        if 'description' in update_data:
            if person.description != update_data['description']:
                changes['description'] = {"old": person.description, "new": update_data['description']}
                person.description = update_data['description']
        
        if 'last_seen_location' in update_data:
            if person.last_seen_location != update_data['last_seen_location']:
                changes['last_seen_location'] = {"old": person.last_seen_location, "new": update_data['last_seen_location']}
                person.last_seen_location = update_data['last_seen_location']
        
        if 'contact_info' in update_data and update_data['contact_info']:
            if person.contact_info != update_data['contact_info']:
                changes['contact_info'] = {"old": person.contact_info, "new": update_data['contact_info']}
                person.contact_info = update_data['contact_info']
        
        person.updated_by = current_user.user_id
        db.commit()
        
        # Create audit log entry if there were changes
        if changes:
            audit_log = AuditLog(
                event_type='update',
                action='update_details',
                user_id=current_user.user_id,
                person_id=person_id,
                admin_name=current_user.username,
                person_name=person.name,
                changes=changes
            )
            db.add(audit_log)
            db.commit()
        
        return {
            "person_id": str(person_id),
            "updated_at": person.updated_at.isoformat(),
            "updated_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update person: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update person: {str(e)}"
        )


@router.get("/export", response_class=None)
async def export_data(
    format: str = 'csv',
    status_filter: Optional[str] = None,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Export missing persons data to CSV or Excel.
    
    Requires admin authentication.
    """
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        # Validate format
        if format not in ['csv', 'excel']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'csv' or 'excel'"
            )
        
        # Build query
        query = db.query(DBMissingPerson)
        
        if status_filter:
            if status_filter not in ['missing', 'traced']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="status must be 'missing' or 'traced'"
                )
            query = query.filter(DBMissingPerson.status == status_filter)
        
        persons = query.all()
        
        if format == 'csv':
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Person ID', 'Name', 'Age', 'Gender', 'Description',
                'Last Seen Location', 'Date Reported', 'Contact Info',
                'Status', 'Traced Date', 'Traced Notes', 'Created At', 'Updated At'
            ])
            
            # Write data
            for person in persons:
                writer.writerow([
                    str(person.person_id),
                    person.name,
                    person.age or '',
                    person.gender or '',
                    person.description or '',
                    person.last_seen_location or '',
                    person.date_reported.isoformat(),
                    person.contact_info,
                    person.status,
                    person.traced_date.isoformat() if person.traced_date else '',
                    person.traced_notes or '',
                    person.created_at.isoformat(),
                    person.updated_at.isoformat()
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=missing_persons_export.csv"}
            )
        
        else:  # excel
            try:
                import openpyxl
                from openpyxl import Workbook
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Excel export requires openpyxl package"
                )
            
            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Missing Persons"
            
            # Write header
            headers = [
                'Person ID', 'Name', 'Age', 'Gender', 'Description',
                'Last Seen Location', 'Date Reported', 'Contact Info',
                'Status', 'Traced Date', 'Traced Notes', 'Created At', 'Updated At'
            ]
            ws.append(headers)
            
            # Write data
            for person in persons:
                ws.append([
                    str(person.person_id),
                    person.name,
                    person.age or '',
                    person.gender or '',
                    person.description or '',
                    person.last_seen_location or '',
                    person.date_reported.isoformat(),
                    person.contact_info,
                    person.status,
                    person.traced_date.isoformat() if person.traced_date else '',
                    person.traced_notes or '',
                    person.created_at.isoformat(),
                    person.updated_at.isoformat()
                ])
            
            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=missing_persons_export.xlsx"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    admin_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with pagination and filtering.
    
    Requires admin authentication.
    """
    try:
        from database.models import AuditLog
        
        # Validate parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if not 1 <= page_size <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size must be between 1 and 100"
            )
        
        # Build query
        query = db.query(AuditLog)
        
        # Apply filters
        if admin_id:
            query = query.filter(AuditLog.user_id == admin_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format"
                )
        
        # Get total count
        total = query.count()
        
        # Apply sorting and pagination
        query = query.order_by(AuditLog.timestamp.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        logs = query.all()
        
        # Format results
        log_entries = []
        for log in logs:
            log_entries.append({
                "log_id": str(log.log_id),
                "timestamp": log.timestamp.isoformat(),
                "admin_id": str(log.user_id) if log.user_id else None,
                "admin_name": log.admin_name,
                "action": log.action,
                "person_id": str(log.person_id) if log.person_id else None,
                "person_name": log.person_name,
                "changes": log.changes
            })
        
        return {
            "logs": log_entries,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )
