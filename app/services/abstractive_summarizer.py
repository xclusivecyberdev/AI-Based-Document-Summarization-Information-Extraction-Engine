"""
Abstractive Summarization Module
Uses transformer models (BART, T5, GPT, etc.) for abstractive summarization
"""
from typing import Dict, List, Optional
import torch
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    BartForConditionalGeneration,
    BartTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer
)
from loguru import logger

from app.core.config import settings


class AbstractiveSummarizer:
    """Abstractive summarization using transformer models"""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize abstractive summarizer

        Args:
            model_name: Model to use (default: BART)
            device: Device to run on ('cpu' or 'cuda')
        """
        self.model_name = model_name or settings.DEFAULT_SUMMARIZATION_MODEL
        self.device = device or settings.DEVICE

        logger.info(f"Loading summarization model: {self.model_name}")

        # Initialize model and tokenizer
        self.tokenizer = None
        self.model = None
        self.pipeline = None

        self._load_model()

    def _load_model(self):
        """Load the summarization model"""
        try:
            # Use pipeline for simplicity
            self.pipeline = pipeline(
                "summarization",
                model=self.model_name,
                device=0 if self.device == 'cuda' and torch.cuda.is_available() else -1
            )

            # Also load tokenizer and model separately for more control
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

            if self.device == 'cuda' and torch.cuda.is_available():
                self.model = self.model.to('cuda')

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def summarize(
        self,
        text: str,
        summary_length: str = 'medium',
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        num_beams: int = 4,
        length_penalty: float = 2.0,
        early_stopping: bool = True
    ) -> Dict:
        """
        Generate abstractive summary

        Args:
            text: Input text
            summary_length: Predefined length ('short', 'medium', 'long')
            min_length: Minimum summary length in tokens
            max_length: Maximum summary length in tokens
            num_beams: Number of beams for beam search
            length_penalty: Length penalty for generation
            early_stopping: Whether to stop early

        Returns:
            Summary dictionary
        """
        logger.info(f"Generating abstractive summary with length: {summary_length}")

        # Calculate lengths if not specified
        if min_length is None or max_length is None:
            min_length, max_length = self._calculate_lengths(text, summary_length)

        try:
            # Generate summary using pipeline
            summary_output = self.pipeline(
                text,
                min_length=min_length,
                max_length=max_length,
                num_beams=num_beams,
                length_penalty=length_penalty,
                early_stopping=early_stopping,
                truncation=True
            )

            summary_text = summary_output[0]['summary_text']

            result = {
                'summary': summary_text,
                'method': 'abstractive',
                'model': self.model_name,
                'original_length': len(text),
                'summary_length': len(summary_text),
                'compression_ratio': len(summary_text) / len(text) if text else 0,
                'parameters': {
                    'min_length': min_length,
                    'max_length': max_length,
                    'num_beams': num_beams,
                    'length_penalty': length_penalty
                }
            }

            return result

        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise

    def summarize_long_document(
        self,
        text: str,
        chunk_size: int = 1024,
        summary_length: str = 'medium'
    ) -> Dict:
        """
        Summarize long documents by chunking

        Args:
            text: Input text
            chunk_size: Size of each chunk
            summary_length: Summary length

        Returns:
            Summary of long document
        """
        logger.info("Summarizing long document with chunking")

        # Split into chunks
        chunks = self._chunk_text(text, chunk_size)

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")

            try:
                chunk_summary = self.summarize(
                    chunk,
                    summary_length='short'  # Use short summaries for chunks
                )
                chunk_summaries.append(chunk_summary['summary'])
            except Exception as e:
                logger.warning(f"Error summarizing chunk {i+1}: {str(e)}")
                continue

        # Combine chunk summaries
        combined_text = ' '.join(chunk_summaries)

        # Summarize the combined summaries
        if len(chunk_summaries) > 1:
            final_summary = self.summarize(combined_text, summary_length)
        else:
            final_summary = {
                'summary': combined_text,
                'method': 'abstractive',
                'model': self.model_name
            }

        final_summary['chunks_processed'] = len(chunks)
        final_summary['chunking_method'] = 'recursive'

        return final_summary

    def summarize_with_bullets(
        self,
        text: str,
        bullet_count: int = 5
    ) -> Dict:
        """
        Generate bullet-point summary

        Args:
            text: Input text
            bullet_count: Number of bullet points

        Returns:
            Bullet-point summary
        """
        # First generate a summary
        summary = self.summarize(text, summary_length='medium')

        # Split into sentences
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(summary['summary'])

        # Select top sentences as bullets
        bullets = [f"• {sent}" for sent in sentences[:bullet_count]]

        return {
            'bullets': bullets,
            'bullet_text': '\n'.join(bullets),
            'count': len(bullets),
            'method': 'abstractive',
            'model': self.model_name
        }

    def generate_multiple_summaries(
        self,
        text: str,
        num_summaries: int = 3,
        temperature: float = 1.0
    ) -> List[Dict]:
        """
        Generate multiple diverse summaries

        Args:
            text: Input text
            num_summaries: Number of summaries to generate
            temperature: Sampling temperature

        Returns:
            List of summaries
        """
        summaries = []

        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=1024,
            truncation=True,
            return_tensors='pt'
        )

        if self.device == 'cuda' and torch.cuda.is_available():
            inputs = {k: v.to('cuda') for k, v in inputs.items()}

        for i in range(num_summaries):
            # Generate with different seeds
            torch.manual_seed(42 + i)

            outputs = self.model.generate(
                **inputs,
                max_length=150,
                min_length=40,
                do_sample=True,
                temperature=temperature,
                top_k=50,
                top_p=0.95,
                num_return_sequences=1
            )

            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            summaries.append({
                'summary': summary,
                'variant': i + 1,
                'temperature': temperature
            })

        return summaries

    def get_summary_with_explanation(
        self,
        text: str,
        summary_length: str = 'medium'
    ) -> Dict:
        """
        Generate summary with explanation of what was extracted

        Args:
            text: Input text
            summary_length: Summary length

        Returns:
            Summary with explanation
        """
        # Generate summary
        summary_result = self.summarize(text, summary_length)

        # Tokenize both texts
        from nltk.tokenize import sent_tokenize, word_tokenize

        original_sentences = sent_tokenize(text)
        summary_sentences = sent_tokenize(summary_result['summary'])

        # Find which parts of original text are most similar to summary
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Calculate similarity
        vectorizer = TfidfVectorizer()

        try:
            all_sentences = original_sentences + summary_sentences
            tfidf_matrix = vectorizer.fit_transform(all_sentences)

            original_vectors = tfidf_matrix[:len(original_sentences)]
            summary_vectors = tfidf_matrix[len(original_sentences):]

            similarities = cosine_similarity(summary_vectors, original_vectors)

            # Find most relevant original sentences
            relevant_sentences = []
            for i, summary_sent in enumerate(summary_sentences):
                most_similar_idx = similarities[i].argmax()
                similarity_score = similarities[i][most_similar_idx]

                if similarity_score > 0.1:  # Threshold
                    relevant_sentences.append({
                        'summary_sentence': summary_sent,
                        'original_sentence': original_sentences[most_similar_idx],
                        'similarity': float(similarity_score),
                        'position': most_similar_idx
                    })

            summary_result['explanation'] = {
                'relevant_sentences': relevant_sentences,
                'coverage': len(relevant_sentences) / len(summary_sentences) if summary_sentences else 0
            }

        except Exception as e:
            logger.warning(f"Could not generate explanation: {str(e)}")
            summary_result['explanation'] = None

        return summary_result

    def _calculate_lengths(self, text: str, summary_length: str) -> tuple:
        """Calculate min and max lengths based on input"""
        word_count = len(text.split())

        if summary_length == 'short':
            min_length = max(30, int(word_count * 0.05))
            max_length = max(50, int(word_count * 0.10))
        elif summary_length == 'medium':
            min_length = max(50, int(word_count * 0.10))
            max_length = max(130, int(word_count * 0.20))
        elif summary_length == 'long':
            min_length = max(100, int(word_count * 0.20))
            max_length = max(200, int(word_count * 0.40))
        else:
            min_length = 50
            max_length = 130

        return min_length, max_length

    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks
