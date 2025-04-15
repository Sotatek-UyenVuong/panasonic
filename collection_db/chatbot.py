from typing import List
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field
from pydantic.types import datetime as pydantic_datetime

class HistoryItem(BaseModel):
    question: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DocumentRef(BaseModel):
    id_document: str

class Chatbot(Document):
    chatbot_id: str = Field(unique=True)
    document: DocumentRef
    history: List[HistoryItem] = Field(default_factory=list)
    created_at: pydantic_datetime = Field(default_factory=datetime.utcnow)
    updated_at: pydantic_datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chatbot"
        indexes = [
            [("chatbot_id", 1)],                # Unique index
            [("document.id_document", 1)],      # Index for document reference
            [("updated_at", -1)]               # Time-based index
        ] 