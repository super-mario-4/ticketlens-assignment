import re
import unicodedata

_APOSTROPHES = str.maketrans("", "", "'’‘ʻʼ`´")
_CYRILLIC = "абвгдежзийклмнопрстуфхчшщъыьэюяўқғҳёц"
_LATIN = "a b v g d e j z i y k l m n o p r s t u f x ch sh sh _ i _ e yu ya o q g h yo ts"
_CYRILLIC_TO_LATIN = str.maketrans(
    dict(zip(_CYRILLIC, _LATIN.split(), strict=True)) | {"ъ": "", "ь": ""}
)


def normalize_text(text: str) -> str:
    """Removes invisible characters that could split a card number or hide an instruction."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    kept = []
    for character in text:
        category = unicodedata.category(character)
        if character == "\n":
            kept.append(character)
        elif category == "Zs" or character == "\t":
            kept.append(" ")
        elif category not in ("Cc", "Cf"):
            kept.append(character)
    lines = (" ".join(line.split()) for line in "".join(kept).split("\n"))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def fold_text(text: str) -> str:
    """One comparable form for Uzbek Latin and Cyrillic, Russian and Russian in Latin letters.

    For matching only: stored text is never replaced with this form.
    """
    folded = unicodedata.normalize("NFKC", text).casefold()
    folded = folded.translate(_APOSTROPHES).translate(_CYRILLIC_TO_LATIN)
    return " ".join(folded.split())
