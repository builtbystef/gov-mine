import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel

from gov_mine.modules.institutions.models import DocumentType


class SourceOutput(BaseModel):
    """A listing page the run found, revisited every `crawl_interval`."""

    id: uuid.UUID
    webpage_id: uuid.UUID
    url: str
    document_type: DocumentType
    crawl_interval: timedelta
    next_crawl_at: datetime


class DocumentTypeCount(BaseModel):
    document_type: DocumentType
    count: int


class DocumentOutput(BaseModel):
    """A document a run's classifications found."""

    id: uuid.UUID
    webpage_id: uuid.UUID
    url: str
    document_type: DocumentType
    title: str | None
    document_date: datetime | None
    created_at: datetime
