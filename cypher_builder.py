from typing import Dict, Any, List


def build_queries(intent: str, entities: Dict[str, List[str]], question_text: str) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []

    if intent == "symptoms":
        specs.append({
            "tag": "Symptoms",
            "query": "MATCH (:Introduction)-[:MENTIONS_SYMPTOM]->(s:Symptom) RETURN s.name AS item",
            "params": {},
        })
    elif intent == "risk_factors":
        specs.append({
            "tag": "RiskFactors",
            "query": "MATCH (:Introduction)-[:IDENTIFIES_RISK_FACTOR]->(r:RiskFactor) RETURN r.name AS item",
            "params": {},
        })
    elif intent == "diagnostic_techniques":
        specs.append({
            "tag": "DiagnosticTechniques",
            "query": "MATCH (:Introduction)-[:USES_TECHNIQUE]->(t:Technique) RETURN t.name AS item",
            "params": {},
        })
    elif intent == "dataset":
        specs.append({
            "tag": "Dataset",
            "query": "MATCH (:Methodology)-[:USES_DATASET]->(d:Dataset) RETURN d.name AS name, d.source AS source, d.instances AS instances, d.features AS features, d.format AS format",
            "params": {},
        })
    elif intent == "cancer_types":
        specs.append({
            "tag": "CancerTypes",
            "query": "MATCH (:Introduction)-[:DISCUSSES_CANCER_TYPE]->(c:CancerType) RETURN c.name AS item",
            "params": {},
        })
    elif intent == "results":
        specs.append({
            "tag": "Results",
            "query": "MATCH (m:Model)-[:HAS_RESULT]->(r:Result) RETURN coalesce(m.full_name,m.name) AS model, r.metric AS metric, r.accuracy AS accuracy",
            "params": {},
        })
        specs.append({
            "tag": "BestModel",
            "query": "MATCH (:Paper)-[:BEST_MODEL]->(m:Model) RETURN coalesce(m.full_name,m.name) AS bestModel",
            "params": {},
        })
    elif intent == "conclusion":
        specs.append({
            "tag": "Conclusion",
            "query": "MATCH (s:Section:Conclusion) RETURN s.name AS name, s.text AS text",
            "params": {},
        })

    
    if not specs:
        specs.append({
            "tag": "Sections",
            "query": "MATCH (s:Section) WHERE toLower(s.text) CONTAINS toLower($q) RETURN s.name AS name, s.text AS text LIMIT 50",
            "params": {"q": question_text},
        })

    return specs


