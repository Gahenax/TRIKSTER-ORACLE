import logging
import json
from typing import Dict, Any

logger = logging.getLogger("oracle.telemetry")

def log_oracle_request(output: Dict[str, Any]):
    """
    Structured logging for Oracle requests (v2 Risk-First).
    Excludes PII/secrets.
    """
    telemetry = {
        "event": "oracle_request_v2",
        "request_id": output.get("request_id"),
        "event_key": output.get("event_key"),
        "verdict": {
            "risk_zone": output["verdict"]["risk_zone"],
            "pls_score": output["verdict"]["pls_score"],
            "fragility": output["verdict"]["fragility"]
        },
        "performance": {
            "n_sims": output["details"]["n_sims"],
            "timing_ms": output["audit"]["timing_ms"]
        }
    }
    
    logger.info(f"ORACLE_METRIC: {json.dumps(telemetry)}")
