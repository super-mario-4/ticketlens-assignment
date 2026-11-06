import re

from app.preprocess.normalize import fold_text

_PLACEHOLDERS = re.compile(r"\[[^\]\n]{0,20}\]|\*+")
_EDGE_PUNCTUATION = re.compile(r"^\W+|\W+$")
_EMPTY_MESSAGES = frozenset(
    {"alo", "allo", "javob yoq", "ok", "otvette", "qayta yozyapman", "salom", "test"}
)


def has_no_content(text: str) -> bool:
    """True when there is nothing to classify: no letters at all, a media placeholder, or only
    a greeting or a request for a reply."""
    folded = _EDGE_PUNCTUATION.sub("", fold_text(_PLACEHOLDERS.sub(" ", text)))
    return not any(character.isalpha() for character in folded) or folded in _EMPTY_MESSAGES
