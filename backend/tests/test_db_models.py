"""Unit tests for SQLAlchemy ORM models, relations, and repositories."""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import (
    User,
    Organization,
    Membership,
    Workspace,
    Document,
    DocumentChunk,
    Conversation,
    Message,
    EvaluationRun,
)
from app.repositories import (
    UserRepository,
    OrganizationRepository,
    WorkspaceRepository,
    DocumentRepository,
    ConversationRepository,
)

from sqlalchemy import event
from sqlalchemy.engine import Engine

# Async SQLite engine for fast, isolated in-memory unit tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def test_session():
    """Provides an isolated in-memory database session for each test."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_user_creation_and_lookup(test_session: AsyncSession):
    """Verify user creation and email lookup via UserRepository."""
    user_repo = UserRepository(test_session)
    user = await user_repo.create_user(
        email="test@enterprise.com",
        hashed_password="argon2_hashed_secret",
        full_name="Alice Engineer",
    )
    assert user.id is not None
    assert user.email == "test@enterprise.com"

    fetched = await user_repo.get_by_email("test@enterprise.com")
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.full_name == "Alice Engineer"


@pytest.mark.asyncio
async def test_organization_and_membership_rbac(test_session: AsyncSession):
    """Verify organization creation, member addition, and role retrieval."""
    user_repo = UserRepository(test_session)
    org_repo = OrganizationRepository(test_session)

    user = await user_repo.create_user(
        email="admin@enterprise.com",
        hashed_password="hashed_password",
        full_name="Admin User",
    )
    org = await org_repo.create_organization(name="Acme Corp")
    membership = await org_repo.add_member(
        organization_id=org.id,
        user_id=user.id,
        role="ADMIN",
    )

    assert membership.role == "ADMIN"
    assert membership.organization_id == org.id

    fetched_membership = await org_repo.get_membership(org.id, user.id)
    assert fetched_membership is not None
    assert fetched_membership.role == "ADMIN"

    user_orgs = await org_repo.list_user_organizations(user.id)
    assert len(user_orgs) == 1
    assert user_orgs[0].name == "Acme Corp"


@pytest.mark.asyncio
async def test_workspace_creation(test_session: AsyncSession):
    """Verify workspace creation scoped to an organization."""
    org_repo = OrganizationRepository(test_session)
    ws_repo = WorkspaceRepository(test_session)

    org = await org_repo.create_organization(name="Engineering Org")
    ws = await ws_repo.create_workspace(
        organization_id=org.id,
        name="Platform Documentation",
        description="Internal technical knowledge base",
    )

    assert ws.id is not None
    assert ws.organization_id == org.id
    assert ws.name == "Platform Documentation"

    listed = await ws_repo.list_for_organization(org.id)
    assert len(listed) == 1
    assert listed[0].id == ws.id


@pytest.mark.asyncio
async def test_document_and_chunks_lifecycle(test_session: AsyncSession):
    """Verify document upload record, chunk insertion, and duplicate detection."""
    user_repo = UserRepository(test_session)
    org_repo = OrganizationRepository(test_session)
    ws_repo = WorkspaceRepository(test_session)
    doc_repo = DocumentRepository(test_session)

    user = await user_repo.create_user("editor@corp.com", "hash", "Editor User")
    org = await org_repo.create_organization("Tech Corp")
    ws = await ws_repo.create_workspace(org.id, "HR Knowledge")

    # 1. Create document
    checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    doc = await doc_repo.create_document(
        organization_id=org.id,
        workspace_id=ws.id,
        uploaded_by=user.id,
        filename="employee_handbook.pdf",
        file_type="pdf",
        file_size=204800,
        storage_path="/storage/docs/handbook.pdf",
        checksum=checksum,
    )
    assert doc.status == "uploaded"

    # 2. Check duplicate detection
    dup = await doc_repo.get_by_checksum(org.id, ws.id, checksum)
    assert dup is not None
    assert dup.id == doc.id

    # 3. Add chunks
    chunks_data = [
        {
            "document_id": doc.id,
            "organization_id": org.id,
            "workspace_id": ws.id,
            "chunk_index": 0,
            "content": "Section 1: Annual Leave. Employees receive 20 days paid leave per annum.",
            "metadata": {"page_number": 1, "filename": "employee_handbook.pdf"},
            "vector_id": "vec-chunk-0",
        },
        {
            "document_id": doc.id,
            "organization_id": org.id,
            "workspace_id": ws.id,
            "chunk_index": 1,
            "content": "Section 2: Parental Leave. Eligible after 12 months continuous service.",
            "metadata": {"page_number": 2, "filename": "employee_handbook.pdf"},
            "vector_id": "vec-chunk-1",
        },
    ]
    created_chunks = await doc_repo.add_chunks(chunks_data)
    assert len(created_chunks) == 2

    # 4. Update status to indexed
    updated_doc = await doc_repo.update_status(
        document_id=doc.id,
        status="indexed",
        page_count=2,
        chunk_count=2,
    )
    assert updated_doc.status == "indexed"
    assert updated_doc.chunk_count == 2

    # 5. Lexical search test
    search_results = await doc_repo.search_chunks_lexical(org.id, ws.id, "Annual Leave")
    assert len(search_results) >= 1
    assert "Annual Leave" in search_results[0].content


@pytest.mark.asyncio
async def test_conversation_and_citations(test_session: AsyncSession):
    """Verify chat session persistence, message ordering, and citation metadata."""
    user_repo = UserRepository(test_session)
    org_repo = OrganizationRepository(test_session)
    ws_repo = WorkspaceRepository(test_session)
    conv_repo = ConversationRepository(test_session)

    user = await user_repo.create_user("asker@corp.com", "hash", "Asker User")
    org = await org_repo.create_organization("Consulting Inc")
    ws = await ws_repo.create_workspace(org.id, "Policies")

    # Create conversation
    conv = await conv_repo.create_conversation(user.id, ws.id, "Leave Inquiries")
    assert conv.id is not None

    # Add user message
    user_msg = await conv_repo.add_message(
        conversation_id=conv.id,
        role="user",
        content="What is the company annual leave policy?",
    )
    assert user_msg.role == "user"

    # Add assistant response with citations
    citations = [
        {
            "citation_id": 1,
            "document_id": str(uuid.uuid4()),
            "filename": "Leave_Policy.pdf",
            "page_number": 5,
            "excerpt": "Employees are eligible for 20 paid leave days annually.",
        }
    ]
    assistant_msg = await conv_repo.add_message(
        conversation_id=conv.id,
        role="assistant",
        content="Employees are eligible for 20 days of paid leave annually. [1]",
        citations=citations,
        retrieval_metadata={"confidence": 0.94, "latency_ms": 320},
    )
    assert assistant_msg.citations is not None
    assert len(assistant_msg.citations) == 1
    assert assistant_msg.citations[0]["page_number"] == 5

    messages = await conv_repo.get_messages(conv.id)
    assert len(messages) == 2
    assert messages[0].id == user_msg.id
    assert messages[1].id == assistant_msg.id


@pytest.mark.asyncio
async def test_cascade_deletion(test_session: AsyncSession):
    """Verify that deleting an organization or document cascades correctly."""
    org_repo = OrganizationRepository(test_session)
    ws_repo = WorkspaceRepository(test_session)
    doc_repo = DocumentRepository(test_session)

    org = await org_repo.create_organization("Ephemeral Corp")
    ws = await ws_repo.create_workspace(org.id, "Temp WS")
    doc = await doc_repo.create_document(
        organization_id=org.id,
        workspace_id=ws.id,
        uploaded_by=None,
        filename="temp.txt",
        file_type="txt",
        file_size=100,
        storage_path="/tmp/temp.txt",
        checksum="1234567890abcdef",
    )
    await doc_repo.add_chunks([
        {
            "document_id": doc.id,
            "organization_id": org.id,
            "workspace_id": ws.id,
            "chunk_index": 0,
            "content": "temporary content",
        }
    ])

    chunks_before = await doc_repo.get_chunks_for_document(doc.id)
    assert len(chunks_before) == 1

    # Delete document directly
    deleted = await doc_repo.delete(doc.id)
    assert deleted is True

    # Chunks must be deleted by cascade
    chunks_after = await doc_repo.get_chunks_for_document(doc.id)
    assert len(chunks_after) == 0
