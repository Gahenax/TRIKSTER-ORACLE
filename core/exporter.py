import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ExportedReport(BaseModel):
    """Strict schema for exported reports (Sprint W1.1)"""
    app_version: str
    policy_version: str
    event_key: str
    snapshot_id: str
    seed: int
    config: Dict[str, Any]
    features_summary: Dict[str, float]
    results: Dict[str, Any] # pls_percent, zone, tail_percentiles, fragility
    audit: Dict[str, Any] # determinism_signature, created_at_utc, inputs_hashes

PROHIBITED_TERMS = ["bet", "value", "opportunity", "roi", "pick", "profit", "win"]

class ExportGuardError(Exception):
    """Raised when prohibited vocabulary is detected in export."""
    pass

def validate_vocabulary(data: Any):
    """
    Recursively scans data for prohibited terms.
    Task W1.3 - Vocabulary Guard.
    """
    if isinstance(data, str):
        lower_text = data.lower()
        for term in PROHIBITED_TERMS:
            if term in lower_text:
                raise ExportGuardError(f"Prohibited term '{term}' detected in export content.")
    elif isinstance(data, dict):
        for k, v in data.items():
            validate_vocabulary(k)
            validate_vocabulary(v)
    elif isinstance(data, list):
        for item in data:
            validate_vocabulary(item)

class ReportExporter:
    """
    Handles generation of a verified Report Pack.
    Task W1.2.
    """
    
    def __init__(self, export_root: str = "exports"):
        self.export_root = export_root

    def _calculate_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def export_pack(self, report_data: Dict[str, Any]) -> str:
        """
        Exports a report pack to a folder.
        Task W1.2.
        """
        # 1. Vocabulary Guard check
        validate_vocabulary(report_data)
        
        # 2. Schema Validation (implicitly via ExportedReport if we wanted to enforce strictly)
        # For now we assume report_data is well-formed from sim results
        
        event_key = report_data.get("event_key", "unknown")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pack_dir = os.path.join(self.export_root, f"report_{event_key[:8]}_{timestamp}")
        os.makedirs(pack_dir, exist_ok=True)
        
        # A. report.json
        report_path = os.path.join(pack_dir, "report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
            
        # B. manifest.json
        manifest = {
            "pack_id": os.path.basename(pack_dir),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": ["report.json"],
            "version": report_data.get("app_version", "0.0.0")
        }
        manifest_path = os.path.join(pack_dir, "manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        # C. hashes.json
        hashes = {
            "report.json": self._calculate_hash(report_path),
            "manifest.json": self._calculate_hash(manifest_path)
        }
        hashes_path = os.path.join(pack_dir, "hashes.json")
        with open(hashes_path, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2)
            
        return pack_dir
