import json

from gov_mine.integrations.ai.jev import encode_body
from gov_mine.modules.classify.service import MAX_REQUEST_BYTES, build_request


def test_a_long_page_fits_the_request_budget_cut_at_a_paragraph():
    links = [
        {"text": f"Link {i} " + "é" * 40, "href": f"https://createto.ca/p/{i}"} for i in range(500)
    ]
    paragraphs = [f"Paragraph {i}: " + 'Toronto "waterfront" ü ' * 30 for i in range(2000)]
    pages = ["\n\n".join(paragraphs[:1000]), "\n\n".join(paragraphs[1000:])]

    body = build_request("typesafe/jev-1.14", "https://createto.ca/news", "News", links, pages)

    assert body["model"] == "typesafe/jev-1.14"
    assert len(encode_body(body)) < MAX_REQUEST_BYTES
    state = body["state"]
    assert set(state) == {"url", "title", "links", "text"}
    assert 0 < len(state["links"]) <= 100
    # As sent: compact JSON, UTF-8.
    sent = json.dumps(state["links"], ensure_ascii=False, separators=(",", ":")).encode()
    assert len(sent) <= 6_000
    text = state["text"]
    assert text.startswith("Paragraph 0: ")
    assert text in "\n\n".join(pages)
    assert text.split("\n\n")[-1] in paragraphs
    # The text fills the rest: one more paragraph would not fit.
    assert len(encode_body(body)) > MAX_REQUEST_BYTES - 1000
    [question] = body["questions"].values()
    assert question["type"] == "choice"
    criteria = question["criteria"]
    assert len(criteria) == 25
    assert "none" in criteria
    assert "listing:staff_directory" in criteria
    assert "document:press_releases" in criteria
    assert not any("project_material" in choice for choice in criteria)
    assert all(criteria.values())
