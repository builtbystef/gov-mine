import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, StringConstraints

from gov_mine.modules.crawl.models import RunStatus
from gov_mine.modules.institutions.models import InstitutionType

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Place = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class InstitutionInput(BaseModel):
    """What the Add and Edit forms send. The website must be http or https."""

    name: Name
    institution_type: InstitutionType
    website_url: Annotated[HttpUrl, Field(max_length=2048)]
    country_code: Annotated[str, StringConstraints(min_length=2, max_length=2)] | None = None
    state: Place | None = None
    city: Place | None = None


class LastRun(BaseModel):
    id: uuid.UUID
    status: RunStatus
    created_at: datetime


class InstitutionOutput(BaseModel):
    id: uuid.UUID
    name: str
    institution_type: InstitutionType
    website_url: str
    country_code: str | None
    state: str | None
    city: str | None
    paused: bool
    created_at: datetime
    last_run: LastRun | None
    # When the full-crawl interval runs out, counted from the last run; None when never run.
    next_run_at: datetime | None
