import pytest
from app.core.oracle_v2 import (
    OutputLimpioV2, Reframe, Exclusions, Finding, Assumption, 
    ValidationQuestion, NextStep, Verdict, VerdictStrength,
    FindingStatus, ValidationAnswerType, enforce_hardening_rules,
    resolve_fact_answer
)

def build_valid_output():
    return OutputLimpioV2(
        reframe=Reframe(statement="Test reframe"),
        exclusions=Exclusions(items=["No data"]),
        rigorous_findings=[],
        critical_assumptions=[
            Assumption(
                assumption_id="A1",
                statement="Assum1",
                unlocks_conclusion="Conclusion1",
                closing_question_ids=["Q1"]
            )
        ],
        validation_interrogatory=[
            ValidationQuestion(
                question_id="Q1",
                targets_assumption_id="A1",
                prompt="Q1 prompt",
                answer_type=ValidationAnswerType.BINARY
            )
        ],
        next_steps=[NextStep(action="Step 1")],
        verdict=Verdict(strength=VerdictStrength.CONDITIONAL, statement="Veredicto condicional.")
    )

def test_enforce_complexity_limits():
    out = build_valid_output()
    # Exceed assumptions
    out.critical_assumptions = [out.critical_assumptions[0]] * 4
    with pytest.raises(ValueError, match="máx 3 supuestos"):
        enforce_hardening_rules(out)

def test_enforce_mapping_integrity():
    out = build_valid_output()
    # Question targets non-existent assumption
    out.validation_interrogatory[0] = ValidationQuestion(
        question_id="Q1",
        targets_assumption_id="A_MISSING",
        prompt="Bad Q",
        answer_type=ValidationAnswerType.BINARY
    )
    with pytest.raises(ValueError, match="apunta a supuesto inexistente"):
        enforce_hardening_rules(out)

def test_enforce_no_imperatives():
    out = build_valid_output()
    out.verdict.statement = "Deberías comprar ahora."
    with pytest.raises(ValueError, match="imperativos prohibidos"):
        enforce_hardening_rules(out)

def test_resolve_fact_answer():
    # Valid official
    assert resolve_fact_answer({
        "value": "32M",
        "source_type": "official",
        "source_ref": "http://ref.com"
    }) is True
    
    # Valid exchange
    assert resolve_fact_answer({
        "value": "100",
        "source_type": "exchange",
        "source_ref": "binance"
    }) is True
    
    # Invalid missing ref
    assert resolve_fact_answer({
        "value": "100",
        "source_type": "official"
    }) is False
    
    # Invalid type
    assert resolve_fact_answer({
        "value": "100",
        "source_type": "other",
        "source_ref": "unknown"
    }) is False

def test_golden_turn1_logic():
    # Verify the specific Turn 1 copy required for 'magic' training
    out = build_valid_output()
    out.verdict.statement = "Si respondes estas preguntas, en el próximo turno promoveré supuestos a hallazgos rigurosos y cerraré el veredicto solo bajo esas condiciones."
    # Should pass without raising
    enforce_hardening_rules(out)
