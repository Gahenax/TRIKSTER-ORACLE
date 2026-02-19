"""
Trikster Oracle - Core Engine V2
--------------------------------
Implementation of the deterministic contract for the Clean Output V2.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Literal

# Re-importing the core logic provided in the spec to make it accessible to the API
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
        """Convert to dictionary for API response."""
        return {
            "reframe": {"statement": self.reframe.statement},
            "exclusions": {"items": self.exclusions.items},
            "rigorous_findings": [
                {
                    "statement": f.statement,
                    "status": f.status.value,
                    "support": f.support,
                    "depends_on": f.depends_on
                } for f in self.rigorous_findings
            ],
            "critical_assumptions": [
                {
                    "assumption_id": a.assumption_id,
                    "statement": a.statement,
                    "unlocks_conclusion": a.unlocks_conclusion,
                    "status": a.status.value,
                    "closing_question_ids": a.closing_question_ids
                } for a in self.critical_assumptions
            ],
            "validation_interrogatory": [
                {
                    "question_id": q.question_id,
                    "targets_assumption_id": q.targets_assumption_id,
                    "prompt": q.prompt,
                    "answer_type": q.answer_type.value,
                    "choices": q.choices,
                    "numeric_unit": q.numeric_unit,
                    "numeric_range": q.numeric_range
                } for q in self.validation_interrogatory
            ],
            "next_steps": [
                {"action": ns.action, "verification": ns.verification} for ns in self.next_steps
            ],
            "verdict": {
                "strength": self.verdict.strength.value,
                "statement": self.verdict.statement,
                "conditions": self.verdict.conditions
            }
        }

def enforce_hardening_rules(out: OutputLimpioV2) -> None:
    """Enforce strict MVP invariants (Rules 1A, 1B, 1C)."""
    
    # Rule 1B: Complexity limits
    if len(out.critical_assumptions) > 3:
        raise ValueError("Límite de complejidad excedido: máx 3 supuestos.")
    if len(out.validation_interrogatory) > 4:
        raise ValueError("Límite de complejidad excedido: máx 4 preguntas.")

    # Rule 1A: Mapping integrity
    assumption_ids = {a.assumption_id for a in out.critical_assumptions}
    for q in out.validation_interrogatory:
        if q.targets_assumption_id not in assumption_ids:
            raise ValueError(f"Pregunta {q.question_id} apunta a supuesto inexistente {q.targets_assumption_id}.")
    
    for a in out.critical_assumptions:
        if not a.closing_question_ids:
            raise ValueError(f"Supuesto {a.assumption_id} no tiene mecanismo de cierre.")

    # Rule 1C: No imperatives
    forbid = ["deberías", "compra", "vende", "haz", "recomiendo", "debe"]
    v_statement = out.verdict.statement.lower()
    if any(word in v_statement for word in forbid):
        raise ValueError("Veredicto contiene imperativos prohibidos.")

def resolve_fact_answer(answer: Any) -> bool:
    """
    Rule 2: Structured FACT validation.
    Expects: {"value": str, "source_type": "official|exchange|other", "source_ref": str}
    """
    if not isinstance(answer, dict):
        return False
    
    source_type = answer.get("source_type")
    source_ref = answer.get("source_ref")
    
    if source_type in ["official", "exchange"] and source_ref:
        return True
    return False
