"""Load the markdown knowledge base, split it into chunks, and search it."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

SKIP_FILES = {"00_README.md"}
MAX_CHARS = 1100


@dataclass
class Chunk:
    id: int
    source: str      # e.g. "categories/10_screw.md"
    title: str
    heading: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.source} > {self.heading}"

    @property
    def search_text(self) -> str:
        return f"{self.title}. {self.heading}. {self.text}"


def _split_long(body: str) -> list[str]:
    if len(body) <= MAX_CHARS:
        return [body]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", body):
        if cur and len(cur) + len(para) > MAX_CHARS:
            parts.append(cur.strip())
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _extract_pdf_chunks(kb: Path, start_id: int) -> list[Chunk]:
    pdf_chunks: list[Chunk] = []
    seen_stems: set[str] = set()
    try:
        import unicodedata
        from pypdf import PdfReader
    except ImportError:
        return pdf_chunks

    for path in sorted(kb.rglob("*.pdf")):
        if path.name in SKIP_FILES or path.name.startswith("."):
            continue
        # Avoid duplicate downloaded files like '... (1).pdf'
        clean_stem = re.sub(r"\s*\(\d+\)$", "", path.stem)
        if clean_stem in seen_stems and "(" in path.stem:
            continue
        seen_stems.add(clean_stem)

        rel = path.relative_to(kb).as_posix()
        try:
            reader = PdfReader(str(path))
        except Exception:
            continue

        # Human-friendly titles for research papers
        title = path.stem
        if "1905.11946" in path.stem:
            title = "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks (Paper)"
        elif "MVTECh" in path.stem:
            title = "MVTec AD: A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection (CVPR 2019 Paper)"
        elif "s11263" in path.stem:
            title = "The MVTec Anomaly Detection Dataset (IJCV 2021 Journal Paper)"

        for page_idx, page in enumerate(reader.pages):
            try:
                raw = page.extract_text() or ""
            except Exception:
                continue
            text = unicodedata.normalize("NFKD", raw)
            text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            cleaned = "\n\n".join(paragraphs)
            if not cleaned:
                continue

            heading = f"Page {page_idx + 1}"
            for part in _split_long(cleaned):
                if len(part) < 50:
                    continue
                pdf_chunks.append(Chunk(start_id + len(pdf_chunks), rel, title, heading, part))

    return pdf_chunks


def load_chunks(kb_dir) -> list[Chunk]:
    kb = Path(kb_dir)
    if not kb.is_dir():
        raise FileNotFoundError(f"Knowledge base folder not found: {kb.resolve()}")
    chunks: list[Chunk] = []

    def emit(rel, title, heading, buf):
        body = "\n".join(buf).strip()
        if body:
            for part in _split_long(body):
                chunks.append(Chunk(len(chunks), rel, title, heading, part))

    for path in sorted(kb.rglob("*.md")):
        if path.name in SKIP_FILES:
            continue
        rel = path.relative_to(kb).as_posix()
        title, heading, buf = path.stem, "Overview", []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## "):
                emit(rel, title, heading, buf)
                heading, buf = line[3:].strip(), []
            else:
                buf.append(line)
        emit(rel, title, heading, buf)

    pdf_chunks = _extract_pdf_chunks(kb, len(chunks))
    chunks.extend(pdf_chunks)

    if not chunks:
        raise ValueError(f"No document content found in {kb.resolve()}")
    return chunks



_TOKEN = re.compile(r"\d+(?:\.\d+)?|[a-z]+")


def _stem(w: str) -> str:
    """Tiny suffix stripper so 'defects/defect', 'preprocessed/preprocessing', 'balanced/balance' match."""
    if w.isdigit() or len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("sses", "ches", "shes", "xes")):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    if w.endswith("ing") and len(w) > 5:
        w = w[:-3]
    elif w.endswith("ed") and len(w) > 4:
        w = w[:-2]
    if w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w


QUESTION_WORDS = {"use", "used", "uses", "using", "tell", "tells", "does", "did"}
STOP_WORDS = ENGLISH_STOP_WORDS | QUESTION_WORDS


def analyze(text: str) -> list[str]:
    text = text.lower().replace("_", " ")
    return [_stem(t) for t in _TOKEN.findall(text) if t not in STOP_WORDS]


# Domain synonym groups: words within the same group are treated as interchangeable
# when matching queries to document terms. This bridges vocabulary mismatch
# (e.g. user says "classes", document says "categories" or "types").
_SYNONYM_GROUPS = [
    {"class", "classes", "category", "categories", "type", "types", "kind", "kinds"},
]

# Pre-compute stem-level synonym map from the groups above.
_STEM_SYNONYMS: dict[str, set[str]] = {}
for _grp in _SYNONYM_GROUPS:
    _stems = {_stem(w) for w in _grp}
    for _s in _stems:
        _STEM_SYNONYMS[_s] = _stems - {_s}


class TfidfRetriever:
    """Keyword retrieval. Needs no downloads and runs fully offline.

    Two domain rules on top of plain TF-IDF:
      * category routing: the 15 category files look alike, so they are boosted when the question names
        that category and down-weighted when it names none (otherwise they crowd out the general documents);
      * coverage: share of the question's content words found in the best passage, used to refuse
        questions that only match by accident (e.g. 'world' in 'real-world').
    """
    name = "tfidf"
    default_min_score = 0.12
    default_min_coverage = 0.34

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vec = TfidfVectorizer(analyzer=analyze, sublinear_tf=True)
        self.X = self.vec.fit_transform([c.search_text for c in chunks])
        self.chunk_terms = [set(analyze(c.search_text)) for c in chunks]
        # category name tokens, e.g. 'metal_nut' -> {'metal', 'nut'}
        self.cat_tokens = {}
        for c in chunks:
            if c.source.startswith("categories/"):
                name = re.sub(r"^\d+_|\.md$", "", c.source.split("/")[-1])
                self.cat_tokens[c.source] = set(analyze(name))

    def _route(self, qterms: set[str], source: str) -> float:
        if not source.startswith("categories/"):
            return 1.0
        named = [
            src for src, toks in self.cat_tokens.items()
            if toks <= qterms or ("nut" in toks and "nut" in qterms)
        ]
        if not named:
            return 0.4
        return 1.5 if source in named else 0.3

    def coverage(self, query: str, chunk: Chunk) -> float:
        """Fraction of query content-words found in the chunk, treating domain synonyms as matches."""
        q = set(analyze(query))
        if not q:
            return 0.0
        chunk_t = self.chunk_terms[chunk.id]
        covered = sum(
            1 for term in q
            if term in chunk_t or any(s in chunk_t for s in _STEM_SYNONYMS.get(term, ()))
        )
        return covered / len(q)

    def has_term_overlap(self, text: str, chunk: Chunk) -> bool:
        """True if at least one analyzed term from *text* (or its synonym) appears in *chunk*."""
        terms = set(analyze(text))
        if not terms:
            return False
        chunk_t = self.chunk_terms[chunk.id]
        return any(
            t in chunk_t or any(s in chunk_t for s in _STEM_SYNONYMS.get(t, ()))
            for t in terms
        )

    @staticmethod
    def _expand_query(query: str) -> str:
        """Append domain synonyms to the query for broader TF-IDF matching."""
        words = set(re.findall(r'[a-zA-Z]+', query.lower()))
        extras: set[str] = set()
        for group in _SYNONYM_GROUPS:
            if words & group:
                extras |= group - words
        if extras:
            return query + " " + " ".join(extras)
        return query

    def search(self, query: str, k: int = 4):
        expanded = self._expand_query(query)
        sims = (self.X @ self.vec.transform([expanded]).T).toarray().ravel()
        qterms = set(analyze(query))          # original terms for routing
        sims = np.array([s * self._route(qterms, c.source) for s, c in zip(sims, self.chunks)])
        order = np.argsort(-sims)[:k]
        return [(self.chunks[i], float(sims[i])) for i in order if sims[i] > 0]


class FaissRetriever:
    """FAISS vector database retriever with Hugging Face Sentence Transformers embeddings."""
    name = "faiss"
    default_min_score = 0.25
    default_min_coverage = 0.0

    def __init__(
        self,
        chunks: list[Chunk],
        model_name: str | None = None,
        cache_dir: Path | None = None,
    ):
        import hashlib
        import os
        import faiss
        from sentence_transformers import SentenceTransformer

        self.chunks = chunks
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.model = SentenceTransformer(self.model_name)

        # Precompute category tokens for routing
        self.cat_tokens = {}
        for c in chunks:
            if c.source.startswith("categories/"):
                name = re.sub(r"^\d+_|\.md$", "", c.source.split("/")[-1])
                self.cat_tokens[c.source] = set(analyze(name))

        # Check for cached index
        cache_dir = cache_dir or (Path(__file__).parent / ".cache")
        cache_dir.mkdir(parents=True, exist_ok=True)

        content_hash = hashlib.sha256(
            (self.model_name + "::" + "||".join(c.search_text for c in chunks)).encode("utf-8")
        ).hexdigest()[:16]

        idx_file = cache_dir / f"faiss_{content_hash}.index"

        if idx_file.is_file():
            self.index = faiss.read_index(str(idx_file))
        else:
            embeddings = self.model.encode(
                [c.search_text for c in chunks],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(np.array(embeddings, dtype=np.float32))
            try:
                faiss.write_index(self.index, str(idx_file))
            except Exception:
                pass

    def _route(self, qterms: set[str], source: str) -> float:
        if not source.startswith("categories/"):
            return 1.0
        named = [
            src for src, toks in self.cat_tokens.items()
            if toks <= qterms or ("nut" in toks and "nut" in qterms)
        ]
        if not named:
            return 0.75
        return 1.25 if source in named else 0.5

    def search(self, query: str, k: int = 4):
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        top_n = min(len(self.chunks), max(k * 4, 25))
        scores, indices = self.index.search(
            np.array([q_emb], dtype=np.float32), top_n
        )
        qterms = set(analyze(query))
        scored = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            c = self.chunks[idx]
            adj = float(score) * self._route(qterms, c.source)
            scored.append((c, adj))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


DenseRetriever = FaissRetriever


def make_retriever(kind: str | None, chunks: list[Chunk]):
    if kind == "tfidf":
        return TfidfRetriever(chunks)
    return FaissRetriever(chunks)

