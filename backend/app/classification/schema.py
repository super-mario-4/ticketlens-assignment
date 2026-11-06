from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Category, Priority


class ClassificationOutput(BaseModel):
    """The only answer accepted from a model (TRD section 7.3). There is no team field: a model
    cannot choose one, and an answer with extra fields is rejected."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: Category
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1)
