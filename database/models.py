"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database.connection import Base


class MissingPerson(Base):
    """Missing person record."""
    __tablename__ = "missing_persons"
    
    person_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    age = Column(Integer)
    gender = Column(String(20))
    last_seen_location = Column(String(500))
    date_reported = Column(TIMESTAMP, nullable=False)
    contact_info = Column(String(500))
    status = Column(String(20), nullable=False, server_default='missing')
    traced_date = Column(TIMESTAMP)
    traced_notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'))
    updated_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'))
    
    # Relationships
    photos = relationship("PersonPhoto", back_populates="person", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="person")
    creator = relationship("AdminUser", foreign_keys=[created_by])
    updater = relationship("AdminUser", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index('idx_missing_persons_date', 'date_reported'),
        Index('idx_missing_persons_status', 'status'),
    )


class PersonPhoto(Base):
    """Photo associated with a missing person."""
    __tablename__ = "person_photos"
    
    photo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey('missing_persons.person_id', ondelete='CASCADE'), nullable=False)
    photo_url = Column(String(1000), nullable=False)
    embedding_id = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    person = relationship("MissingPerson", back_populates="photos")


class AdminUser(Base):
    """Administrator user."""
    __tablename__ = "admin_users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    """Audit log for tracking system events."""
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)  # 'search', 'upload', 'delete', 'update', 'status_change'
    action = Column(String(50))  # More specific action description
    user_id = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'))
    person_id = Column(UUID(as_uuid=True), ForeignKey('missing_persons.person_id'))
    result_count = Column(Integer)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    ip_address = Column(INET)
    changes = Column(JSON)  # Store change details as JSON
    admin_name = Column(String(100))  # Denormalized for easier querying
    person_name = Column(String(255))  # Denormalized for easier querying
    
    # Relationships
    user = relationship("AdminUser", back_populates="audit_logs")
    person = relationship("MissingPerson", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_event_type', 'event_type'),
    )
