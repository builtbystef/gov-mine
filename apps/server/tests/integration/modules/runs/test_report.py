import uuid
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select

from gov_mine.db.base import utcnow
from gov_mine.modules.classify.models import Classification, Document
from gov_mine.modules.crawl.models import (
    CrawlPolicy,
    CrawlRun,
    Domain,
    Fetch,
    FetchOutcome,
    RunStatus,
    Webpage,
)
from gov_mine.modules.extract.models import (
    Extraction,
    FallbackReason,
    Record,
    RecordSnapshot,
    RecordType,
)
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot
from gov_mine.modules.institutions.models import DocumentType, Institution, InstitutionType
from gov_mine.modules.ledger.models import AICall, AIPurpose
from gov_mine.modules.runs.schemas import RunReport
from gov_mine.modules.runs.service import report_markdown

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from tests.integration.conftest import Database

CLASSIFIER = "jev:classify@1"


def _call(
    run: CrawlRun, purpose: AIPurpose, cost: str, reported: str | None, model: str = "m"
) -> AICall:
    return AICall(
        crawl_run_id=run.id,
        purpose=purpose,
        provider="openrouter",
        model=model,
        input_tokens=100,
        output_tokens=10,
        cost=Decimal(cost),
        reported_cost=None if reported is None else Decimal(reported),
        price_list_version="2026-10-27",
    )


async def _seed(db: Database) -> uuid.UUID:
    """An earlier run that found two documents, then the run reported on: a new document, a
    changed one, a removed one, a failed file, a retry, a refusal, an unchanged page and three
    paid calls (one with no reported cost)."""
    now = utcnow()
    async with db.session() as session:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url="https://createto.ca/",
        )
        domain = Domain(name="createto.ca", crawl_policy=CrawlPolicy.CRAWL)
        session.add_all([institution, domain])
        await session.flush()
        earlier = CrawlRun(
            institution_id=institution.id, settings={"trigger": "cli", "mode": "full"}
        )
        run = CrawlRun(
            institution_id=institution.id,
            status=RunStatus.FINISHED,
            settings={"trigger": "cli", "mode": "full"},
            started_at=now,
            finished_at=now + timedelta(seconds=90),
        )
        pages = {
            name: Webpage(url=f"https://createto.ca/{name}", domain_id=domain.id)
            for name in ("home", "new", "changed", "removed", "file.pdf", "slow", "same", "out")
        }
        session.add_all([earlier, run, *pages.values()])
        await session.flush()

        async def snapshot(name: str, status: TextStatus) -> WebpageSnapshot:
            row = WebpageSnapshot(
                webpage_id=pages[name].id,
                content_hash=uuid.uuid4().hex * 2,
                media_type="text/html",
                size_bytes=10,
                text_status=status,
            )
            session.add(row)
            await session.flush()
            return row

        async def classify(
            in_run: CrawlRun, row: WebpageSnapshot, name: str, *, document: bool
        ) -> None:
            choice = "document:press_releases" if document else "none"
            session.add(
                Classification(
                    crawl_run_id=in_run.id, snapshot_id=row.id, classifier=CLASSIFIER, choice=choice
                )
            )
            if document:
                session.add(
                    Document(
                        institution_id=institution.id,
                        webpage_id=pages[name].id,
                        document_type=DocumentType.PRESS_RELEASES,
                        title=name,
                    )
                )

        for name in ("changed", "removed"):
            await classify(earlier, await snapshot(name, TextStatus.READY), name, document=True)

        def fetch(name: str, seconds: int, outcome: FetchOutcome, **kwargs: object) -> Fetch:
            return Fetch(
                crawl_run_id=run.id,
                webpage_id=pages[name].id,
                requested_at=now + timedelta(seconds=seconds),
                outcome=outcome,
                **kwargs,
            )

        home = await snapshot("home", TextStatus.READY)
        new = await snapshot("new", TextStatus.READY)
        changed = await snapshot("changed", TextStatus.PARSING)
        failed = await snapshot("file.pdf", TextStatus.FAILED)
        await classify(run, home, "home", document=False)
        await classify(run, new, "new", document=True)
        sent = {"duration_ms": 50}
        removed_at = now + timedelta(seconds=5)
        pages["removed"].missing_since = removed_at
        session.add_all(
            [
                fetch(
                    "home", 1, FetchOutcome.FETCHED, snapshot_id=home.id, http_status=200, **sent
                ),
                fetch("new", 2, FetchOutcome.FETCHED, snapshot_id=new.id, http_status=200, **sent),
                fetch("changed", 3, FetchOutcome.FETCHED, snapshot_id=changed.id, **sent),
                fetch("file.pdf", 4, FetchOutcome.FETCHED, snapshot_id=failed.id, **sent),
                fetch("removed", 5, FetchOutcome.FAILED_HTTP, http_status=404, **sent),
                fetch("slow", 6, FetchOutcome.FAILED_TIMEOUT, **sent),
                fetch("same", 7, FetchOutcome.UNCHANGED, http_status=200, **sent),
                fetch("out", 8, FetchOutcome.SKIPPED_SCOPE, reason="outside"),
                _call(run, AIPurpose.CLASSIFY, "0.001", "0.001"),
                _call(run, AIPurpose.CLASSIFY, "0.001", None),
                _call(run, AIPurpose.EXTRACT, "0.010", "0.012"),
                _call(earlier, AIPurpose.CLASSIFY, "5", "5"),
            ]
        )
        await session.commit()
        return run.id


