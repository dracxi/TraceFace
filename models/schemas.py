"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime
from typing import List, Optional


class FaceDetection(BaseModel):
    """Face detection result."""
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    landmarks: List[List[float]] = Field(..., description="5 facial landmarks")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class FaceEmbedding(BaseModel):
    """Face embedding with detection info."""
    embedding: List[float] = Field(..., description="512-dimensional embedding vector")
    detection: FaceDetection
    
    @validator('embedding')
    def validate_embedding_dimension(cls, v):
        if len(v) != 512:
            raise ValueError('Embedding must be 512-dimensional')
        return v


class MissingPersonBase(BaseModel):
    """Base missing person model."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    last_seen_location: Optional[str] = Field(None, max_length=500)
    date_reported: datetime
    contact_info: str = Field(..., min_length=1, max_length=500)


class MissingPersonCreate(MissingPersonBase):
    """Model for creating a missing person record."""
    pass


class MissingPerson(MissingPersonBase):
    """Complete missing person model."""
    person_id: UUID4
    photo_urls: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchMatch(BaseModel):
    """Search match result."""
    person_id: UUID4
    name: str
    similarity_score: float = Field(..., ge=-1.0, le=1.0)
    photo_url: str
    last_seen_location: Optional[str]
    date_reported: datetime
    contact_info: str


class SearchRequest(BaseModel):
    """Search request parameters."""
    threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")


class SearchResponse(BaseModel):
    """Search response."""
    matches: List[SearchMatch]
    query_face_detected: bool
    processing_time_ms: int


class UploadRequest(MissingPersonBase):
    """Upload request model."""
    pass


class UploadResponse(BaseModel):
    """Upload response."""
    person_id: UUID4
    faces_detected: int
    embeddings_stored: int
    status: str = "success"


class LoginRequest(BaseModel):
    """Login request."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class AdminUser(BaseModel):
    """Admin user model."""
    user_id: UUID4
    username: str
    email: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """Model for creating admin user."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    email: Optional[str] = Field(None, max_length=255)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: dict
    timestamp: datetime
    request_id: str
