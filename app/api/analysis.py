"""
NLP Analysis and Information Extraction API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.models.database import get_db, User, Document
from app.schemas.schemas import (
    NLPAnalysisRequest,
    NLPAnalysisResponse,
    InformationExtractionRequest,
    InformationExtractionResponse,
    TopicModelingRequest,
    TopicModelingResponse,
    EmbeddingRequest,
    SimilaritySearchRequest
)
from app.services.nlp_pipeline import NLPPipeline
from app.services.information_extractor import InformationExtractor
from app.services.topic_modeling import TopicModelingService
from app.services.document_processor import DocumentProcessor
from loguru import logger

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

nlp_pipeline = NLPPipeline()
info_extractor = InformationExtractor()
topic_service = TopicModelingService()
document_processor = DocumentProcessor()


@router.post("/nlp", response_model=NLPAnalysisResponse)
async def analyze_text(
    request: NLPAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform comprehensive NLP analysis"""
    # Get text
    text = request.text

    if not text and request.file_id:
        document = db.query(Document).filter(Document.file_id == request.file_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = document_processor.process_document(document.file_path)
        text = result['text']

    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # Run NLP pipeline
        options = {'chunk_size': request.chunk_size}
        analysis = nlp_pipeline.process(text, options)

        # Filter results based on request
        response_data = {
            'cleaned_text': analysis['cleaned_text'],
            'word_count': analysis['word_count'],
            'sentence_count': analysis['sentence_count'],
            'statistics': analysis['statistics']
        }

        if request.include_entities:
            response_data['entities'] = analysis['entities']

        if request.include_keywords:
            response_data['keywords'] = analysis['keywords']

        if request.include_pos:
            response_data['pos_tags'] = analysis['pos_tags']

        return NLPAnalysisResponse(**response_data)

    except Exception as e:
        logger.error(f"NLP analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/extract", response_model=InformationExtractionResponse)
async def extract_information(
    request: InformationExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Extract structured information from text"""
    # Get text
    text = request.text

    if not text and request.file_id:
        document = db.query(Document).filter(Document.file_id == request.file_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = document_processor.process_document(document.file_path)
        text = result['text']

    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # Extract all information
        extracted = info_extractor.extract_all(text)

        # Filter based on request
        response_data = {}

        if request.extract_persons:
            response_data['persons'] = extracted['persons']
        else:
            response_data['persons'] = []

        if request.extract_organizations:
            response_data['organizations'] = extracted['organizations']
        else:
            response_data['organizations'] = []

        response_data['locations'] = extracted['locations']

        if request.extract_dates:
            response_data['dates'] = extracted['dates']
        else:
            response_data['dates'] = []

        if request.extract_monetary:
            response_data['monetary_values'] = extracted['monetary_values']
        else:
            response_data['monetary_values'] = []

        if request.extract_emails:
            response_data['emails'] = extracted['emails']
        else:
            response_data['emails'] = []

        if request.extract_phones:
            response_data['phone_numbers'] = extracted['phone_numbers']
        else:
            response_data['phone_numbers'] = []

        response_data['addresses'] = extracted['addresses']
        response_data['urls'] = extracted['urls']

        if request.extract_cybersecurity:
            response_data['cybersecurity_indicators'] = extracted['cybersecurity_indicators']

        if request.extract_medical:
            response_data['medical_terms'] = extracted['medical_terms']

        response_data['legal_references'] = extracted['legal_references']

        return InformationExtractionResponse(**response_data)

    except Exception as e:
        logger.error(f"Information extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/topics", response_model=TopicModelingResponse)
async def extract_topics(
    request: TopicModelingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Extract topics from text"""
    # Get text
    text = request.text

    if not text and request.file_id:
        document = db.query(Document).filter(Document.file_id == request.file_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = document_processor.process_document(document.file_path)
        text = result['text']

    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # Split text into chunks for topic modeling
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)

        # Group sentences into documents
        chunk_size = max(5, len(sentences) // request.num_topics)
        texts = [
            ' '.join(sentences[i:i+chunk_size])
            for i in range(0, len(sentences), chunk_size)
        ]

        # Extract topics based on method
        if request.method == 'lda':
            topics_result = topic_service.extract_topics_lda(texts, request.num_topics)
        elif request.method == 'nmf':
            topics_result = topic_service.extract_topics_nmf(texts, request.num_topics)
        elif request.method == 'gensim':
            topics_result = topic_service.extract_topics_gensim(texts, request.num_topics)
        else:
            raise ValueError(f"Unknown method: {request.method}")

        return TopicModelingResponse(
            topics=topics_result['topics'],
            num_topics=topics_result['num_topics'],
            method=topics_result['method'],
            coherence_score=topics_result.get('coherence_score')
        )

    except Exception as e:
        logger.error(f"Topic modeling error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Topic modeling failed: {str(e)}")


@router.post("/embeddings")
async def generate_embeddings(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate embeddings for texts"""
    try:
        embeddings = topic_service.generate_embeddings(request.texts)

        return {
            "embeddings": embeddings['embeddings'],
            "shape": embeddings['shape'],
            "model": embeddings['model'],
            "dimension": embeddings['dimension']
        }

    except Exception as e:
        logger.error(f"Embedding generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/similarity")
async def find_similar(
    request: SimilaritySearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Find similar documents"""
    try:
        results = topic_service.find_similar_documents(
            request.query,
            request.documents,
            request.top_k
        )

        return {
            "query": request.query,
            "results": results,
            "top_k": request.top_k
        }

    except Exception as e:
        logger.error(f"Similarity search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")
