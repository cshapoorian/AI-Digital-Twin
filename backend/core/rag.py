"""
RAG (Retrieval-Augmented Generation) module.

Handles loading training data and retrieving relevant chunks based on user
queries. Uses semantic embeddings (fastembed, ONNX-based, no PyTorch) for
real synonym/paraphrase matching, with an automatic fallback to TF-IDF if
the embedding model can't load (e.g. constrained memory or no network on
first run) so retrieval never goes fully offline.
"""

from pathlib import Path
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

try:
    from fastembed import TextEmbedding
    _FASTEMBED_AVAILABLE = True
except ImportError:
    _FASTEMBED_AVAILABLE = False

# Small (~90MB), ONNX-based, no torch dependency - fits Render's free-tier RAM
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# Query expansion for common interview/personal questions
# Maps common query terms to related terms that might appear in training data
QUERY_EXPANSIONS = {
    "weakness": ["weakness", "weaknesses", "flaw", "flaws", "struggle", "challenge"],
    "weaknesses": ["weakness", "weaknesses", "flaw", "flaws", "struggle", "challenge"],
    "strength": ["strength", "strengths", "strong", "excel", "best"],
    "strengths": ["strength", "strengths", "strong", "excel", "best"],
    "hire": ["hire", "why hire", "should hire", "hiring"],
    "goal": ["goal", "goals", "5 year", "five year", "career", "future"],
    "goals": ["goal", "goals", "5 year", "five year", "career", "future"],
    "left": ["left", "leaving", "quit", "resigned", "departure", "position", "last position"],
    "last job": ["left", "last position", "why left", "departure", "previous role"],
    "leave": ["left", "leaving", "quit", "resigned", "departure", "last position"],
    "failure": ["failure", "failed", "mistake", "learning", "lesson"],
    "conflict": ["conflict", "disagreement", "difficult", "coworker", "handling"],
    "stress": ["stress", "pressure", "deadline", "deadlines", "handle stress"],
    "motivate": ["motivate", "motivation", "motivates", "driven", "drive"],
    "environment": ["environment", "work environment", "ideal", "culture"],
    "project": ["project", "favorite project", "proud", "accomplishment"],
    "technical": ["technical", "problem", "challenge", "engineering"],
    "personality": ["personality", "communication style", "humor", "mannerisms", "phrases", "values conversation"],
    "opinions": ["opinions", "hot takes", "pet peeves", "food", "lifestyle", "technology opinions"],
    "opinion": ["opinions", "hot takes", "pet peeves", "views", "beliefs"],
    "how does he talk": ["communication style", "phrases", "mannerisms", "slang", "gen-z"],
    "how does cameron talk": ["communication style", "phrases", "mannerisms", "slang", "gen-z"],
    "talk": ["communication style", "phrases", "mannerisms"],
    "communication": ["communication style", "phrases", "mannerisms", "humor"],
    "experience": ["experience", "work", "job", "role", "position", "employment"],
    "skills": ["skills", "languages", "technologies", "proficient", "expertise"],
}


