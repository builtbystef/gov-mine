import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from gov_mine.modules.crawl.models import FetchOutcome, RunStatus
from gov_mine.modules.ingest.models import TextStatus
from gov_mine.modules.ledger.models import AIPurpose

RunTrigger = Literal["cli", "dashboard", "scheduled"]
RunMode = Literal["full", "incremental"]


class RunSettings(BaseModel):
    """What a run was asked to do, kept on the run so two runs can be compared."""

    trigger: RunTrigger
    # A full run crawls the whole site from the homepage; an incremental one, the due sources.
    mode: RunMode
    # At most this many requests are sent (`--limit`, a development knob); refusals don't count.
    limit: int | None = None
    # The largest file the run downloads, in bytes; None on runs from before it was recorded.
    max_file_bytes: int | None = None
    # The extractor per record type (`model:<record_type>@<version>`); None on older runs.
    extractors: dict[str, str] | None = None
    # The replay server's address on a replay run, which sends it every request; None on a live
    # run.
    replay: str | None = None
    # The five-year window: documents dated before this day (the run's creation day minus five
    # years) are kept and not extracted; None on older runs.
    cutoff: date | None = None


class RunCreate(BaseModel):
    """A run started from the dashboard; only full runs exist until sources do."""

    institution_id: uuid.UUID
    mode: Literal["full"] = "full"


class RunCounts(BaseModel):
    """What the run's fetch log and ledger say so far. `skipped` is every `skipped_*` outcome,
    `failed` every `failed_*`, `not_modified` includes `unchanged`."""

    fetched: int
    not_modified: int
    skipped: int
    blocked: int
    failed: int
    snapshots: int
    cost: Decimal


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
    # From start to finish, or to now while it runs; None before it starts.
    elapsed_seconds: float | None
    counts: RunCounts


class SnapshotSummary(BaseModel):
    id: uuid.UUID
    content_hash: str
    media_type: str
    size_bytes: int


class FetchOutput(BaseModel):
    """One attempt at a URL. `snapshot` is the copy it wrote, if it wrote one."""

    id: uuid.UUID
    crawl_run_id: uuid.UUID
    webpage_id: uuid.UUID
    url: str
    requested_at: datetime
    duration_ms: int | None
    outcome: FetchOutcome
    http_status: int | None
    reason: str | None
    snapshot: SnapshotSummary | None


class SnapshotOutput(BaseModel):
    """A stored copy of a webpage. Its text is at `GET /snapshots/{id}/text/{page}` once
    `text_status` is `ready`, and its bytes at `GET /snapshots/{id}/bytes`."""

    id: uuid.UUID
    webpage_id: uuid.UUID
    url: str
    content_hash: str
    media_type: str
    size_bytes: int
    text_status: TextStatus
    text_error: str | None
    parser: str | None
    stated_date: datetime | None
    created_at: datetime


class WebpageOutput(BaseModel):
    """A URL the crawler has seen, with every fetch of it (newest first) and its snapshots."""

    id: uuid.UUID
    url: str
    domain: str
    missing_since: datetime | None
    fetches: list[FetchOutput]
    snapshots: list[SnapshotOutput]


class OutcomeCount(BaseModel):
    """The run's `fetches` rows with one outcome; `requests` are those that sent a request."""

    outcome: FetchOutcome
    fetches: int
    requests: int


class PurposeCalls(BaseModel):
    """Paid calls for one purpose. `estimated_cost` is USD from the price list; `reported_cost`
    is what OpenRouter said it charged, summed over the calls it reported a cost for."""

    purpose: AIPurpose
    calls: int
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal
    reported_cost: Decimal | None


class ProviderCost(BaseModel):
    """Like `PurposeCalls`, per provider. `calls_without_reported_cost` are left out of
    `reported_cost`."""

    provider: str
    calls: int
    estimated_cost: Decimal
    reported_cost: Decimal | None
    calls_without_reported_cost: int


class RemovedDocument(BaseModel):
    """A document whose webpage first returned 404 in the run."""

    document_id: uuid.UUID
    url: str
    title: str | None
    missing_since: datetime


class RecordCounts(BaseModel):
    created: int
    amended: int


class RunReport(BaseModel):
    """A run's numbers, each a query over the logs. `elapsed_seconds` is null until the run has
    finished. `records`, `unextracted_document_ids` and `fallback_reasons_by_source` are null
    while extraction (023) does not exist."""

    run: RunOutput
    elapsed_seconds: float | None
    requests_sent: int
    fetches_by_outcome: list[OutcomeCount]
    snapshots_written: int
    # Snapshots written in the run whose parsing has ended, and of those, the failed ones.
    files_processed: int
    files_failed: int
    files_parsing: int
    documents_new: int
    documents_changed: int
    records: RecordCounts | None
    paid_calls: int
    estimated_cost: Decimal
    reported_cost: Decimal | None
    calls_by_purpose: list[PurposeCalls]
    cost_by_provider: list[ProviderCost]
    removed_documents: list[RemovedDocument]
    unextracted_document_ids: list[uuid.UUID] | None
    # Source id to `fallback_reason` to extractions.
    fallback_reasons_by_source: dict[str, dict[str, int]] | None
