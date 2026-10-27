"""The record types: one Pydantic model per type, which validates `record_snapshots.data`, names
its key field, and requires its identifying field (section 5.6). From each the extractor builds
its structured-output schema, every field cited by page and excerpt."""

from datetime import date
from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, create_model

from gov_mine.modules.institutions.models import DocumentType

Name = Annotated[str, Field(min_length=1)]


class RecordData(BaseModel):
    """`key_field` tells apart several records of the type in one document; None means one per
    document. Dates are ISO dates: a month or year alone is its first day."""

    model_config = ConfigDict(extra="forbid")

    record_type: ClassVar[str]
    key_field: ClassVar[str | None] = None
    # What one record is, for the prompt.
    one: ClassVar[str]

    def key(self) -> str:
        if self.key_field is None:
            return ""
        value = getattr(self, self.key_field)
        return value.isoformat() if isinstance(value, date) else str(value)


class Project(RecordData):
    record_type = "project"
    one = "the one project the document describes"

    name: Name
    location: str | None = None
    phase: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    partners: list[str] | None = None
    description: str | None = None
    materials: list[str] | None = None


class NewsItem(RecordData):
    record_type = "news_item"
    one = "the one news release or announcement the document is"

    headline: Name
    published_at: date | None = None
    summary: str | None = None


class Meeting(RecordData):
    record_type = "meeting"
    key_field = "held_at"
    one = "each meeting the agenda or minutes are of"

    held_at: date
    body: str | None = None
    video_url: str | None = None
    transcript_key: str | None = None


class Contact(RecordData):
    record_type = "contact"
    key_field = "name"
    one = "each person listed"

    name: Name
    title: str | None = None
    email: str | None = None
    phone: str | None = None


class Rfp(RecordData):
    record_type = "rfp"
    key_field = "title"
    one = "each tender or call for bids"

    title: Name
    description: str | None = None
    solicitation_number: str | None = None
    solicitation_type: str | None = None
    location: str | None = None
    published_at: date | None = None
    due_date: date | None = None
    status: Literal["open", "closed", "awarded"] | None = None
    naics_code: str | None = None
    contract_value: float | None = None


class Grant(RecordData):
    record_type = "grant"
    key_field = "title"
    one = "each grant, funding program or award"

    title: Name
    awardee_name: str | None = None
    funding_agency: str | None = None
    obligated_amount: float | None = None
    outlayed_amount: float | None = None
    performance_start: date | None = None
    performance_end: date | None = None


class Contract(RecordData):
    record_type = "contract"
    key_field = "vendor_name"
    one = "each contract or purchase order, by vendor"

    vendor_name: Name
    vendor_address: str | None = None
    solicitation_number: str | None = None
    awarded_at: date | None = None
    products: list[str] | None = None
    total_value: float | None = None
    annual_value: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    signer: str | None = None
    payment_terms: str | None = None
    origin: Literal["purchase_order", "award", "foia"] | None = None


RECORD_TYPES: dict[str, type[RecordData]] = {
    model.record_type: model
    for model in (Project, NewsItem, Meeting, Contact, Rfp, Grant, Contract)
}

# Budgets, procurement guidelines, videos, project materials, annual reports and strategic
# plans are kept and not extracted.
DOCUMENT_RECORD_TYPES: dict[DocumentType, type[RecordData]] = {
    DocumentType.PROJECTS: Project,
    DocumentType.PRESS_RELEASES: NewsItem,
    DocumentType.MEETING_MINUTES: Meeting,
    DocumentType.RFP: Rfp,
    DocumentType.GRANTS: Grant,
    DocumentType.PURCHASE_ORDER: Contract,
    DocumentType.STAFF_DIRECTORY: Contact,
}


class Cited[T](BaseModel):
    value: T
    page: int = Field(description="The page number the value is on, from 1.")
    excerpt: str = Field(
        description=(
            "A short passage, copied word for word from that page, that states the value:"
            " a phrase or one sentence, never more than about 30 words."
        )
    )


class ExtractionOutput(BaseModel):
    """What the model returns for a document; `records` holds the record type's drafts."""

    document_date: date | None = Field(
        description=(
            "The date the document was published, announced, issued or last updated, as it"
            " states it; null when it states none."
        )
    )
    records: list[Any]


def _identifying(record_type: type[RecordData]) -> str:
    return next(name for name, field in record_type.model_fields.items() if field.is_required())


def output_type(record_type: type[RecordData]) -> type[ExtractionOutput]:
    """What the model returns for a document: the date it was published or issued, if it says,
    and its records, each field null or a cited value. Every property is required, as strict
    structured output wants; the identifying field is never null."""
    identifying = _identifying(record_type)
    fields: dict[str, Any] = {}
    for name, field in record_type.model_fields.items():
        value_type = field.annotation if name == identifying else _non_null(field.annotation)
        cited: Any = Cited.__class_getitem__(cast("Any", value_type))
        fields[name] = (cited if name == identifying else cited | None, ...)
    draft = create_model(f"{record_type.__name__}Draft", **fields)
    records: Any = list.__class_getitem__(draft)
    return create_model(
        f"{record_type.__name__}Extraction",
        __base__=ExtractionOutput,
        records=(records, ...),
    )


def _non_null(annotation: Any) -> Any:  # noqa: ANN401 - a type annotation
    args = [arg for arg in getattr(annotation, "__args__", ()) if arg is not type(None)]
    return args[0] if len(args) == 1 else annotation


def draft_data(draft: BaseModel) -> tuple[dict[str, Any], dict[str, Cited[Any]]]:
    """A draft's plain values, and the citation of each field that has one."""
    cited: dict[str, Cited[Any]] = {
        name: value for name, value in draft if isinstance(value, Cited) and value is not None
    }
    data = {name: None if value is None else value.value for name, value in draft}
    return data, cited


__all__ = [
    "DOCUMENT_RECORD_TYPES",
    "RECORD_TYPES",
    "Cited",
    "ExtractionOutput",
    "RecordData",
    "draft_data",
    "output_type",
]
