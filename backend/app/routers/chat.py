import uuid
import json
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models import Session, Message, Artifact, Citation
from app.schemas import ChatRequest
from app.agent.router import get_agent
from app.agent.skills.ship30 import run_ship30_skill
from app.agent.skills.artifact_gen import run_artifact_skill
from app.rag.retriever import retriever
from app.rag.citations import format_context_for_prompt, format_citations_for_display
from app.config import settings
from app.logging_config import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

CHAT_SYSTEM = """You are The Lenny Growth Assistant, an expert AI trained exclusively on Lenny's Podcast transcripts.

Your job is to answer product management and growth questions with grounded, specific advice drawn from the transcript excerpts provided.

Rules you must follow:
1. Base your answers ONLY on the provided transcript excerpts. Do not invent claims.
2. When you use information from a source, naturally mention the guest's name and episode in your response.
3. If the transcripts don't contain enough information to answer the question, say so clearly. Do not hallucinate.
4. Keep answers concise and actionable. Use bullet points for lists, bold for key terms.
5. When a user's question is a follow-up, use conversation history to understand context.
6. You can detect when the user wants an artifact or essay and suggest using those features.

Available skills the user can trigger:
- "Ship 30 essay" — turns your answer into a formatted ~1,250-word Ship 30 for 30 essay
- "Generate artifact" or "create HTML report" — generates a rendered document in the artifact viewer"""


def _detect_skill(message: str, explicit_skill: str | None) -> str | None:
    if explicit_skill:
        return explicit_skill
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in ["ship 30", "ship30", "essay", "write an essay"]):
        return "ship30"
    if any(kw in msg_lower for kw in ["artifact", "html report", "generate a report", "create a document", "markdown doc"]):
        artifact_type = "html" if "html" in msg_lower else "markdown"
        return f"artifact:{artifact_type}"
    return None


async def _build_history(session_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages[-10:]]


async def _save_message(db: AsyncSession, session_id: str, role: str, content: str) -> Message:
    msg = Message(id=str(uuid.uuid4()), session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.flush()
    return msg


async def _save_artifact(db: AsyncSession, message_id: str, artifact_type: str, title: str, content: str) -> Artifact:
    art = Artifact(
        id=str(uuid.uuid4()),
        message_id=message_id,
        artifact_type=artifact_type,
        title=title,
        content=content,
    )
    db.add(art)
    return art


async def _save_citations(db: AsyncSession, message_id: str, citation_data: list[dict]):
    for c in citation_data:
        cit = Citation(
            id=str(uuid.uuid4()),
            message_id=message_id,
            episode_title=c.get("episode_title", ""),
            guest=c.get("guest", ""),
            chunk_text=c.get("chunk_text", ""),
            youtube_url=c.get("youtube_url", ""),
            relevance_score=c.get("relevance_score", 0),
        )
        db.add(cit)


async def _update_session_title(db: AsyncSession, session_id: str, first_message: str):
    title = first_message[:60] + "..." if len(first_message) > 60 else first_message
    await db.execute(
        update(Session).where(Session.id == session_id).values(title=title)
    )


@router.post("/stream")
async def chat_stream(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, session_id=body.session_id)

    result = await db.execute(select(Session).where(Session.id == body.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = await _build_history(body.session_id, db)
    if not history:
        await _update_session_title(db, body.session_id, body.message)

    chunks = retriever.retrieve(body.message)
    context = format_context_for_prompt(chunks)
    citations = format_citations_for_display(chunks)

    skill = _detect_skill(body.message, body.skill)
    logger.info("chat_request", skill=skill, chunks_retrieved=len(chunks))

    user_msg = await _save_message(db, body.session_id, "user", body.message)
    await db.commit()

    async def event_stream():
        full_response = []
        artifact_data = None

        try:
            if skill == "ship30":
                yield f"data: {json.dumps({'type': 'skill_start', 'skill': 'ship30'})}\n\n"
                essay = await run_ship30_skill(body.message, context)
                full_response.append(essay)
                for token in essay:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                artifact_data = ("ship30", "Ship 30 Essay", essay)

            elif skill and skill.startswith("artifact:"):
                artifact_type = skill.split(":")[1] if ":" in skill else "markdown"
                yield f"data: {json.dumps({'type': 'skill_start', 'skill': 'artifact'})}\n\n"
                title, art_content = await run_artifact_skill(body.message, artifact_type, context)
                summary = f"I've generated a {artifact_type.upper()} artifact: **{title}**. You can see it rendered in the panel on the right."
                full_response.append(summary)
                for token in summary:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                artifact_data = (artifact_type, title, art_content)

            else:
                augmented_messages = history + [
                    {
                        "role": "user",
                        "content": f"{body.message}\n\n<transcript_sources>\n{context}\n</transcript_sources>",
                    }
                ]
                agent = get_agent()
                async for token in agent.stream(augmented_messages, CHAT_SYSTEM):
                    full_response.append(token)
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            assistant_content = "".join(full_response)

            async with db.begin():
                asst_msg = await _save_message(db, body.session_id, "assistant", assistant_content)
                if artifact_data:
                    await _save_artifact(db, asst_msg.id, artifact_data[0], artifact_data[1], artifact_data[2])
                await _save_citations(db, asst_msg.id, citations)

            done_payload = {
                "type": "done",
                "message_id": asst_msg.id,
                "citations": citations,
                "artifact": {
                    "type": artifact_data[0],
                    "title": artifact_data[1],
                    "content": artifact_data[2],
                } if artifact_data else None,
            }
            yield f"data: {json.dumps(done_payload)}\n\n"

        except RuntimeError as exc:
            err = {"type": "error", "message": str(exc)}
            yield f"data: {json.dumps(err)}\n\n"
        except Exception as exc:
            logger.error("chat_stream_failed", error=str(exc))
            err = {"type": "error", "message": "Something went wrong. Check the server logs."}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
