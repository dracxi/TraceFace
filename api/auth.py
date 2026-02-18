"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from models.schemas import LoginRequest, TokenResponse, AdminUserCreate, AdminUser as AdminUserSchema
from services.auth import login, create_admin_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AdminUserSchema, status_code=status.HTTP_201_CREATED)
async def register(user_data: AdminUserCreate, db: Session = Depends(get_db)):
    """Register a new admin user."""
    try:
        user = create_admin_user(db, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT token."""
    token_response = login(db, login_data.username, login_data.password)
    
    if token_response is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_response