def test_the_report_counts_the_runs_logs(client: TestClient, db: Database):
    run_id = db.run(_seed, db)

    response = client.get(f"/runs/{run_id}/report")

    assert response.status_code == 200
    report = RunReport.model_validate(response.json())
    assert report.elapsed_seconds == 90.0
    assert report.requests_sent == 7
    assert [(o.outcome, o.fetches, o.requests) for o in report.fetches_by_outcome] == [
        ("failed_http", 1, 1),
        ("failed_timeout", 1, 1),
        ("fetched", 4, 4),
        ("skipped_scope", 1, 0),
        ("unchanged", 1, 1),
    ]
    assert (report.snapshots_written, report.files_processed) == (4, 3)
    assert (report.files_failed, report.files_parsing) == (1, 1)
    assert (report.documents_new, report.documents_changed) == (1, 1)
    assert [d.url for d in report.removed_documents] == ["https://createto.ca/removed"]
    assert report.paid_calls == 3
    assert report.estimated_cost == Decimal("0.012")
    assert report.reported_cost == Decimal("0.013")
    assert [(p.purpose, p.calls) for p in report.calls_by_purpose] == [
        ("classify", 2),
        ("extract", 1),
    ]
    (provider,) = report.cost_by_provider
    assert (provider.provider, provider.calls, provider.calls_without_reported_cost) == (
        "openrouter",
        3,
        1,
    )
    assert (provider.estimated_cost, provider.reported_cost) == (Decimal("0.012"), Decimal("0.013"))
    assert report.records is not None
    assert (report.records.created, report.records.amended) == (0, 0)
    assert report.unextracted_document_ids == []
    assert report.fallback_reasons_by_source == {}

    markdown = report_markdown(report)
    assert "| Time taken | 90.0 s |" in markdown
    assert "| Cost, estimated from the price list | $0.012000 |" in markdown
    assert "| Cost, reported by OpenRouter | $0.013000 |" in markdown


async def _seed_extractions(db: Database, run_id: uuid.UUID) -> uuid.UUID:
    """In the run: the new document's record created, the changed one's record (created by the
    earlier run) amended, and the removed one's extraction failed. Returns the removed one."""
    async with db.session() as session:
        run = await session.get_one(CrawlRun, run_id)
        earlier = await session.scalar(select(CrawlRun).where(CrawlRun.id != run_id))
        assert earlier is not None
        documents = {d.title: d for d in await session.scalars(select(Document))}

        async def extraction(
            in_run: CrawlRun, title: str, reason: FallbackReason, error: str | None = None
        ) -> Extraction:
            snapshot = WebpageSnapshot(
                webpage_id=documents[title].webpage_id,
                content_hash=uuid.uuid4().hex * 2,
                media_type="text/html",
                size_bytes=10,
                text_status=TextStatus.READY,
            )
            session.add(snapshot)
            await session.flush()
            row = Extraction(
                crawl_run_id=in_run.id,
                snapshot_id=snapshot.id,
                record_type=RecordType.NEWS_ITEM,
                extractor="model:news_item@1",
                fallback_reason=reason,
                error=error,
            )
            session.add(row)
            await session.flush()
            return row

        async def record(title: str) -> Record:
            row = Record(
                record_type=RecordType.NEWS_ITEM,
                institution_id=run.institution_id,
                document_id=documents[title].id,
                key="",
            )
            session.add(row)
            await session.flush()
            return row

        def state(row: Record, by: Extraction, headline: str) -> RecordSnapshot:
            return RecordSnapshot(
                record_id=row.id, extraction_id=by.id, data={"headline": headline}
            )

        new, changed = await record("new"), await record("changed")
        session.add(
            state(changed, await extraction(earlier, "changed", FallbackReason.NO_RULE), "A")
        )
        await session.flush()
        session.add(state(new, await extraction(run, "new", FallbackReason.NO_RULE), "N"))
        validation = FallbackReason.VALIDATION_FAILED
        session.add(state(changed, await extraction(run, "changed", validation), "B"))
        await extraction(run, "removed", FallbackReason.NO_RULE, error="ModelHTTPError: 502")
        await session.commit()
        return documents["removed"].id


def test_the_report_counts_records_failed_extractions_and_fallback_reasons(
    client: TestClient, db: Database
):
    run_id = db.run(_seed, db)
    removed = db.run(_seed_extractions, db, run_id)

    report = RunReport.model_validate(client.get(f"/runs/{run_id}/report").json())

    assert report.records is not None
    assert (report.records.created, report.records.amended) == (1, 1)
    assert report.unextracted_document_ids == [removed]
    assert report.fallback_reasons_by_source == {"none": {"no_rule": 2, "validation_failed": 1}}
    markdown = report_markdown(report)
    assert "| Records created | 1 |" in markdown
    assert "| Records amended | 1 |" in markdown


def test_an_unknown_run_has_no_report(client: TestClient):
    assert client.get(f"/runs/{uuid.uuid4()}/report").status_code == 404
