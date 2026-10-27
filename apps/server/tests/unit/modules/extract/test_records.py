import pytest
from pydantic import ValidationError

from gov_mine.modules.classify.models import Document  # noqa: F401 - mappers configured
from gov_mine.modules.extract.records import (
    DOCUMENT_RECORD_TYPES,
    RECORD_TYPES,
    Contact,
    NewsItem,
    output_type,
)
from gov_mine.modules.institutions.models import DocumentType


def test_a_draft_missing_its_identifying_field_fails_validation():
    with pytest.raises(ValidationError):
        NewsItem.model_validate({"headline": None, "summary": "Approved."})
    assert Contact.model_validate({"name": "Ada Lovelace"}).key() == "Ada Lovelace"


def test_record_types_and_what_is_not_extracted():
    assert set(RECORD_TYPES) == {
        "project",
        "news_item",
        "meeting",
        "contact",
        "rfp",
        "grant",
        "contract",
    }
    assert DOCUMENT_RECORD_TYPES[DocumentType.STAFF_DIRECTORY] is Contact
    for kept in (
        "budget",
        "procurement_guidelines",
        "youtube",
        "project_material",
        "annual_report",
        "strategic_plan",
    ):
        assert DocumentType(kept) not in DOCUMENT_RECORD_TYPES
    schema = output_type(NewsItem).model_json_schema()
    assert set(schema["properties"]) == {"document_date", "records"}
