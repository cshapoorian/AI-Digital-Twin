"""
RAG (Retrieval-Augmented Generation) module.

Loads training data from disk and retrieves relevant chunks using
lightweight TF-IDF similarity.

This implementation is intentionally memory-efficient so it can run
reliably on small Render instances.
"""

from pathlib import Path
from typing import List, Tuple
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# File extensions treated as training data in the data directory.
DATA_FILE_SUFFIXES = (".md", ".txt")


# Query expansion for common interview/personal questions.
# Maps common query terms to related terms that might appear in training data.
QUERY_EXPANSIONS = {
    "weakness": [
        "weakness",
        "weaknesses",
        "flaw",
        "flaws",
        "struggle",
        "challenge",
    ],
    "weaknesses": [
        "weakness",
        "weaknesses",
        "flaw",
        "flaws",
        "struggle",
        "challenge",
    ],
    "strength": [
        "strength",
        "strengths",
        "strong",
        "excel",
        "best",
    ],
    "strengths": [
        "strength",
        "strengths",
        "strong",
        "excel",
        "best",
    ],
    "hire": [
        "hire",
        "why hire",
        "should hire",
        "hiring",
    ],
    "goal": [
        "goal",
        "goals",
        "5 year",
        "five year",
        "career",
        "future",
    ],
    "goals": [
        "goal",
        "goals",
        "5 year",
        "five year",
        "career",
        "future",
    ],
    "left": [
        "left",
        "leaving",
        "quit",
        "resigned",
        "departure",
        "position",
        "last position",
    ],
    "last job": [
        "left",
        "last position",
        "why left",
        "departure",
        "previous role",
    ],
    "leave": [
        "left",
        "leaving",
        "quit",
        "resigned",
        "departure",
        "last position",
    ],
    "failure": [
        "failure",
        "failed",
        "mistake",
        "learning",
        "lesson",
    ],
    "conflict": [
        "conflict",
        "disagreement",
        "difficult",
        "coworker",
        "handling",
    ],
    "stress": [
        "stress",
        "pressure",
        "deadline",
        "deadlines",
        "handle stress",
    ],
    "motivate": [
        "motivate",
        "motivation",
        "motivates",
        "driven",
        "drive",
    ],
    "environment": [
        "environment",
        "work environment",
        "ideal",
        "culture",
    ],
    "project": [
        "project",
        "favorite project",
        "proud",
        "accomplishment",
    ],
    "technical": [
        "technical",
        "problem",
        "challenge",
        "engineering",
    ],
    "personality": [
        "personality",
        "communication style",
        "humor",
        "mannerisms",
        "phrases",
        "values conversation",
    ],
    "opinions": [
        "opinions",
        "hot takes",
        "pet peeves",
        "food",
        "lifestyle",
        "technology opinions",
    ],
    "opinion": [
        "opinions",
        "hot takes",
        "pet peeves",
        "views",
        "beliefs",
    ],
    "how does he talk": [
        "communication style",
        "phrases",
        "mannerisms",
        "slang",
        "gen-z",
    ],
    "how does cameron talk": [
        "communication style",
        "phrases",
        "mannerisms",
        "slang",
        "gen-z",
    ],
    "talk": [
        "communication style",
        "phrases",
        "mannerisms",
    ],
    "communication": [
        "communication style",
        "phrases",
        "mannerisms",
        "humor",
    ],
    "experience": [
        "experience",
        "work",
        "job",
        "role",
        "position",
        "employment",
    ],
    "skills": [
        "skills",
        "languages",
        "technologies",
        "proficient",
        "expertise",
    ],
}


