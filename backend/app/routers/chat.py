"""Chat session and messaging endpoints."""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from ..database import get_db
from ..schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionResponse,
)
from ..services.chat_service import chat_service
from ..services.llm_service import llm_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    body: ChatSessionCreate | None = None,
    db: Session = Depends(get_db),
):
    payload = body or ChatSessionCreate()
    session = chat_service.create_session(
        db, user_id=payload.user_id, title=payload.title
    )
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    user_id: str = "default",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    sessions = chat_service.get_sessions(db, user_id=user_id, limit=limit)
    results = []
    for s in sessions:
        results.append(
            ChatSessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages),
            )
        )
    return results


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages),
        messages=[
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                jurisdiction_id=m.jurisdiction_id,
                field_name=m.field_name,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def send_message(
    session_id: str,
    body: ChatMessageCreate,
    db: Session = Depends(get_db),
):
    session = chat_service.get_session(db, session_id)
    if not session:
        logger.warning("POST /chat/sessions/%s/messages → 404 session not found", session_id)
        raise HTTPException(404, "Session not found")

    logger.info(
        "POST /chat/sessions/%s/messages — jid=%s field=%s len=%d",
        session_id, body.jurisdiction_id, body.field_name, len(body.content),
    )
    t_llm = time.perf_counter()

    # Persist user message
    user_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="user",
        content=body.content,
        jurisdiction_id=body.jurisdiction_id,
        field_name=body.field_name,
    )

    # Auto-set session title from first message
    if not session.title:
        session.title = body.content[:80]
        db.commit()

    # Get LLM response
    answer = await llm_service.answer_chat_query(
        question=body.content,
        jurisdiction_id=body.jurisdiction_id,
        field_name=body.field_name,
    )
    logger.info(
        "LLM response for session %s in %.2fs (answer_len=%d)",
        session_id, time.perf_counter() - t_llm, len(answer),
    )

    # Persist assistant message
    assistant_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="assistant",
        content=answer,
        jurisdiction_id=body.jurisdiction_id,
        field_name=body.field_name,
    )

    return [
        ChatMessageResponse(
            id=user_msg.id,
            session_id=user_msg.session_id,
            role=user_msg.role,
            content=user_msg.content,
            jurisdiction_id=user_msg.jurisdiction_id,
            field_name=user_msg.field_name,
            created_at=user_msg.created_at,
        ),
        ChatMessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            jurisdiction_id=assistant_msg.jurisdiction_id,
            field_name=assistant_msg.field_name,
            created_at=assistant_msg.created_at,
        ),
    ]


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    deleted = chat_service.delete_session(db, session_id)
    if not deleted:
        logger.warning("DELETE /chat/sessions/%s → 404 not found", session_id)
        raise HTTPException(404, "Session not found")
    logger.info("DELETE /chat/sessions/%s → deleted", session_id)
    return {"status": "deleted", "session_id": session_id}
