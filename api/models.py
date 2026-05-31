from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    innkalling = "innkalling"
    saksdokument = "saksdokument"
    protokoll = "protokoll"
    vedlegg = "vedlegg"


class EnrichmentType(str, Enum):
    law = "law"
    news = "news"
    research = "research"
    municipal_comparison = "municipal_comparison"
    budget = "budget"


class ContentType(str, Enum):
    tale = "tale"
    leserinnlegg = "leserinnlegg"


class SummaryCreate(BaseModel):
    length_setting: int = Field(default=50, ge=1, le=100)


class EnrichmentRequest(BaseModel):
    types: List[EnrichmentType]


class ContentGenerateRequest(BaseModel):
    content_type: ContentType
    length_setting: int = Field(default=50, ge=1, le=100)
    sentiment_setting: int = Field(default=50, ge=1, le=100)


class StyleMemoryCreate(BaseModel):
    content_type: ContentType
    example_text: str


class PoliticalContextCreate(BaseModel):
    topic: str
    stance: str
    notes: Optional[str] = None


class SettingsUpdate(BaseModel):
    user_name: Optional[str] = None
    party: Optional[str] = None
    portal_url: Optional[str] = None
