import re

from app.preprocess.normalize import fold_text

# Applied to folded text, so one pattern covers Latin, Cyrillic and Russian in Latin letters.
_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        # Cancelling earlier instructions.
        r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,40}"
        r"\b(?:instructions?|prompts?|rules?|directions?)\b",
        r"\b(?:ignorir|zabud|otmeni|proignorir)\w*.{0,40}\b(?:instruktsi|ukazani|pravil|prompt)\w*",
        r"\b(?:oldingi|avvalgi|yuqoridagi|barcha)\b.{0,40}"
        r"\b(?:korsatma|buyruq|yoriqnoma|instruktsiya)\w*.{0,40}"
        r"\b(?:etiborsiz|etibor berma|bekor qil|unut)\w*",
        r"\bnew instructions?\b",
        r"\byangi (?:korsatma|buyruq)\w*\s*:",
        r"\bnovaya instruktsiya\b",
        # Replacing the model's role.
        r"\byou are no longer\b",
        r"\bti (?:bolshe|teper) ne\b.{0,30}\b(?:klassifikator|bot|assistent|model)\w*",
        r"\bsen endi\b.{0,30}\b(?:klassifikator|bot|assistent|model)\w*.{0,10}\bemas\w*",
        # Dictating the exact answer.
        r"\b(?:reply|answer|respond)\b.{0,15}\b(?:only|just)\b.{0,15}\bwith\b",
        r"\botvet\w* tolko (?:slovom|odnim)\b",
        r"\bfaqat\b.{0,30}\b(?:sozi bilan|deb) javob ber\w*",
        # Revealing the system prompt.
        r"\bsystem prompt\b",
        r"\b(?:sistemn\w+|tizim\w*) (?:prompt|instruktsi|korsatma)\w*",
        # Forcing a classification result.
        r"\b(?:mark|set|classify|label|tag|flag|assign|treat)\b.{0,30}"
        r"\b(?:ticket|message|request)\b.{0,30}\b(?:as|to)\b.{0,20}"
        r"\b(?:p[0-4]|critical|high|urgent|fraud|priority)\b",
        r"\b(?:verni|postav|pomet|ustanov|naznach|klassifitsir)\w*.{0,30}\b(?:kategori|prioritet)\w*",
        r"\b(?:murojaat|ticket|tiket|xabar)\w*.{0,40}"
        r"\b(?:prioritet|ustuvorlik|kategoriya)\w*.{0,20}\b(?:qoy|belgila|ozgartir)\w*",
    )
)
_FAKE_TAG = re.compile(r"</?\s*(?:ticket|system|assistant|user|instructions?)\s*>", re.IGNORECASE)


def is_suspicious(text: str) -> bool:
    """Looks for instructions aimed at the model. Words such as "P1" or "fraud" alone are normal
    in a fintech ticket and are not a signal (TRD section 7.4). No pattern list catches every
    attempt: this is one layer of several."""
    if _FAKE_TAG.search(text):
        return True
    folded = fold_text(text)
    return any(pattern.search(folded) for pattern in _PATTERNS)
