"""Replay (UC-004, decision 32): a local server that stands in for every website with the saved
copies in `fixtures/`, and what the crawler needs to talk to it.

A replay run sends every request, whatever its URL's host, to the replay server's address, with
the URL it wants in `X-Replay-URL`. The server answers with the saved body of that URL (only the
copies saved with a 200), or 404 for one it does not hold. Without the header it answers with
the list of the URLs it holds, normalised, which is how the fence knows the saved set.

By default it serves the two variants: one project page with its phase changed, and one PDF
replaced by a file no parser reads. `variants=False` serves the copies as they were saved."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from gov_mine.shared.urls import normalise_url

URL_HEADER = "X-Replay-URL"
# The saved headers the server sends back; the rest described the original transfer.
KEPT_HEADERS = ("content-type", "etag", "last-modified")

# The project page whose phase the replay changes, from what it was saved with to the next one.
EDITED_PAGE = "https://createto.ca/projects/dunn-house-phase-2"
SAVED_PHASE = ("preConstruction", "Pre-construction")
REPLAYED_PHASE = ("deliveryAndConstruction", "Delivery and Construction")
# The PDF the replay serves as a corrupt file, linked from the Parkdale Hub page.
CORRUPT_FILE = "https://www.toronto.ca/legdocs/mmis/2017/mm/bgrd/backgroundfile-101969.pdf"
CORRUPT_BYTES = b"%PDF-1.7\n%corrupt: replaced by gov-mine dev replay\n"

_NEXT_DATA = re.compile(
    r'(<script id="__NEXT_DATA__" type="application/json">)(.*?)(</script>)', re.DOTALL
)
_SHOWN_PHASE = re.compile(r"(Current Phase</dt><dd[^>]*>)" + re.escape(SAVED_PHASE[1]) + "(</dd>)")


@dataclass(frozen=True)
class Saved:
    body: Path
    headers: dict[str, str]


def load_saved(directory: Path) -> dict[str, Saved]:
    """Every copy under `directory` saved with a 200, by normalised URL: a body file next to its
    `<name>.meta.json`."""
    saved: dict[str, Saved] = {}
    for meta_path in sorted(directory.rglob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        body = meta_path.with_name(meta_path.name.removesuffix(".meta.json"))
        if meta.get("status") != httpx.codes.OK or not body.is_file():
            continue
        headers = {
            name.lower(): value
            for name, value in meta.get("headers", {}).items()
            if name.lower() in KEPT_HEADERS
        }
        saved[normalise_url(meta["url"])] = Saved(body, headers)
    return saved


def edit_phase(html: str) -> str:
    """The project page with its own current phase moved from `SAVED_PHASE` to `REPLAYED_PHASE`,
    in `__NEXT_DATA__` and where the page shows it. Raises `ValueError` when the page has no
    such phase, so a fixture that changed is not served unedited."""
    data_match = _NEXT_DATA.search(html)
    if data_match is None:
        raise ValueError("no __NEXT_DATA__ in the edited page")
    data = json.loads(data_match.group(2))
    content = data["props"]["pageProps"]["page"]["content"]
    if content.get("phase") != SAVED_PHASE[0]:
        raise ValueError(f"the edited page's phase is {content.get('phase')!r}")
    content["phase"] = REPLAYED_PHASE[0]
    html = (
        html[: data_match.start(2)]
        # Escaped as Next.js does, so no string in it can end the script early.
        + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        + html[data_match.end(2) :]
    )
    html, shown = _SHOWN_PHASE.subn(rf"\g<1>{REPLAYED_PHASE[1]}\g<2>", html)
    if not shown:
        raise ValueError("the edited page does not show its phase")
    return html


def replay_app(directory: Path, *, variants: bool = True) -> Starlette:
    """The replay server over the copies saved under `directory`."""
    saved = load_saved(directory)
    replaced: dict[str, bytes] = {}
    if variants:
        for url in (EDITED_PAGE, CORRUPT_FILE):
            if url not in saved:
                raise ValueError(f"{url} is not saved under {directory}")
        page = saved[EDITED_PAGE].body.read_text(encoding="utf-8")
        replaced[EDITED_PAGE] = edit_phase(page).encode()
        replaced[CORRUPT_FILE] = CORRUPT_BYTES

    async def serve(request: Request) -> Response:
        wanted = request.headers.get(URL_HEADER)
        if wanted is None:
            return JSONResponse(sorted(saved))
        try:
            url = normalise_url(wanted)
        except ValueError:
            return Response(status_code=httpx.codes.NOT_FOUND)
        copy = saved.get(url)
        if copy is None:
            return Response(status_code=httpx.codes.NOT_FOUND)
        if url in replaced:
            # A changed body does not keep the validators of the saved one.
            return Response(replaced[url], media_type=copy.headers.get("content-type"))
        return Response(copy.body.read_bytes(), headers=copy.headers)

    return Starlette(routes=[Route("/{path:path}", serve)])


def replay_address(value: str) -> str:
    """`value` as a replay server's address: an http(s) URL with a host, without a trailing
    slash. Raises `ValueError` otherwise."""
    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"not an http(s) address: {value!r}")
    return value.strip().rstrip("/")


def replay_request(url: str, replay: str | None) -> tuple[str, dict[str, str]]:
    """Where a request for `url` goes and the headers it adds: the URL itself on a live run, the
    replay server's address with `url` in `URL_HEADER` on a replay run."""
    if replay is None:
        return url, {}
    return f"{replay}/", {URL_HEADER: url}


async def saved_urls(http: httpx.AsyncClient, replay: str) -> frozenset[str]:
    """The normalised URLs the replay server at `replay` holds."""
    response = await http.get(f"{replay}/")
    response.raise_for_status()
    return frozenset(response.json())


__all__ = [
    "CORRUPT_FILE",
    "EDITED_PAGE",
    "URL_HEADER",
    "edit_phase",
    "load_saved",
    "replay_address",
    "replay_app",
    "replay_request",
    "saved_urls",
]
