"""Document and Chunk repository for ingestion persistence and lexical search."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update, delete, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Data operations for Document entities and DocumentChunk records."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def create_document(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        uploaded_by: Optional[uuid.UUID],
        filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        checksum: str,
        status: str = "uploaded",
    ) -> Document:
        """Create a new document record."""
        doc = Document(
            id=uuid.uuid4(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            filename=filename,
            file_type=file_type.lower(),
            file_size=file_size,
            storage_path=storage_path,
            checksum=checksum,
            status=status,
        )
        return await self.create(doc)

    async def get_by_checksum(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        checksum: str,
    ) -> Optional[Document]:
        """Detect existing duplicate document within the same organization and workspace."""
        result = await self.session.execute(
            select(Document).where(
                Document.organization_id == organization_id,
                Document.workspace_id == workspace_id,
                Document.checksum == checksum,
                Document.status != "failed",
            )
        )
        return result.scalars().first()

    async def list_by_workspace(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Document]:
        """List documents in a workspace with optional status filter."""
        query = select(Document).where(
            Document.organization_id == organization_id,
            Document.workspace_id == workspace_id,
        )
        if status_filter:
            query = query.where(Document.status == status_filter)

        query = query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
    ) -> Optional[Document]:
        """Update processing status and indexing stats of a document."""
        values: Dict[str, Any] = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if page_count is not None:
            values["page_count"] = page_count
        if chunk_count is not None:
            values["chunk_count"] = chunk_count

        await self.session.execute(
            update(Document).where(Document.id == document_id).values(**values)
        )
        await self.session.flush()
        return await self.get(document_id)

    async def add_chunks(
        self,
        chunks_data: List[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """Bulk insert document chunks with metadata."""
        chunks = []
        for item in chunks_data:
            chunk = DocumentChunk(
                id=item.get("id") or uuid.uuid4(),
                document_id=item["document_id"],
                organization_id=item["organization_id"],
                workspace_id=item["workspace_id"],
                chunk_index=item["chunk_index"],
                content=item["content"],
                metadata_json=item.get("metadata", {}),
                vector_id=item.get("vector_id"),
            )
            chunks.append(chunk)

        self.session.add_all(chunks)
        await self.session.flush()
        return chunks

    async def get_chunks_for_document(
        self,
        document_id: uuid.UUID,
    ) -> List[DocumentChunk]:
        """Fetch all chunks belonging to a document ordered by index."""
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def search_chunks_lexical(
        self,
        organization_id: uuid.UUID,
        workspace_id: uuid.UUID,
        query_text: str,
        limit: int = 20,
    ) -> List[DocumentChunk]:
        """
        Lexical full-text search over chunks within the workspace.
        Supports both PostgreSQL tsvector match and substring/ilike fallback.
        """
        # Multi-term ILIKE fallback that works in SQLite tests and PostgreSQL
        terms = [t.strip() for t in query_text.split() if len(t.strip()) > 2]
        if not terms:
            terms = [query_text.strip()]

        conditions = [DocumentChunk.content.ilike(f"%{term}%") for term in terms]
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.organization_id == organization_id,
                DocumentChunk.workspace_id == workspace_id,
                or_(*conditions),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
