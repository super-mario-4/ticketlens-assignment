import re

_CVV_WORD = r"(?:cvv2?|cvc2?|свв2?|сvv2?|сvс2?|код безопасности|защитный код)"
_CVV = re.compile(
    rf"(?<!\w){_CVV_WORD}(?!\w)[^\d\n]{{0,15}}\d{{3,4}}(?!\d)|(?<!\d)\d{{3,4}} ?{_CVV_WORD}(?!\w)",
    re.IGNORECASE,
)
_EXPIRY_WORD = r"(?:срок\w*|muddat\w*|муддат\w*|expir\w*|exp\.?|valid\w*)"
_EXPIRY_DATE = r"\d{1,2} ?[/.\-] ?\d{2,4}(?!\d)"
_EXPIRY = re.compile(rf"(?<!\w)({_EXPIRY_WORD}[^\d\n]{{0,20}}){_EXPIRY_DATE}", re.IGNORECASE)
# Not after "+", the start of a phone number, and not into a following "11/27".
_CARD = re.compile(r"(?<![\d+])\d(?:[ \-]?\d){12,18}(?!\d)(?![/.]\d)")
_EXPIRY_AFTER_CARD = re.compile(rf"(\*{{4}} \d{{4}}[ ,;:()\-]{{0,5}}){_EXPIRY_DATE}")
_INTERNATIONAL_PHONE = r"(?:\+ ?)?998[ \-().]*\d{2}[ \-().]*\d{3}[ \-().]*\d{2}[ \-().]*\d{2}"
# The mobile prefixes keep amounts such as "120 000 000" out of this pattern.
_LOCAL_PHONE = r"\(?(?:33|50|55|77|88|90|91|93|94|95|97|98|99)\)?[ \-]?\d{3}[ \-]?\d{2}[ \-]?\d{2}"
_PHONE = re.compile(rf"(?<![\d+])(?:{_INTERNATIONAL_PHONE}|{_LOCAL_PHONE})(?!\d)")
# Any two letters: the dataset mixes Latin and Cyrillic, even inside one series ("АC").
_PASSPORT = re.compile(
    r"(?<!\w)[^\W\d_]{2}[ \-]?\d{7}(?!\d)|(?<=pasport)[: ]{1,2}\d{7}(?!\d)|"
    r"(?<=паспорт)[: ]{1,2}\d{7}(?!\d)",
    re.IGNORECASE,
)

_SENSITIVE_PATTERNS = (_CVV, _CARD, _PHONE, _PASSPORT)


class MaskingError(Exception):
    """Sensitive data is still present after masking."""


def _mask_card(match: re.Match[str]) -> str:
    digits = re.sub(r"\D", "", match.group())
    return f"**** **** **** {digits[-4:]}"


def mask_sensitive_data(text: str) -> str:
    text = _CVV.sub("[CVV]", text)
    text = _EXPIRY.sub(r"\1[EXP]", text)
    text = _CARD.sub(_mask_card, text)
    text = _EXPIRY_AFTER_CARD.sub(r"\1[EXP]", text)
    text = _PHONE.sub("[PHONE]", text)
    return _PASSPORT.sub("[PASSPORT]", text)


def contains_sensitive_data(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SENSITIVE_PATTERNS)


def assert_masked(text: str) -> None:
    """Second check, so that a masking fault stops the ticket instead of storing its data."""
    if contains_sensitive_data(text):
        raise MaskingError
