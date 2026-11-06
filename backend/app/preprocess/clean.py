import re

_SUBJECT = re.compile(r"(?i:mavzu|мавзу|тема|subject)\s*:.*")
_DEVICE = re.compile(r"(?i:sent from|sent via|отправлено (?:с|со|из))(?: \S+){1,4}")
_KEYWORD = r"(?i:hurmat bilan|ҳурмат билан|с уважением|best regards|kind regards|regards)"
_NAME = r"[A-ZА-ЯЁЎҚҒҲ][\w'’‘.-]*"
_LOWERCASE_NAME = r"[a-zа-яёўқғҳ][\w'’‘.-]*"
# A name is one or two words, so text that follows it on the same line stays.
_SIGNATURE = re.compile(
    rf"^{_KEYWORD}[,:.]?(?: {_LOWERCASE_NAME}){{1,2}} *$|"
    rf"(?:^|(?<=[.!?] )){_KEYWORD}[,:.]?(?: {_NAME}){{0,2}}",
    re.MULTILINE,
)
_KEYWORD_ONLY = re.compile(rf"{_KEYWORD}[,:.]?")
_NAME_ONLY = re.compile(rf"{_NAME}(?: {_NAME})?")


def clean_text(text: str) -> str:
    """Removes email noise and signatures. Only these parts go: text after a signature stays,
    because it may be an instruction meant for the model (TRD section 4)."""
    kept: list[str] = []
    seen_content = False
    after_bare_signature = False

    for line in text.split("\n"):
        stripped = line.strip()
        if after_bare_signature and _NAME_ONLY.fullmatch(stripped):
            after_bare_signature = False
            continue
        if stripped:
            after_bare_signature = False
        if not seen_content and _SUBJECT.fullmatch(stripped):
            seen_content = True
            continue
        if stripped.startswith(">") or _DEVICE.fullmatch(stripped):
            continue
        if _KEYWORD_ONLY.fullmatch(stripped):
            after_bare_signature = True
            continue
        if stripped:
            seen_content = True
        kept.append(_SIGNATURE.sub("", line).strip())

    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
