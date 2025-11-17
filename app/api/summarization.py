"""
Summarization API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.models.database import get_db, User, Document, Summary
from app.schemas.schemas import SummarizationRequest, SummarizationResponse
from app.services.extractive_summarizer import ExtractiveSummarizer
from app.services.abstractive_summarizer import AbstractiveSummarizer
from app.services.document_processor import DocumentProcessor
from loguru import logger

router = APIRouter(prefix="/api/summarize", tags=["Summarization"])

extractive_summarizer = ExtractiveSummarizer()
abstractive_summarizer = None  # Lazy load
document_processor = DocumentProcessor()


def get_abstractive_summarizer():
    """Lazy load abstractive summarizer"""
    global abstractive_summarizer
    if abstractive_summarizer is None:
        abstractive_summarizer = AbstractiveSummarizer()
    return abstractive_summarizer


@router.post("/", response_model=SummarizationResponse)
async def summarize_text(
    request: SummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Summarize text or document"""
    # Get text from request or file
    text = request.text

    if not text and request.file_id:
        # Load from file
        document = db.query(Document).filter(Document.file_id == request.file_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Process document if not already processed
        if not document.processed:
            result = document_processor.process_document(document.file_path)
            text = result['text']
        else:
            result = document_processor.process_document(document.file_path)
            text = result['text']

    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # Generate summary based on method
        if request.method == 'abstractive':
            summarizer = get_abstractive_summarizer()

            if request.sentence_count:
                # Approximate with max_length
                max_length = request.sentence_count * 20
                summary_result = summarizer.summarize(
                    text,
                    max_length=max_length,
                    min_length=max(10, max_length // 2)
                )
            else:
                summary_result = summarizer.summarize(text, summary_length=request.summary_length.value)

        else:
            # Extractive methods
            summary_result = extractive_summarizer.summarize(
                text,
                method=request.method.value,
                summary_length=request.summary_length.value,
                sentence_count=request.sentence_count
            )

        # Generate bullets if requested
        bullets = None
        if request.include_bullets:
            from nltk.tokenize import sent_tokenize
            sentences = sent_tokenize(summary_result['summary'])[:5]
            bullets = [f"• {sent}" for sent in sentences]

        # Save summary to database if associated with a file
        if request.file_id:
            db_summary = Summary(
                file_id=request.file_id,
                summary_text=summary_result['summary'],
                method=request.method.value,
                summary_length=request.summary_length.value,
                compression_ratio=summary_result.get('compression_ratio', 0)
            )
            db.add(db_summary)
            db.commit()

        logger.info(f"Summary generated using {request.method.value}")

        return SummarizationResponse(
            summary=summary_result['summary'],
            method=summary_result.get('method', request.method.value),
            sentence_count=summary_result.get('sentence_count', len(summary_result['summary'].split('.'))),
            original_length=summary_result.get('original_length', len(text)),
            summary_length=summary_result.get('summary_length', len(summary_result['summary'])),
            compression_ratio=summary_result.get('compression_ratio', 0),
            bullets=bullets,
            metadata=summary_result
        )

    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/compare")
async def compare_summaries(
    request: SummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Compare summaries from different methods"""
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
        # Generate summaries with all extractive methods
        extractive_summaries = extractive_summarizer.summarize_all_methods(
            text,
            summary_length=request.summary_length.value
        )

        # Generate abstractive summary
        try:
            summarizer = get_abstractive_summarizer()
            abstractive_summary = summarizer.summarize(text, summary_length=request.summary_length.value)
            extractive_summaries['abstractive'] = abstractive_summary
        except Exception as e:
            logger.warning(f"Abstractive summarization failed: {str(e)}")

        return {
            "summaries": extractive_summaries,
            "comparison": {
                "methods_compared": list(extractive_summaries.keys()),
                "original_length": len(text)
            }
        }

    except Exception as e:
        logger.error(f"Summary comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/bullets")
async def generate_bullet_summary(
    request: SummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate bullet-point summary"""
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

    bullet_count = request.sentence_count or 5

    try:
        if request.method == 'abstractive':
            summarizer = get_abstractive_summarizer()
            bullets_result = summarizer.summarize_with_bullets(text, bullet_count)
        else:
            bullets_result = extractive_summarizer.summarize_with_bullets(
                text,
                bullet_count,
                method=request.method.value
            )

        return bullets_result

    except Exception as e:
        logger.error(f"Bullet summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bullet summary failed: {str(e)}")


@router.get("/{file_id}/history")
async def get_summary_history(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary history for a document"""
    # Verify document ownership
    document = db.query(Document).filter(Document.file_id == file_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get summaries
    summaries = db.query(Summary).filter(Summary.file_id == file_id).all()

    return [
        {
            "summary_text": summary.summary_text,
            "method": summary.method,
            "summary_length": summary.summary_length,
            "compression_ratio": summary.compression_ratio,
            "created_at": summary.created_at
        }
        for summary in summaries
    ]
