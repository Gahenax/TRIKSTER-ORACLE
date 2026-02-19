"""
Trikster Oracle - Hardening Specification
-----------------------------------------
JSON Examples for Turn 1 and Turn 2 Interaction.
"""

# Turn 1: Initial Request
TURN1_REQUEST = {
    "text": "¿Debería invertir en el activo X ahora mismo?",
    "session_id": "session-rigor-001"
}

# Turn 1: Expected Response (Filtered/Cleaned)
TURN1_RESPONSE = {
    "reframe": {
        "statement": "Análisis de oportunidad de entrada en activo X bajo marco de riesgo-beneficio."
    },
    "exclusions": {
        "items": [
            "No se emite orden de compra sin perfil de riesgo.",
            "No se infiere liquidez sin datos del exchange."
        ]
    },
    "rigorous_findings": [
        {
            "statement": "Falta de parámetros operativos impide cierre de veredicto.",
            "status": "rigorous",
            "support": ["Regla de rigor: datos insuficientes."],
            "depends_on": []
        }
    ],
    "critical_assumptions": [
        {
            "assumption_id": "A1",
            "statement": "El operador posee fondos que puede permitirse perder.",
            "unlocks_conclusion": "Riesgo de ruina manejable.",
            "status": "open",
            "closing_question_ids": ["Q1"]
        },
        {
            "assumption_id": "A2",
            "statement": "Existen fuentes de datos confiables para el volumen de trading.",
            "unlocks_conclusion": "Validación de liquidez operativa.",
            "status": "open",
            "closing_question_ids": ["Q2"]
        }
    ],
    "validation_interrogatory": [
        {
            "question_id": "Q1",
            "targets_assumption_id": "A1",
            "prompt": "¿Cuál es tu pérdida máxima tolerable (%)?",
            "answer_type": "numeric",
            "numeric_unit": "%"
        },
        {
            "question_id": "Q2",
            "targets_assumption_id": "A2",
            "prompt": "Indica volumen 24h y fuente oficial.",
            "answer_type": "fact"
        }
    ],
    "next_steps": [
        {"action": "Check exchange listings for Activo X.", "verification": None}
    ],
    "verdict": {
        "strength": "conditional",
        "statement": "Si respondes estas preguntas, en el próximo turno promoveré supuestos a hallazgos rigurosos y cerraré el veredicto solo bajo esas condiciones.",
        "conditions": ["Resolver A1", "Resolver A2"]
    }
}

# Turn 2: Follow-up Request
TURN2_REQUEST = {
    "text": "Aquí están los datos.",
    "session_id": "session-rigor-001",
    "context_answers": {
        "Q1": 15.0,
        "Q2": {
            "value": "32M USDT",
            "source_type": "official",
            "source_ref": "https://exchange.com/api/v1/ticker/X"
        }
    }
}
