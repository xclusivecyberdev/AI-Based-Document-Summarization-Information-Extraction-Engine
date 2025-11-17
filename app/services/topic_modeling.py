"""
Topic Modeling and Contextual Embeddings Module
Implements LDA, NMF, and transformer-based embeddings
"""
from typing import Dict, List, Optional, Tuple
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from gensim import corpora, models
from gensim.models import CoherenceModel
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModel

from nltk.tokenize import sent_tokenize, word_tokenize
from loguru import logger


class TopicModelingService:
    """Topic modeling and document embeddings"""

    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize topic modeling service

        Args:
            embedding_model: Model for generating embeddings
        """
        self.embedding_model_name = embedding_model
        self.sentence_transformer = None

    def _load_sentence_transformer(self):
        """Lazy load sentence transformer"""
        if self.sentence_transformer is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.sentence_transformer = SentenceTransformer(self.embedding_model_name)

        return self.sentence_transformer

    def extract_topics_lda(
        self,
        texts: List[str],
        num_topics: int = 5,
        max_features: int = 1000
    ) -> Dict:
        """
        Extract topics using Latent Dirichlet Allocation

        Args:
            texts: List of documents
            num_topics: Number of topics to extract
            max_features: Maximum number of features

        Returns:
            Topic modeling results
        """
        logger.info(f"Extracting {num_topics} topics using LDA")

        # Vectorize
        vectorizer = CountVectorizer(
            max_features=max_features,
            stop_words='english',
            max_df=0.95,
            min_df=2
        )

        doc_term_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # LDA
        lda = LatentDirichletAllocation(
            n_components=num_topics,
            random_state=42,
            max_iter=20
        )

        lda.fit(doc_term_matrix)

        # Extract topics
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            top_weights = [topic[i] for i in top_indices]

            topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weights': [float(w) for w in top_weights],
                'top_words_str': ', '.join(top_words[:5])
            })

        # Document-topic distributions
        doc_topics = lda.transform(doc_term_matrix)

        return {
            'topics': topics,
            'num_topics': num_topics,
            'document_topics': doc_topics.tolist(),
            'perplexity': lda.perplexity(doc_term_matrix),
            'log_likelihood': lda.score(doc_term_matrix),
            'method': 'LDA'
        }

    def extract_topics_nmf(
        self,
        texts: List[str],
        num_topics: int = 5,
        max_features: int = 1000
    ) -> Dict:
        """
        Extract topics using Non-negative Matrix Factorization

        Args:
            texts: List of documents
            num_topics: Number of topics
            max_features: Maximum features

        Returns:
            Topic modeling results
        """
        logger.info(f"Extracting {num_topics} topics using NMF")

        # Use TF-IDF for NMF
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            max_df=0.95,
            min_df=2
        )

        doc_term_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # NMF
        nmf = NMF(
            n_components=num_topics,
            random_state=42,
            max_iter=200
        )

        nmf.fit(doc_term_matrix)

        # Extract topics
        topics = []
        for topic_idx, topic in enumerate(nmf.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            top_weights = [topic[i] for i in top_indices]

            topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weights': [float(w) for w in top_weights],
                'top_words_str': ', '.join(top_words[:5])
            })

        # Document-topic distributions
        doc_topics = nmf.transform(doc_term_matrix)

        return {
            'topics': topics,
            'num_topics': num_topics,
            'document_topics': doc_topics.tolist(),
            'reconstruction_error': nmf.reconstruction_err_,
            'method': 'NMF'
        }

    def extract_topics_gensim(
        self,
        texts: List[str],
        num_topics: int = 5
    ) -> Dict:
        """
        Extract topics using Gensim LDA

        Args:
            texts: List of documents
            num_topics: Number of topics

        Returns:
            Topic modeling results with coherence scores
        """
        logger.info(f"Extracting {num_topics} topics using Gensim LDA")

        # Tokenize
        tokenized_texts = [word_tokenize(text.lower()) for text in texts]

        # Create dictionary and corpus
        dictionary = corpora.Dictionary(tokenized_texts)

        # Filter extremes
        dictionary.filter_extremes(no_below=2, no_above=0.95)

        # Create corpus
        corpus = [dictionary.doc2bow(text) for text in tokenized_texts]

        # Build LDA model
        lda_model = models.LdaMulticore(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            random_state=42,
            passes=10,
            per_word_topics=True
        )

        # Extract topics
        topics = []
        for topic_id in range(num_topics):
            topic_words = lda_model.show_topic(topic_id, topn=10)
            words = [word for word, _ in topic_words]
            weights = [float(weight) for _, weight in topic_words]

            topics.append({
                'topic_id': topic_id,
                'words': words,
                'weights': weights,
                'top_words_str': ', '.join(words[:5])
            })

        # Calculate coherence
        coherence_model = CoherenceModel(
            model=lda_model,
            texts=tokenized_texts,
            dictionary=dictionary,
            coherence='c_v'
        )
        coherence_score = coherence_model.get_coherence()

        return {
            'topics': topics,
            'num_topics': num_topics,
            'coherence_score': coherence_score,
            'perplexity': lda_model.log_perplexity(corpus),
            'method': 'Gensim LDA'
        }

    def generate_embeddings(
        self,
        texts: List[str],
        pooling: str = 'mean'
    ) -> Dict:
        """
        Generate contextual embeddings using sentence transformers

        Args:
            texts: List of texts to embed
            pooling: Pooling strategy

        Returns:
            Embeddings and metadata
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")

        model = self._load_sentence_transformer()

        # Generate embeddings
        embeddings = model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        return {
            'embeddings': embeddings.tolist(),
            'shape': embeddings.shape,
            'model': self.embedding_model_name,
            'dimension': embeddings.shape[1] if len(embeddings.shape) > 1 else 0
        }

    def generate_document_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single document

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        model = self._load_sentence_transformer()
        embedding = model.encode(text, convert_to_numpy=True)

        return embedding

    def find_similar_documents(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar documents using embeddings

        Args:
            query: Query text
            documents: List of documents
            top_k: Number of similar documents to return

        Returns:
            List of similar documents with scores
        """
        logger.info(f"Finding top {top_k} similar documents")

        model = self._load_sentence_transformer()

        # Generate embeddings
        query_embedding = model.encode(query, convert_to_numpy=True)
        doc_embeddings = model.encode(documents, convert_to_numpy=True)

        # Calculate similarity
        from sklearn.metrics.pairwise import cosine_similarity

        similarities = cosine_similarity([query_embedding], doc_embeddings)[0]

        # Get top-k
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = [
            {
                'document': documents[idx],
                'similarity': float(similarities[idx]),
                'rank': rank + 1
            }
            for rank, idx in enumerate(top_indices)
        ]

        return results

    def cluster_documents(
        self,
        texts: List[str],
        num_clusters: int = 5,
        method: str = 'kmeans'
    ) -> Dict:
        """
        Cluster documents using embeddings

        Args:
            texts: List of documents
            num_clusters: Number of clusters
            method: Clustering method ('kmeans' or 'hierarchical')

        Returns:
            Clustering results
        """
        logger.info(f"Clustering {len(texts)} documents into {num_clusters} clusters")

        # Generate embeddings
        embeddings_result = self.generate_embeddings(texts)
        embeddings = np.array(embeddings_result['embeddings'])

        if method == 'kmeans':
            from sklearn.cluster import KMeans

            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            labels = kmeans.fit_predict(embeddings)

            cluster_centers = kmeans.cluster_centers_

            results = {
                'labels': labels.tolist(),
                'cluster_centers': cluster_centers.tolist(),
                'inertia': kmeans.inertia_,
                'method': 'KMeans'
            }

        elif method == 'hierarchical':
            from sklearn.cluster import AgglomerativeClustering

            clustering = AgglomerativeClustering(n_clusters=num_clusters)
            labels = clustering.fit_predict(embeddings)

            results = {
                'labels': labels.tolist(),
                'method': 'Hierarchical'
            }

        else:
            raise ValueError(f"Unknown clustering method: {method}")

        # Group documents by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append({
                'index': idx,
                'text': texts[idx][:100] + '...' if len(texts[idx]) > 100 else texts[idx]
            })

        results['clusters'] = clusters
        results['num_clusters'] = num_clusters

        return results

    def extract_contextual_embeddings_bert(
        self,
        text: str,
        model_name: str = 'bert-base-uncased'
    ) -> Dict:
        """
        Extract contextual embeddings using BERT

        Args:
            text: Input text
            model_name: BERT model to use

        Returns:
            Contextual embeddings
        """
        logger.info(f"Extracting BERT embeddings using {model_name}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        # Tokenize
        inputs = tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding=True
        )

        # Get embeddings
        with torch.no_grad():
            outputs = model(**inputs)

        # Last hidden state
        last_hidden_state = outputs.last_hidden_state

        # Pool (mean)
        embeddings = last_hidden_state.mean(dim=1).squeeze().numpy()

        return {
            'embeddings': embeddings.tolist(),
            'shape': embeddings.shape,
            'model': model_name,
            'tokens': tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        }

    def analyze_document_structure(
        self,
        text: str,
        num_topics: int = 3
    ) -> Dict:
        """
        Analyze document structure using topic modeling

        Args:
            text: Input document
            num_topics: Number of topics

        Returns:
            Document structure analysis
        """
        # Split into paragraphs/sections
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if len(paragraphs) < 2:
            # Fall back to sentence-level
            paragraphs = sent_tokenize(text)

        # Extract topics
        if len(paragraphs) >= num_topics:
            topics = self.extract_topics_lda(paragraphs, num_topics)

            # Assign topics to paragraphs
            doc_topics = topics['document_topics']

            paragraph_analysis = []
            for idx, para in enumerate(paragraphs):
                if idx < len(doc_topics):
                    dominant_topic = int(np.argmax(doc_topics[idx]))
                    topic_strength = float(doc_topics[idx][dominant_topic])

                    paragraph_analysis.append({
                        'paragraph': para[:200] + '...' if len(para) > 200 else para,
                        'dominant_topic': dominant_topic,
                        'topic_strength': topic_strength,
                        'topic_words': topics['topics'][dominant_topic]['top_words_str']
                    })

            return {
                'topics': topics['topics'],
                'paragraph_analysis': paragraph_analysis,
                'num_paragraphs': len(paragraphs)
            }
        else:
            return {
                'error': 'Not enough paragraphs for topic modeling',
                'num_paragraphs': len(paragraphs)
            }
