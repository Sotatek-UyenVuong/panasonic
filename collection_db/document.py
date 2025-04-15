from datetime import datetime
from beanie import Document
from pydantic import Field
from pydantic.types import datetime as pydantic_datetime
from typing import Optional

class DocumentModel(Document):
    document_id: str = Field(unique=True)
    link_document: str
    model: str = "mistral-ocr-latest"
    documents_path: Optional[str] = None
    vector_path: Optional[str] = None
    created_at: pydantic_datetime = Field(default_factory=datetime.utcnow)
    updated_at: pydantic_datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "document"
        indexes = [
            [("document_id", 1)],  # Unique index
            [("updated_at", -1)]   # Time-based index
        ] 