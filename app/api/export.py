"""
Export and Visualization API endpoints
"""
import os
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.database import get_db, User, Summary
from app.schemas.schemas import ExportRequest
from app.services.export_service import ExportService
from app.services.visualization_service import VisualizationService
from loguru import logger

router = APIRouter(prefix="/api/export", tags=["Export & Visualization"])

export_service = ExportService()
viz_service = VisualizationService()


@router.post("/docx")
async def export_to_docx(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export summary to DOCX"""
    # Get summary if file_id provided
    if request.file_id:
        summary = db.query(Summary).filter(Summary.file_id == request.file_id).first()

        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")

        content = {
            'summary': summary.summary_text,
            'method': summary.method,
            'compression_ratio': summary.compression_ratio,
            'metadata': {
                'created_at': summary.created_at,
                'summary_length': summary.summary_length
            }
        }
    else:
        content = {'summary': request.content}

    try:
        # Generate filename
        filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        output_path = Path(settings.PROCESSED_DIR) / filename

        # Export
        export_service.export_to_docx(
            content,
            str(output_path),
            include_metadata=request.include_metadata
        )

        logger.info(f"DOCX exported: {filename}")

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(f"Export to DOCX failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/pdf")
async def export_to_pdf(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export summary to PDF"""
    # Get summary if file_id provided
    if request.file_id:
        summary = db.query(Summary).filter(Summary.file_id == request.file_id).first()

        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")

        content = {
            'summary': summary.summary_text,
            'method': summary.method,
            'compression_ratio': summary.compression_ratio,
            'metadata': {
                'created_at': summary.created_at,
                'summary_length': summary.summary_length
            }
        }
    else:
        content = {'summary': request.content}

    try:
        # Generate filename
        filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = Path(settings.PROCESSED_DIR) / filename

        # Export
        export_service.export_to_pdf(
            content,
            str(output_path),
            include_metadata=request.include_metadata
        )

        logger.info(f"PDF exported: {filename}")

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type='application/pdf'
        )

    except Exception as e:
        logger.error(f"Export to PDF failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/visualize/wordcloud")
async def generate_wordcloud(
    text: str,
    current_user: User = Depends(get_current_active_user)
):
    """Generate word cloud visualization"""
    try:
        img_base64 = viz_service.generate_word_cloud(text)

        return {
            "image": img_base64,
            "type": "wordcloud"
        }

    except Exception as e:
        logger.error(f"Word cloud generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/visualize/entities")
async def visualize_entities(
    entities: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Generate entity distribution chart"""
    try:
        img_base64 = viz_service.generate_entity_chart(entities)

        if not img_base64:
            raise HTTPException(status_code=400, detail="No entities to visualize")

        return {
            "image": img_base64,
            "type": "entity_chart"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/visualize/keywords")
async def visualize_keywords(
    keywords: list,
    current_user: User = Depends(get_current_active_user)
):
    """Generate keyword chart"""
    try:
        img_base64 = viz_service.generate_keyword_chart(keywords)

        if not img_base64:
            raise HTTPException(status_code=400, detail="No keywords to visualize")

        return {
            "image": img_base64,
            "type": "keyword_chart"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keyword visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/visualize/topics")
async def visualize_topics(
    topics: list,
    current_user: User = Depends(get_current_active_user)
):
    """Generate topic distribution visualization"""
    try:
        img_base64 = viz_service.generate_topic_distribution(topics)

        if not img_base64:
            raise HTTPException(status_code=400, detail="No topics to visualize")

        return {
            "image": img_base64,
            "type": "topic_chart"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/visualize/statistics")
async def visualize_statistics(
    statistics: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Generate statistics visualization"""
    try:
        img_base64 = viz_service.generate_statistics_chart(statistics)

        return {
            "image": img_base64,
            "type": "statistics_chart"
        }

    except Exception as e:
        logger.error(f"Statistics visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/visualize/summary-comparison")
async def visualize_summary_comparison(
    summaries: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Generate summary comparison visualization"""
    try:
        img_base64 = viz_service.generate_summary_comparison(summaries)

        if not img_base64:
            raise HTTPException(status_code=400, detail="No summaries to compare")

        return {
            "image": img_base64,
            "type": "comparison_chart"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")