class RAGRetriever:
    """
    Retrieves relevant text chunks from training data based on query similarity.
    Uses TF-IDF vectorization for lightweight, efficient retrieval.
    """

    def __init__(self, data_dir: str = None, use_embeddings: bool = True):
        """
        Initialize the retriever with training data.

        Args:
            data_dir: Path to directory containing training text files.
                      Defaults to backend/data/
            use_embeddings: Try to use semantic embeddings for retrieval.
                             Falls back to TF-IDF automatically if the
                             embedding model can't be loaded.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.chunks: List[Tuple[str, str]] = []  # (chunk_text, source_file)

        # TF-IDF is always set up as the fallback path
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),  # Unigrams and bigrams for better matching
            token_pattern=r'(?u)\b\w+\b'  # Include single-character tokens
        )  # No max_features limit - we don't have enough data to need it
        self.tfidf_matrix = None

        self._use_embeddings = use_embeddings and _FASTEMBED_AVAILABLE
        self._embedding_model = None
        self.chunk_embeddings = None  # np.ndarray, shape (n_chunks, dim)

        self._load_data()

    def _load_data(self):
        """
        Load all .txt files from data directory and split into chunks.
        Each paragraph becomes a separate chunk for granular retrieval.
        Builds semantic embeddings when available, otherwise TF-IDF.
        """
        self.chunks = []
        self.chunk_embeddings = None
        self.tfidf_matrix = None

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

        if not self.chunks:
            print("Warning: No training data loaded")
            return

        chunk_texts = [chunk[0] for chunk in self.chunks]
        n_files = len(list(self.data_dir.glob('*.txt')))

        if self._use_embeddings:
            try:
                if self._embedding_model is None:
                    self._embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
                self.chunk_embeddings = np.array(list(self._embedding_model.embed(chunk_texts)))
                print(f"Loaded {len(self.chunks)} chunks from {n_files} files (semantic embeddings)")
            except Exception as e:
                print(f"Warning: embedding model unavailable ({e}), falling back to TF-IDF")
                self._use_embeddings = False

        if not self._use_embeddings:
            self.tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
            print(f"Loaded {len(self.chunks)} chunks from {n_files} files (TF-IDF)")

    def _split_into_chunks(self, content: str, source: str) -> List[Tuple[str, str]]:
        """
        Split content into chunks based on sections (## headers) or paragraphs.
        Keeps section headers with their content for better retrieval.

        Args:
            content: Full text content
            source: Source file name for reference

        Returns:
            List of (chunk_text, source_file) tuples
        """
        chunks = []

        # First, try to split by ## headers (keeps header with content)
        sections = re.split(r'\n(?=## )', content)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section starts with ##, it's a headed section - keep it together
            if section.startswith('## ') or section.startswith('# '):
                # Merge short consecutive paragraphs within the section
                if len(section) > 50:
                    chunks.append((section, source))
            else:
                # For non-headed content, split by paragraphs but merge small ones
                paragraphs = re.split(r'\n\s*\n', section)
                current_chunk = ""

                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    # Merge short paragraphs together
                    if len(current_chunk) + len(para) < 500:
                        current_chunk = f"{current_chunk}\n\n{para}".strip()
                    else:
                        if len(current_chunk) > 50:
                            chunks.append((current_chunk, source))
                        current_chunk = para

                # Don't forget the last chunk
                if len(current_chunk) > 50:
                    chunks.append((current_chunk, source))

        return chunks

    def _expand_query(self, query: str) -> str:
        """
        Expand query with related terms for better matching.

        Args:
            query: Original user query

        Returns:
            Expanded query string with additional relevant terms
        """
        query_lower = query.lower()
        expanded_terms = [query]

        for keyword, expansions in QUERY_EXPANSIONS.items():
            if keyword in query_lower:
                expanded_terms.extend(expansions)

        return " ".join(expanded_terms)

    def retrieve(
        self, query: str, top_k: int = 3, min_similarity: float = 0.05
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieve the most relevant chunks for a given query.

        Args:
            query: User's question or message
            top_k: Number of top chunks to return
            min_similarity: Minimum similarity score to include a result

        Returns:
            List of (chunk_text, source_file, similarity_score) tuples,
            sorted by relevance (highest first)
        """
        has_index = self.chunk_embeddings is not None or self.tfidf_matrix is not None
        if not self.chunks or not has_index:
            return []

        # Expand query with related terms for better matching
        expanded_query = self._expand_query(query)

        if self._use_embeddings and self.chunk_embeddings is not None:
            query_vector = np.array(list(self._embedding_model.embed([expanded_query])))
            similarities = cosine_similarity(query_vector, self.chunk_embeddings)[0]
        else:
            query_vector = self.vectorizer.transform([expanded_query])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Filter out low-similarity results
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score > min_similarity:
                chunk_text, source = self.chunks[idx]
                results.append((chunk_text, source, float(score)))

        return results

    def get_context_string(
        self, query: str, top_k: int = 3, min_similarity: float = 0.05
    ) -> str:
        """
        Get a formatted context string for the LLM prompt.

        Args:
            query: User's question
            top_k: Number of chunks to include
            min_similarity: Minimum similarity score to include a result

        Returns:
            Formatted string with relevant context, or empty string if none found
        """
        results = self.retrieve(query, top_k, min_similarity)

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
