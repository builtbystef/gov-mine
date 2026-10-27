"""Capture gov-mine test fixtures from CreateTO and MERX.

Stdlib only. Run with `python3 -I capture.py <out_dir> [stage ...]`.
Stages: createto, merx (default: both). Re-runnable: files already saved are skipped.

Politeness: one request at a time, a fixed delay per host (MERX asks for
Crawl-delay: 5), a plain user agent, no cookies, public pages only.
Every saved body gets a sibling `<name>.meta.json` with status, final URL,
response headers and fetch time, so ETag / Last-Modified are kept for tests.
"""

from __future__ import annotations

import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

USER_AGENT = "gov-mine-fixtures/0.1"
DELAYS = {"www.merx.com": 5.0}
DEFAULT_DELAY = 1.5
TIMEOUT = 60

_last_hit: dict[str, float] = {}


def fetch(url: str, out: Path, extra_headers: dict[str, str] | None = None) -> bytes | None:
    """Fetch url into out (skip if present). Returns the body, or None on failure."""
    meta_path = out.with_name(out.name + ".meta.json")
    if out.exists() and meta_path.exists():
        return out.read_bytes()
    host = urlparse(url).hostname or ""
    wait = DELAYS.get(host, DEFAULT_DELAY) - (time.monotonic() - _last_hit.get(host, -1e9))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip", **(extra_headers or {})}
    )
    status, headers, body, final_url, error = None, {}, b"", url, None
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status, headers, final_url = resp.status, dict(resp.headers), resp.url
            body = resp.read()
    except urllib.error.HTTPError as e:
        status, headers, body, error = e.code, dict(e.headers), e.read(), str(e)
    except Exception as e:  # network failure: record it, keep going
        error = repr(e)
    finally:
        _last_hit[host] = time.monotonic()
    if headers.get("Content-Encoding") == "gzip" and body:
        body = gzip.decompress(body)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "url": url,
        "final_url": final_url,
        "status": status,
        "error": error,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "user_agent": USER_AGENT,
        "request_headers": extra_headers or {},
        "headers": headers,
        "bytes": len(body),
    }
    print(f"{status} {len(body):>9} {url}", flush=True)
    if status != 200:
        meta_path.write_text(json.dumps(meta, indent=2))
        return None
    out.write_bytes(body)
    meta_path.write_text(json.dumps(meta, indent=2))
    return body


def slug(url: str) -> str:
    path = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1] or "index"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", path)[:120]


# --- CreateTO -----------------------------------------------------------------

CREATETO = "https://createto.ca"
PROJECT_PAGE = "/projects/dunn-house-phase-2"
PARKDALE = "/projects/parkdale-hub"


