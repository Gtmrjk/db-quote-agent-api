from typing import Literal

from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    quote: str = Field(..., min_length=1, max_length=800)
    author: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=40)
    template: str | None = Field(default=None, max_length=120)
    size: str | None = Field(default=None, max_length=80)
    theme: str | None = Field(default=None, max_length=120)
    output: Literal["base64", "png"] = "base64"


class QuoteResponse(BaseModel):
    mime_type: str
    image_base64: str
    source: str
