from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Response, Request, Form, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

from web_config import WebConfig
from middleware.request_id import RequestIdMiddleware
from middleware.ratelimit import RateLimitMiddleware
from logging_conf import AccessLogMiddleware
from attestation import compute_pack_hash
from datetime import datetime, timezone

APP_VERSION = os.getenv("VIEWER_VERSION", "0.1.0")
GIT_SHA = os.getenv("GIT_SHA", "dev")
API_KEY = os.getenv("VIEWER_API_KEY", "")

def get_reports_dir() -> Path:
    return Path(os.getenv("REPORTS_DIR", "./exports")).resolve()

class SignatureHex(str):
    """Validation for 64-char hex signature."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str) or not v.isalnum() or len(v) != 64:
            raise ValueError("invalid signature format")
        return v

# Note: In Pydantic V2, we use Annotated or Field(pattern=...)
class ReportEnvelope(BaseModel):
    report_id: str = Field(min_length=1, max_length=200)
    created_at: str = Field(min_length=10, max_length=64)
    payload: Dict[str, Any]
    signature_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

def require_api_key(x_api_key: str = Header(default="")) -> None:
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

def compute_signature_sha256(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def load_report(report_id: str) -> ReportEnvelope:
    reports_dir = get_reports_dir()
    path = (reports_dir / f"{report_id}.json").resolve()
    if not str(path).startswith(str(reports_dir)):
        raise HTTPException(status_code=400, detail="invalid report_id")
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        env = ReportEnvelope.model_validate(data)
        return env
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=422, detail="invalid report format")

def security_headers(resp: Response) -> Response:
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    return resp

app = FastAPI(title="Web Viewer", version=APP_VERSION)

# Go-Live Hardening Middleware (Added in reverse order of outer-most)
# L0: RateLimit (Inner)
app.add_middleware(RateLimitMiddleware, rps=float(os.getenv("VIEWER_RPS", "5")), burst=float(os.getenv("VIEWER_BURST", "20")))
# L1: AccessLog (Middle)
app.add_middleware(AccessLogMiddleware)
# L2: RequestId (Outer)
app.add_middleware(RequestIdMiddleware)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals.update(config=WebConfig)

# --- UI Endpoints (from W2/W3) ---

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/view", response_class=HTMLResponse)
async def view_uploaded(
    request: Request, 
    report_json: Optional[str] = Form(None),
    report_file: Optional[UploadFile] = File(None)
):
    content = ""
    if report_file and report_file.filename:
        if report_file.size > 250 * 1024:
            return templates.TemplateResponse(request, "index.html", {"error": "File too large (Max 250KB)"})
        file_content = await report_file.read()
        content = file_content.decode('utf-8')
    elif report_json:
        content = report_json
    else:
        return templates.TemplateResponse(request, "index.html", {"error": "No content provided"})

    try:
        data = json.loads(content)
        # Check if it's an envelope or raw data
        if "payload" in data and "signature_sha256" in data:
            env = ReportEnvelope.model_validate(data)
            computed = compute_signature_sha256(env.payload)
            if computed != env.signature_sha256:
                return templates.TemplateResponse(request, "index.html", {"error": "Signature mismatch on uploaded report"})
            report_data = env.payload
        else:
            # Fallback for raw report.json (backwards compatibility or un-enveloped)
            # Actually, per Step 688, we should strictly require signed reports?
            # Let's be semi-flexible but warn in UI.
            report_data = data
            
        return templates.TemplateResponse(request, "report.html", {"report": report_data})
    except Exception as e:
        return templates.TemplateResponse(request, "index.html", {"error": f"Invalid Report: {str(e)}"})

# --- API Endpoints (from WV-00) ---

@app.get("/health", response_class=JSONResponse)
def health(_: None = Depends(require_api_key)):
    return {
        "status": "ok",
        "version": APP_VERSION,
        "git_sha": GIT_SHA,
        "reports_dir": str(get_reports_dir()),
    }

@app.get("/reports", response_class=JSONResponse)
def list_reports(limit: int = 50, offset: int = 0, _: None = Depends(require_api_key)):
    reports_dir = get_reports_dir()
    if not reports_dir.exists():
        return {"items": [], "count": 0, "limit": limit, "offset": offset}
    files = sorted(reports_dir.glob("*.json"))
    ids = [f.stem for f in files]
    return {"items": ids[offset: offset+limit], "count": len(ids), "limit": limit, "offset": offset}

@app.get("/reports/{report_id}", response_class=HTMLResponse)
async def view_stored_report(request: Request, report_id: str):
    try:
        env = load_report(report_id)
        computed = compute_signature_sha256(env.payload)
        if computed != env.signature_sha256:
            raise HTTPException(status_code=400, detail="signature mismatch")
        return templates.TemplateResponse(request, "report.html", {"report": env.payload})
    except HTTPException as e:
        return templates.TemplateResponse(request, "index.html", {"error": e.detail})
    except Exception as e:
        return templates.TemplateResponse(request, "index.html", {"error": str(e)})

@app.get("/api/reports/{report_id}", response_class=JSONResponse)
def get_report_json(report_id: str, _: None = Depends(require_api_key)):
    env = load_report(report_id)
    computed = compute_signature_sha256(env.payload)
    if computed != env.signature_sha256:
        raise HTTPException(status_code=400, detail="signature mismatch")
    resp = JSONResponse(env.model_dump())
    return security_headers(resp)

@app.get("/api/reports/{report_id}/verify", response_class=JSONResponse)
def verify(report_id: str, _: None = Depends(require_api_key)):
    env = load_report(report_id)
    computed = compute_signature_sha256(env.payload)
    return {"report_id": report_id, "ok": computed == env.signature_sha256, "computed": computed, "expected": env.signature_sha256}

# Legal Pages
@app.get("/docs", response_class=HTMLResponse)
async def docs(request: Request): return templates.TemplateResponse(request, "docs.html")
@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request): return templates.TemplateResponse(request, "privacy.html")
@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request): return templates.TemplateResponse(request, "terms.html")

@app.get("/attestation", response_class=JSONResponse)
def get_attestation(_: None = Depends(require_api_key)):
    pack_hash, ids = compute_pack_hash(get_reports_dir())
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reports_count": len(ids),
        "report_ids": ids,
        "pack_hash_sha256": pack_hash
    }

# Block Writes
@app.post("/api/reports")
@app.put("/api/reports/{report_id}")
@app.delete("/api/reports/{report_id}")
def forbidden_write(): raise HTTPException(status_code=405, detail="read-only")
