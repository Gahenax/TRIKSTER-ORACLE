from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class FrictionStage(str, Enum):
    FORMULATE = "formular_problema"
    SEPARATE = "separar_hechos_inferencias"
    LIMITS = "definir_limites"
    NEXT_STEP = "disenar_siguiente_paso"
    INTERPRET = "interpretar_output"

class FrictionType(str, Enum):
    CONCEPTUAL = "ambigüedad_conceptual"
    DATA_LACK = "falta_de_datos"
    CRITERIA_CONFLICT = "conflicto_de_criterios"
    CLOSURE_PRESSURE = "presion_por_cierre"
    UNCLEAR_OUTPUT = "output_poco_claro"

class FrictionEvent(BaseModel):
    """
    Captures a cognitive friction event (Atasco) without storing private content.
    """
    session_id: str
    stage: FrictionStage
    friction_type: FrictionType
    clarity_vote: bool = Field(..., description="Was the output eventually clear? ✅/❌")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "anon-123",
                "stage": "definir_limites",
                "friction_type": "falta_de_datos",
                "clarity_vote": True
            }
        }