class RAGRetriever:
    """
    Lightweight RAG retriever using TF-IDF.

    Designed for small-memory deployments such as Render's 512 MB
    instances. Training files are loaded once and represented as a
    sparse TF-IDF matrix.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the retriever.

        Args:
            data_dir:
                Directory containing training text files.
                Defaults to backend/data/.
        """

        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir

        # Each tuple is:
        # (chunk_text, source_file)
        self.chunks: List[Tuple[str, str]] = []

        # Sparse TF-IDF representation keeps memory usage low.
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b",
            max_features=10000,
            dtype="float32",
        )

        self.tfidf_matrix = None

        self._load_data()

    def _load_data(self):
        """
        Load training files and build the TF-IDF index.
        """

        self.chunks = []
        self.tfidf_matrix = None

        if not self.data_dir.exists():
            print(
                f"Warning: Data directory does not exist: "
                f"{self.data_dir}"
            )
            return

        # Training data is authored as Markdown. ".txt" remains
        # supported so older/plain-text knowledge files keep working.
        data_files = sorted(
            path
            for suffix in DATA_FILE_SUFFIXES
            for path in self.data_dir.glob(f"*{suffix}")
        )

        if not data_files:
            print(
                "Warning: No training files found "
                f"({', '.join(DATA_FILE_SUFFIXES)})"
            )
            return

        for data_file in data_files:
            try:
                content = data_file.read_text(encoding="utf-8")

                file_chunks = self._split_into_chunks(
                    content,
                    data_file.name,
                )

                self.chunks.extend(file_chunks)

            except Exception as exc:
                print(
                    f"Error loading {data_file.name}: {exc}"
                )

        if not self.chunks:
            print("Warning: No training data loaded")
            return

        chunk_texts = [
            chunk[0]
            for chunk in self.chunks
        ]

        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(
                chunk_texts
            )

            print(
                f"Loaded {len(self.chunks)} chunks "
                f"from {len(data_files)} files "
                f"(TF-IDF)"
            )

        except Exception as exc:
            print(
                f"Error building TF-IDF index: {exc}"
            )

            self.chunks = []
            self.tfidf_matrix = None

    # Maximum characters for a heading-based chunk before it is split
    # further. Oversized chunks dilute TF-IDF scores and retrieve poorly.
    MAX_SECTION_CHARS = 2500

    # Approximate target size for chunks built from bare paragraphs.
    PARAGRAPH_CHUNK_CHARS = 500

    def _split_into_chunks(
        self,
        content: str,
        source: str,
    ) -> List[Tuple[str, str]]:
        """
        Split Markdown/text into retrieval-friendly chunks.

        Sections beginning with ## are kept together when reasonably
        sized. An oversized section is split again on its ###
        subheadings, with the parent heading prepended so each chunk
        keeps its context. Content with no headings at all is grouped
        into chunks of roughly PARAGRAPH_CHUNK_CHARS characters.
        """

        chunks = []

        # Split on Markdown ## headings. "### " does not match the
        # lookahead, so subheadings stay with their parent section.
        sections = re.split(
            r"\n(?=## )",
            content,
        )

        for section in sections:
            section = section.strip()

            if not section:
                continue

            is_headed = (
                section.startswith("## ")
                or section.startswith("# ")
            )

            if not is_headed:
                chunks.extend(
                    self._split_paragraphs(section, source)
                )
                continue

            # Keep headed sections together when they aren't enormous.
            if 50 < len(section) <= self.MAX_SECTION_CHARS:
                chunks.append(
                    (section, source)
                )
                continue

            # Oversized section: prefer its ### subheadings so the
            # subsections keep a heading instead of becoming loose text.
            parent_heading = section.split("\n", 1)[0].strip()

            subsections = re.split(
                r"\n(?=### )",
                section,
            )

            if len(subsections) == 1:
                chunks.extend(
                    self._split_paragraphs(section, source)
                )
                continue

            for subsection in subsections:
                subsection = subsection.strip()

                if not subsection:
                    continue

                if not subsection.startswith("### "):
                    # Intro text ahead of the first subheading.
                    chunks.extend(
                        self._split_paragraphs(subsection, source)
                    )
                    continue

                # Carry the parent heading so the chunk keeps context.
                subsection = f"{parent_heading}\n\n{subsection}"

                if len(subsection) <= self.MAX_SECTION_CHARS:
                    chunks.append(
                        (subsection, source)
                    )

                else:
                    chunks.extend(
                        self._split_paragraphs(subsection, source)
                    )

        return chunks

    def _split_paragraphs(
        self,
        section: str,
        source: str,
    ) -> List[Tuple[str, str]]:
        """
        Group content without usable headings into size-bounded chunks.
        """

        chunks = []

        paragraphs = re.split(
            r"\n\s*\n",
            section,
        )

        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                continue

            # Keep chunks reasonably small.
            if (
                current_chunk
                and len(current_chunk) + len(paragraph) + 2
                > self.PARAGRAPH_CHUNK_CHARS
            ):
                if len(current_chunk) > 50:
                    chunks.append(
                        (current_chunk, source)
                    )

                current_chunk = paragraph

            else:
                if current_chunk:
                    current_chunk += "\n\n"

                current_chunk += paragraph

        if len(current_chunk) > 50:
            chunks.append(
                (current_chunk, source)
            )

        return chunks

    def _expand_query(self, query: str) -> str:
        """
        Expand a query with related terms.
        """

        query_lower = query.lower()

        expanded_terms = [query]

        for keyword, expansions in QUERY_EXPANSIONS.items():
            if keyword in query_lower:
                expanded_terms.extend(expansions)

        return " ".join(expanded_terms)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.05,
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieve the most relevant chunks.

        Returns:
            List of:
            (chunk_text, source_file, similarity_score)
        """

        if (
            not self.chunks
            or self.tfidf_matrix is None
        ):
            return []

        expanded_query = self._expand_query(query)

        query_vector = self.vectorizer.transform(
            [expanded_query]
        )

        similarities = cosine_similarity(
            query_vector,
            self.tfidf_matrix,
        )[0]

        # Avoid requesting more chunks than exist.
        top_k = min(
            max(1, top_k),
            len(self.chunks),
        )

        top_indices = similarities.argsort()[
            -top_k:
        ][::-1]

        results = []

        for idx in top_indices:
            score = float(similarities[idx])

            if score > min_similarity:
                chunk_text, source = self.chunks[idx]

                results.append(
                    (
                        chunk_text,
                        source,
                        score,
                    )
                )

        return results

    def get_context_string(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.05,
    ) -> str:
        """
        Get formatted retrieval context for the LLM.
        """

        results = self.retrieve(
            query,
            top_k,
            min_similarity,
        )

        if not results:
            return ""

        context_parts = []

        for chunk_text, source, score in results:
            context_parts.append(
                f"[From {source}]:\n{chunk_text}"
            )

        return "\n\n".join(context_parts)

    def reload(self):
        """
        Reload the training data and rebuild the TF-IDF index.
        """

        self._load_data()