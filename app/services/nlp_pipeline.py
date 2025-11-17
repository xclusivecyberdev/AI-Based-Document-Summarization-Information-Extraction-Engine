"""
NLP Preprocessing Pipeline
Handles cleaning, tokenization, chunking, POS tagging, NER, keyword extraction
"""
import re
from typing import Dict, List, Tuple, Optional
import string

import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag
import yake
from rake_nltk import Rake
from bs4 import BeautifulSoup
from loguru import logger

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class NLPPipeline:
    """Comprehensive NLP preprocessing and analysis pipeline"""

    def __init__(self, spacy_model: str = 'en_core_web_sm'):
        """
        Initialize NLP pipeline

        Args:
            spacy_model: spaCy model to use
        """
        # Load spaCy model
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"spaCy model {spacy_model} not found. Using blank model.")
            self.nlp = spacy.blank('en')

        # Initialize tools
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

        # Keyword extractors
        self.rake = Rake()
        self.yake_extractor = yake.KeywordExtractor()

    def process(self, text: str, options: Optional[Dict] = None) -> Dict:
        """
        Run complete NLP pipeline on text

        Args:
            text: Input text
            options: Processing options

        Returns:
            Dictionary with all NLP analysis results
        """
        options = options or {}

        logger.info("Running NLP pipeline...")

        # Clean text
        cleaned_text = self.clean_text(text)

        # Tokenization
        sentences = self.sentence_tokenize(cleaned_text)
        words = self.word_tokenize(cleaned_text)

        # Process with spaCy
        doc = self.nlp(cleaned_text)

        # POS tagging
        pos_tags = self.pos_tag(cleaned_text)

        # Named Entity Recognition
        entities = self.extract_entities(doc)

        # Keyword extraction
        keywords = self.extract_keywords(cleaned_text)

        # Chunking
        chunks = self.chunk_text(cleaned_text, chunk_size=options.get('chunk_size', 512))

        result = {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'sentences': sentences,
            'sentence_count': len(sentences),
            'words': words,
            'word_count': len(words),
            'pos_tags': pos_tags,
            'entities': entities,
            'keywords': keywords,
            'chunks': chunks,
            'statistics': self._calculate_statistics(cleaned_text, sentences, words)
        }

        return result

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove HTML tags
        text = BeautifulSoup(text, 'html.parser').get_text()

        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        # text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-\'\"]', '', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def sentence_tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        return sent_tokenize(text)

    def word_tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words

        Args:
            text: Input text

        Returns:
            List of words
        """
        return word_tokenize(text)

    def pos_tag(self, text: str) -> List[Tuple[str, str]]:
        """
        Perform Part-of-Speech tagging

        Args:
            text: Input text

        Returns:
            List of (word, POS tag) tuples
        """
        words = word_tokenize(text)
        return pos_tag(words)

    def extract_entities(self, doc) -> Dict[str, List[Dict]]:
        """
        Extract named entities using spaCy

        Args:
            doc: spaCy Doc object

        Returns:
            Dictionary of entities grouped by type
        """
        entities = {}

        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []

            entities[ent.label_].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'label': ent.label_
            })

        return entities

    def extract_keywords(self, text: str, top_n: int = 20) -> Dict:
        """
        Extract keywords using multiple methods

        Args:
            text: Input text
            top_n: Number of top keywords to extract

        Returns:
            Dictionary with keywords from different methods
        """
        keywords = {}

        # RAKE
        try:
            self.rake.extract_keywords_from_text(text)
            rake_keywords = self.rake.get_ranked_phrases()[:top_n]
            keywords['rake'] = [{'keyword': kw, 'method': 'RAKE'} for kw in rake_keywords]
        except Exception as e:
            logger.warning(f"RAKE extraction failed: {str(e)}")
            keywords['rake'] = []

        # YAKE
        try:
            yake_keywords = self.yake_extractor.extract_keywords(text)
            keywords['yake'] = [
                {'keyword': kw, 'score': score, 'method': 'YAKE'}
                for kw, score in yake_keywords[:top_n]
            ]
        except Exception as e:
            logger.warning(f"YAKE extraction failed: {str(e)}")
            keywords['yake'] = []

        # Simple frequency-based
        try:
            freq_keywords = self._extract_frequency_keywords(text, top_n)
            keywords['frequency'] = freq_keywords
        except Exception as e:
            logger.warning(f"Frequency extraction failed: {str(e)}")
            keywords['frequency'] = []

        return keywords

    def _extract_frequency_keywords(self, text: str, top_n: int) -> List[Dict]:
        """Extract keywords based on frequency"""
        words = word_tokenize(text.lower())

        # Filter out stopwords and punctuation
        filtered_words = [
            word for word in words
            if word not in self.stop_words
            and word not in string.punctuation
            and len(word) > 2
        ]

        # Count frequency
        from collections import Counter
        word_freq = Counter(filtered_words)

        # Get top keywords
        top_keywords = word_freq.most_common(top_n)

        return [
            {'keyword': word, 'frequency': freq, 'method': 'Frequency'}
            for word, freq in top_keywords
        ]

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict]:
        """
        Split text into chunks with optional overlap

        Args:
            text: Input text
            chunk_size: Size of each chunk in tokens
            overlap: Number of overlapping tokens

        Returns:
            List of text chunks with metadata
        """
        sentences = self.sentence_tokenize(text)
        chunks = []

        current_chunk = []
        current_length = 0
        chunk_id = 0

        for sentence in sentences:
            sentence_length = len(word_tokenize(sentence))

            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'word_count': current_length,
                    'sentence_count': len(current_chunk)
                })

                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > 1:
                    # Keep last few sentences for overlap
                    overlap_sentences = []
                    overlap_length = 0

                    for sent in reversed(current_chunk):
                        sent_length = len(word_tokenize(sent))
                        if overlap_length + sent_length <= overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_length += sent_length
                        else:
                            break

                    current_chunk = overlap_sentences
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0

                chunk_id += 1

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'word_count': current_length,
                'sentence_count': len(current_chunk)
            })

        return chunks

    def lemmatize(self, words: List[str]) -> List[str]:
        """Lemmatize words"""
        return [self.lemmatizer.lemmatize(word) for word in words]

    def stem(self, words: List[str]) -> List[str]:
        """Stem words"""
        return [self.stemmer.stem(word) for word in words]

    def remove_stopwords(self, words: List[str]) -> List[str]:
        """Remove stopwords from word list"""
        return [word for word in words if word.lower() not in self.stop_words]

    def _calculate_statistics(
        self,
        text: str,
        sentences: List[str],
        words: List[str]
    ) -> Dict:
        """Calculate text statistics"""
        import textstat

        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
            'gunning_fog': textstat.gunning_fog(text),
            'automated_readability_index': textstat.automated_readability_index(text)
        }
