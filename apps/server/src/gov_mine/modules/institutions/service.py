import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import CrawlPolicy, CrawlRun
from gov_mine.modules.institutions.models import Institution, InstitutionType
from gov_mine.modules.institutions.schemas import InstitutionInput, InstitutionOutput, LastRun
from gov_mine.shared.exceptions import NotFoundError

CREATETO_URL = "https://createto.ca/"


@dataclass(frozen=True, slots=True)
class SeedResult:
    institution: Institution
    created: bool


async def seed(session: AsyncSession) -> SeedResult:
    """The CreateTO institution, and a `crawl` domain for its host. Adds what is missing and
    changes nothing that is there, so running it again creates nothing new."""
    institution = await session.scalar(
        select(Institution).where(Institution.website_url == CREATETO_URL)
    )
    created = institution is None
    if institution is None:
        institution = Institution(
            name="CreateTO",
            institution_type=InstitutionType.MUNICIPAL_AGENCY,
            website_url=CREATETO_URL,
            country_code="CA",
            state="Ontario",
            city="Toronto",
        )
        session.add(institution)
    await crawl.ensure_domain(session, crawl.host_of(institution.website_url), CrawlPolicy.CRAWL)
    await session.flush()
    return SeedResult(institution=institution, created=created)


async def get_institution(session: AsyncSession, institution_id: uuid.UUID) -> Institution:
    institution = await session.get(Institution, institution_id)
    if institution is None:
        raise NotFoundError(f"No institution {institution_id}")
    return institution


async def _crawl_host(session: AsyncSession, website_url: str) -> None:
    """The website's host becomes a `crawl` domain, whatever its policy was."""
    domain = await crawl.ensure_domain(session, crawl.host_of(website_url), CrawlPolicy.CRAWL)
    domain.crawl_policy = CrawlPolicy.CRAWL


def _apply(institution: Institution, data: InstitutionInput) -> None:
    institution.name = data.name
    institution.institution_type = data.institution_type
    institution.website_url = str(data.website_url)
    institution.country_code = data.country_code.upper() if data.country_code else None
    institution.state = data.state or None
    institution.city = data.city or None


async def create_institution(session: AsyncSession, data: InstitutionInput) -> Institution:
    """The institution, with a `crawl` domain for its website's host."""
    institution = Institution()
    _apply(institution, data)
    session.add(institution)
    await _crawl_host(session, institution.website_url)
    await session.flush()
    return institution


async def update_institution(
    session: AsyncSession, institution_id: uuid.UUID, data: InstitutionInput
) -> Institution:
    """Replaces the institution's fields and sets its website's host to `crawl`."""
    institution = await get_institution(session, institution_id)
    _apply(institution, data)
    await _crawl_host(session, institution.website_url)
    await session.flush()
    return institution


_LAST_RUNS = (
    select(CrawlRun)
    .ext(distinct_on(CrawlRun.institution_id))
    .order_by(CrawlRun.institution_id, CrawlRun.created_at.desc())
)


async def _outputs(
    session: AsyncSession, institutions: list[Institution]
) -> list[InstitutionOutput]:
    """Each institution with its newest run. The next run is due a full-crawl interval after
    the last one started; sources, with their own `next_crawl_at`, do not exist yet."""
    ids = [institution.id for institution in institutions]
    last_runs = {
        run.institution_id: run
        for run in await session.scalars(_LAST_RUNS.where(CrawlRun.institution_id.in_(ids)))
    }
    outputs = []
    for institution in institutions:
        run = last_runs.get(institution.id)
        outputs.append(
            InstitutionOutput(
                id=institution.id,
                name=institution.name,
                institution_type=institution.institution_type,
                website_url=institution.website_url,
                country_code=institution.country_code,
                state=institution.state,
                city=institution.city,
                paused=institution.paused,
                created_at=institution.created_at,
                last_run=None
                if run is None
                else LastRun(id=run.id, status=run.status, created_at=run.created_at),
                next_run_at=None
                if run is None
                else (run.started_at or run.created_at) + institution.full_crawl_interval,
            )
        )
    return outputs


async def list_institutions(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[InstitutionOutput], int]:
    """By name."""
    total = await session.scalar(select(func.count()).select_from(Institution)) or 0
    institutions = list(
        await session.scalars(
            select(Institution)
            .order_by(Institution.name, Institution.id)
            .limit(limit)
            .offset(offset)
        )
    )
    return await _outputs(session, institutions), total


async def read_institution(session: AsyncSession, institution_id: uuid.UUID) -> InstitutionOutput:
    return (await _outputs(session, [await get_institution(session, institution_id)]))[0]


__all__ = [
    "CREATETO_URL",
    "SeedResult",
    "create_institution",
    "get_institution",
    "list_institutions",
    "read_institution",
    "seed",
    "update_institution",
]
