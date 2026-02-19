from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./missing_persons.db"
    POSTGRES_DB: str = "missing_persons_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Face Recognition
    FACE_DETECTION_MODEL: str = "retinaface"
    FACE_RECOGNITION_MODEL: str = "arcface"
    FACE_DETECTION_CONFIDENCE: float = 0.9
    EMBEDDING_DIMENSION: int = 512
    
    # Vector Database
    FAISS_INDEX_PATH: str = "./data/faiss_index.bin"
    FAISS_INDEX_TYPE: str = "IndexFlatIP"
    
    # Search
    DEFAULT_MATCH_THRESHOLD: float = 0.6
    DEFAULT_MAX_RESULTS: int = 10
    SEARCH_TIMEOUT_SECONDS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
