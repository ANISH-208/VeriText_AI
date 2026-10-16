import re
from difflib import SequenceMatcher
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import LEXICAL_THRESHOLD, SEMANTIC_THRESHOLD
from app.models.embedding_model import encode, status as semantic_status
from app.utils.text_utils import normalize_text, split_passages, word_count


def _token_highlights(left: str, right: str) -> tuple[list[dict], list[dict]]:
    left_tokens = list(re.finditer(r"\b[\w’'-]+\b", left, re.UNICODE))
    right_tokens = list(re.finditer(r"\b[\w’'-]+\b", right, re.UNICODE))
    matcher = SequenceMatcher(None, [m.group().casefold() for m in left_tokens], [m.group().casefold() for m in right_tokens], autojunk=False)
    left_ranges, right_ranges = [], []
    for a, b, size in matcher.get_matching_blocks():
        if size < 2:
            continue
        first, last = left_tokens[a], left_tokens[a + size - 1]
        left_ranges.append({"start": first.start(), "end": last.end()})
        first, last = right_tokens[b], right_tokens[b + size - 1]
        right_ranges.append({"start": first.start(), "end": last.end()})
    return left_ranges, right_ranges


def _page_for(passage: str, pages: list[str]) -> int | None:
    target = re.sub(r"\s+", " ", passage).strip().casefold()
    if not target:
        return None
    for page_number, page in enumerate(pages, start=1):
        candidate = re.sub(r"\s+", " ", page).strip().casefold()
        if target in candidate:
            return page_number
    return None


