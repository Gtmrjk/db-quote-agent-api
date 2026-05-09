from typing import Literal

from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    quote: str = Field(..., min_length=1, max_length=800)
    author: str | None = Field(default=None, max_length=120)
    designation: str | None = Field(default=None, max_length=120)
    brand: Literal["bhaskar", "divyabhaskar", "divyamarathi", "englishbhaskar"] = "bhaskar"
    image_base64: str | None = None
    image_mime_type: Literal["image/png", "image/jpeg"] = "image/png"
    image_format: Literal["jpeg", "png"] = "jpeg"
    output: Literal["base64", "png"] = "base64"


class QuoteResponse(BaseModel):
    mime_type: str
    image_base64: str
    source: str
