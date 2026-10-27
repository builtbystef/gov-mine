"""Classifying each webpage once, on its first snapshot with text, as `none`, `listing:<type>` or
`document:<type>` with Jev, and turning the answer into a source or a document of the run's
institution."""

import logging
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser
from sqlalchemy import Select, String, func, select
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.orm import aliased

from gov_mine.integrations.ai import PROVIDER, jev
from gov_mine.integrations.parser.html import HTML_MEDIA_TYPES
from gov_mine.jobs import registry
from gov_mine.jobs.tasks import defer
from gov_mine.modules.classify.models import Classification, Document, Source
from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import Fetch, Webpage
from gov_mine.modules.ingest import service as ingest
from gov_mine.modules.ingest.models import TextStatus, WebpageSnapshot
from gov_mine.modules.institutions.models import DocumentType, Institution
from gov_mine.modules.ledger import service as ledger
from gov_mine.modules.ledger.models import AIPurpose
from gov_mine.shared.exceptions import NotFoundError

if TYPE_CHECKING:
    import httpx
    from sqlalchemy.ext.asyncio import AsyncSession

    from gov_mine.config import Settings
    from gov_mine.integrations.storage import ObjectStore

logger = logging.getLogger(__name__)

CLASSIFY_TASK = "classify.page"
CLASSIFIER = "jev:classify@1"
QUESTION = "page_type"
NONE = "none"

# Above this TypeSafe runs a slower, less accurate long-context mode (decision 36).
MAX_REQUEST_BYTES = 32_000
MAX_LINKS = 100
MAX_LINKS_BYTES = 6_000
MAX_LINK_TEXT = 200
MAX_TITLE = 500
PARAGRAPH = "\n\n"

INSTRUCTIONS = (
    "This is one page or file from a public institution's website. Is it a listing page that"
    " links to many items of one type (a source to revisit), a single item of one type (a"
    " document to keep), or neither?"
)

# What one item of each type is, and what many are called. `project_material` is assigned by a
# project's extraction, never by the classifier.
_TYPES: dict[DocumentType, tuple[str, str]] = {
    DocumentType.PURCHASE_ORDER: ("a purchase order the institution issued", "purchase orders"),
    DocumentType.MEETING_MINUTES: (
        "the agenda or minutes of one meeting of a board, council or committee",
        "meeting agendas and minutes",
    ),
    DocumentType.BUDGET: ("a budget or financial statement for one period", "budgets"),
    DocumentType.PROCUREMENT_GUIDELINES: (
        "the institution's procurement policy, guidelines or how to sell to it",
        "procurement policies and guidelines",
    ),
    DocumentType.YOUTUBE: ("one video recording, such as a meeting video", "videos"),
    DocumentType.RFP: (
        "one tender, RFP, RFQ or other call for bids, or its award",
        "tenders and calls for bids",
    ),
    DocumentType.GRANTS: ("one grant or funding program or award", "grants or funding programs"),
    DocumentType.PRESS_RELEASES: (
        "one news release, announcement or news story",
        "news releases and announcements",
    ),
    DocumentType.PROJECTS: (
        "one project: a development, construction or initiative the institution runs",
        "projects",
    ),
    DocumentType.ANNUAL_REPORT: ("an annual report", "annual reports"),
    DocumentType.STRATEGIC_PLAN: ("a strategic, corporate or master plan", "strategic plans"),
    DocumentType.STAFF_DIRECTORY: (
        (
            "a page of the people who work for or govern the institution (staff directory, team,"
            " leadership, board or council) with their roles or contact details"
        ),
        "staff directory, team or board pages",
    ),
}

CRAWL_INTERVALS: dict[DocumentType, timedelta] = {
    DocumentType.PRESS_RELEASES: timedelta(days=1),
    DocumentType.PROJECTS: timedelta(days=7),
    DocumentType.RFP: timedelta(days=7),
}
DEFAULT_CRAWL_INTERVAL = timedelta(days=30)


def criteria() -> dict[str, str]:
    """The 25 choices, each with its description."""
    choices = {NONE: "Neither a listing nor a document of any type below."}
    for document_type, (one, many) in _TYPES.items():
        choices[f"listing:{document_type}"] = (
            f"A page whose main content is a list of links to {many}, such as an index,"
            " archive or search results."
        )
        choices[f"document:{document_type}"] = f"A single item: {one}."
    return choices


def crawl_interval(document_type: DocumentType) -> timedelta:
    return CRAWL_INTERVALS.get(document_type, DEFAULT_CRAWL_INTERVAL)


def _json_bytes(value: object) -> int:
    return len(jev.encode_body({"v": value})) - len('{"v":}')


