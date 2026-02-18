"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, ForeignKey, Index
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
    last_seen_location = Column(String(500))
    date_reported = Column(TIMESTAMP, nullable=False)
    contact_info = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    photos = relationship("PersonPhoto", back_populates="person", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="person")
    
    __table_args__ = (
        Index('idx_missing_persons_date', 'date_reported'),
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
    event_type = Column(String(50), nullable=False)  # 'search', 'upload', 'delete'
    user_id = Column(UUID(as_uuid=True), ForeignKey('admin_users.user_id'))
    person_id = Column(UUID(as_uuid=True), ForeignKey('missing_persons.person_id'))
    result_count = Column(Integer)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    ip_address = Column(INET)
    
    # Relationships
    user = relationship("AdminUser", back_populates="audit_logs")
    person = relationship("MissingPerson", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_event_type', 'event_type'),
    )
