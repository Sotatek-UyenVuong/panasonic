from typing import List
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field
from pydantic.types import datetime as pydantic_datetime

class Image(BaseModel):
    id: str
    image_b64: str

class Page(Document):
    document_id: str
    page_id: str = Field(unique=True)
    page_number: int
    markdown: str
    images: List[Image] = Field(default_factory=list)
    created_at: pydantic_datetime = Field(default_factory=datetime.utcnow)
    updated_at: pydantic_datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "page"
        indexes = [
            [("document_id", 1)],      # Index for document reference
            [("page_id", 1)],          # Unique index
            [("page_number", 1)],      # Index for page ordering
            [("updated_at", -1)]       # Time-based index
        ] 