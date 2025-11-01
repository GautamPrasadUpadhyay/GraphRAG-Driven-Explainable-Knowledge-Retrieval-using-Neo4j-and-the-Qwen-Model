import math
import re
from typing import Dict, List, Any


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", (text or "").lower())


def lexical_overlap_score(question: str, text: str) -> float:
    q_tokens = set(_tokenize(question))
    t_tokens = set(_tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    inter = len(q_tokens & t_tokens)
    return inter / max(1, len(q_tokens))


def entity_match_boost(text: str, entities: Dict[str, List[str]]) -> float:
    score = 0.0
    t = (text or "").lower()
    for alg in entities.get("algorithms", []):
        if alg in t:
            score += 0.2
    for dis in entities.get("diseases", []):
        if dis in t:
            score += 0.2
    return min(score, 0.6)


def score_items(question: str, tag: str, rows: List[Dict[str, Any]], entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for r in rows:
        text = r.get("text") or r.get("item") or r.get("model") or ""
        lex = lexical_overlap_score(question, text)
        ent = entity_match_boost(text, entities)
        prox = 0.2 if tag in {"Symptoms","RiskFactors","DiagnosticTechniques","CancerTypes","Dataset","Results","Conclusion"} else 0.0
        final = 0.5 * lex + 0.3 * ent + 0.2 * prox
        r_scored = dict(r)
        r_scored["_score"] = final
        r_scored["_tag"] = tag
        scored.append(r_scored)
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def select_top_n(scored_items: List[Dict[str, Any]], n: int = 8) -> List[Dict[str, Any]]:
    return scored_items[:n]


