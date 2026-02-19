from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from app.schemas.contract_v2 import (
    InferenceRequest, 
    OutputLimpioV2Schema, 
    FeedbackRequest, 
    DonationRequest
)
from app.core.oracle_v2 import (
    OutputLimpioV2, 
    Reframe, 
    Exclusions, 
    Finding, 
    Assumption, 
    ValidationQuestion, 
    NextStep, 
    Verdict,
    VerdictStrength,
    FindingStatus,
    AssumptionStatus,
    ValidationAnswerType
)
import uuid

router = APIRouter(prefix="/api/v2/clean", tags=["Clean Oracle V2"])

@router.post("/infer", response_model=OutputLimpioV2Schema)
async def infer(request: InferenceRequest):
    """
    Main inference endpoint using Clean Output V2 protocol.
    Note: For the MVP, this uses a mock implementation of the transition logic.
    Actual LLM integration would wrap this contract.
    """
    # 1. Enforce privacy: session_id generation if missing
    session_id = request.session_id or str(uuid.uuid4())
    
    # 2. Extract information (Mock behavior for first turn vs follow-up)
    # In a real scenario, an LLM would process 'request.text' and 'request.context_answers'
    # to produce the structured OutputLimpioV2 components.
    
    # Mock Example (Based on the spec crypto example)
    is_follow_up = bool(request.context_answers)
    
    if not is_follow_up:
        # First turn: Passive enumeration -> Active Interrogatory
        reframe = Reframe(statement=f"Análisis estructural de: {request.text[:100]}...")
        exclusions = Exclusions(items=["No se emite veredicto sin validación de fondos y liquidez."])
        findings = [
            Finding(
                statement="Sin datos de riesgo personal, cualquier recomendación es ruido.",
                status=FindingStatus.RIGOROUS
            )
        ]
        assumptions = [
            Assumption(
                assumption_id="A1",
                statement="El operador posee fondos que puede permitirse perder.",
                unlocks_conclusion="Riesgo de ruina manejable.",
                closing_question_ids=["Q1"]
            ),
             Assumption(
                assumption_id="A2",
                statement="Existen fuentes de datos confiables para el volumen de trading.",
                unlocks_conclusion="Validación de liquidez operativa.",
                closing_question_ids=["Q2"]
            )
        ]
        questions = [
            ValidationQuestion(
                question_id="Q1",
                targets_assumption_id="A1",
                prompt="¿Cuál es tu pérdida máxima tolerable (%)?",
                answer_type=ValidationAnswerType.NUMERIC,
                numeric_unit="%"
            ),
            ValidationQuestion(
                question_id="Q2",
                targets_assumption_id="A2",
                prompt="Indica volumen 24h y fuente oficial.",
                answer_type=ValidationAnswerType.FACT
            )
        ]
        verdict = Verdict(
            strength=VerdictStrength.CONDITIONAL,
            statement="Si respondes estas preguntas, en el próximo turno promoveré supuestos a hallazgos rigurosos y cerraré el veredicto solo bajo esas condiciones.",
            conditions=["Resolver A1 para habilitar conclusión.", "Resolver A2 para liquidez."]
        )
    else:
        # Turn 2: Resolve based on context_answers
        from app.core.oracle_v2 import resolve_fact_answer
        
        q1_answer = request.context_answers.get("Q1")
        q2_answer = request.context_answers.get("Q2")
        
        reframe = Reframe(statement=f"Resolución de inferencia para sesión {session_id}")
        exclusions = Exclusions(items=[])
        findings = []
        assumptions = []
        
        # Rule 2: Robust validation for Q1 (Numeric) and Q2 (Fact)
        if isinstance(q1_answer, (int, float)):
            findings.append(Finding(
                statement=f"Riesgo validado en {q1_answer}%.",
                status=FindingStatus.RIGOROUS,
                support=["Declaración directa del operador."]
            ))
        
        if resolve_fact_answer(q2_answer):
            findings.append(Finding(
                statement=f"Liquidez operativa validada vía {q2_answer.get('source_type')}.",
                status=FindingStatus.RIGOROUS,
                support=[f"Fuente: {q2_answer.get('source_ref')}"]
            ))

        verdict = Verdict(
            strength=VerdictStrength.RIGOROUS if len(findings) >= 2 else VerdictStrength.CONDITIONAL,
            statement="Análisis cerrado bajo validaciones recibidas." if len(findings) >= 2 else "Veredicto parcial.",
            conditions=["Todas las críticas resueltas."] if len(findings) >= 2 else ["Pendiente validación de liquidez o riesgo."]
        )
        questions = []

    output = OutputLimpioV2(
        reframe=reframe,
        exclusions=exclusions,
        rigorous_findings=findings,
        critical_assumptions=assumptions,
        validation_interrogatory=questions,
        next_steps=[NextStep(action="Ejecutar monitor de eventos 24h.")],
        verdict=verdict
    )

    # Rule 1: Enforce Hardening (Final Check before sending)
    from app.core.oracle_v2 import enforce_hardening_rules
    enforce_hardening_rules(output)

    # Rule 5: Telemetry Mock (Non-PII)
    print(f"TELEMETRY: session={session_id}, turn={1 if not is_follow_up else 2}, assumptions={len(assumptions)}, findings={len(findings)}")

    return output.to_dict()

@router.post("/feedback")
async def feedback(request: FeedbackRequest):
    """
    Captures cognitive friction (Atascos) without sensitive content.
    """
    # Logic to store in telemetry DB (sqlite/jsonl)
    return {"status": "recorded", "event_id": str(uuid.uuid4())}

@router.post("/donate")
async def donate(request: DonationRequest):
    """
    Records interest in supporting the project.
    """
    return {"status": "recorded", "message": "Gracias por apoyar el rigor."}
