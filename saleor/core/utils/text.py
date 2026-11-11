import unicodedata


def strip_accents(text: str) -> str:
    """Remove diacritical marks from text, e.g. 'Magnésium' → 'Magnesium'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def safe_truncate(text: str, max_length: int) -> str:
    """Truncate text to a safe length while avoiding breaking combining diacritical marks."""
    if max_length <= 0:
        raise ValueError("max_length must be greater than 0")
    # normalize text to its shortest Unicode representation
    text = unicodedata.normalize("NFC", text)
    if len(text) <= max_length:
        return text
    # keep text[:end_pos] and leave room for the ellipsis
    end_pos = max_length - 1
    # if the first dropped character is a combining mark, its base character is
    # still in the kept part; drop the base and all of its marks instead of
    # splitting them
    while end_pos > 0 and unicodedata.combining(text[end_pos]):
        end_pos -= 1
    return text[:end_pos] + "…"
