from pydantic import BaseModel, Field

class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000)
    references: list[dict[str, str]] = Field(default_factory=list, max_length=8)
