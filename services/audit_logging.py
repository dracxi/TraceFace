"""Audit logging service."""
from sqlalchemy.orm import Session
from database.models import AuditLog
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)


def log_search(
    db: Session,
    user_id: Optional[uuid.UUID],
    result_count: int,
    ip_address: Optional[str] = None
) -> bool:
    """
    Log a search event.
    
    Args:
        db: Database session
        user_id: User ID (if authenticated)
        result_count: Number of results returned
        ip_address: Client IP address
    
    Returns:
        Success status
    """
    try:
        audit_log = AuditLog(
            event_type='search',
            user_id=user_id,
            result_count=result_count,
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        logger.info(f"Logged search event: user={user_id}, results={result_count}")
        return True
    except Exception as e:
        logger.error(f"Failed to log search: {e}")
        db.rollback()
        return False


def log_upload(
    db: Session,
    user_id: uuid.UUID,
    person_id: uuid.UUID,
    face_count: int,
    ip_address: Optional[str] = None
) -> bool:
    """
    Log an upload event.
    
    Args:
        db: Database session
        user_id: Admin user ID
        person_id: Created person ID
        face_count: Number of faces detected
        ip_address: Client IP address
    
    Returns:
        Success status
    """
    try:
        audit_log = AuditLog(
            event_type='upload',
            user_id=user_id,
            person_id=person_id,
            result_count=face_count,
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        logger.info(f"Logged upload event: user={user_id}, person={person_id}, faces={face_count}")
        return True
    except Exception as e:
        logger.error(f"Failed to log upload: {e}")
        db.rollback()
        return False


def log_deletion(
    db: Session,
    user_id: uuid.UUID,
    person_id: uuid.UUID,
    ip_address: Optional[str] = None
) -> bool:
    """
    Log a deletion event.
    
    Args:
        db: Database session
        user_id: Admin user ID
        person_id: Deleted person ID
        ip_address: Client IP address
    
    Returns:
        Success status
    """
    try:
        audit_log = AuditLog(
            event_type='delete',
            user_id=user_id,
            person_id=person_id,
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        logger.info(f"Logged deletion event: user={user_id}, person={person_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to log deletion: {e}")
        db.rollback()
        return False
