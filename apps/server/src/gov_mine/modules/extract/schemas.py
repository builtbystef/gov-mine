import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from gov_mine.modules.extract.models import RecordType
from gov_mine.modules.institutions.models import DocumentType


class RecordTypeOutput(BaseModel):
    """A record type and its fields, in the order the dashboard shows them."""

    record_type: RecordType
    fields: list[str]


class RecordSummary(BaseModel):
    """A record's current state, with the document it was extracted from."""

    id: uuid.UUID
    record_type: RecordType
    key: str
    data: dict[str, Any]
    extracted_at: datetime
    institution_id: uuid.UUID
    institution_name: str
    document_id: uuid.UUID
    document_title: str | None
    url: str


class CitationOutput(BaseModel):
    """Where a value was read: a page (from 1) of a snapshot of `url`, and the excerpt. `verified`
    is the quote check's verdict."""

    snapshot_id: uuid.UUID
    url: str
    page: int
    excerpt: str
    verified: bool


class FieldOutput(BaseModel):
    field: str
    value: Any
    citation: CitationOutput | None


class FieldChange(BaseModel):
    field: str
    before: Any
    after: Any


class RecordSnapshotOutput(BaseModel):
    """One state of the record, as the fields that changed from the state before it."""

    id: uuid.UUID
    extracted_at: datetime
    extraction_id: uuid.UUID
    snapshot_id: uuid.UUID
    changes: list[FieldChange]


class RecordDetail(BaseModel):
    """A record's current fields, each with its citation, and its history, newest first."""

    id: uuid.UUID
    record_type: RecordType
    key: str
    extracted_at: datetime
    institution_id: uuid.UUID
    institution_name: str
    document_id: uuid.UUID
    document_title: str | None
    document_type: DocumentType
    url: str
    fields: list[FieldOutput]
    history: list[RecordSnapshotOutput]
