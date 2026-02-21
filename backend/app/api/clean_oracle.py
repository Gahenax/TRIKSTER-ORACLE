from fastapi import APIRouter, HTTPException
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
    ValidationAnswerType,
    DialogueState,
    CognitiveSignals,
    ActionChoice,
    RenderProfile,
    enforce_hardening_rules,
    resolve_fact_answer,
    infer_render_profile
)
import uuid
import time

router = APIRouter(prefix="/api/v2/clean", tags=["Clean Oracle V2"])

# In-memory store for MVP sessions
SESSION_STORE: Dict[str, DialogueState] = {}

@router.post("/infer")
async def infer(request: Dict[str, Any]):
    """
    Orchestrated inference endpoint based on the Python Integration Blueprint.
    """
    session_id = request.get("session_id")
    turn_index = request.get("turn_index", 1)
    
    if turn_index == 1:
        # Turn 1: Logic Initialization
        sid = session_id or str(uuid.uuid4())
        state = DialogueState(session_id=sid, turn_index=1)
        
        # Mock Turn 1 Inference Logic
        a1 = Assumption(
            assumption_id="A1",
            statement="El operador tiene un umbral de pérdida definido.",
            unlocks_conclusion="Evaluación de riesgo-beneficio sin adivinar.",
            closing_question_ids=["Q1"]
        )
        a2 = Assumption(
            assumption_id="A2",
            statement="Existe evidencia verificable de condiciones externas.",
            unlocks_conclusion="Veredicto condicionado a hechos.",
            closing_question_ids=["Q2"]
        )
        q1 = ValidationQuestion(
            question_id="Q1",
            targets_assumption_id="A1",
            prompt="¿Cuál es tu pérdida máxima tolerable (%)?",
            answer_type=ValidationAnswerType.NUMERIC,
            numeric_unit="%",
            numeric_range=(0.1, 100.0)
        )
        q2 = ValidationQuestion(
            question_id="Q2",
            targets_assumption_id="A2",
            prompt="Aporta un hecho verificable (dato + fuente).",
            answer_type=ValidationAnswerType.FACT
        )
        
        state.assumptions = {"A1": a1, "A2": a2}
        state.questions = {"Q1": q1, "Q2": q2}
        state.findings = {"F1": Finding(
            statement="Con umbral de pérdida y evidencia, la evaluación puede cerrarse.",
            status=FindingStatus.PROVISIONAL,
            depends_on=["A1", "A2"]
        )}
        
        SESSION_STORE[sid] = state
        
        out = OutputLimpioV2(
            reframe=Reframe(statement=f"Análisis estructural de: {request.get('text', '')[:50]}..."),
            exclusions=Exclusions(items=["No conclusions without validation."]),
            rigorous_findings=[],
            critical_assumptions=[a1, a2],
            validation_interrogatory=[q1, q2],
            next_steps=[NextStep(action="Responde Q1 y Q2.")],
            verdict=Verdict(
                strength=VerdictStrength.CONDITIONAL,
                statement="Si respondes estas preguntas, en el próximo turno promoveré supuestos y cerraré el veredicto.",
                conditions=["Resolver A1", "Resolver A2"]
            )
        )
    
    elif turn_index == 2:
        # Turn 2: State Resolution
        if not session_id or session_id not in SESSION_STORE:
            raise HTTPException(status_code=400, detail="Invalid session_id for turn 2.")
        
        state = SESSION_STORE[session_id]
        state.turn_index = 2
        
        context_answers = request.get("context_answers", {})
        signals = CognitiveSignals(
            action_choice=request.get("action_choice"),
            clarity_vote=request.get("clarity_vote")
        )
        
        # Apply Answers & Infer Profile
        for qid, raw in context_answers.items():
            if qid in state.questions:
                q = state.questions[qid]
                # Logic to resolver assumption
                a = state.assumptions.get(q.targets_assumption_id)
                if a:
                    if q.answer_type == ValidationAnswerType.FACT:
                        if resolve_fact_answer(raw): a.status = AssumptionStatus.VALIDATED
                    else:
                        a.status = AssumptionStatus.VALIDATED # Simplification for mock
        
        state.render_profile = infer_render_profile(state, signals)
        
        # Promote findings
        validated_ids = {aid for aid, a in state.assumptions.items() if a.status == AssumptionStatus.VALIDATED}
        for f in state.findings.values():
            if all(aid in validated_ids for aid in f.depends_on):
                f.status = FindingStatus.RIGOROUS

        out = OutputLimpioV2(
            reframe=Reframe(statement="Cierre de análisis bajo validaciones."),
            exclusions=Exclusions(items=[]),
            rigorous_findings=list(state.findings.values()),
            critical_assumptions=list(state.assumptions.values()),
            validation_interrogatory=[],
            next_steps=[NextStep(action="Seguimiento")],
            verdict=Verdict(
                strength=VerdictStrength.RIGOROUS if len(validated_ids) >= 2 else VerdictStrength.CONDITIONAL,
                statement="Veredicto final alcanzado." if len(validated_ids) >= 2 else "Veredicto parcial.",
                conditions=["Validaciones completas."] if len(validated_ids) >= 2 else ["Pendiente Q1/Q2."]
            )
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported turn index.")

    # Apply Hardening
    enforce_hardening_rules(out)
    
    return {
        "session_id": out.reframe.statement if turn_index == 1 else session_id, # Simplified for demo
        "session_id_real": SESSION_STORE[session_id].session_id if turn_index == 2 else sid,
        "turn_index": turn_index,
        "render_profile": state.render_profile.value,
        "output_markdown": out.to_markdown(state.render_profile),
        "output": out.to_dict()
    }

@router.post("/feedback")
async def feedback(request: FeedbackRequest):
    return {"status": "recorded"}

@router.post("/donate")
async def donate(request: DonationRequest):
    return {"status": "recorded"}
