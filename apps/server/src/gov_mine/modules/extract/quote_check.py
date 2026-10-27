"""The quote check: whether a model's excerpt is really on the page it cites. Public Atlas's
check (`modules/evidence/quote_checks.py`), reading one page of a snapshot's markdown."""

from gov_mine.shared.text import normalize_markdown

# Shorter than this is a stray word, not a phrase: "the" is on every page.
MIN_EXCERPT_CHARS = 12


def excerpt_on_page(page_text: str, excerpt: str) -> bool:
    """Whether `excerpt` is in `page_text` word for word, markdown syntax, case, spacing and
    typographic punctuation aside, starting and ending at word edges. Failing that, it is
    searched for with all whitespace removed (a PDF that broke a word across lines), at word
    edges all the same. An excerpt under twelve characters never is."""
    needle = normalize_markdown(excerpt)
    if len(needle) < MIN_EXCERPT_CHARS:
        return False
    text = normalize_markdown(page_text)
    return _found_at_word_edges(text, needle) or _found_at_word_edges(
        text, needle.replace(" ", ""), squashed=True
    )


def _found_at_word_edges(text: str, needle: str, *, squashed: bool = False) -> bool:
    """Whether `needle` is in `text` starting and ending at word edges. `squashed` searches the
    text with its spaces removed and checks the edges at the original positions."""
    if not needle:
        return False
    positions = [index for index, char in enumerate(text) if char != " "] if squashed else None
    searched = "".join(text[index] for index in positions) if positions is not None else text
    start = searched.find(needle)
    while start >= 0:
        end = start + len(needle) - 1
        first, last = (start, end) if positions is None else (positions[start], positions[end])
        if _starts_a_word(text, first, needle) and _ends_a_word(text, last, needle):
            return True
        start = searched.find(needle, start + 1)
    return False


def _starts_a_word(text: str, first: int, needle: str) -> bool:
    return not needle[0].isalnum() or first == 0 or not text[first - 1].isalnum()


def _ends_a_word(text: str, last: int, needle: str) -> bool:
    return not needle[-1].isalnum() or last == len(text) - 1 or not text[last + 1].isalnum()


__all__ = ["MIN_EXCERPT_CHARS", "excerpt_on_page"]
