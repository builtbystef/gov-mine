"""Files to markdown pages with MarkItDown: a PDF one page at a time, a slide or a sheet per page,
a Word file as one. csv and plain text are read as they are."""

import io
import re
import threading

import pypdfium2
from markitdown import MarkItDown, StreamInfo

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLS = "application/vnd.ms-excel"
TEXT_MEDIA_TYPES = frozenset({"text/csv", "text/plain"})

# Media type: (parser name, extension MarkItDown picks its converter by).
OFFICE = {
    DOCX: ("docx:markitdown@1", ".docx"),
    PPTX: ("pptx:markitdown@1", ".pptx"),
    XLSX: ("xlsx:markitdown@1", ".xlsx"),
    XLS: ("xls:markitdown@1", ".xls"),
}
PDF_PARSER = "pdf:markitdown@1"
TEXT_PARSER = "text:plain@1"

# MarkItDown starts every slide with this comment, and every sheet with its name as a heading.
_SLIDE = re.compile(r"^<!-- Slide number: \d+ -->$", re.MULTILINE)
_SHEET = re.compile(r"^(?=## )", re.MULTILINE)

# Plugins (the OCR one) stay off: scans are read in 034.
_markitdown = MarkItDown(enable_plugins=False)
# PDFium is not thread-safe, and parses run in worker threads: two at once fail with "Data
# format error" on sound files. Only the split into pages holds it; converting them does not.
_pdfium = threading.Lock()


def _convert(data: bytes, media_type: str, extension: str) -> str:
    info = StreamInfo(mimetype=media_type, extension=extension)
    return _markitdown.convert_stream(io.BytesIO(data), stream_info=info).markdown.strip()


def _pdf_pages(data: bytes) -> list[bytes]:
    """Each page of the PDF as a PDF of its own."""
    with _pdfium:
        return _split(data)


def _split(data: bytes) -> list[bytes]:
    document = pypdfium2.PdfDocument(data)
    try:
        pages = []
        for index in range(len(document)):
            single = pypdfium2.PdfDocument.new()
            single.import_pages(document, [index])
            out = io.BytesIO()
            single.save(out)
            single.close()
            pages.append(out.getvalue())
        return pages
    finally:
        document.close()


def parse_pdf(data: bytes) -> list[str]:
    return [_convert(page, PDF, ".pdf") + "\n" for page in _pdf_pages(data)]


def parse_office(data: bytes, media_type: str) -> list[str]:
    markdown = _convert(data, media_type, OFFICE[media_type][1])
    if media_type == PPTX:
        chunks = _SLIDE.split(markdown)[1:]
    elif media_type in {XLSX, XLS}:
        chunks = _SHEET.split(markdown)
    else:
        chunks = [markdown]
    return [chunk.strip() + "\n" for chunk in chunks if chunk.strip()] or ["\n"]


def parse_text(data: bytes) -> list[str]:
    return [data.decode("utf-8", errors="replace")]
