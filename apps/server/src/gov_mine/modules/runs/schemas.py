import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from gov_mine.modules.crawl.models import FetchOutcome, RunStatus

RunTrigger = Literal["cli", "dashboard", "scheduled"]
RunMode = Literal["full", "incremental"]


class RunSettings(BaseModel):
    """What a run was asked to do, kept on the run so two runs can be compared."""

    trigger: RunTrigger
    # A full run crawls the whole site from the homepage; an incremental one, the due sources.
    mode: RunMode


class RunOutput(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    institution_name: str
    status: RunStatus
    settings: RunSettings
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    created_at: datetime


class SnapshotSummary(BaseModel):
    id: uuid.UUID
    content_hash: str
    media_type: str
    size_bytes: int


class FetchOutput(BaseModel):
    """One attempt at a URL. `snapshot` is the copy it wrote, if it wrote one."""

    id: uuid.UUID
    webpage_id: uuid.UUID
    url: str
    requested_at: datetime
    duration_ms: int | None
    outcome: FetchOutcome
    http_status: int | None
    reason: str | None
    snapshot: SnapshotSummary | None
