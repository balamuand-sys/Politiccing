from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    innkalling = "innkalling"
    saksdokument = "saksdokument"
    protokoll = "protokoll"
    vedlegg = "vedlegg"


class DocumentSource(str, Enum):
    upload = "upload"
    scrape = "scrape"


class EnrichmentType(str, Enum):
    law = "law"
    news = "news"
    research = "research"
    municipal_comparison = "municipal_comparison"
    budget = "budget"


class ContentType(str, Enum):
    tale = "tale"
    leserinnlegg = "leserinnlegg"


class DocumentBase(BaseModel):
    title: str
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
    document_type: Optional[DocumentType] = None
    source: Optional[DocumentSource] = None


class DocumentCreate(DocumentBase):
    raw_text: str
    file_path: Optional[str] = None


class Document(DocumentBase):
    id: int
    raw_text: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    id: int
    title: str
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
    document_type: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryCreate(BaseModel):
    length_setting: int = Field(default=50, ge=1, le=100)


class Summary(BaseModel):
    id: int
    document_id: int
    summary_text: str
    length_setting: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnrichmentRequest(BaseModel):
    types: List[EnrichmentType]


class Enrichment(BaseModel):
    id: int
    document_id: int
    enrichment_type: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContentGenerateRequest(BaseModel):
    content_type: ContentType
    length_setting: int = Field(default=50, ge=1, le=100)
    sentiment_setting: int = Field(default=50, ge=1, le=100)


class GeneratedContent(BaseModel):
    id: int
    document_id: int
    content_type: str
    content_text: str
    length_setting: int
    sentiment_setting: int
    created_at: datetime

    class Config:
        from_attributes = True


class StyleMemoryCreate(BaseModel):
    content_type: ContentType
    example_text: str


class StyleMemory(BaseModel):
    id: int
    content_type: str
    example_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class PoliticalContextCreate(BaseModel):
    topic: str
    stance: str
    notes: Optional[str] = None


class PoliticalContext(BaseModel):
    id: int
    topic: str
    stance: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    portal_url: Optional[str] = None
    user_name: Optional[str] = None
    party: Optional[str] = None


class Settings(BaseModel):
    api_key: Optional[str] = None
    portal_url: Optional[str] = None
    user_name: Optional[str] = None
    party: Optional[str] = None


class SearchResult(BaseModel):
    document_id: int
    title: str
    chunk_text: str
    score: float
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
