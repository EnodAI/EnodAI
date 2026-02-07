"""
Authentication endpoints
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.auth import (
    create_access_token,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password,
    get_current_user,
    User
)

router = APIRouter()
basic_auth = HTTPBasic()

# Mock user database (replace with real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "scopes": ["read:analysis", "write:analysis", "admin"]
    },
    "user": {
        "username": "user",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "scopes": ["read:analysis"]
    }
}


@router.post("/token", response_model=Token)
async def login(credentials: HTTPBasicCredentials = Depends(basic_auth)):
    """
    Login endpoint to get JWT token

    Use Basic Authentication with username and password:
    - Username: admin
    - Password: secret

    Returns JWT token for subsequent requests
    """
    user = fake_users_db.get(credentials.username)

    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "scopes": user["scopes"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    Requires JWT token in Authorization header:
    Authorization: Bearer <token>
    """
    return {
        "username": current_user.username,
        "scopes": current_user.scopes,
        "authenticated": True
    }
