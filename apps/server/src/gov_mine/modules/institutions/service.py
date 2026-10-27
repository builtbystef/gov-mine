import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.modules.crawl import service as crawl
from gov_mine.modules.crawl.models import CrawlPolicy
from gov_mine.modules.institutions.models import Institution, InstitutionType
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


__all__ = ["CREATETO_URL", "SeedResult", "get_institution", "seed"]
