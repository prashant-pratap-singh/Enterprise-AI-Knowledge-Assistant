"""Conversation repository for chat sessions and message history."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Data operations for Conversations and Messages."""

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create and persist a new conversation session."""
        conv = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            workspace_id=workspace_id,
            title=title.strip(),
        )
        return await self.create(conv)

    async def get_with_messages(
        self,
        conversation_id: uuid.UUID,
    ) -> Optional[Conversation]:
        """Fetch conversation with its messages eager loaded."""
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return result.scalars().first()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Conversation]:
        """List conversations in a workspace, optionally filtered by user."""
        query = select(Conversation).where(Conversation.workspace_id == workspace_id)
        if user_id:
            query = query.where(Conversation.user_id == user_id)

        query = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        title: str,
    ) -> Optional[Conversation]:
        """Update conversation title."""
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(title=title.strip())
        )
        await self.session.flush()
        return await self.get(conversation_id)

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        retrieval_metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Append a message to a conversation."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role.lower(),
            content=content,
            citations=citations or [],
            retrieval_metadata=retrieval_metadata or {},
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> List[Message]:
        """Retrieve recent messages for a conversation ordered chronologically."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
