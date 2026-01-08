"""
RAG (Retrieval-Augmented Generation) module.

Handles loading training data and retrieving relevant chunks
based on user queries using TF-IDF similarity.
"""

from pathlib import Path
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


class RAGRetriever:
    """
    Retrieves relevant text chunks from training data based on query similarity.
    Uses TF-IDF vectorization for lightweight, efficient retrieval.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the retriever with training data.

        Args:
            data_dir: Path to directory containing training text files.
                      Defaults to backend/data/
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.chunks: List[Tuple[str, str]] = []  # (chunk_text, source_file)
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=1000,
            ngram_range=(1, 2)  # Unigrams and bigrams for better matching
        )
        self.tfidf_matrix = None
        self._load_data()

    def _load_data(self):
        """
        Load all .txt files from data directory and split into chunks.
        Each paragraph becomes a separate chunk for granular retrieval.
        """
        self.chunks = []

        if not self.data_dir.exists():
            print(f"Warning: Data directory {self.data_dir} does not exist")
            return

        for txt_file in self.data_dir.glob("*.txt"):
            try:
                content = txt_file.read_text(encoding="utf-8")
                file_chunks = self._split_into_chunks(content, txt_file.name)
                self.chunks.extend(file_chunks)
            except Exception as e:
                print(f"Error loading {txt_file}: {e}")

        if self.chunks:
            # Build TF-IDF matrix for all chunks
            chunk_texts = [chunk[0] for chunk in self.chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
            print(f"Loaded {len(self.chunks)} chunks from {len(list(self.data_dir.glob('*.txt')))} files")
        else:
            print("Warning: No training data loaded")

    def _split_into_chunks(self, content: str, source: str) -> List[Tuple[str, str]]:
        """
        Split content into chunks based on paragraphs.
        Filters out very short chunks that lack meaningful content.

        Args:
            content: Full text content
            source: Source file name for reference

        Returns:
            List of (chunk_text, source_file) tuples
        """
        # Split by double newlines (paragraphs) or section breaks
        paragraphs = re.split(r'\n\s*\n', content)

        chunks = []
        for para in paragraphs:
            # Clean and validate chunk
            cleaned = para.strip()
            if len(cleaned) > 50:  # Skip very short chunks
                chunks.append((cleaned, source))

        return chunks

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Retrieve the most relevant chunks for a given query.

        Args:
            query: User's question or message
            top_k: Number of top chunks to return

        Returns:
            List of (chunk_text, source_file, similarity_score) tuples,
            sorted by relevance (highest first)
        """
        if not self.chunks or self.tfidf_matrix is None:
            return []

        # Vectorize the query
        query_vector = self.vectorizer.transform([query])

        # Calculate similarity with all chunks
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Filter out low-similarity results (threshold: 0.1)
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score > 0.1:  # Minimum relevance threshold
                chunk_text, source = self.chunks[idx]
                results.append((chunk_text, source, float(score)))

        return results

    def get_context_string(self, query: str, top_k: int = 3) -> str:
        """
        Get a formatted context string for the LLM prompt.

        Args:
            query: User's question
            top_k: Number of chunks to include

        Returns:
            Formatted string with relevant context, or empty string if none found
        """
        results = self.retrieve(query, top_k)

        if not results:
            return ""

        context_parts = []
        for chunk_text, source, score in results:
            context_parts.append(f"[From {source}]:\n{chunk_text}")

        return "\n\n".join(context_parts)

    def reload(self):
        """
        Reload training data from disk.
        Call this after adding new training files.
        """
        self._load_data()
