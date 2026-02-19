from pydantic import BaseModel, Field
from typing import List, Optional

class CleanOutput(BaseModel):
    """
    Schema for the Clean Output Contract (V1.0).
    Enforces a rigorous structure on all AI responses.
    """
    reframe: str = Field(
        ..., 
        description="Reframed technical version of the user's query, neutralizing bias."
    )
    findings: List[str] = Field(
        ..., 
        description="List of rigorous, provable facts or explicit data points."
    )
    exclusions: List[str] = Field(
        ..., 
        description="List of conclusions or inferences that CANNOT be made with current data."
    )
    assumptions: List[str] = Field(
        ..., 
        description="Inferences that need validation mapping to potential conclusions."
    )
    verification_questions: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="High-precision questions to turn assumptions into facts."
    )
    next_steps: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=3,
        description="Verifiable binary actions for the user outside the system."
    )

    class Config:
        schema_extra = {
            "example": {
                "reframe": "Análisis de correlación entre incentivos y motivación.",
                "findings": ["Incentivos implementados: salario y fruta.", "Percepción de baja motivación reportada."],
                "exclusions": ["No se puede concluir causalidad salarial.", "Falta métrica de rendimiento."],
                "assumptions": ["El salario es competitivo.", "El equipo valora incentivos materiales."],
                "next_steps": ["Medir rotación", "Encuesta de Herzberg"]
            }
        }