def _fit_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    kept: list[dict[str, str]] = []
    for link in links[:MAX_LINKS]:
        if _json_bytes([*kept, link]) > MAX_LINKS_BYTES:
            break
        kept.append(link)
    return kept


def _fit_text(pages: list[str], room: int) -> str:
    """The markdown from the top, cut at a paragraph boundary to fit `room` encoded bytes; a
    first paragraph longer than that is cut where it fills it."""
    paragraphs = [p for p in PARAGRAPH.join(pages).split(PARAGRAPH) if p.strip()]
    kept: list[str] = []
    used = 0
    separator = _json_bytes(PARAGRAPH)
    for paragraph in paragraphs:
        cost = _json_bytes(paragraph) + (separator if kept else 0)
        if used + cost > room:
            break
        kept.append(paragraph)
        used += cost
    if kept or not paragraphs:
        return PARAGRAPH.join(kept)
    head = paragraphs[0]
    while head and _json_bytes(head) > room:
        head = head[: max(0, len(head) * room // _json_bytes(head) - 1)]
    return head


def build_request(
    model: str, url: str, title: str | None, links: list[dict[str, str]], pages: list[str]
) -> dict[str, Any]:
    """The Decisions API body: URL, title, at most 100 links within 6,000 bytes, and the
    markdown from the top filling the rest, the whole under 32,000 bytes."""
    body: dict[str, Any] = {
        "model": model,
        "state": {
            "url": url,
            "title": (title or "")[:MAX_TITLE],
            "links": _fit_links(links),
            "text": "",
        },
        "questions": {
            QUESTION: {"type": "choice", "instructions": INSTRUCTIONS, "criteria": criteria()}
        },
    }
    room = MAX_REQUEST_BYTES - 1 - len(jev.encode_body(body))
    body["state"]["text"] = _fit_text(pages, room)
    return body


def read_html(data: bytes, page_url: str) -> tuple[str | None, list[dict[str, str]]]:
    """An HTML page's `<title>` and its `<a href>` links with their text, each href once."""
    tree = LexborHTMLParser(data.decode(errors="replace"))
    node = tree.css_first("title")
    title = node.text(strip=True) if node is not None else None
    links: dict[str, str] = {}
    for anchor in tree.css("a[href]"):
        href = urljoin(page_url, anchor.attributes.get("href") or "")
        if urlsplit(href).scheme in {"http", "https"} and href not in links:
            links[href] = " ".join(anchor.text().split())[:MAX_LINK_TEXT]
    return title or None, [{"text": text, "href": href} for href, text in links.items()]


def _file_title(url: str) -> str | None:
    return urlsplit(url).path.rstrip("/").rpartition("/")[2] or None


async def _classified(session: AsyncSession, webpage_id: uuid.UUID) -> bool:
    """Whether the webpage has a classification or is a document already."""
    classified = await session.scalar(
        select(Classification.id)
        .join(WebpageSnapshot, WebpageSnapshot.id == Classification.snapshot_id)
        .where(WebpageSnapshot.webpage_id == webpage_id, Classification.classifier == CLASSIFIER)
        .limit(1)
    )
    document = await session.scalar(select(Document.id).where(Document.webpage_id == webpage_id))
    return classified is not None or document is not None


async def queue_page(
    session: AsyncSession, settings: Settings, run_id: uuid.UUID, snapshot_id: uuid.UUID
) -> bool:
    """Queue `classify.page` for a snapshot with text whose webpage is not classified yet and
    is not a document. Nothing is queued when no model key is configured."""
    if settings.openrouter_api_key is None:
        return False
    snapshot = await ingest.get_snapshot(session, snapshot_id)
    if snapshot.text_status is not TextStatus.READY or await _classified(
        session, snapshot.webpage_id
    ):
        return False
    await defer(
        session, registry.tasks[CLASSIFY_TASK], run_id=str(run_id), snapshot_id=str(snapshot_id)
    )
    return True


async def _pages(session: AsyncSession, store: ObjectStore, snapshot_id: uuid.UUID) -> list[str]:
    """The snapshot's markdown pages from the first, as many as the request can hold."""
    pages: list[str] = []
    size = 0
    while size < MAX_REQUEST_BYTES:
        try:
            page = await ingest.text(session, store, snapshot_id, len(pages) + 1)
        except NotFoundError:
            break
        pages.append(page)
        size += len(page.encode())
    return pages


async def _decide(
    http: httpx.AsyncClient, api_key: str, body: dict[str, Any]
) -> jev.Decision | str:
    """Jev's decision, tried twice; the error message when both fail."""
    try:
        return await jev.decide(http, api_key, body, QUESTION)
    except jev.JevError as exc:
        logger.warning("Jev failed, trying again: %s", exc)
    try:
        return await jev.decide(http, api_key, body, QUESTION)
    except jev.JevError as exc:
        return str(exc)


async def classify_page(  # noqa: PLR0913 - the job's inputs and what it works with
    session: AsyncSession,
    store: ObjectStore,
    http: httpx.AsyncClient,
    settings: Settings,
    *,
    run_id: uuid.UUID,
    snapshot_id: uuid.UUID,
) -> Classification | None:
    """Classify the snapshot's webpage unless it already is: one `classifications` row, one
    `ai_calls` row for the paid call, and a source or document for the run's institution. A
    provider error is retried once, then recorded on the row. None when nothing was done."""
    if settings.openrouter_api_key is None:
        return None
    snapshot = await ingest.get_snapshot(session, snapshot_id)
    if await _classified(session, snapshot.webpage_id):
        return None
    model = settings.classify_model
    ledger.price_of(model)
    run = await crawl.get_run(session, run_id)
    webpage = await session.get_one(Webpage, snapshot.webpage_id)
    title: str | None
    links: list[dict[str, str]] = []
    if snapshot.media_type.split(";")[0].strip() in HTML_MEDIA_TYPES:
        data, _ = await ingest.raw_bytes(session, store, snapshot.id)
        title, links = read_html(data, webpage.url)
    else:
        title = _file_title(webpage.url)
    body = build_request(
        model, webpage.url, title, links, await _pages(session, store, snapshot.id)
    )
    decided = await _decide(http, settings.openrouter_api_key.get_secret_value(), body)

    values: dict[str, Any] = {"crawl_run_id": run_id, "snapshot_id": snapshot.id}
    if isinstance(decided, str):
        values |= {"error": decided}
    else:
        values |= {
            "choice": decided.choice,
            "confidence": decided.probability,
            "raw_output": decided.answer,
        }
    classification_id = await session.scalar(
        insert(Classification)
        .values(id=uuid.uuid7(), classifier=CLASSIFIER, **values)
        .on_conflict_do_nothing()
        .returning(Classification.id)
    )
    if classification_id is None:
        return None
    if not isinstance(decided, str):
        await ledger.record(
            session,
            run_id=run_id,
            purpose=AIPurpose.CLASSIFY,
            provider=PROVIDER,
            model=model,
            usage=decided.usage,
            classification_id=classification_id,
        )
        await _apply(
            session,
            choice=decided.choice,
            institution_id=run.institution_id,
            webpage=webpage,
            snapshot=snapshot,
            title=title,
        )
    return await session.get_one(Classification, classification_id)


async def _apply(  # noqa: PLR0913
    session: AsyncSession,
    *,
    choice: str,
    institution_id: uuid.UUID,
    webpage: Webpage,
    snapshot: WebpageSnapshot,
    title: str | None,
) -> None:
    """A listing becomes a source, a document a document; `none` neither."""
    kind, _, type_name = choice.partition(":")
    if kind == "listing":
        document_type = DocumentType(type_name)
        fetched_at = await session.scalar(
            select(func.min(Fetch.requested_at)).where(Fetch.snapshot_id == snapshot.id)
        )
        interval = crawl_interval(document_type)
        await session.execute(
            insert(Source)
            .values(
                id=uuid.uuid7(),
                institution_id=institution_id,
                webpage_id=webpage.id,
                document_type=document_type,
                crawl_interval=interval,
                next_crawl_at=(fetched_at or snapshot.created_at) + interval,
            )
            .on_conflict_do_nothing()
        )
    elif kind == "document":
        source_id = None
        if webpage.discovered_from_webpage_id is not None:
            source_id = await session.scalar(
                select(Source.id)
                .where(
                    Source.webpage_id == webpage.discovered_from_webpage_id,
                    Source.institution_id == institution_id,
                )
                .order_by(Source.created_at)
                .limit(1)
            )
        await session.execute(
            insert(Document)
            .values(
                id=uuid.uuid7(),
                institution_id=institution_id,
                source_id=source_id,
                webpage_id=webpage.id,
                document_type=DocumentType(type_name),
                title=title,
                document_date=snapshot.stated_date,
            )
            .on_conflict_do_nothing()
        )


def _found_in(run_id: uuid.UUID) -> Select[uuid.UUID]:
    """The webpages classified in the run."""
    return (
        select(WebpageSnapshot.webpage_id)
        .join(Classification, Classification.snapshot_id == WebpageSnapshot.id)
        .where(Classification.crawl_run_id == run_id)
    )


async def list_run_sources(
    session: AsyncSession, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[tuple[Source, str]], int]:
    """The sources the run found, with their listing page's URL, next crawl first."""
    await crawl.get_run(session, run_id)
    found = Source.webpage_id.in_(_found_in(run_id))
    total = await session.scalar(select(func.count()).select_from(Source).where(found)) or 0
    rows = await session.execute(
        select(Source, Webpage.url)
        .join(Webpage, Webpage.id == Source.webpage_id)
        .where(found)
        .order_by(Source.next_crawl_at, Source.id)
        .limit(limit)
        .offset(offset)
    )
    return [(source, url) for source, url in rows], total


async def count_run_documents(session: AsyncSession, run_id: uuid.UUID) -> dict[DocumentType, int]:
    """How many documents the run found, by type."""
    await crawl.get_run(session, run_id)
    rows = await session.execute(
        select(Document.document_type, func.count())
        .where(Document.webpage_id.in_(_found_in(run_id)))
        .group_by(Document.document_type)
        .order_by(Document.document_type)
    )
    return {row[0]: row[1] for row in rows}


async def list_run_documents(
    session: AsyncSession, run_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[tuple[Document, str]], int]:
    """The documents the run created (their webpage was classified in it) or gave a new version
    (a snapshot written in it), with their webpage's URL, by type then title."""
    await crawl.get_run(session, run_id)
    written = select(Fetch.webpage_id).where(
        Fetch.crawl_run_id == run_id, Fetch.snapshot_id.is_not(None)
    )
    found = Document.webpage_id.in_(_found_in(run_id)) | Document.webpage_id.in_(written)
    total = await session.scalar(select(func.count()).select_from(Document).where(found)) or 0
    rows = await session.execute(
        select(Document, Webpage.url)
        .join(Webpage, Webpage.id == Document.webpage_id)
        .where(found)
        .order_by(Document.document_type, Document.title, Document.id)
        .limit(limit)
        .offset(offset)
    )
    return [(document, url) for document, url in rows.tuples()], total


async def list_documents(  # noqa: PLR0913 - the page and its three filters
    session: AsyncSession,
    *,
    institution_id: uuid.UUID | None,
    document_type: DocumentType | None,
    since: date | None,
    limit: int,
    offset: int,
) -> tuple[list[tuple[Document, str]], int]:
    """Documents with their webpage's URL, newest dated first, undated last. `since` keeps
    those dated on or after that day."""
    where = []
    if institution_id is not None:
        where.append(Document.institution_id == institution_id)
    if document_type is not None:
        where.append(Document.document_type == document_type)
    if since is not None:
        where.append(Document.document_date >= datetime.combine(since, time(), UTC))
    total = await session.scalar(select(func.count()).select_from(Document).where(*where)) or 0
    rows = await session.execute(
        select(Document, Webpage.url)
        .join(Webpage, Webpage.id == Document.webpage_id)
        .where(*where)
        .order_by(
            Document.document_date.desc().nulls_last(), Document.created_at.desc(), Document.id
        )
        .limit(limit)
        .offset(offset)
    )
    return [(document, url) for document, url in rows], total


async def read_document(
    session: AsyncSession, document_id: uuid.UUID
) -> tuple[Document, str, str, Document | None, list[WebpageSnapshot]]:
    """The document, its URL, its institution's name, its parent document if any, and its
    versions: the first snapshot of each distinct text, newest first (a snapshot without text
    counts as its own)."""
    parent = aliased(Document)
    row = (
        await session.execute(
            select(Document, Webpage.url, Institution.name, parent)
            .join(Webpage, Webpage.id == Document.webpage_id)
            .join(Institution, Institution.id == Document.institution_id)
            .outerjoin(parent, parent.id == Document.parent_document_id)
            .where(Document.id == document_id)
        )
    ).one_or_none()
    if row is None:
        raise NotFoundError(f"Document {document_id} not found")
    document, url, institution, parent_document = row
    text = func.coalesce(WebpageSnapshot.text_hash, func.cast(WebpageSnapshot.id, String))
    first = (
        select(WebpageSnapshot.id)
        .where(WebpageSnapshot.webpage_id == document.webpage_id)
        .ext(distinct_on(text))
        .order_by(text, WebpageSnapshot.created_at, WebpageSnapshot.id)
    )
    versions = await session.scalars(
        select(WebpageSnapshot)
        .where(WebpageSnapshot.id.in_(first))
        .order_by(WebpageSnapshot.created_at.desc(), WebpageSnapshot.id.desc())
    )
    return document, url, institution, parent_document, list(versions)


__all__ = [
    "CLASSIFIER",
    "CLASSIFY_TASK",
    "MAX_REQUEST_BYTES",
    "build_request",
    "classify_page",
    "count_run_documents",
    "crawl_interval",
    "criteria",
    "list_documents",
    "list_run_documents",
    "list_run_sources",
    "queue_page",
    "read_document",
    "read_html",
]
