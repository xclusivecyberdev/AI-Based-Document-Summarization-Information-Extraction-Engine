"""
Visualization Service for generating charts and graphs
"""
import io
import base64
from typing import Dict, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np
from loguru import logger


class VisualizationService:
    """Generate visualizations for document analysis"""

    def __init__(self):
        # Set style
        sns.set_theme(style="whitegrid")
        self.colors = sns.color_palette("husl", 10)

    def generate_word_cloud(
        self,
        text: str,
        width: int = 800,
        height: int = 400
    ) -> str:
        """
        Generate word cloud from text

        Args:
            text: Input text
            width: Image width
            height: Image height

        Returns:
            Base64 encoded image
        """
        logger.info("Generating word cloud")

        wordcloud = WordCloud(
            width=width,
            height=height,
            background_color='white',
            colormap='viridis',
            max_words=100
        ).generate(text)

        # Create figure
        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)

        # Convert to base64
        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def generate_entity_chart(
        self,
        entities: Dict[str, List]
    ) -> str:
        """
        Generate bar chart of entity counts

        Args:
            entities: Dictionary of entities by type

        Returns:
            Base64 encoded image
        """
        logger.info("Generating entity chart")

        # Count entities by type
        entity_counts = {
            entity_type: len(entity_list)
            for entity_type, entity_list in entities.items()
            if entity_list
        }

        if not entity_counts:
            return None

        # Create chart
        plt.figure(figsize=(10, 6))

        types = list(entity_counts.keys())
        counts = list(entity_counts.values())

        plt.barh(types, counts, color=self.colors[:len(types)])
        plt.xlabel('Count')
        plt.title('Named Entities by Type')
        plt.tight_layout()

        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def generate_keyword_chart(
        self,
        keywords: List[Dict],
        top_n: int = 15
    ) -> str:
        """
        Generate keyword frequency chart

        Args:
            keywords: List of keyword dictionaries
            top_n: Number of top keywords to show

        Returns:
            Base64 encoded image
        """
        logger.info("Generating keyword chart")

        # Extract keywords and scores
        if not keywords:
            return None

        keywords_sorted = sorted(
            keywords[:top_n],
            key=lambda x: x.get('frequency', x.get('score', 0)),
            reverse=True
        )

        words = [kw.get('keyword', str(kw)) for kw in keywords_sorted]
        scores = [kw.get('frequency', kw.get('score', 1)) for kw in keywords_sorted]

        # Create chart
        plt.figure(figsize=(10, 8))

        plt.barh(words, scores, color=self.colors[:len(words)])
        plt.xlabel('Score/Frequency')
        plt.title(f'Top {len(words)} Keywords')
        plt.gca().invert_yaxis()
        plt.tight_layout()

        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def generate_topic_distribution(
        self,
        topics: List[Dict]
    ) -> str:
        """
        Generate topic distribution visualization

        Args:
            topics: List of topics with words and weights

        Returns:
            Base64 encoded image
        """
        logger.info("Generating topic distribution")

        if not topics:
            return None

        # Create subplots for each topic
        num_topics = len(topics)
        fig, axes = plt.subplots(
            num_topics,
            1,
            figsize=(12, 4 * num_topics)
        )

        if num_topics == 1:
            axes = [axes]

        for idx, topic in enumerate(topics):
            ax = axes[idx]

            words = topic['words'][:10]
            weights = topic['weights'][:10]

            ax.barh(words, weights, color=self.colors[idx % len(self.colors)])
            ax.set_xlabel('Weight')
            ax.set_title(f"Topic {topic['topic_id']}: {topic.get('top_words_str', '')}")
            ax.invert_yaxis()

        plt.tight_layout()

        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def generate_statistics_chart(
        self,
        statistics: Dict
    ) -> str:
        """
        Generate chart for text statistics

        Args:
            statistics: Dictionary of statistics

        Returns:
            Base64 encoded image
        """
        logger.info("Generating statistics chart")

        # Select relevant metrics
        metrics = {
            'Word Count': statistics.get('word_count', 0),
            'Sentence Count': statistics.get('sentence_count', 0),
            'Avg Word Length': statistics.get('avg_word_length', 0),
            'Avg Sentence Length': statistics.get('avg_sentence_length', 0)
        }

        readability_metrics = {
            'Flesch Reading Ease': statistics.get('flesch_reading_ease', 0),
            'Flesch-Kincaid Grade': statistics.get('flesch_kincaid_grade', 0),
            'Gunning Fog': statistics.get('gunning_fog', 0)
        }

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Basic metrics
        names = list(metrics.keys())
        values = list(metrics.values())

        ax1.bar(names, values, color=self.colors[:len(names)])
        ax1.set_title('Document Metrics')
        ax1.set_ylabel('Value')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Readability metrics
        names2 = list(readability_metrics.keys())
        values2 = list(readability_metrics.values())

        ax2.bar(names2, values2, color=self.colors[4:4+len(names2)])
        ax2.set_title('Readability Scores')
        ax2.set_ylabel('Score')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()

        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def generate_summary_comparison(
        self,
        summaries: Dict[str, Dict]
    ) -> str:
        """
        Generate comparison chart for different summary methods

        Args:
            summaries: Dictionary of summaries by method

        Returns:
            Base64 encoded image
        """
        logger.info("Generating summary comparison")

        methods = []
        lengths = []
        ratios = []

        for method, summary in summaries.items():
            if 'error' not in summary:
                methods.append(method)
                lengths.append(summary.get('summary_length', 0))
                ratios.append(summary.get('compression_ratio', 0))

        if not methods:
            return None

        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Summary lengths
        ax1.bar(methods, lengths, color=self.colors[:len(methods)])
        ax1.set_title('Summary Length by Method')
        ax1.set_ylabel('Characters')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Compression ratios
        ax2.bar(methods, ratios, color=self.colors[:len(methods)])
        ax2.set_title('Compression Ratio by Method')
        ax2.set_ylabel('Ratio')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()

        img_base64 = self._fig_to_base64()

        plt.close()

        return img_base64

    def _fig_to_base64(self) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return f"data:image/png;base64,{img_base64}"
