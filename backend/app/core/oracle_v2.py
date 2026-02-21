"""
Trikster Oracle - Core Engine V2 (Cohesive Architecture)
-------------------------------------------------------
Implementation based on the Python Integration Blueprint.
Includes: Render Profiles, Hardening, State Machine, and Telemetry.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import time
import uuid

# =============================================================================
# 0) Enums & Constants
# =============================================================================

class RenderProfile(str, Enum):
    DAILY = "daily"   # default: "amigo muy culto"
    DENSE = "dense"   # less scaffolding, more density (same rigor)

class VerdictStrength(str, Enum):
    NO_VERDICT = "no_verdict"
    CONDITIONAL = "conditional"
    RIGOROUS = "rigorous"

class ValidationAnswerType(str, Enum):
    BINARY = "binary"
    NUMERIC = "numeric"
    FACT = "fact"
    CHOICE = "choice"

class AssumptionStatus(str, Enum):
    OPEN = "open"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    STALE = "stale"

class FindingStatus(str, Enum):
    PROVISIONAL = "provisional"
    RIGOROUS = "rigorous"

class ActionChoice(str, Enum):
    REFRAME = "A) Reformular mi pregunta"
    GET_DATA = "B) Buscar datos adicionales"
    DECIDE_ANYWAY = "C) Tomar una decisión igual"
    NOT_SURE = "D) No estoy seguro / no me sirve"

# Hard limits (fusibles)
MAX_CRITICAL_ASSUMPTIONS_PER_TURN = 3
MAX_VALIDATION_QUESTIONS_PER_TURN = 4

# Imperatives blacklist (simple hardening)
IMPERATIVE_BLOCKLIST = [
    "deberías", "compra", "vende", "recomiendo", "haz", "debe", "tienes que",
    "invierte", "no inviertas", "hazlo", "no lo hagas"
]

# Allowed FACT sources
FACT_ALLOWED_SOURCE_TYPES = {"official", "exchange"}

# =============================================================================
# 1) Data Models
# =============================================================================

@dataclass(frozen=True)
class Reframe:
    statement: str

@dataclass(frozen=True)
class Exclusions:
    items: List[str]

@dataclass
class Finding:
    statement: str
    status: FindingStatus = FindingStatus.PROVISIONAL
    support: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)

@dataclass
class Assumption:
    assumption_id: str
    statement: str
    unlocks_conclusion: str
    status: AssumptionStatus = AssumptionStatus.OPEN
    closing_question_ids: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class ValidationQuestion:
    question_id: str
    targets_assumption_id: str
    prompt: str
    answer_type: ValidationAnswerType
    choices: Optional[List[str]] = None
    numeric_unit: Optional[str] = None
    numeric_range: Optional[Tuple[float, float]] = None

@dataclass(frozen=True)
class NextStep:
    action: str
    verification: Optional[str] = None

@dataclass
class Verdict:
    strength: VerdictStrength
    statement: str
    conditions: List[str] = field(default_factory=list)

@dataclass
class OutputLimpioV2:
    reframe: Reframe
    exclusions: Exclusions
    rigorous_findings: List[Finding]
    critical_assumptions: List[Assumption]
    validation_interrogatory: List[ValidationQuestion]
    next_steps: List[NextStep]
    verdict: Verdict

    def to_dict(self) -> Dict[str, Any]:
        return _as_jsonable(self)

    def to_markdown(self, profile: RenderProfile) -> str:
        def h(title: str) -> str:
            return f"## {title}\n"

        daily_leadin = ""
        if profile == RenderProfile.DAILY:
            daily_leadin = (
                "Nota: no cierro conclusiones por cortesía. "
                "Si falta evidencia, propongo validaciones que permiten cerrar en el próximo turno.\n\n"
            )

        lines: List[str] = []
        lines.append(daily_leadin.rstrip())

        lines.append(h("Reencuadre").rstrip())
        lines.append(self.reframe.statement.strip())
        lines.append("")

        lines.append(h("Exclusiones").rstrip())
        if self.exclusions.items:
            for it in self.exclusions.items:
                lines.append(f"- {it.strip()}")
        else:
            lines.append("- (Ninguna)")
        lines.append("")

        lines.append(h("Hallazgos rigurosos").rstrip())
        if self.rigorous_findings:
            for f in self.rigorous_findings:
                tag = "RIGUROSO" if f.status == FindingStatus.RIGOROUS else "PROVISIONAL"
                lines.append(f"- **[{tag}]** {f.statement.strip()}")
                for s in f.support[:3]:
                    lines.append(f"  - {s.strip()}")
        else:
            lines.append("- (Aún no hay hallazgos cerrados)")
        lines.append("")

        lines.append(h("Supuestos críticos").rstrip())
        if self.critical_assumptions:
            for a in self.critical_assumptions:
                if profile == RenderProfile.DAILY:
                    lines.append(f"- **{a.assumption_id}**: Esto depende de que: {a.statement.strip()}")
                else:
                    lines.append(f"- **{a.assumption_id}**: {a.statement.strip()}")
                lines.append(f"  - → Si se valida: {a.unlocks_conclusion.strip()}")
                lines.append(f"  - Estado: {a.status.value}")
        else:
            lines.append("- (Ninguno)")
        lines.append("")

        lines.append(h("Interrogatorio de validación").rstrip())
        if self.validation_interrogatory:
            if profile == RenderProfile.DAILY:
                lines.append("Si quieres avanzar sin adivinar, necesito solo estas respuestas:\n")
            for q in self.validation_interrogatory:
                extra = ""
                if q.answer_type == ValidationAnswerType.CHOICE and q.choices:
                    extra = f" (opciones: {', '.join(q.choices)})"
                if q.answer_type == ValidationAnswerType.NUMERIC and q.numeric_unit:
                    extra = f" (unidad: {q.numeric_unit})"
                lines.append(
                    f"- **{q.question_id}** → {q.targets_assumption_id} "
                    f"[{q.answer_type.value}]{extra}: {q.prompt.strip()}"
                )
        else:
            lines.append("- (No hay preguntas de cierre necesarias)")
        lines.append("")

        lines.append(h("Próximos pasos verificables").rstrip())
        if self.next_steps:
            for ns in self.next_steps:
                if ns.verification:
                    lines.append(f"- {ns.action.strip()}\n  Verificación: {ns.verification.strip()}")
                else:
                    lines.append(f"- {ns.action.strip()}")
        else:
            lines.append("- (Ninguno)")
        lines.append("")

        lines.append(h("Veredicto").rstrip())
        lines.append(f"**[{self.verdict.strength.value}]** {self.verdict.statement.strip()}")
        if self.verdict.conditions:
            lines.append("\nCondiciones:")
            for c in self.verdict.conditions:
                lines.append(f"- {c.strip()}")

        return "\n".join([l for l in lines if l is not None])

# =============================================================================
# 2) Hardening & Helper Functions
# =============================================================================

def enforce_hardening_rules(out: OutputLimpioV2) -> None:
    if len(out.critical_assumptions) > MAX_CRITICAL_ASSUMPTIONS_PER_TURN:
        raise ValueError("Too many critical assumptions (max 3).")
    if len(out.validation_interrogatory) > MAX_VALIDATION_QUESTIONS_PER_TURN:
        raise ValueError("Too many validation questions (max 4).")

    a_ids = {a.assumption_id for a in out.critical_assumptions}
    for q in out.validation_interrogatory:
        if q.targets_assumption_id not in a_ids:
            raise ValueError(f"Question {q.question_id} targets missing assumption {q.targets_assumption_id}.")

    v = out.verdict.statement.lower()
    if any(w in v for w in IMPERATIVE_BLOCKLIST):
        raise ValueError("Verdict contains imperatives (blocked).")

def _as_jsonable(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        d = {}
        for k, v in asdict(obj).items():
            d[k] = _as_jsonable(v)
        return d
    if isinstance(obj, dict):
        return {k: _as_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_as_jsonable(x) for x in obj]
    return obj

def resolve_fact_answer(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    value = raw.get("value")
    source_type = raw.get("source_type")
    source_ref = raw.get("source_ref")
    if not value or not source_type or not source_ref:
        return False
    if source_type not in FACT_ALLOWED_SOURCE_TYPES:
        return False
    return True

# =============================================================================
# 3) State Management
# =============================================================================

@dataclass
class DialogueState:
    session_id: str
    turn_index: int = 1
    render_profile: RenderProfile = RenderProfile.DAILY
    assumptions: Dict[str, Assumption] = field(default_factory=dict)
    questions: Dict[str, ValidationQuestion] = field(default_factory=dict)
    findings: Dict[str, Finding] = field(default_factory=dict)
    validated_answers: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

@dataclass
class CognitiveSignals:
    action_choice: Optional[ActionChoice] = None
    clarity_vote: Optional[bool] = None
    friction_stage: Optional[str] = None
    friction_type: Optional[str] = None

def infer_render_profile(state: DialogueState, signals: CognitiveSignals) -> RenderProfile:
    if signals.action_choice in (ActionChoice.REFRAME, ActionChoice.GET_DATA) and signals.clarity_vote is True:
        return RenderProfile.DENSE
    return RenderProfile.DAILY
