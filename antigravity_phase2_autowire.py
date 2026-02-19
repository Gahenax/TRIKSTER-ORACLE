#!/usr/bin/env python3
"""
ANTIGRAVITY IMPLEMENTATION PROMPT (Python)
Task: Implement Phase 2 of the Kernel Integration Implementation Plan for Trickster Oracle.

You already have the sim_kernel scaffolding and new tests created. Now you must:
1) Wire kernel into /api/v2/simulate WITHOUT breaking the existing response contract.
2) Add service wrappers to call existing engine + explain modules.
3) Preserve token gating logic exactly as-is.
4) Add optional observability fields ONLY inside response["meta"].
5) Ensure all existing tests still pass + new kernel tests pass.

CRITICAL CONSTRAINT:
- /api/v2/simulate response shape MUST remain identical (except optional meta fields).

Execution approach:
- This script will:
  - discover repo anchors (backend/app/*)
  - verify sim_kernel exists
  - create/ensure missing action modules (if the scaffolding was placed elsewhere)
  - inject kernel wiring into the /api/v2/simulate handler (routes_v2.py or equivalent)
  - add a safe response_mapper that returns the current response shape unchanged
  - run pytest (instructions) and stop if failures

Important:
- Do NOT refactor unrelated files.
- If auto-patching cannot be done safely, emit exact patch blocks to apply manually.

"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


ROOT = Path(".").resolve()
BACKEND = ROOT / "backend"
APP = BACKEND / "app"


def die(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def log(msg: str) -> None:
    print(msg)


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def file_exists(p: Path) -> bool:
    return p.exists() and p.is_file()


def find_py_files(root: Path) -> List[Path]:
    return list(root.rglob("*.py"))


def grep_files(root: Path, pattern: str) -> List[Path]:
    rx = re.compile(pattern)
    hits: List[Path] = []
    for p in find_py_files(root):
        try:
            t = read_text(p)
        except Exception:
            continue
        if rx.search(t):
            hits.append(p)
    return hits


def choose_routes_v2_file() -> Path:
    # Prefer explicit routes_v2.py under backend/app
    candidates = []
    for name in ["routes_v2.py", "routes.py", "api_v2.py", "routes_v2/__init__.py"]:
        p = APP / name
        if file_exists(p):
            candidates.append(p)
    if candidates:
        return candidates[0]

    # Grep for a FastAPI router defining /api/v2/simulate or /simulate
    hits = grep_files(APP, r"(api/v2/simulate|/api/v2/simulate|/simulate)")
    if hits:
        # Prefer file names containing 'routes' or 'v2'
        hits_sorted = sorted(
            hits,
            key=lambda p: (
                0 if "routes_v2" in p.name else
                1 if "routes" in p.name else
                2 if "v2" in p.name else 3,
                len(str(p))
            ),
        )
        return hits_sorted[0]

    die("Could not locate routes file containing /api/v2/simulate or /simulate under backend/app.")


def assert_scaffolding_present() -> None:
    sim_kernel = APP / "sim_kernel"
    if not sim_kernel.exists():
        # Some repos place it in backend/app/sim_kernel already; if missing, fail fast.
        die("backend/app/sim_kernel not found. Ensure Phase 1 scaffolding is present in backend/app/sim_kernel/")
    required = [
        sim_kernel / "kernel.py",
        sim_kernel / "config.py",
        sim_kernel / "state.py",
        sim_kernel / "journal.py",
        sim_kernel / "actions",
        sim_kernel / "actions" / "emit.py",
        sim_kernel / "actions" / "mc_run.py",
        sim_kernel / "actions" / "explain.py",
        sim_kernel / "actions" / "ingest.py",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        die("Missing sim_kernel scaffolding files:\n- " + "\n- ".join(missing))


def locate_engine_and_explain() -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (engine_import_path, explain_import_path) to use inside routes file.

    Expectation per plan:
      - engine function: app.core.engine.simulate_event_v2
      - explain function: app.core.explain.explain (or similar)
    We will verify via grep to reduce friction.
    """
    engine_hits = grep_files(APP, r"\bsimulate_event_v2\b")
    explain_hits = grep_files(APP, r"\bdef\s+explain\b|\bexplain\(")

    engine_path = None
    explain_path = None

    for p in engine_hits:
        if "core/engine.py" in str(p).replace("\\", "/"):
            engine_path = "app.core.engine"
            break
    if engine_path is None and engine_hits:
        # Use first hit as fallback
        # Derive module path from filesystem
        rel = engine_hits[0].relative_to(BACKEND)
        engine_path = ".".join(rel.with_suffix("").parts)

    for p in explain_hits:
        if "core/explain.py" in str(p).replace("\\", "/"):
            explain_path = "app.core.explain"
            break
    if explain_path is None and explain_hits:
        rel = explain_hits[0].relative_to(BACKEND)
        explain_path = ".".join(rel.with_suffix("").parts)

    return engine_path, explain_path


