import re
from typing import TYPE_CHECKING

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Value

from .utils.text import strip_accents

if TYPE_CHECKING:
    from django.db.models import QuerySet


def _sanitize_word(word: str) -> str:
    """Remove PostgreSQL tsquery metacharacters from a word.

    Replaces special characters that have meaning in tsquery syntax with spaces,
    so that e.g. "22:20" becomes "22 20" (two separate tokens) rather than "2220".

    Preserved: alphanumeric, underscore, hyphen, @, period
    Replaced with space: parentheses, &, |, !, :, <, >, ', *
    """
    return re.sub(r"[()&|!:<>\'*]", " ", word).strip()


def _tokenize(value: str) -> list[dict]:
    """Tokenize a search string into structured tokens.

    Recognizes:
    - Quoted phrases: "green tea"
    - OR operator: coffee OR tea
    - Negation: -decaf
    - Regular words: coffee
    """
    tokens: list[dict] = []
    i = 0

    while i < len(value):
        # Skip whitespace
        if value[i].isspace():
            i += 1
            continue

        # Check for negation prefix
        negated = False
        if value[i] == "-" and i + 1 < len(value) and not value[i + 1].isspace():
            negated = True
            i += 1

        # Quoted phrase
        if i < len(value) and value[i] == '"':
            end = value.find('"', i + 1)
            if end == -1:
                phrase = value[i + 1 :]
                i = len(value)
            else:
                phrase = value[i + 1 : end]
                i = end + 1
            words = []
            for w in phrase.split():
                sanitized = _sanitize_word(w)
                words.extend(sanitized.split())
            if words:
                tokens.append({"type": "phrase", "words": words, "negated": negated})
            continue

        # Read the next word
        end = i
        while end < len(value) and not value[end].isspace():
            end += 1
        raw_word = value[i:end]
        i = end

        # OR operator (must not be negated)
        if raw_word == "OR" and not negated:
            tokens.append({"type": "or"})
            continue

        # AND operator – explicit AND is a no-op (AND is implicit between terms)
        if raw_word == "AND" and not negated:
            continue

        sanitized = _sanitize_word(raw_word)
        for word in sanitized.split():
            tokens.append({"type": "word", "word": word, "negated": negated})

    return tokens


def parse_search_query(value: str) -> str | None:
    """Parse a search string into a raw PostgreSQL tsquery with prefix matching.

    Supports websearch-compatible syntax:
    - Multiple words (implicit AND): "coffee shop" -> coffee:* & shop:*
    - OR operator: "coffee OR tea" -> coffee:* | tea:*
    - Negation: "-decaf" -> !decaf:*
    - Quoted phrases (exact match): '"green tea"' -> (green <-> tea)

    Returns:
        A raw tsquery string, or None if the input yields no searchable terms.

    """
    value = value.strip()
    if not value:
        return None

    tokens = _tokenize(value)
    if not tokens:
        return None

    parts: list[str] = []
    pending_connector = " & "

    for token in tokens:
        if token["type"] == "or":
            pending_connector = " | "
            continue

        # Insert connector between terms
        if parts:
            parts.append(pending_connector)
        pending_connector = " & "

        neg = "!" if token["negated"] else ""

        if token["type"] == "word":
            parts.append(f"{neg}{token['word']}:*")

        elif token["type"] == "phrase":
            words = token["words"]
            if len(words) == 1:
                parts.append(f"{neg}{words[0]}")
            else:
                # Use <-> (followed-by) for phrase matching
                phrase_tsquery = " <-> ".join(words)
                if neg:
                    parts.append(f"!({phrase_tsquery})")
                else:
                    parts.append(f"({phrase_tsquery})")

    result = "".join(parts)
    return result if result else None


def prefix_search(qs: "QuerySet", value: str) -> "QuerySet":
    """Apply prefix-based search to a queryset with perfect match prioritization.

    Supports websearch-compatible syntax (AND, OR, negation, quoted phrases)
    while adding prefix matching so partial words produce results.

    Scoring: exact (websearch) matches get 2x weight, prefix matches get 1x.

    The queryset must have a ``search_vector`` SearchVectorField.
    """
    if not value:
        # return a original queryset annotated with search_rank=0
        # to allow default RANK sorting
        return qs.annotate(search_rank=Value(0))

    value = strip_accents(value)

    parsed_query = parse_search_query(value)
    if not parsed_query:
        # return empty queryset as the provided value is not searchable
        # annotated with search_rank=0 to allow default RANK sorting
        return qs.annotate(search_rank=Value(0)).none()

    # Prefix query – broadens matching via :*
    prefix_query = SearchQuery(parsed_query, search_type="raw", config="simple")

    # Exact (websearch) query – used only for ranking, not filtering
    exact_query = SearchQuery(value, search_type="websearch", config="simple")

    qs = qs.filter(search_vector=prefix_query).annotate(
        prefix_rank=SearchRank(F("search_vector"), prefix_query),
        exact_rank=SearchRank(F("search_vector"), exact_query),
        search_rank=F("exact_rank") * 2 + F("prefix_rank"),
    )

    return qs
