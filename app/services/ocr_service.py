"""
OCR Service Module
Supports Tesseract and EasyOCR for scanned documents
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

import pytesseract
import easyocr
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
from loguru import logger

from app.core.config import settings


class OCRService:
    """Optical Character Recognition service with multiple engines"""

    def __init__(self, engine: str = 'tesseract'):
        """
        Initialize OCR service

        Args:
            engine: OCR engine to use ('tesseract' or 'easyocr')
        """
        self.engine = engine

        # Configure Tesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        # Initialize EasyOCR reader (lazy loading)
        self._easyocr_reader = None

    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self._easyocr_reader is None:
            logger.info("Initializing EasyOCR reader...")
            self._easyocr_reader = easyocr.Reader(settings.EASYOCR_LANGUAGES)
        return self._easyocr_reader

    def process_image(self, image_path: str, engine: Optional[str] = None) -> Dict:
        """
        Extract text from an image using OCR

        Args:
            image_path: Path to image file
            engine: OCR engine to use (overrides default)

        Returns:
            Dictionary with extracted text and metadata
        """
        engine = engine or self.engine

        logger.info(f"Processing image with {engine}: {image_path}")

        # Preprocess image
        processed_image = self._preprocess_image(image_path)

        if engine == 'tesseract':
            return self._ocr_tesseract(processed_image, image_path)
        elif engine == 'easyocr':
            return self._ocr_easyocr(processed_image, image_path)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")

    def process_pdf(self, pdf_path: str, engine: Optional[str] = None) -> Dict:
        """
        Extract text from scanned PDF using OCR

        Args:
            pdf_path: Path to PDF file
            engine: OCR engine to use

        Returns:
            Dictionary with extracted text from all pages
        """
        engine = engine or self.engine

        logger.info(f"Converting PDF to images: {pdf_path}")

        result = {
            'text': '',
            'pages': [],
            'metadata': {
                'ocr_engine': engine
            }
        }

        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)

            result['metadata']['num_pages'] = len(images)

            # Process each page
            for page_num, image in enumerate(images, 1):
                logger.info(f"OCR processing page {page_num}/{len(images)}")

                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    image.save(tmp_file.name, 'PNG')
                    tmp_path = tmp_file.name

                try:
                    # Process with OCR
                    page_result = self.process_image(tmp_path, engine)

                    result['pages'].append({
                        'page_number': page_num,
                        'text': page_result['text'],
                        'confidence': page_result.get('confidence'),
                        'word_count': len(page_result['text'].split())
                    })

                    result['text'] += page_result['text'] + '\n\n'

                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Error processing PDF with OCR: {str(e)}")
            raise

        return result

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results

        Args:
            image_path: Path to image

        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        img = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Deskew if needed
        deskewed = self._deskew(thresh)

        return deskewed

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Correct image skew"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def _ocr_tesseract(self, image: np.ndarray, image_path: str) -> Dict:
        """
        Perform OCR using Tesseract

        Args:
            image: Preprocessed image
            image_path: Original image path

        Returns:
            OCR results dictionary
        """
        try:
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(image)

            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Extract word-level details
            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:
                    words.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': {
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })

            result = {
                'text': text,
                'confidence': avg_confidence,
                'words': words,
                'engine': 'tesseract',
                'language': 'eng'
            }

            logger.info(f"Tesseract OCR completed with {avg_confidence:.2f}% confidence")

            return result

        except Exception as e:
            logger.error(f"Tesseract OCR error: {str(e)}")
            raise

    def _ocr_easyocr(self, image: np.ndarray, image_path: str) -> Dict:
        """
        Perform OCR using EasyOCR

        Args:
            image: Preprocessed image
            image_path: Original image path

        Returns:
            OCR results dictionary
        """
        try:
            # EasyOCR works better with original image
            original_image = cv2.imread(image_path)

            # Perform OCR
            results = self.easyocr_reader.readtext(original_image)

            # Parse results
            text_parts = []
            words = []
            confidences = []

            for (bbox, text, confidence) in results:
                text_parts.append(text)
                confidences.append(confidence)

                words.append({
                    'text': text,
                    'confidence': confidence * 100,  # Convert to percentage
                    'bbox': {
                        'points': bbox
                    }
                })

            full_text = ' '.join(text_parts)
            avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 0

            result = {
                'text': full_text,
                'confidence': avg_confidence,
                'words': words,
                'engine': 'easyocr',
                'language': settings.EASYOCR_LANGUAGES
            }

            logger.info(f"EasyOCR completed with {avg_confidence:.2f}% confidence")

            return result

        except Exception as e:
            logger.error(f"EasyOCR error: {str(e)}")
            raise

    def compare_engines(self, image_path: str) -> Dict:
        """
        Compare results from both OCR engines

        Args:
            image_path: Path to image

        Returns:
            Comparison results
        """
        processed_image = self._preprocess_image(image_path)

        tesseract_result = self._ocr_tesseract(processed_image, image_path)
        easyocr_result = self._ocr_easyocr(processed_image, image_path)

        return {
            'tesseract': tesseract_result,
            'easyocr': easyocr_result,
            'comparison': {
                'tesseract_confidence': tesseract_result['confidence'],
                'easyocr_confidence': easyocr_result['confidence'],
                'tesseract_word_count': len(tesseract_result['text'].split()),
                'easyocr_word_count': len(easyocr_result['text'].split())
            }
        }
