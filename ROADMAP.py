#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANTIGRAVITY EXEC ROADMAP — Proyecto Trickster (0 → Demo Escalable)

USAGE (Antigravity-friendly):
- Run this script as the "single source of truth" plan.
- It outputs a deterministic execution checklist, file tree, and DoD tests.
- Antigravity should implement tasks in strict order and record evidence per task.

NON-NEGOTIABLES
1) Causal order: Foundations → Engine → Explainability → API → UI → Tokens → Scale
2) Minimal changes per step. After each step: run tests + capture evidence.
3) Keep it educational/analytical: no gambling language, no "bets", no "picks".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# =========================
# Core Plan Data Structures
# =========================

@dataclass
class Evidence:
    required: List[str]


@dataclass
class DoD:
    """Definition of Done."""
    checks: List[str]


@dataclass
class Task:
    id: str
    title: str
    goal: str
    actions: List[str]
    dod: DoD
    evidence: Evidence
    risks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class Phase:
    name: str
    objective: str
    tasks: List[Task]


# =========================
# Project Scaffolding Specs
# =========================

TARGET_STACK = {
    "backend": "Python + FastAPI",
    "engine": "Pure Python (deterministic core) + NumPy optional",
    "frontend": "Vite + React (or Astro/Next if already used); keep demo simple",
    "charts": "Chart.js or Recharts",
    "storage": "In-memory cache for demo; upgrade path to Redis/DB",
}

REPO_TREE = r"""
trickster/
  README.md
  .gitignore
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py
      api/
        __init__.py
        routes.py
        schemas.py
      core/
        __init__.py
        engine.py
        model.py
        explain.py
        risk.py
        cache.py
      data/
        __init__.py
        sample_events.json
        sample_history.csv
      tests/
        test_engine.py
        test_api.py
        test_explain.py
  frontend/
    package.json
    vite.config.*
    src/
      main.tsx
      app/
        App.tsx
        pages/
          Home.tsx
          Simulator.tsx
          Result.tsx
        components/
          EventPicker.tsx
          ProbabilityCard.tsx
          DistributionChart.tsx
          ExplainPanel.tsx
          FooterDisclaimer.tsx
        lib/
          api.ts
          types.ts
"""

# =========================
# Roadmap Phases & Tasks
# =========================