def ensure_kernel_import_block(routes_text: str) -> str:
    """
    Add required imports for kernel wiring if missing.
    """
    needed_imports = [
        "from app.sim_kernel.kernel import TricksterKernel",
        "from app.sim_kernel.state import SimulationState",
        "from app.sim_kernel.config import SimulationConfig as KernelSimulationConfig",
        "from app.sim_kernel.actions.ingest import IngestAction",
        "from app.sim_kernel.actions.mc_run import MonteCarloAction",
        "from app.sim_kernel.actions.explain import ExplainAction",
        "from app.sim_kernel.actions.emit import EmitAction",
    ]

    # Place imports after existing imports block (best-effort).
    if all(imp in routes_text for imp in needed_imports):
        return routes_text

    # Find insertion point: after last import line near top.
    lines = routes_text.splitlines()
    last_import_idx = -1
    for i, line in enumerate(lines[:200]):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i

    insertion = []
    for imp in needed_imports:
        if imp not in routes_text:
            insertion.append(imp)
    if not insertion:
        return routes_text

    if last_import_idx == -1:
        # No imports found; prepend.
        new_text = "\n".join(insertion) + "\n\n" + routes_text
        return new_text

    new_lines = lines[: last_import_idx + 1] + [""] + insertion + [""] + lines[last_import_idx + 1 :]
    return "\n".join(new_lines)


def inject_service_wrappers(routes_text: str, engine_module: str, explain_module: str) -> str:
    """
    Inject service wrappers once into the routes file, guarded by a marker.

    The wrappers must:
    - call existing simulate_event_v2 + explain
    - preserve old response shape via response_mapper delegating to original code
      (we will use a placeholder mapper and instruct Antigravity to wire it to the existing builder)
    """
    marker = "# --- SIM_KERNEL_SERVICES (autogen) ---"
    if marker in routes_text:
        return routes_text

    engine_import = f"from {engine_module} import simulate_event_v2" if engine_module else None
    explain_import = f"from {explain_module} import explain" if explain_module else None

    block_lines = []
    block_lines.append(marker)
    if engine_import:
        block_lines.append(engine_import)
    else:
        block_lines.append("# NOTE: Could not auto-detect engine module for simulate_event_v2; import it manually.")
    if explain_import:
        block_lines.append(explain_import)
    else:
        block_lines.append("# NOTE: Could not auto-detect explain module; import it manually.")

    block_lines.append("")
    block_lines.append("def _mc_engine_service(request, features, rating, seed, depth, max_runs):")
    block_lines.append("    \"\"\"Wrapper around existing simulate_event_v2. Must honor max_runs.\"\"\"")
    block_lines.append("    # IMPORTANT: Preserve existing request parsing and token gating; do not duplicate gating here.")
    block_lines.append("    # Map incoming request dict to your existing engine input contract.")
    block_lines.append("    # If your engine already accepts a dict, pass through with minimal adaptation.")
    block_lines.append("    # If it requires Pydantic models, construct them exactly like the pre-kernel code did.")
    block_lines.append("    #")
    block_lines.append("    # REQUIRED: ensure n_simulations <= max_runs (budget).")
    block_lines.append("    return simulate_event_v2(request=request, features=features, rating=rating, seed=seed, depth=depth, max_runs=max_runs)")
    block_lines.append("")
    block_lines.append("def _explainer_service(request, features, rating, mc_result, max_chars):")
    block_lines.append("    \"\"\"Wrapper around existing explain(). Must honor max_chars.\"\"\"")
    block_lines.append("    return explain(request=request, features=features, rating=rating, mc_result=mc_result, max_chars=max_chars)")
    block_lines.append("")
    block_lines.append("def _response_mapper_service(state):")
    block_lines.append("    \"\"\"")
    block_lines.append("    Map SimulationState -> EXISTING /api/v2/simulate response shape.")
    block_lines.append("    CRITICAL: This must produce the exact same dict structure as before kernel integration.")
    block_lines.append("    The only permitted additions are optional keys inside response['meta'].")
    block_lines.append("    \"\"\"")
    block_lines.append("    # TODO (MANDATORY): Replace this placeholder with a call to the pre-kernel response builder.")
    block_lines.append("    # For now, return the pre-kernel response by reusing existing logic in this routes file.")
    block_lines.append("    # Example pattern:")
    block_lines.append("    #   resp = build_simulate_response(original_inputs...)")
    block_lines.append("    #   return resp")
    block_lines.append("    return state.artifacts.get('pre_kernel_response') or {}")
    block_lines.append("# --- /SIM_KERNEL_SERVICES (autogen) ---")

    # Insert block near top after imports (best-effort).
    lines = routes_text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines[:250]):
        if line.strip() == "" and i > 10:
            insert_at = i + 1
            break
    new_lines = lines[:insert_at] + block_lines + [""] + lines[insert_at:]
    return "\n".join(new_lines)


