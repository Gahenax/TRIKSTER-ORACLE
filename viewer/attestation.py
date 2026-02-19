from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field

# For Pydantic V2 use Field(pattern=...)
class Attestation(BaseModel):
    created_at: str = Field(min_length=10, max_length=64)
    reports_count: int = Field(ge=0)
    report_ids: List[str]
    pack_hash_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def compute_pack_hash(reports_dir: Path) -> Tuple[str, List[str]]:
    """
    Pack hash = SHA256 of concatenation of:
      each report_id + ":" + file_sha256
    in sorted report_id order.
    """
    if not reports_dir.exists():
        return hashlib.sha256(b"").hexdigest(), []
    files = sorted(reports_dir.glob("*.json"))
    ids = [f.stem for f in files]
    parts: List[str] = []
    for rid in ids:
        p = (reports_dir / f"{rid}.json").read_bytes()
        fh = hashlib.sha256(p).hexdigest()
        parts.append(f"{rid}:{fh}")
    raw = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), ids
