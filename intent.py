import re
from typing import Dict, List, Tuple


INTENTS = {
    "symptoms": ["symptom", "symptoms"],
    "risk_factors": ["risk", "risk factor", "risk factors", "increase the risk"],
    "diagnostic_techniques": ["diagnostic", "diagnosis", "technique", "techniques"],
    "dataset": ["dataset", "data set", "instances", "features", "source"],
    "cancer_types": ["type of cancer", "types of cancer", "cancer types", "stage", "stages"],
    "results": ["accuracy", "result", "results", "benchmark", "performance", "best model"],
    "conclusion": ["conclusion", "summary"],
}


ALGORITHM_ALIASES = {
    "svm": ["svm", "support vector"],
    "ann": ["ann", "artificial neural"],
    "rf": ["rf", "random forest"],
    "mlr": ["mlr", "multiple linear regression"],
}


SECTION_NAMES = ["abstract", "introduction", "methodology", "results", "conclusion"]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _detect_intent(question: str) -> str:
    q = _normalize(question)
    for intent, keywords in INTENTS.items():
        for kw in keywords:
            if kw in q:
                return intent
    return "generic"


def _extract_entities(question: str) -> Dict[str, List[str]]:
    q = _normalize(question)

    diseases: List[str] = []
    if "lung cancer" in q:
        diseases.append("lung cancer")

    algorithms: List[str] = []
    for short, kws in ALGORITHM_ALIASES.items():
        if any(kw in q for kw in kws):
            algorithms.append(short)

    sections: List[str] = []
    for s in SECTION_NAMES:
        if s in q:
            sections.append(s)

    return {"diseases": diseases, "algorithms": algorithms, "sections": sections}


def classify_intent_and_entities(question: str) -> Dict[str, object]:
    intent = _detect_intent(question)
    entities = _extract_entities(question)
    return {"intent": intent, "entities": entities}