def wrap_simulate_handler(routes_file: Path, routes_text: str) -> str:
    """
    Replace the body of the /api/v2/simulate handler with kernel pipeline,
    but preserve all existing gating logic.

    Strategy:
    - Find the function that handles the endpoint by searching for decorator usage.
    - Insert a minimal kernel-run block AFTER the gating logic and AFTER the request payload is validated.
    - To minimize risk, we do NOT delete old code. We:
        (1) compute old_resp using the existing code path
        (2) stash it into state.artifacts['pre_kernel_response']
        (3) run kernel actions that call mc/explain and then emit uses response_mapper to return old_resp
      This ensures the response shape stays identical.
    - Then we allow emit action to add optional meta fields.

    If we cannot safely locate the handler, emit instructions and do nothing.
    """
    # Detect simulate function by common names, and/or decorator patterns.
    # Try to find a def that includes "simulate" and is decorated by router.post(...simulate...)
    rx_def = re.compile(r"^def\s+(simulate_v2|simulate|simulate_event|simulate_endpoint)\b", re.M)
    rx_route = re.compile(r"@.*\.(post|api_route)\(.*(api/v2/simulate|/api/v2/simulate|/simulate)", re.S)

    if not rx_route.search(routes_text):
        log("WARN: Could not find a route decorator for /api/v2/simulate in the selected routes file.")
        log("      You must manually wire kernel into the correct endpoint handler.")
        return routes_text

    # Find the first def after the route decorator that matches "simulate"
    # Best-effort parse: locate the decorator line, then the next def line.
    lines = routes_text.splitlines(True)
    idx_route = None
    for i, line in enumerate(lines):
        if "api/v2/simulate" in line or "/simulate" in line:
            if "@".encode():  # no-op for readability
                pass
        if re.search(r"@.*\.(post|api_route)\(.*(api/v2/simulate|/api/v2/simulate|/simulate)", line):
            idx_route = i
            break
    if idx_route is None:
        # fallback: crude scan window
        for i, line in enumerate(lines):
            if "api/v2/simulate" in line or "/simulate" in line:
                if line.strip().startswith("@"):
                    idx_route = i
                    break

    if idx_route is None:
        log("WARN: Could not locate decorator line index for simulate endpoint.")
        return routes_text

    # Locate the def line after decorator
    idx_def = None
    for i in range(idx_route, min(idx_route + 40, len(lines))):
        if lines[i].lstrip().startswith("def "):
            idx_def = i
            break
        if lines[i].lstrip().startswith("async def "):
            idx_def = i
            break

    if idx_def is None:
        log("WARN: Could not locate function definition after simulate decorator.")
        return routes_text

    # We will inject a guarded kernel integration block near the end of handler,
    # right before the original return statement (or at end if none).
    text = routes_text

    marker = "# --- SIM_KERNEL_INTEGRATION (autogen) ---"
    if marker in text:
        return text

    # Insert near first "return" inside that function: best effort with indentation detection.
    # Determine function indent (0 typically) and inner indent (4 spaces).
    def_line = lines[idx_def]
    base_indent = len(def_line) - len(def_line.lstrip(" "))
    inner_indent = " " * (base_indent + 4)

    # Find end of function by scanning until next top-level def with <= base_indent (best effort).
    end_idx = None
    for i in range(idx_def + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            continue
        cur_indent = len(line) - len(line.lstrip(" "))
        if (line.lstrip().startswith("def ") or line.lstrip().startswith("async def ")) and cur_indent <= base_indent:
            end_idx = i
            break
    if end_idx is None:
        end_idx = len(lines)

    func_block = "".join(lines[idx_def:end_idx])

    # Try to find last return line in function block.
    return_pos = func_block.rfind("\n" + inner_indent + "return ")
    if return_pos == -1:
        # No return found; inject at end before function ends.
        insert_point_global = sum(len(l) for l in lines[:end_idx])
    else:
        insert_point_global = sum(len(l) for l in lines[:idx_def]) + return_pos

    integration_block = []
    integration_block.append(f"{inner_indent}{marker}\n")
    integration_block.append(f"{inner_indent}# Kernel integration is designed to be non-breaking.\n")
    integration_block.append(f"{inner_indent}# Steps:\n")
    integration_block.append(f"{inner_indent}#  1) Compute the pre-kernel response using existing logic (already done above).\n")
    integration_block.append(f"{inner_indent}#  2) Run kernel pipeline to attach observability meta only.\n")
    integration_block.append(f"{inner_indent}#\n")
    integration_block.append(f"{inner_indent}# REQUIRED: ensure `pre_kernel_response` exists before this block.\n")
    integration_block.append(f"{inner_indent}try:\n")
    integration_block.append(f"{inner_indent}    # Build kernel config from request if possible; otherwise default.\n")
    integration_block.append(f"{inner_indent}    _kcfg = KernelSimulationConfig(\n")
    integration_block.append(f"{inner_indent}        scheduler='FIFO',\n")
    integration_block.append(f"{inner_indent}        seed=int(getattr(request, 'seed', 1337)) if hasattr(request, 'seed') else 1337,\n")
    integration_block.append(f"{inner_indent}        depth='standard',\n")
    integration_block.append(f"{inner_indent}    )\n")
    integration_block.append(f"{inner_indent}    _kstate = SimulationState(request=(request.dict() if hasattr(request, 'dict') else request))\n")
    integration_block.append(f"{inner_indent}    # Stash the already-built response to guarantee exact response shape.\n")
    integration_block.append(f"{inner_indent}    _kstate.artifacts['pre_kernel_response'] = locals().get('response') or locals().get('resp') or locals().get('result')\n")
    integration_block.append(f"{inner_indent}    _kernel = TricksterKernel(services={{\n")
    integration_block.append(f"{inner_indent}        'mc_engine': _mc_engine_service,\n")
    integration_block.append(f"{inner_indent}        'explainer': _explainer_service,\n")
    integration_block.append(f"{inner_indent}        'response_mapper': _response_mapper_service,\n")
    integration_block.append(f"{inner_indent}    }})\n")
    integration_block.append(f"{inner_indent}    _actions = [IngestAction(), MonteCarloAction(), ExplainAction(), EmitAction()]\n")
    integration_block.append(f"{inner_indent}    _kstate2, _journal = _kernel.run(_actions, _kstate, _kcfg)\n")
    integration_block.append(f"{inner_indent}    # Replace outgoing response with kernel-emitted response (identical shape, with optional meta additions).\n")
    integration_block.append(f"{inner_indent}    _kernel_response = _kstate2.artifacts.get('response')\n")
    integration_block.append(f"{inner_indent}    if isinstance(_kernel_response, dict):\n")
    integration_block.append(f"{inner_indent}        response = _kernel_response\n")
    integration_block.append(f"{inner_indent}except Exception:\n")
    integration_block.append(f"{inner_indent}    # Non-breaking guarantee: if anything fails, keep original response.\n")
    integration_block.append(f"{inner_indent}    pass\n")
    integration_block.append(f"{inner_indent}# --- /SIM_KERNEL_INTEGRATION (autogen) ---\n")

    patched = text[:insert_point_global] + "".join(integration_block) + text[insert_point_global:]
    return patched


def main() -> None:
    if not BACKEND.exists():
        die("Expected repo structure with ./backend folder. Run this from repo root.")

    assert_scaffolding_present()

    routes_file = choose_routes_v2_file()
    log(f"Selected routes file: {routes_file}")

    engine_module, explain_module = locate_engine_and_explain()
    log(f"Detected engine module: {engine_module}")
    log(f"Detected explain module: {explain_module}")

    routes_text = read_text(routes_file)
    routes_text = ensure_kernel_import_block(routes_text)
    routes_text = inject_service_wrappers(routes_text, engine_module or "", explain_module or "")
    routes_text = wrap_simulate_handler(routes_file, routes_text)

    # Write patched routes file
    write_text(routes_file, routes_text)
    log("Patched routes file with kernel imports, service wrappers, and integration block.")

    log("")
    log("MANDATORY MANUAL STEP (do this now):")
    log("1) Open the simulate endpoint handler in the routes file.")
    log("2) Identify the variable holding the pre-kernel response dict. Ensure it is assigned to `response` before the autogen integration block runs.")
    log("   - If your handler uses `return {...}` directly, refactor minimally to:")
    log("       response = {...}")
    log("       <autogen kernel block>")
    log("       return response")
    log("3) Ensure `request` refers to the request model or dict as used previously. The autogen block expects it.")
    log("4) In _mc_engine_service and _explainer_service, replace the placeholder call signatures with the REAL ones used pre-kernel.")
    log("   - The wrapper MUST honor max_runs / max_chars.")
    log("5) In _response_mapper_service, replace placeholder with the real pre-kernel response builder (or return the stashed pre-kernel response).")
    log("")

    log("TEST COMMANDS (run exactly):")
    log("cd backend")
    log("pytest -q")
    log("")
    log("If any failures occur:")
    log("- Do NOT change existing tests.")
    log("- Fix by wiring wrappers correctly and ensuring `response` is identical to pre-kernel shape.")
    log("- Keep kernel integration non-breaking (try/except).")


if __name__ == "__main__":
    main()
