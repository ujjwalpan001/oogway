import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models import Session, Message
from app.schemas import SessionCreate, SessionOut, SessionWithMessages, MessageOut, ArtifactOut, CitationOut
from app.config import settings
from app.logging_config import get_logger

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = get_logger(__name__)


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(
        id=str(uuid.uuid4()),
        title=body.title,
        model_provider=settings.llm_provider,
        model_name=settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("session_created", session_id=session.id)
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(desc(Session.updated_at)))
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    session_dict = {
        "id": session.id,
        "title": session.title,
        "model_provider": session.model_provider,
        "model_name": session.model_name,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                artifact=ArtifactOut(
                    id=m.artifact.id,
                    artifact_type=m.artifact.artifact_type,
                    title=m.artifact.title,
                    content=m.artifact.content,
                    created_at=m.artifact.created_at,
                ) if m.artifact else None,
                citations=[
                    CitationOut(
                        id=c.id,
                        episode_title=c.episode_title,
                        guest=c.guest,
                        chunk_text=c.chunk_text,
                        youtube_url=c.youtube_url,
                        relevance_score=c.relevance_score,
                    ) for c in m.citations
                ],
            )
            for m in messages
        ],
    }
    return session_dict


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    logger.info("session_deleted", session_id=session_id)
