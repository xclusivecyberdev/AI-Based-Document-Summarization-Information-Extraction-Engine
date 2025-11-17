"""
Document upload and processing endpoints
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.database import get_db, User, Document
from app.schemas.schemas import DocumentUploadResponse
from app.services.document_processor import DocumentProcessor
from app.services.ocr_service import OCRService
from loguru import logger

router = APIRouter(prefix="/api/documents", tags=["Documents"])

document_processor = DocumentProcessor()
ocr_service = OCRService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a document for processing"""
    # Validate file type
    if not document_processor.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {document_processor.supported_extensions}"
        )

    # Check file size
    contents = await file.read()
    file_size = len(contents)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
        )

    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix

    # Save file
    file_path = Path(settings.UPLOAD_DIR) / f"{file_id}{file_extension}"
    with open(file_path, "wb") as f:
        f.write(contents)

    # Get file type
    file_type = document_processor.get_file_type(file.filename)

    # Save to database
    db_document = Document(
        file_id=file_id,
        filename=file.filename,
        file_type=file_type,
        file_path=str(file_path),
        size=file_size,
        user_id=current_user.id,
        upload_time=datetime.utcnow(),
        status="uploaded"
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    logger.info(f"Document uploaded: {file_id} - {file.filename}")

    return DocumentUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file_type,
        size=file_size,
        upload_time=db_document.upload_time,
        status="uploaded"
    )


@router.get("/{file_id}/process")
async def process_document(
    file_id: str,
    use_ocr: bool = False,
    ocr_engine: str = "tesseract",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process a document and extract text"""
    # Get document from database
    document = db.query(Document).filter(Document.file_id == file_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Process document
        result = document_processor.process_document(document.file_path)

        # Apply OCR if needed
        if use_ocr or result.get('requires_ocr'):
            logger.info(f"Applying OCR to document: {file_id}")

            if result.get('file_type') == 'image':
                ocr_result = ocr_service.process_image(document.file_path, engine=ocr_engine)
                result['text'] = ocr_result['text']
                result['ocr_metadata'] = {
                    'engine': ocr_result['engine'],
                    'confidence': ocr_result.get('confidence')
                }
            elif result.get('file_type') == 'pdf':
                # Check if PDF has text
                if len(result.get('text', '').strip()) < 100:
                    ocr_result = ocr_service.process_pdf(document.file_path, engine=ocr_engine)
                    result['text'] = ocr_result['text']
                    result['ocr_metadata'] = {
                        'engine': ocr_result['engine'],
                        'pages_processed': ocr_result['metadata']['num_pages']
                    }

        # Update document status
        document.processed = True
        document.status = "processed"
        db.commit()

        logger.info(f"Document processed successfully: {file_id}")

        return {
            "file_id": file_id,
            "status": "processed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error processing document {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/{file_id}")
async def get_document_info(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get document information"""
    document = db.query(Document).filter(Document.file_id == file_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "file_id": document.file_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "size": document.size,
        "upload_time": document.upload_time,
        "processed": document.processed,
        "status": document.status
    }


@router.delete("/{file_id}")
async def delete_document(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document"""
    document = db.query(Document).filter(Document.file_id == file_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully", "file_id": file_id}


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List user's documents"""
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return [
        {
            "file_id": doc.file_id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "size": doc.size,
            "upload_time": doc.upload_time,
            "processed": doc.processed,
            "status": doc.status
        }
        for doc in documents
    ]
