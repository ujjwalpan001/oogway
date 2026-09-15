from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class CitationOut(BaseModel):
    id: str
    episode_title: str
    guest: str
    chunk_text: str
    youtube_url: str
    relevance_score: int

    class Config:
        from_attributes = True


class ArtifactOut(BaseModel):
    id: str
    artifact_type: str
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    artifact: ArtifactOut | None = None
    citations: list[CitationOut] = []

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    title: str = "New conversation"


class SessionOut(BaseModel):
    id: str
    title: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionWithMessages(SessionOut):
    messages: list[MessageOut] = []


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=8000)
    skill: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    provider: str
    model: str
    checks: dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    claude_api_key: str | None = None
    openai_api_key: str | None = None

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    claude_api_key: str | None = None
    openai_api_key: str | None = None
