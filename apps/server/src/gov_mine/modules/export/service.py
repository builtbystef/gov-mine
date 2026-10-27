"""Exporting what we know for another service: a JSON Lines file per record type, one for
documents and one for citations, and a manifest. Only documents within the window, and their
records, are written; each line comes from the database alone, so exporting twice from the same
database gives the same lines."""

import asyncio
import json
import uuid
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from gov_mine.db.base import utcnow
from gov_mine.modules.classify.models import Document
from gov_mine.modules.crawl.models import CrawlRun, RunStatus, Webpage
from gov_mine.modules.extract import service as extract
from gov_mine.modules.extract.models import Citation, Extraction, Record, RecordType
from gov_mine.modules.institutions.models import Institution

DOCUMENTS_FILE = "documents.jsonl"
CITATIONS_FILE = "citations.jsonl"
MANIFEST_FILE = "manifest.json"


def records_file(record_type: str) -> str:
    return f"{record_type}s.jsonl"


def _line(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, default=str)


def _iso(value: datetime | date | None) -> str | None:
    return None if value is None else value.isoformat()


async def export(
    session: AsyncSession, out: Path, *, since: date | None = None, now: datetime | None = None
) -> dict[str, Any]:
    """Write the export files into `out` (created if missing) and return the manifest. The
    cutoff is `since`, or today minus five years: a document whose latest stated date is before
    it is left out with its records; an undated one is kept."""
    now = now or utcnow()
    cutoff = since or extract.window_cutoff(now.date())
    parent = aliased(Document)
    parent_page = aliased(Webpage)
    documents = (
        await session.execute(
            select(Document, Webpage.url, Institution.name, parent_page.url)
            .join(Webpage, Webpage.id == Document.webpage_id)
            .join(Institution, Institution.id == Document.institution_id)
            .outerjoin(parent, parent.id == Document.parent_document_id)
            .outerjoin(parent_page, parent_page.id == parent.webpage_id)
            .order_by(Webpage.url, Document.id)
        )
    ).all()
    current = await extract.list_current_records(session)
    records_of: dict[uuid.UUID, list[Any]] = defaultdict(list)
    for row in current:
        records_of[row.document_id].append(row)

    kept = {}
    lines: dict[str, list[str]] = {records_file(t): [] for t in RecordType}
    lines[DOCUMENTS_FILE] = []
    lines[CITATIONS_FILE] = []
    for document, url, institution, parent_url in documents:
        dated = extract.latest_date(
            document.document_date, (row.data for row in records_of[document.id])
        )
        if dated is not None and dated < cutoff:
            continue
        kept[document.id] = (url, institution, document.institution_id)
        lines[DOCUMENTS_FILE].append(
            _line(
                {
                    "id": str(document.id),
                    "institution": institution,
                    "url": url,
                    "document_type": document.document_type,
                    "title": document.title,
                    "document_date": _iso(dated),
                    "parent": parent_url,
                    "first_seen_at": _iso(document.created_at),
                }
            )
        )

    exported = [row for row in current if row.document_id in kept]
    citations: dict[uuid.UUID, list[Citation]] = defaultdict(list)
    for citation in await session.scalars(
        select(Citation)
        .where(Citation.record_snapshot_id.in_([row.record_snapshot_id for row in exported]))
        .order_by(Citation.field, Citation.id)
    ):
        citations[citation.record_snapshot_id].append(citation)
    first_seen = dict(
        (
            await session.execute(
                select(Record.id, Record.created_at).where(
                    Record.id.in_([row.record_id for row in exported])
                )
            )
        ).all()
    )
    exported.sort(key=lambda row: (kept[row.document_id][0], row.key, row.record_id))
    for row in exported:
        url, institution, _ = kept[row.document_id]
        cited = [
            {
                "field": c.field,
                "url": url,
                "page": c.page,
                "excerpt": c.excerpt,
                "verified": c.verified,
            }
            for c in citations[row.record_snapshot_id]
        ]
        lines[records_file(row.record_type)].append(
            _line(
                {
                    "id": str(row.record_id),
                    "institution": institution,
                    "document": url,
                    "key": row.key,
                    **row.data,
                    "citations": cited,
                    "first_seen_at": _iso(first_seen[row.record_id]),
                    "last_changed_at": _iso(row.extracted_at),
                }
            )
        )
        lines[CITATIONS_FILE] += [
            _line({"record": str(row.record_id), "record_type": row.record_type, **c})
            for c in cited
        ]

    institution_ids = {institution_id for _, _, institution_id in kept.values()}
    latest_runs = (
        await session.execute(
            select(CrawlRun.id, CrawlRun.finished_at, Institution.name)
            .ext(distinct_on(CrawlRun.institution_id))
            .join(Institution, Institution.id == CrawlRun.institution_id)
            .where(
                CrawlRun.institution_id.in_(institution_ids),
                CrawlRun.status == RunStatus.FINISHED,
            )
            .order_by(CrawlRun.institution_id, CrawlRun.finished_at.desc().nulls_last())
        )
    ).all()
    extractors = await session.scalars(
        select(Extraction.extractor)
        .distinct()
        .where(Extraction.id.in_([row.extraction_id for row in exported]))
        .order_by(Extraction.extractor)
    )

    manifest = {
        "exported_at": _iso(now),
        "cutoff": _iso(cutoff),
        "runs": [
            {"institution": name, "run": str(run_id), "finished_at": _iso(finished_at)}
            for run_id, finished_at, name in sorted(latest_runs, key=lambda run: run[2])
        ],
        "extractors": list(extractors),
        "files": {name: len(file_lines) for name, file_lines in sorted(lines.items())},
    }
    await asyncio.to_thread(_write, out, lines, manifest)
    return manifest


def _write(out: Path, lines: dict[str, list[str]], manifest: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, file_lines in lines.items():
        (out / name).write_text("".join(f"{line}\n" for line in file_lines), encoding="utf-8")
    (out / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


__all__ = ["export", "records_file"]