PHASES: List[Phase] = [
    Phase(
        name="FASE 0 — Fundaciones",
        objective="Definir identidad, alcance y reglas duras del demo (sin humo, sin apuestas).",
        tasks=[
            Task(
                id="T0.1",
                title="Definir tesis, límites y copy anti-gambling",
                goal="Asegurar que Trickster es analítica educativa: probabilidades, escenarios, riesgo, sensibilidad.",
                actions=[
                    "Crear README.md con: qué es, qué no es, promesa central, limitaciones del demo.",
                    "Crear un glosario de términos permitidos/prohibidos (ej. prohibir: bet/pick/odd/ganancia).",
                    "Definir 1 deporte y 1 mercado para el demo (recomendación: Fútbol winner o MMA winner).",
                    "Definir 'Demo Mode': menor número de corridas y avisos visibles.",
                ],
                dod=DoD(checks=[
                    "README explica claramente: no predice, no recomienda apuestas, no vende picks.",
                    "Lista de términos prohibidos aplicada en UI/Docs.",
                    "Alcance cerrado: 1 deporte + 1 mercado + 1 modelo base.",
                ]),
                evidence=Evidence(required=[
                    "Commit: README.md + GLOSSARY.md (o sección equivalente).",
                    "Captura/Log: texto UI con disclaimer visible.",
                ]),
                risks=[
                    "Deriva hacia lenguaje de apuestas reduce credibilidad y aumenta riesgo de compliance."
                ],
            ),
            Task(
                id="T0.2",
                title="Scaffold del repo (backend + frontend) con contrato API",
                goal="Estructura limpia y extensible desde el día 1.",
                actions=[
                    "Crear estructura de carpetas según REPO_TREE (ajustar si ya existe repo).",
                    "Backend: configurar FastAPI minimal con /health y /version.",
                    "Frontend: configurar Vite+React minimal con Home page.",
                    "Definir contrato API inicial en backend/app/api/schemas.py (EventInput, SimulationResult).",
                ],
                dod=DoD(checks=[
                    "backend levanta en local y responde /health 200.",
                    "frontend levanta en local y muestra Home.",
                    "Contrato API definido (schemas) y versionado en /version.",
                ]),
                evidence=Evidence(required=[
                    "Logs de arranque backend y frontend.",
                    "Respuesta JSON de /health y /version.",
                ]),
            ),
        ],
    ),

    Phase(
        name="FASE 1 — Núcleo Analítico (Monte Carlo)",
        objective="Construir motor auditable: simula, entrega distribución, CI y score de riesgo.",
        tasks=[
            Task(
                id="T1.1",
                title="Modelo base + simulación Monte Carlo determinista",
                goal="Implementar engine.py y model.py con simulación reproducible por seed.",
                actions=[
                    "Implementar backend/app/core/model.py: modelo simple (ELO o win-rate ponderado).",
                    "Implementar backend/app/core/engine.py: simulate_event(event, n_sims, seed) -> dict.",
                    "Outputs mínimos: prob_A, prob_B (o prob_home/prob_away), dist (hist bins), CI (95/99).",
                    "Incluir 'seed' opcional para reproducibilidad.",
                    "Agregar dataset de ejemplo en backend/app/data/sample_events.json y sample_history.csv.",
                ],
                dod=DoD(checks=[
                    "Mismo input+seed => mismos outputs (determinismo).",
                    "n_sims configurable y validado (min, max).",
                    "CI calculado y retornado explícitamente.",
                ]),
                evidence=Evidence(required=[
                    "Test unitario: test_engine_determinism pasa.",
                    "Ejemplo de output JSON (guardado en artifacts/logs).",
                ]),
                risks=[
                    "Sin determinismo no hay QA confiable.",
                    "Sin CI, el producto se vuelve 'numerología'."
                ],
            ),
            Task(
                id="T1.2",
                title="Score de riesgo y volatilidad",
                goal="Traducir varianza/dispersión a un indicador simple: baja/media/alta + score numérico.",
                actions=[
                    "Implementar backend/app/core/risk.py: risk_score(distribution) -> {score, band, rationale}.",
                    "Bandas recomendadas: LOW/MED/HIGH según std/entropy/CI width.",
                    "Integrar risk.py al resultado del engine.",
                ],
                dod=DoD(checks=[
                    "Resultado incluye risk: score, band y rationale legible.",
                    "Tests cubren al menos 3 casos (distribución estrecha, media, amplia).",
                ]),
                evidence=Evidence(required=[
                    "Test: test_risk_bands pasa.",
                    "Ejemplos: 3 outputs comparados.",
                ]),
            ),
        ],
    ),

    Phase(
        name="FASE 2 — Interpretación & Explicabilidad",
        objective="Hacer que el resultado se entienda: resumen ejecutivo, escenarios y sensibilidad ligera.",
        tasks=[
            Task(
                id="T2.1",
                title="Generador de explicación humana",
                goal="Transformar outputs técnicos en narrativa breve, sobria y útil.",
                actions=[
                    "Implementar backend/app/core/explain.py: explain(result, context) -> {summary, scenarios, caveats}.",
                    "Generar 3 bloques: resumen (3–4 líneas), escenarios (más probable + sorpresa), caveats (limitaciones).",
                    "Prohibir lenguaje de apuestas y promesas absolutas.",
                ],
                dod=DoD(checks=[
                    "Texto generado es consistente y no usa términos prohibidos.",
                    "Incluye limitaciones y evita 'certezas'.",
                    "Devuelve estructura JSON estable (para UI).",
                ]),
                evidence=Evidence(required=[
                    "Test: test_explain_no_forbidden_terms pasa.",
                    "2 ejemplos de explicaciones (eventos distintos).",
                ]),
            ),
            Task(
                id="T2.2",
                title="Sensibilidad ligera (what-if)",
                goal="Mostrar qué variable impacta más sin volverlo un paper.",
                actions=[
                    "En model.py, identificar 1–2 features controlables (ej. forma reciente, ventaja local).",
                    "Implementar explain.py: sensitivity = top_factors + delta effect (pequeño cambio).",
                    "Retornar 'sensitivity' con impacto estimado (Δ prob).",
                ],
                dod=DoD(checks=[
                    "Sensitivity retorna lista ordenada de factores con Δprob aproximado.",
                    "No rompe determinismo (usar misma seed o método estable).",
                ]),
                evidence=Evidence(required=[
                    "Test: test_sensitivity_shape pasa.",
                    "Ejemplo: sensitivity visible en output JSON.",
                ]),
            ),
        ],
    ),

    Phase(
        name="FASE 3 — API Lista para Demo",
        objective="Exponer el motor por API con validación, límites y caching demo.",
        tasks=[
            Task(
                id="T3.1",
                title="Endpoint /simulate con validación estricta",
                goal="Crear API robusta: inputs limpios, límites claros, errores amigables.",
                actions=[
                    "Implementar backend/app/api/schemas.py con Pydantic: EventInput, SimConfig, SimResult.",
                    "Implementar backend/app/api/routes.py: POST /simulate.",
                    "Validar: n_sims (max demo), seed optional, event_id o payload completo.",
                    "Errores: devolver 4xx con mensaje claro (sin stacktrace).",
                ],
                dod=DoD(checks=[
                    "POST /simulate funciona con sample_events.json.",
                    "Inputs inválidos devuelven 422/400 con mensaje claro.",
                    "No hay leakage de stacktrace en producción.",
                ]),
                evidence=Evidence(required=[
                    "Curl/HTTPie logs: request/response para caso OK y caso error.",
                    "Test API: test_api_simulate_ok y test_api_simulate_invalid.",
                ]),
            ),
            Task(
                id="T3.2",
                title="Cache demo para performance",
                goal="Evitar recalcular lo mismo y soportar tráfico leve del demo.",
                actions=[
                    "Implementar backend/app/core/cache.py: key por (event_id, n_sims, seed, model_version).",
                    "Cache en memoria con TTL (ej. 5–15 min) para demo.",
                    "Integrar cache en /simulate.",
                ],
                dod=DoD(checks=[
                    "Segunda llamada idéntica responde más rápido y marca cache_hit=true.",
                    "TTL expira correctamente.",
                ]),
                evidence=Evidence(required=[
                    "Log comparativo de latencia (1st vs 2nd).",
                    "Test: test_cache_hit pasa.",
                ]),
                risks=[
                    "Sin cache, el demo se derrite si lo comparten."
                ],
            ),
        ],
    ),

    Phase(
        name="FASE 4 — UI Demo (usable, sobria, bonita)",
        objective="Una UI que parezca producto, no dashboard crudo.",
        tasks=[
            Task(
                id="T4.1",
                title="Home + Event Picker + Simulator",
                goal="Que el usuario llegue, elija evento, simule y vea resultados en 2 minutos.",
                actions=[
                    "Frontend: crear páginas Home, Simulator, Result.",
                    "Crear componente EventPicker (cargar lista de sample_events desde backend o stub).",
                    "Crear api client src/app/lib/api.ts (fetch /simulate).",
                    "Añadir 'Demo Mode' badge y disclaimer visible.",
                ],
                dod=DoD(checks=[
                    "Flujo completo: elegir evento → simular → ver resultado.",
                    "Loading state + manejo de errores (mensaje legible).",
                    "Disclaimer visible en Simulator/Result.",
                ]),
                evidence=Evidence(required=[
                    "Video/GIF corto del flujo completo (o capturas secuenciales).",
                    "Logs de consola sin errores.",
                ]),
            ),
            Task(
                id="T4.2",
                title="Visualización: Probabilidades + Distribución + Explicación",
                goal="Mostrar probabilidad y distribución (no solo un numerito).",
                actions=[
                    "ProbabilityCard: mostrar prob% y CI.",
                    "DistributionChart: histograma o curva simple del output.",
                    "ExplainPanel: summary + scenarios + caveats + sensitivity.",
                ],
                dod=DoD(checks=[
                    "Gráfico renderiza sin romper en mobile.",
                    "Se ve CI y risk band de forma clara.",
                    "Explicación legible y sin lenguaje prohibido.",
                ]),
                evidence=Evidence(required=[
                    "Capturas de Result page en desktop y móvil.",
                    "Snapshot de JSON mostrado (debug optional).",
                ]),
            ),
        ],
    ),

    Phase(
        name="FASE 5 — Tokens (demo) + Control de uso",
        objective="Monetización insinuada: tokens diarios + límites + telemetría mínima.",
        tasks=[
            Task(
                id="T5.1",
                title="Tokens demo (anónimo) + rate limit básico",
                goal="Probar economía sin login pesado.",
                actions=[
                    "Implementar token bucket simple: daily_tokens=5 (local storage en frontend + validación server por IP).",
                    "Backend: middleware rate limit por IP (suave).",
                    "UI: mostrar tokens restantes y costo por simulación.",
                ],
                dod=DoD(checks=[
                    "Tokens decrementan al simular.",
                    "Cuando tokens=0, UI bloquea y muestra opción: 'Vuelve mañana' (sin ads aún).",
                    "Rate limit evita spam básico.",
                ]),
                evidence=Evidence(required=[
                    "Prueba: consumir tokens hasta 0 (capturas).",
                    "Logs backend: rate limit trigger (controlado).",
                ]),
                risks=[
                    "Sin control de uso, demo puede ser abusado y caer.",
                ],
            ),
        ],
    ),

    Phase(
        name="FASE 6 — Escalabilidad (demo escalable)",
        objective="Preparar el salto: workers, separación, configuración y despliegue.",
        tasks=[
            Task(
                id="T6.1",
                title="Separación Engine/API + configuración por env",
                goal="Que el motor sea un módulo portable y el API sea una capa delgada.",
                actions=[
                    "Refactor: core/engine.py no debe importar FastAPI ni app context.",
                    "Agregar config central (env vars): MAX_SIMS_DEMO, CACHE_TTL, VERSION.",
                    "Agregar /metrics mínimo (counts, cache hits) o logging estructurado.",
                ],
                dod=DoD(checks=[
                    "Engine corre standalone (python -m app.core.engine demo).",
                    "Cambiar env var modifica límites sin tocar código.",
                ]),
                evidence=Evidence(required=[
                    "Comando standalone + output.",
                    "Prueba cambiando MAX_SIMS_DEMO.",
                ]),
            ),
            Task(
                id="T6.2",
                title="Plan de despliegue demo (1-click) + docs",
                goal="Dejar el demo desplegable con instrucciones claras.",
                actions=[
                    "Agregar docs: DEPLOY.md con Render/Fly/Railway (uno) para backend.",
                    "Frontend: build y deploy a Vercel/Netlify (uno).",
                    "CORS y endpoints configurados.",
                ],
                dod=DoD(checks=[
                    "Deploy reproducible siguiendo DEPLOY.md.",
                    "Demo online: /simulate responde y UI funciona.",
                ]),
                evidence=Evidence(required=[
                    "URL demo + /health output (si aplica).",
                    "Checklist de deploy completado.",
                ]),
            ),
        ],
    ),
]


