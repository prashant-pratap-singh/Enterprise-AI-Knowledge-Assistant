"""Application-specific exceptions and error handlers."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class EnterpriseRAGException(Exception):
    """Base exception class for Enterprise AI Knowledge Assistant."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundException(EnterpriseRAGException):
    """Raised when a requested resource is not found."""
    pass


class PermissionDeniedException(EnterpriseRAGException):
    """Raised when access to a resource or action is denied."""
    pass


class DocumentIngestionError(EnterpriseRAGException):
    """Raised when parsing, chunking, or indexing a document fails."""
    pass


class InsufficientEvidenceError(EnterpriseRAGException):
    """Raised when retrieved evidence is insufficient to answer the query."""
    pass


class DuplicateEntityException(EnterpriseRAGException):
    """Raised when a unique constraint or deduplication check triggers."""
    pass