def analyze(submitted: str, references: list[dict], standalone: bool = False, submitted_pages: list[str] | None = None) -> dict:
    submitted = normalize_text(submitted)
    if not submitted:
        raise ValueError("Submitted text is empty.")
    source_passages = split_passages(submitted)
    ref_rows = []
    for ref in references:
        if ref.get("pages"):
            for page_number, page_text in enumerate(ref["pages"], start=1):
                ref_rows.extend((ref["filename"], passage, page_number) for passage in split_passages(page_text))
        else:
            ref_rows.extend((ref["filename"], passage, None) for passage in split_passages(ref["text"]))
    exact_map = {re.sub(r"\W+", " ", p.lower()).strip(): name for name, p, _ in ref_rows}
    candidates = [p for _, p, _ in ref_rows]
    lexical_best = [0.0] * len(source_passages)
    lexical_idx = [-1] * len(source_passages)
    semantic_best = [0.0] * len(source_passages)
    semantic_idx = [-1] * len(source_passages)
    semantic_available = False
    if candidates:
        combined = source_passages + candidates
        word = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)
        try:
            w = word.fit_transform(combined)
            c = char.fit_transform(combined)
            source_count = len(source_passages)
            for start in range(0, source_count, 128):
                end = min(source_count, start + 128)
                sim = .55 * cosine_similarity(w[start:end], w[source_count:]) + .45 * cosine_similarity(c[start:end], c[source_count:])
                for offset, row in enumerate(sim):
                    lexical_idx[start + offset] = int(row.argmax()); lexical_best[start + offset] = float(row.max())
        except ValueError:
            pass
        embeddings = encode(combined)
        if embeddings is not None:
            semantic_available = True
            matrix = np.asarray(embeddings)
            source_count = len(source_passages)
            candidate_vectors = matrix[source_count:]
            for start in range(0, source_count, 128):
                end = min(source_count, start + 128)
                sem = matrix[start:end] @ candidate_vectors.T
                for offset, row in enumerate(sem):
                    semantic_idx[start + offset] = int(row.argmax()); semantic_best[start + offset] = max(0.0, float(row.max()))
    matches = []
    matched_words = 0
    for i, passage in enumerate(source_passages):
        normalized = re.sub(r"\W+", " ", passage.lower()).strip()
        exact = len(normalized) >= 25 and normalized in exact_map
        lex, sem = lexical_best[i], semantic_best[i]
        category = "exact" if exact else "near_exact" if lex >= LEXICAL_THRESHOLD else "semantic" if sem >= SEMANTIC_THRESHOLD else None
        idx = semantic_idx[i] if category == "semantic" else lexical_idx[i]
        if category and idx >= 0:
            name, refpass, ref_page = ref_rows[idx]
            # Exact candidate by direct lookup if best vector candidate differs.
            if exact:
                name = exact_map[normalized]
                matched_exact = next(((p, page) for n, p, page in ref_rows if n == name and re.sub(r"\W+", " ", p.lower()).strip() == normalized), (refpass, ref_page))
                refpass, ref_page = matched_exact
            submitted_highlights, reference_highlights = _token_highlights(passage, refpass)
            matches.append({"submitted_passage": passage, "reference_name": name, "reference_passage": refpass,
                "lexical_score": round(lex, 4), "semantic_score": round(sem, 4), "category": category,
                "detection_method": "normalized exact text" if exact else "word/character TF-IDF" if category == "near_exact" else "sentence embedding",
                "submitted_highlights": submitted_highlights, "reference_highlights": reference_highlights,
                "submitted_page": _page_for(passage, submitted_pages or []), "reference_page": ref_page,
                "citation_note": ""})
            matched_words += word_count(passage)
    # Sentence-level passages are non-overlapping, so each submitted word contributes at most once.
    lex_scores = [m["lexical_score"] for m in matches]
    sem_scores = [m["semantic_score"] for m in matches]
    counts = {key: sum(m["category"] == key for m in matches) for key in ("exact", "near_exact", "semantic")}
    refs = []
    for ref in references:
        rm = [m for m in matches if m["reference_name"] == ref["filename"]]
        refs.append({"filename": ref["filename"], "match_count": len(rm), "strongest_lexical": max((m["lexical_score"] for m in rm), default=0), "strongest_semantic": max((m["semantic_score"] for m in rm), default=0)})
    ai = writing_signals(submitted)
    return {"submitted_word_count": word_count(submitted), "standalone": standalone,
        "metrics": {"matched_text_coverage": round(min(100, 100 * matched_words / max(1, word_count(submitted))), 2) if references else None,
        "mean_lexical_similarity": round(float(np.mean(lex_scores)), 4) if lex_scores else 0,
        "max_lexical_similarity": round(max(lex_scores, default=0), 4), "mean_semantic_similarity": (round(float(np.mean(sem_scores)), 4) if sem_scores else 0) if semantic_available else None,
        "max_semantic_similarity": (round(max(sem_scores, default=0), 4)) if semantic_available else None, "matched_passage_count": len(matches), **{f"{k}_match_count": v for k,v in counts.items()}},
        "matches": matches, "references": refs, "semantic_available": semantic_available, "semantic_model": semantic_status(), "ai_writing_signals": ai,
        "limitations": ["Similarity is an indicator for human review, not a finding of plagiarism.", "Semantic similarity can reflect shared subject matter and is not evidence of copying.", "No external source database is searched."] if not references else ["Matches require human review; shared facts, quotations, and common phrasing can produce similarity.", "No external source database is searched."]}


def writing_signals(text: str) -> dict:
    passages = split_passages(text)
    sentences = [word_count(s) for s in passages if word_count(s)]
    words = re.findall(r"\b[\w’'-]+\b", text.lower())
    diversity = len(set(words)) / max(1, len(words))
    variation = float(np.std(sentences) / max(1, np.mean(sentences))) if sentences else 0.0
    # This is an exploratory feature score, not a probability or classifier output.
    pattern_score = round(max(0, min(100, (1 - min(variation, 1)) * 50 + (1 - diversity) * 50)), 1)
    return {"label": "Exploratory writing-pattern signals", "pattern_score": pattern_score, "sentence_length_variation": round(variation, 3), "lexical_diversity": round(diversity, 3), "disclaimer": "Not a validated AI detector or probability of AI authorship. Do not use alone to accuse or penalize an author."}