def next_data(page: bytes) -> dict | None:
    m = re.search(rb'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    return json.loads(m.group(1)) if m else None


def pdf_urls(page: bytes) -> list[str]:
    """Every PDF URL anywhere in the raw HTML, including inside __NEXT_DATA__."""
    text = page.decode("utf-8", "replace").replace("\\/", "/").replace("\\u002F", "/")
    found = re.findall(r'(?:https?:)?//[^\s"\'<>()\\]+?\.pdf\b', text, re.I)
    seen: dict[str, None] = {}
    for u in found:
        u = html.unescape(u)
        seen.setdefault("https:" + u if u.startswith("//") else u, None)
    return list(seen)


def capture_createto(root: Path) -> None:
    d = root / "createto"
    for name in ("robots.txt", "sitemap.xml", "sitemap-0.xml"):
        fetch(f"{CREATETO}/{name}", d / name)
    fetch(f"{CREATETO}/", d / "homepage.html")
    fetch(f"{CREATETO}/our-work/procurement", d / "procurement.html")

    for path, name in ((PROJECT_PAGE, slug(PROJECT_PAGE)), (PARKDALE, "parkdale-hub")):
        page = fetch(CREATETO + path, d / "projects" / f"{name}.html")
        if page and (nd := next_data(page)):
            (d / "projects" / f"{name}.next_data.json").write_text(
                json.dumps(nd, indent=2, ensure_ascii=False)
            )

    # The page's raw HTML also embeds related initiatives' data with ~50 more PDFs.
    # Keep only the PDFs in Parkdale Hub's own body (spec: 14, most only in the JSON).
    page = (d / "projects" / "parkdale-hub.html").read_bytes()
    nd = next_data(page) or {}
    body = nd.get("props", {}).get("pageProps", {}).get("page", {}).get("content", {}).get("body")
    urls = pdf_urls(json.dumps(body).encode())
    rendered = page.split(b'<script id="__NEXT_DATA__"')[0]
    in_html = set(pdf_urls(rendered))
    pdf_dir = d / "projects" / "parkdale-hub-files"
    index = []
    for u in urls:
        name = slug(u)
        ok = fetch(u, pdf_dir / name) is not None
        index.append({"url": u, "file": name, "in_rendered_html": u in in_html, "saved": ok})
    (pdf_dir / "index.json").write_text(json.dumps(index, indent=2))
    print(f"parkdale-hub: {len(urls)} body PDFs, {sum(i['in_rendered_html'] for i in index)} also in rendered HTML")


# --- MERX ---------------------------------------------------------------------

MERX = "https://www.merx.com"
TABS = ("open", "closed", "awarded")
SEARCH = MERX + "/public/solicitations/{tab}?keywords=createto&pageNumber={n}"
CLOSED_NOT_AWARDED = 3
AWARDED_MIN, AWARDED_MAX = 4, 10
# The award panel is an AJAX endpoint: without this header MERX returns its welcome
# page; with it, the panel's HTML wrapped in a jQuery `$("#innerTabContent").html(...)`.
AJAX = {"X-Requested-With": "XMLHttpRequest", "Accept": "*/*"}


def result_links(page: bytes) -> list[str]:
    """Result rows on a search page, in order (tender pages and login-gated notices)."""
    hrefs = re.findall(r'href="([^"]*/\d{8,}\?origin=[^"]*)"', page.decode("utf-8", "replace"))
    return [urljoin(MERX, html.unescape(h)) for h in hrefs]


def page_count(page: bytes) -> int:
    nums = re.findall(rb"pageNumber=(\d+)", page)
    return max((int(n) for n in nums), default=1)


def tender_id(url: str) -> str:
    return re.findall(r"/(\d{8,})", urlparse(url).path)[-1]


def capture_merx(root: Path) -> None:
    d = root / "merx"
    fetch(f"{MERX}/robots.txt", d / "robots.txt")
    rows: dict[str, list[str]] = {}
    for tab in TABS:
        first = fetch(SEARCH.format(tab=tab, n=1), d / "search" / f"{tab}-page-1.html")
        if not first:
            continue
        rows[tab] = result_links(first)
        for n in range(2, page_count(first) + 1):
            p = fetch(SEARCH.format(tab=tab, n=n), d / "search" / f"{tab}-page-{n}.html")
            rows[tab] += result_links(p or b"")
    summary = {
        tab: {
            "rows": len(r),
            "distinct": len(set(r)),
            "login_gated": sorted({u for u in r if "/interception/" in u}),
            "tenders": list(dict.fromkeys(u for u in r if "/solicitations/" in u)),
        }
        for tab, r in rows.items()
    }
    (d / "search" / "summary.json").write_text(json.dumps(summary, indent=2))
    for tab, s in summary.items():
        print(f"merx {tab}: {s['rows']} rows, {s['distinct']} distinct, "
              f"{len(s['login_gated'])} login-gated, {len(s['tenders'])} tender pages")

    awarded_ids = {tender_id(u) for u in summary.get("awarded", {}).get("tenders", [])}
    picks = {
        "open": summary.get("open", {}).get("tenders", [])[:1],
        "closed": [u for u in summary.get("closed", {}).get("tenders", [])
                   if tender_id(u) not in awarded_ids][:CLOSED_NOT_AWARDED],
    }
    for tab, links in picks.items():
        for u in links:
            fetch(u, d / "tenders" / tab / f"{tender_id(u)}.html")

    # Awarded: keep going until there is a panel with a value and one "Undisclosed".
    seen_value = seen_undisclosed = False
    awarded = summary.get("awarded", {}).get("tenders", [])
    for i, u in enumerate(awarded[:AWARDED_MAX]):
        if i >= AWARDED_MIN and seen_value and seen_undisclosed:
            break
        tid = tender_id(u)
        page = fetch(u, d / "tenders" / "awarded" / f"{tid}.html")
        if not page:
            continue
        m = re.search(r'data-ajax-url="([^"]*/abstract/award)"', page.decode("utf-8", "replace"))
        if not m:
            print(f"no award tab on {u}")
            continue
        panel = fetch(urljoin(MERX, m.group(1)), d / "tenders" / "awarded" / f"{tid}.award.js", AJAX)
        text = (panel or b"").decode("utf-8", "replace")
        if "Undisclosed" in text:
            seen_undisclosed = True
        if re.search(r"\$\s?[0-9][0-9,]*", text):
            seen_value = True
    print(f"award panels: value seen={seen_value}, undisclosed seen={seen_undisclosed}")


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    stages = sys.argv[2:] or ["createto", "merx"]
    if "createto" in stages:
        capture_createto(root)
    if "merx" in stages:
        capture_merx(root)


if __name__ == "__main__":
    main()
