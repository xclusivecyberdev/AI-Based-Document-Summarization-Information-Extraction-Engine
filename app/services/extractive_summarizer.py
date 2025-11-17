"""
Extractive Summarization Module
Implements TextRank, LSA, and other extractive methods
"""
from typing import List, Dict, Optional
import numpy as np

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from nltk.tokenize import sent_tokenize
import networkx as nx

from loguru import logger


class ExtractiveSummarizer:
    """Extractive summarization using multiple algorithms"""

    def __init__(self, language: str = 'english'):
        """
        Initialize extractive summarizer

        Args:
            language: Language for summarization
        """
        self.language = language
        self.stemmer = Stemmer(language)
        self.stop_words = get_stop_words(language)

    def summarize(
        self,
        text: str,
        method: str = 'textrank',
        summary_length: str = 'medium',
        sentence_count: Optional[int] = None
    ) -> Dict:
        """
        Generate extractive summary

        Args:
            text: Input text
            method: Summarization method ('textrank', 'lsa', 'luhn', 'lexrank')
            summary_length: Predefined length ('short', 'medium', 'long')
            sentence_count: Specific number of sentences (overrides summary_length)

        Returns:
            Summary dictionary with sentences and metadata
        """
        logger.info(f"Generating {method} summary with length: {summary_length}")

        # Calculate sentence count if not specified
        if sentence_count is None:
            sentence_count = self._calculate_sentence_count(text, summary_length)

        # Parse text
        parser = PlaintextParser.from_string(text, Tokenizer(self.language))

        # Select summarizer
        if method == 'textrank':
            summarizer = TextRankSummarizer(self.stemmer)
        elif method == 'lsa':
            summarizer = LsaSummarizer(self.stemmer)
        elif method == 'luhn':
            summarizer = LuhnSummarizer(self.stemmer)
        elif method == 'lexrank':
            summarizer = LexRankSummarizer(self.stemmer)
        else:
            raise ValueError(f"Unknown method: {method}")

        summarizer.stop_words = self.stop_words

        # Generate summary
        summary_sentences = summarizer(parser.document, sentence_count)

        # Build result
        summary_text = ' '.join(str(sentence) for sentence in summary_sentences)

        result = {
            'summary': summary_text,
            'sentences': [str(s) for s in summary_sentences],
            'sentence_count': len(summary_sentences),
            'method': method,
            'original_length': len(text),
            'summary_length': len(summary_text),
            'compression_ratio': len(summary_text) / len(text) if text else 0
        }

        return result

    def summarize_all_methods(
        self,
        text: str,
        summary_length: str = 'medium'
    ) -> Dict:
        """
        Generate summaries using all available methods

        Args:
            text: Input text
            summary_length: Summary length

        Returns:
            Dictionary with summaries from all methods
        """
        methods = ['textrank', 'lsa', 'luhn', 'lexrank']
        results = {}

        for method in methods:
            try:
                results[method] = self.summarize(text, method, summary_length)
            except Exception as e:
                logger.error(f"Error with {method}: {str(e)}")
                results[method] = {'error': str(e)}

        return results

    def summarize_with_bullets(
        self,
        text: str,
        bullet_count: int = 5,
        method: str = 'textrank'
    ) -> Dict:
        """
        Generate bullet-point summary

        Args:
            text: Input text
            bullet_count: Number of bullet points
            method: Extraction method

        Returns:
            Bullet-point summary
        """
        summary = self.summarize(text, method, sentence_count=bullet_count)

        bullets = [f"• {sentence}" for sentence in summary['sentences']]

        return {
            'bullets': bullets,
            'bullet_text': '\n'.join(bullets),
            'count': len(bullets),
            'method': method
        }

    def extract_key_sentences(
        self,
        text: str,
        top_n: int = 5,
        method: str = 'tfidf'
    ) -> List[Dict]:
        """
        Extract most important sentences with scores

        Args:
            text: Input text
            top_n: Number of sentences to extract
            method: Scoring method ('tfidf' or 'pagerank')

        Returns:
            List of sentences with scores
        """
        sentences = sent_tokenize(text)

        if method == 'tfidf':
            scores = self._score_sentences_tfidf(sentences)
        elif method == 'pagerank':
            scores = self._score_sentences_pagerank(sentences)
        else:
            raise ValueError(f"Unknown scoring method: {method}")

        # Rank sentences
        ranked_sentences = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        # Sort by original position
        ranked_sentences.sort(key=lambda x: x[0])

        result = [
            {
                'sentence': sentences[idx],
                'score': score,
                'position': idx
            }
            for idx, score in ranked_sentences
        ]

        return result

    def _score_sentences_tfidf(self, sentences: List[str]) -> np.ndarray:
        """Score sentences using TF-IDF"""
        vectorizer = TfidfVectorizer(stop_words='english')

        try:
            tfidf_matrix = vectorizer.fit_transform(sentences)
            scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        except Exception as e:
            logger.warning(f"TF-IDF scoring failed: {str(e)}")
            scores = np.ones(len(sentences))

        return scores

    def _score_sentences_pagerank(self, sentences: List[str]) -> np.ndarray:
        """Score sentences using PageRank algorithm"""
        # Build similarity matrix
        vectorizer = TfidfVectorizer(stop_words='english')

        try:
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Calculate similarity
            similarity_matrix = (tfidf_matrix * tfidf_matrix.T).toarray()

            # Build graph
            graph = nx.from_numpy_array(similarity_matrix)

            # Calculate PageRank
            scores_dict = nx.pagerank(graph)
            scores = np.array([scores_dict[i] for i in range(len(sentences))])

        except Exception as e:
            logger.warning(f"PageRank scoring failed: {str(e)}")
            scores = np.ones(len(sentences))

        return scores

    def _calculate_sentence_count(self, text: str, summary_length: str) -> int:
        """Calculate number of sentences based on desired length"""
        sentences = sent_tokenize(text)
        total_sentences = len(sentences)

        if summary_length == 'short':
            # 10-15% of original
            return max(3, int(total_sentences * 0.12))
        elif summary_length == 'medium':
            # 20-30% of original
            return max(5, int(total_sentences * 0.25))
        elif summary_length == 'long':
            # 40-50% of original
            return max(8, int(total_sentences * 0.45))
        else:
            return max(5, int(total_sentences * 0.25))

    def generate_topic_based_summary(
        self,
        text: str,
        num_topics: int = 5,
        sentences_per_topic: int = 2
    ) -> Dict:
        """
        Generate summary based on topic modeling

        Args:
            text: Input text
            num_topics: Number of topics to extract
            sentences_per_topic: Sentences per topic

        Returns:
            Topic-based summary
        """
        sentences = sent_tokenize(text)

        # Vectorize
        vectorizer = CountVectorizer(
            max_features=1000,
            stop_words='english',
            max_df=0.95,
            min_df=2
        )

        try:
            doc_term_matrix = vectorizer.fit_transform(sentences)

            # LDA
            lda = LatentDirichletAllocation(
                n_components=num_topics,
                random_state=42
            )
            lda.fit(doc_term_matrix)

            # Get topic distribution for each sentence
            topic_distributions = lda.transform(doc_term_matrix)

            # Select top sentences for each topic
            topics = []
            selected_indices = set()

            for topic_idx in range(num_topics):
                # Get sentences most representative of this topic
                topic_scores = topic_distributions[:, topic_idx]
                top_sentence_indices = np.argsort(topic_scores)[::-1]

                topic_sentences = []
                for idx in top_sentence_indices:
                    if idx not in selected_indices and len(topic_sentences) < sentences_per_topic:
                        topic_sentences.append(sentences[idx])
                        selected_indices.add(idx)

                topics.append({
                    'topic_id': topic_idx,
                    'sentences': topic_sentences
                })

            # Combine all sentences in original order
            all_selected = sorted(list(selected_indices))
            summary_sentences = [sentences[i] for i in all_selected]

            return {
                'summary': ' '.join(summary_sentences),
                'topics': topics,
                'num_topics': num_topics,
                'sentence_count': len(summary_sentences)
            }

        except Exception as e:
            logger.error(f"Topic-based summarization failed: {str(e)}")
            # Fallback to simple extraction
            return self.summarize(text, method='textrank')
