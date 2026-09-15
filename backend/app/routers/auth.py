import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut, SettingsUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    result = await db.execute(select(User).where(User.session_token == token))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")
        
    return user

@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    session_token = secrets.token_hex(32)
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        session_token=session_token
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=86400*30, samesite="lax")
    # For simplicity, returning session token in body so frontend can easily send Bearer
    return user

@router.post("/login", response_model=UserOut)
async def login(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    session_token = secrets.token_hex(32)
    user.session_token = session_token
    await db.commit()
    
    response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=86400*30, samesite="lax")
    return user

@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.session_token = None
    await db.commit()
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user

@router.put("/settings", response_model=UserOut)
async def update_settings(
    settings: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if settings.claude_api_key is not None:
        user.claude_api_key = settings.claude_api_key
    if settings.openai_api_key is not None:
        user.openai_api_key = settings.openai_api_key
        
    await db.commit()
    await db.refresh(user)
    return user
