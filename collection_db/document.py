from datetime import datetime
from beanie import Document
from pydantic import Field
from pydantic.types import datetime as pydantic_datetime

class DocumentModel(Document):
    document_id: str = Field(unique=True)
    link_document: str
    created_at: pydantic_datetime = Field(default_factory=datetime.utcnow)
    updated_at: pydantic_datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "document"
        indexes = [
            [("document_id", 1)],  # Unique index
            [("updated_at", -1)]   # Time-based index
        ] 