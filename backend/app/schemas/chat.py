"""Pydantic schemas for chat endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    content: str
    jurisdiction_id: str | None = None
    field_name: str | None = None


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    jurisdiction_id: str | None = None
    field_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    title: str | None = None
    user_id: str = "default"


class ChatSessionResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    messages: list[ChatMessageResponse] = []

    model_config = {"from_attributes": True}
