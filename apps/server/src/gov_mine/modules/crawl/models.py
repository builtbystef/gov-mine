"""The web as fetched, and the runs that fetch it. Nothing here carries an institution but the
run: ownership starts at sources and documents."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string

# A host's wait between two requests when its robots.txt asks for none longer.
DEFAULT_CRAWL_DELAY_MS = 1000


class CrawlPolicy(StrEnum):
    CRAWL = "crawl"
    FILES_ONLY = "files_only"
    PLATFORM = "platform"
    BLOCKED = "blocked"


class FetchOutcome(StrEnum):
    FETCHED = "fetched"
    NOT_MODIFIED = "not_modified"
    UNCHANGED = "unchanged"
    BLOCKED_ROBOTS = "blocked_robots"
    SKIPPED_SCOPE = "skipped_scope"
    SKIPPED_TYPE = "skipped_type"
    SKIPPED_SIZE = "skipped_size"
    SKIPPED_DEPTH = "skipped_depth"
    FAILED_HTTP = "failed_http"
    FAILED_TIMEOUT = "failed_timeout"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Domain(UUIDPrimaryKey, CreatedAt, Base):
    """A host. Scope, politeness and the robots cache are per host."""

    __tablename__ = "domains"

    name: Mapped[str] = mapped_column(String(253), unique=True)
    crawl_policy: Mapped[CrawlPolicy] = checked_string(CrawlPolicy, "crawl_policy")
    robots_txt: Mapped[str | None] = mapped_column(Text)
    robots_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    crawl_delay_ms: Mapped[int] = mapped_column(default=DEFAULT_CRAWL_DELAY_MS)
    # When the crawler last sent the host a request, of any kind: the next waits
    # `crawl_delay_ms` from here.
    last_request_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Webpage(UUIDPrimaryKey, CreatedAt, Base):
    """One row per URL ever seen. Everything else about a URL's state is its latest fetch or
    snapshot; `etag` and `last_modified` are here because a 304 writes no snapshot."""

    __tablename__ = "webpages"

    url: Mapped[str] = mapped_column(String(2048), unique=True)
    domain_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("domains.id"), index=True)
    discovered_from_webpage_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("webpages.id"))
    etag: Mapped[str | None] = mapped_column(String(1024))
    last_modified: Mapped[str | None] = mapped_column(String(100))
    missing_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CrawlRun(UUIDPrimaryKey, CreatedAt, Base):
    """One run over one institution. `settings` records what the run was asked to do (trigger,
    full or incremental, ...), so two runs can be compared; its counts are queries."""

    __tablename__ = "crawl_runs"

    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    status: Mapped[RunStatus] = checked_string(RunStatus, "status", default=RunStatus.QUEUED)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class Fetch(UUIDPrimaryKey, CreatedAt, Base):
    """One attempt at a URL in a run, including attempts never sent, so the request count is a
    count of rows."""

    __tablename__ = "fetches"
    __table_args__ = (Index("ix_fetches_crawl_run_id_outcome", "crawl_run_id", "outcome"),)

    crawl_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crawl_runs.id"))
    webpage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("webpages.id"), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # None when no request was sent.
    duration_ms: Mapped[int | None]
    outcome: Mapped[FetchOutcome] = checked_string(FetchOutcome, "outcome")
    http_status: Mapped[int | None]
    # Why a URL was refused or failed.
    reason: Mapped[str | None] = mapped_column(Text)
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("webpage_snapshots.id"))
