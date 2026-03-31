"""Chat session and message persistence service."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.chat import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class ChatService:
    def create_session(
        self, db: Session, user_id: str = "default", title: str | None = None
    ) -> ChatSession:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info("Created chat session %s for user '%s'", session.id, user_id)
        return session

    def get_sessions(
        self, db: Session, user_id: str = "default", limit: int = 50
    ) -> list[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_session(self, db: Session, session_id: str) -> ChatSession | None:
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def add_message(
        self,
        db: Session,
        session_id: str,
        role: str,
        content: str,
        jurisdiction_id: str | None = None,
        field_name: str | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            jurisdiction_id=jurisdiction_id,
            field_name=field_name,
            created_at=datetime.now(timezone.utc),
        )
        db.add(message)
        # Touch session updated_at
        session = self.get_session(db, session_id)
        if session:
            session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(message)
        logger.debug(
            "Message persisted — session=%s role=%s jid=%s field=%s len=%d",
            session_id, role, jurisdiction_id, field_name, len(content),
        )
        return message

    def get_messages(
        self, db: Session, session_id: str, limit: int = 100
    ) -> list[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    def delete_session(self, db: Session, session_id: str) -> bool:
        session = self.get_session(db, session_id)
        if not session:
            logger.warning("delete_session: session %s not found", session_id)
            return False
        db.delete(session)
        db.commit()
        logger.info("Deleted chat session %s", session_id)
        return True


chat_service = ChatService()