# =========================
# Output Helpers
# =========================

def print_header(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}\n")


def render_phase(phase: Phase) -> None:
    print_header(phase.name)
    print(f"Objective: {phase.objective}\n")
    for task in phase.tasks:
        print(f"- [{task.id}] {task.title}")
        print(f"  Goal: {task.goal}")
        print("  Actions:")
        for a in task.actions:
            print(f"    - {a}")
        print("  DoD:")
        for c in task.dod.checks:
            print(f"    - {c}")
        print("  Evidence Required:")
        for e in task.evidence.required:
            print(f"    - {e}")
        if task.risks:
            print("  Risks:")
            for r in task.risks:
                print(f"    - {r}")
        if task.notes:
            print("  Notes:")
            for n in task.notes:
                print(f"    - {n}")
        print("")


def render_master_plan() -> None:
    print_header("ANTIGRAVITY EXEC ROADMAP — Proyecto Trickster (0 → Demo Escalable)")
    print("Target Stack:")
    for k, v in TARGET_STACK.items():
        print(f"  - {k}: {v}")

    print("\nProposed Repo Tree:")
    print(REPO_TREE)

    print_header("Execution Rules")
    rules = [
        "Implement tasks in order. Do NOT skip ahead.",
        "After each task: run tests, capture evidence, commit with message 'T#.#+ <title>'.",
        "No 'gambling' language in UI/Docs. Keep it educational and analytical.",
        "Keep engine deterministic with seed to enable QA and reproducibility.",
        "If a task fails DoD, stop and fix before proceeding.",
    ]
    for r in rules:
        print(f"- {r}")

    for phase in PHASES:
        render_phase(phase)

    print_header("Global QA Gate (Demo-Ready)")
    qa = [
        "No console errors in frontend.",
        "Backend has no stacktrace leakage; errors are structured JSON.",
        "Deterministic simulation verified by unit tests.",
        "Result page shows: probabilities, CI, distribution chart, risk band, explanation, sensitivity.",
        "Tokens/limits prevent abuse (basic).",
        "Deploy docs exist and are reproducible.",
    ]
    for q in qa:
        print(f"- {q}")

    print_header("Stop Conditions (Do NOT proceed if...)")
    stops = [
        "Engine outputs vary for same input+seed.",
        "UI includes betting/picks language.",
        "API allows unbounded n_sims (risk of meltdown).",
        "No evidence captured for a completed task.",
    ]
    for s in stops:
        print(f"- {s}")

    print("\nEND OF PLAN\n")


# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    render_master_plan()
