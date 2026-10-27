from datetime import timedelta
from enum import StrEnum

from sqlalchemy import Interval, String
from sqlalchemy.orm import Mapped, mapped_column

from gov_mine.db.base import Base, CreatedAt, UUIDPrimaryKey
from gov_mine.db.checked_strings import checked_string

DEFAULT_FULL_CRAWL_INTERVAL = timedelta(days=30)


class InstitutionType(StrEnum):
    STATE = "state"
    STATE_AGENCY = "state_agency"
    COUNTY = "county"
    CITY = "city"
    POLICE_AGENCY = "police_agency"
    FIRE_DEPARTMENT = "fire_department"
    SPECIAL_DISTRICT = "special_district"
    K12_DISTRICT = "k12_district"
    HIGHER_EDUCATION = "higher_education"
    MUNICIPAL_AGENCY = "municipal_agency"


class Institution(UUIDPrimaryKey, CreatedAt, Base):
    """A public body and its website. `website_url` is the trusted starting point and the
    crawl's scope prefix; the location columns are for display only."""

    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(300))
    institution_type: Mapped[InstitutionType] = checked_string(InstitutionType, "institution_type")
    website_url: Mapped[str] = mapped_column(String(2048))
    country_code: Mapped[str | None] = mapped_column(String(2))
    state: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    # How often the whole site is crawled again from the homepage.
    full_crawl_interval: Mapped[timedelta] = mapped_column(
        Interval, default=DEFAULT_FULL_CRAWL_INTERVAL
    )
    # The scheduler creates no runs for a paused institution.
    paused: Mapped[bool] = mapped_column(default=False)
