from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Any
from enum import Enum

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

class ReframeSchema(BaseModel):
    statement: str

class ExclusionsSchema(BaseModel):
    items: List[str]

class FindingSchema(BaseModel):
    statement: str
    status: FindingStatus
    support: List[str] = []
    depends_on: List[str] = []

class AssumptionSchema(BaseModel):
    assumption_id: str
    statement: str
    unlocks_conclusion: str
    status: AssumptionStatus
    closing_question_ids: List[str] = []

class ValidationQuestionSchema(BaseModel):
    question_id: str
    targets_assumption_id: str
    prompt: str
    answer_type: ValidationAnswerType
    choices: Optional[List[str]] = None
    numeric_unit: Optional[str] = None
    numeric_range: Optional[Tuple[float, float]] = None

class NextStepSchema(BaseModel):
    action: str
    verification: Optional[str] = None

class VerdictSchema(BaseModel):
    strength: VerdictStrength
    statement: str
    conditions: List[str] = []

class OutputLimpioV2Schema(BaseModel):
    reframe: ReframeSchema
    exclusions: ExclusionsSchema
    rigorous_findings: List[FindingSchema]
    critical_assumptions: List[AssumptionSchema]
    validation_interrogatory: List[ValidationQuestionSchema]
    next_steps: List[NextStepSchema]
    verdict: VerdictSchema

class InferenceRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    context_answers: Dict[str, Any] = {} # qid -> answer

class FeedbackRequest(BaseModel):
    session_id: str
    stage: str
    friction_type: str
    clarity_vote: bool

class DonationRequest(BaseModel):
    session_id: str
    amount_optional: Optional[float] = None
