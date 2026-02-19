import uuid
import time
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.utils import generate_event_key
from sim.scenario import Scenario
from core.db.models import RiskProfileEnum
from .language_guard import language_guard
from .telemetry import log_oracle_request

def evaluate_oracle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Oracle Composer Pipeline (Hardware-aligned v2).
    Focus: Risk mitigation and quantified uncertainty.
    """
    t_start = time.time()
    request_id = str(uuid.uuid4())
    
    sport = request.get("sport", "FOOTBALL")
    primary = request.get("primary")
    opponent = request.get("opponent")
    profile_str = request.get("risk_profile", "NEUTRAL")
    stake = request.get("stake", 100.0)
    
    # Validation
    if not primary or not opponent:
        raise ValueError("Both actors (primary/opponent) are required.")

    # 1. Selection & Identification
    # In a real run, we'd fetch actual features. For MVP, we mock.
    features = {
        "rating_diff": request.get("rating_diff", 0.0),
        "home_advantage": request.get("home_advantage", 100.0)
    }
    
    event_key = generate_event_key(sport, "PRO_LEAGUE", primary, opponent, datetime.now(timezone.utc))
    snapshot_id = f"snap_{request_id[:8]}"
    snapshot_data = {"primary": primary, "opponent": opponent, "features": features}

    # 2. Execute Simulation (Risk-First Engine)
    scenario = Scenario(
        event_key=event_key,
        risk_profile=profile_str,
        stake=stake,
        features=features,
        snapshot_id=snapshot_id,
        snapshot_data=snapshot_data
    )
    
    sim_result = scenario.evaluate() # Uses adaptive sims
    pls_percent = sim_result["pls"] * 100
    zone = sim_result["zone"]

    # 3. Narrative Composition (Sober, No Recommendations)
    title = f"EVALUACIÓN DE RIESGO: {primary} vs {opponent}"
    
    body_sections = [
        {
            "header": "ZONA DE RIESGO",
            "content": f"El escenario se clasifica en zona [{zone}] basado en el perfil {profile_str}."
        },
        {
            "header": "PROBABILIDAD DE PÉRDIDA MAYOR (PLS)",
            "content": f"Existe un {pls_percent:.1f}% de probabilidad de pérdida sustancial (>= 30% del capital)."
        },
        {
            "header": "FRAGILIDAD DEL ESCENARIO",
            "content": f"Indicador de sensibilidad: {sim_result['fragility']:.4f}. Las condiciones negativas muestran alta varianza."
        }
    ]

    # Apply Language Guard
    title = language_guard(title)
    for section in body_sections:
        section["header"] = language_guard(section["header"])
        section["content"] = language_guard(section["content"])

    output = {
        "version": "oracle.v2.risk",
        "request_id": request_id,
        "event_key": event_key,
        "verdict": {
            "risk_zone": zone,
            "pls_score": sim_result["pls"],
            "fragility": sim_result["fragility"]
        },
        "details": {
            "tail_percentiles": sim_result["tail_percentiles"],
            "n_sims": sim_result["n_sims"],
            "signature": sim_result["determinism_signature"]
        },
        "text": {
            "title": title,
            "body_sections": body_sections
        },
        "audit": {
            "timing_ms": (time.time() - t_start) * 1000,
            "snapshot_id": snapshot_id
        }
    }
    
    log_oracle_request(output)
    return output
