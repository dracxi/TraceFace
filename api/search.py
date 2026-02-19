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
                age=person.age,
                gender=person.gender,
                similarity_score=similarity_score,
                photo_url=photo_url,
                last_seen_location=person.last_seen_location,
                date_reported=person.date_reported,
                contact_info=person.contact_info,
                status=person.status
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



@router.get("/text", response_model=dict)
async def text_search_missing_persons(
    q: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    gender: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = 'date_reported',
    sort_order: str = 'desc',
    db: Session = Depends(get_db)
):
    """
    Text-based search for missing persons with filters.
    
    Public endpoint - no authentication required.
    
    Args:
        q: Name or partial name search
        age_min: Minimum age filter
        age_max: Maximum age filter
        gender: Gender filter
        location: Last seen location filter (partial match)
        status: Status filter ('missing' or 'traced')
        page: Page number (starts at 1)
        page_size: Results per page (1-100)
        sort_by: Sort field ('name', 'date_reported', 'status')
        sort_order: Sort order ('asc' or 'desc')
    """
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
    
    if sort_by not in ['name', 'date_reported', 'status']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_by must be 'name', 'date_reported', or 'status'"
        )
    
    if sort_order not in ['asc', 'desc']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'"
        )
    
    if status and status not in ['missing', 'traced']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be 'missing' or 'traced'"
        )
    
    try:
        # Build query
        query = db.query(DBMissingPerson)
        
        # Apply filters
        if q:
            # Case-insensitive partial name search
            query = query.filter(DBMissingPerson.name.ilike(f'%{q}%'))
        
        if age_min is not None:
            query = query.filter(DBMissingPerson.age >= age_min)
        
        if age_max is not None:
            query = query.filter(DBMissingPerson.age <= age_max)
        
        if gender:
            query = query.filter(DBMissingPerson.gender.ilike(gender))
        
        if location:
            # Case-insensitive partial location search
            query = query.filter(DBMissingPerson.last_seen_location.ilike(f'%{location}%'))
        
        if status:
            query = query.filter(DBMissingPerson.status == status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(DBMissingPerson, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        persons = query.all()
        
        # Build results
        results = []
        for person in persons:
            # Get photo URLs
            photos = db.query(PersonPhoto).filter(
                PersonPhoto.person_id == person.person_id
            ).all()
            photo_urls = [photo.photo_url for photo in photos]
            
            result = {
                "person_id": str(person.person_id),
                "name": person.name,
                "age": person.age,
                "gender": person.gender,
                "description": person.description,
                "photo_urls": photo_urls,
                "last_seen_location": person.last_seen_location,
                "date_reported": person.date_reported.isoformat(),
                "status": person.status,
                "traced_date": person.traced_date.isoformat() if person.traced_date else None,
                "traced_notes": person.traced_notes,
                "contact_info": person.contact_info,
                "created_at": person.created_at.isoformat(),
                "updated_at": person.updated_at.isoformat()
            }
            results.append(result)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
