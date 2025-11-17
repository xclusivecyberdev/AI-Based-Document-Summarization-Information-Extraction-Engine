"""
Unit tests for summarization services
"""
import pytest
from app.services.extractive_summarizer import ExtractiveSummarizer

# Sample text for testing
SAMPLE_TEXT = """
Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural
intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of
"intelligent agents": any device that perceives its environment and takes actions that maximize its
chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often
used to describe machines (or computers) that mimic "cognitive" functions that humans associate with
the human mind, such as "learning" and "problem solving".

As machines become increasingly capable, tasks considered to require "intelligence" are often removed
from the definition of AI, a phenomenon known as the AI effect. A quip in Tesler's Theorem says
"AI is whatever hasn't been done yet." For instance, optical character recognition is frequently
excluded from things considered to be AI, having become a routine technology. Modern machine learning
capabilities falling under the umbrella of AI include successfully understanding human speech,
competing at the highest level in strategic game systems, autonomously operating cars, intelligent
routing in content delivery networks, and military simulations.
"""


class TestExtractiveSummarizer:
    """Test extractive summarization"""

    def setup_method(self):
        """Setup test fixtures"""
        self.summarizer = ExtractiveSummarizer()

    def test_textrank_summarization(self):
        """Test TextRank summarization"""
        result = self.summarizer.summarize(
            SAMPLE_TEXT,
            method='textrank',
            summary_length='short'
        )

        assert result is not None
        assert 'summary' in result
        assert 'method' in result
        assert result['method'] == 'textrank'
        assert len(result['summary']) > 0
        assert len(result['summary']) < len(SAMPLE_TEXT)

    def test_lsa_summarization(self):
        """Test LSA summarization"""
        result = self.summarizer.summarize(
            SAMPLE_TEXT,
            method='lsa',
            summary_length='medium'
        )

        assert result is not None
        assert result['method'] == 'lsa'
        assert result['compression_ratio'] < 1.0

    def test_sentence_count(self):
        """Test specific sentence count"""
        result = self.summarizer.summarize(
            SAMPLE_TEXT,
            method='textrank',
            sentence_count=2
        )

        assert result['sentence_count'] <= 3  # Allow some variation

    def test_bullet_summary(self):
        """Test bullet point summary"""
        result = self.summarizer.summarize_with_bullets(
            SAMPLE_TEXT,
            bullet_count=3
        )

        assert 'bullets' in result
        assert len(result['bullets']) <= 3

    def test_all_methods(self):
        """Test all summarization methods"""
        results = self.summarizer.summarize_all_methods(SAMPLE_TEXT)

        assert 'textrank' in results
        assert 'lsa' in results
        assert 'luhn' in results
        assert 'lexrank' in results


class TestNLPPipeline:
    """Test NLP pipeline"""

    def test_text_cleaning(self):
        """Test text cleaning"""
        from app.services.nlp_pipeline import NLPPipeline

        pipeline = NLPPipeline()

        dirty_text = "  This is a test.   Multiple  spaces.  "
        cleaned = pipeline.clean_text(dirty_text)

        assert cleaned == "This is a test. Multiple spaces."

    def test_tokenization(self):
        """Test tokenization"""
        from app.services.nlp_pipeline import NLPPipeline

        pipeline = NLPPipeline()

        text = "This is a test. Second sentence."
        sentences = pipeline.sentence_tokenize(text)

        assert len(sentences) == 2

        words = pipeline.word_tokenize(text)
        assert len(words) > 0


class TestInformationExtractor:
    """Test information extraction"""

    def test_email_extraction(self):
        """Test email extraction"""
        from app.services.information_extractor import InformationExtractor

        extractor = InformationExtractor()

        text = "Contact us at support@example.com or sales@company.org"
        emails = extractor.extract_emails(text)

        assert len(emails) == 2
        assert any(e['email'] == 'support@example.com' for e in emails)

    def test_phone_extraction(self):
        """Test phone number extraction"""
        from app.services.information_extractor import InformationExtractor

        extractor = InformationExtractor()

        text = "Call us at (123) 456-7890 or 555-123-4567"
        phones = extractor.extract_phone_numbers(text)

        assert len(phones) >= 1

    def test_monetary_extraction(self):
        """Test monetary value extraction"""
        from app.services.information_extractor import InformationExtractor

        extractor = InformationExtractor()

        text = "The price is $1,234.56 or 500 USD"
        monetary = extractor.extract_monetary_values(text)

        assert len(monetary) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
