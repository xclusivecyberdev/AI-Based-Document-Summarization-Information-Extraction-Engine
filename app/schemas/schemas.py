"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SummaryLength(str, Enum):
    """Summary length options"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class SummarizationMethod(str, Enum):
    """Summarization methods"""
    TEXTRANK = "textrank"
    LSA = "lsa"
    LUHN = "luhn"
    LEXRANK = "lexrank"
    ABSTRACTIVE = "abstractive"


class OCREngine(str, Enum):
    """OCR engines"""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


# Authentication Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Document Processing Schemas
class DocumentUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    size: int
    upload_time: datetime
    status: str


class SummarizationRequest(BaseModel):
    text: Optional[str] = None
    file_id: Optional[str] = None
    method: SummarizationMethod = SummarizationMethod.ABSTRACTIVE
    summary_length: SummaryLength = SummaryLength.MEDIUM
    include_bullets: bool = False
    sentence_count: Optional[int] = None


class SummarizationResponse(BaseModel):
    summary: str
    method: str
    sentence_count: int
    original_length: int
    summary_length: int
    compression_ratio: float
    bullets: Optional[List[str]] = None
    metadata: Optional[Dict] = None


class NLPAnalysisRequest(BaseModel):
    text: Optional[str] = None
    file_id: Optional[str] = None
    include_entities: bool = True
    include_keywords: bool = True
    include_pos: bool = False
    chunk_size: int = 512


class InformationExtractionRequest(BaseModel):
    text: Optional[str] = None
    file_id: Optional[str] = None
    extract_persons: bool = True
    extract_organizations: bool = True
    extract_dates: bool = True
    extract_monetary: bool = True
    extract_emails: bool = True
    extract_phones: bool = True
    extract_cybersecurity: bool = False
    extract_medical: bool = False


class TopicModelingRequest(BaseModel):
    text: Optional[str] = None
    file_id: Optional[str] = None
    num_topics: int = Field(default=5, ge=2, le=20)
    method: str = "lda"  # lda, nmf, gensim


class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: str = "all-MiniLM-L6-v2"


class SimilaritySearchRequest(BaseModel):
    query: str
    documents: List[str]
    top_k: int = Field(default=5, ge=1, le=50)


class OCRRequest(BaseModel):
    file_id: str
    engine: OCREngine = OCREngine.TESSERACT


class ExportRequest(BaseModel):
    file_id: str
    content: str
    format: str = "docx"  # docx or pdf
    include_metadata: bool = True


# Response Schemas
class NLPAnalysisResponse(BaseModel):
    cleaned_text: str
    word_count: int
    sentence_count: int
    entities: Optional[Dict] = None
    keywords: Optional[Dict] = None
    pos_tags: Optional[List] = None
    statistics: Dict


class InformationExtractionResponse(BaseModel):
    persons: List[Dict]
    organizations: List[Dict]
    locations: List[Dict]
    dates: List[Dict]
    monetary_values: List[Dict]
    emails: List[Dict]
    phone_numbers: List[Dict]
    addresses: List[Dict]
    urls: List[Dict]
    legal_references: Optional[List[Dict]] = None
    cybersecurity_indicators: Optional[Dict] = None
    medical_terms: Optional[List[Dict]] = None


class TopicModelingResponse(BaseModel):
    topics: List[Dict]
    num_topics: int
    method: str
    coherence_score: Optional[float] = None


class UsageLog(BaseModel):
    user_id: str
    action: str
    timestamp: datetime
    details: Optional[Dict] = None
