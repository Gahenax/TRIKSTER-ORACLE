# 🚀 EJECUTAR JULES — Instrucciones Completas

**Objetivo**: Asignar FASE 1 (Motor Monte Carlo + Risk Assessment) a Google Jules

---

## ✅ PASO 1: Abrir GitHub Issues

**Acción**: Abre tu navegador y ve a:

```
https://github.com/Gahenax/TRIKSTER-ORACLE/issues/new
```

**O alternativamente**:
1. Ve a https://github.com/Gahenax/TRIKSTER-ORACLE
2. Click en la pestaña "Issues"
3. Click en el botón verde "New issue"

---

## ✅ PASO 2: Rellenar el Formulario del Issue

### **Campo: Title** (Título)
Copia exactamente esto:

```
Implement Monte Carlo Engine & Risk Assessment (Phase 1)
```

### **Campo: Comment** (Descripción)
Copia TODO lo siguiente (incluye el @google-jules al inicio):

```markdown
@google-jules 

Please implement **Phase 1** of the Trickster Oracle project according to the detailed specifications in `TASKS_FOR_JULES.md`.

---

## 📋 Context

This is an **educational probabilistic analytics platform** for sports events. The project uses Monte Carlo simulations, confidence intervals, and risk assessment to teach probability concepts.

**Key Documentation**:
- `TASKS_FOR_JULES.md` - Detailed task specifications (YOUR PRIMARY REFERENCE)
- `ROADMAP.py` - Complete project roadmap with 6 phases
- `README.md` - Project identity and scope
- `GLOSSARY.md` - **CRITICAL**: Anti-gambling terminology rules (forbidden/permitted terms)
- `backend/app/api/schemas.py` - Pydantic schemas (already defined)
- `backend/app/core/explain.py` - Explainability module (already implemented)

---

## 🎯 Your Mission: Phase 1 — Core Analytics Engine

### **Task T1.1: Monte Carlo Simulation Engine**

#### **File: `backend/app/core/model.py`**
Implement the ELO-based probability model:

```python
def calculate_win_probability(
    home_rating: float,
    away_rating: float,
    home_advantage: float = 100
) -> tuple[float, float, float]:
    """
    Calculate win probabilities using ELO formula.
    
    Returns:
        (prob_home, prob_draw, prob_away) - All probabilities sum to 1.0
    """
```

**Requirements**:
- Use standard ELO formula: Expected = 1 / (1 + 10^((Rating_B - Rating_A) / 400))
- Include home advantage in calculation
- Support draw probability (use 3-way split)
- Must be deterministic (no randomness here)

---

#### **File: `backend/app/core/engine.py`**
Implement the Monte Carlo simulation engine:

```python
def simulate_event(
    event: EventInput,
    config: SimulationConfig
) -> dict:
    """
    Run Monte Carlo simulation for a sports event.
    
    CRITICAL: Must be DETERMINISTIC.
    Same input + same seed → EXACT same output.
    
    Returns dict with:
    - prob_home, prob_draw, prob_away
    - distribution: {"bins": [...], "frequencies": [...]}
    - confidence_intervals: {"95": {"lower": ..., "upper": ...}, "99": {...}}
    - execution_time_ms
    """
```

**Requirements**:
- **DETERMINISTIC**: Use `numpy.random.seed(config.seed)` if seed provided
- Run `config.n_simulations` iterations (100-1000 range)
- Calculate 95% and 99% confidence intervals
- Return probability distribution (bins + frequencies)
- Measure execution time in milliseconds
- **NO forbidden gambling terms** in docstrings/comments (see GLOSSARY.md)

---

### **Task T1.2: Risk Assessment Module**

#### **File: `backend/app/core/risk.py`**
Implement risk scoring and banding:

```python
def assess_risk(
    probabilities: dict[str, float],
    distribution_data: dict,
    confidence_intervals: dict
) -> RiskInfo:
    """
    Calculate risk score (0-100) and band (LOW/MEDIUM/HIGH).
    
    Returns RiskInfo with:
    - score: float (0-100)
    - band: str ("LOW" | "MEDIUM" | "HIGH")
    - rationale: str (human-readable explanation)
    """
```

**Risk Calculation Logic**:
1. **Variance/Spread**: Higher variance = higher risk
2. **CI Width**: Wider confidence intervals = higher risk
3. **Entropy**: More balanced probabilities = higher risk
4. **Combined Score**: Weighted average → 0-100 scale

**Risk Bands**:
- `LOW`: score < 33
- `MEDIUM`: 33 ≤ score < 67
- `HIGH`: score ≥ 67

**Rationale Requirements**:
- Must be 1-2 sentences
- **MUST NOT use forbidden terms** from GLOSSARY.md
- Use permitted terms: "estimate", "uncertainty", "variance", "statistical", etc.
- Example: "Moderate uncertainty based on rating differential and simulation variance"

---

### **Task T1.3: Sample Data**

#### **File: `backend/app/data/sample_events.json`**
Create at least 3 sample events:

```json
[
  {
    "event_id": "demo_001",
    "home_team": "Barcelona",
    "away_team": "Real Madrid",
    "home_rating": 2100,
    "away_rating": 2050,
    "home_advantage": 100,
    "sport": "football"
  },
  {
    "event_id": "demo_002",
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "home_rating": 2150,
    "away_rating": 2080,
    "home_advantage": 100,
    "sport": "football"
  },
  {
    "event_id": "demo_003",
    "home_team": "Bayern Munich",
    "away_team": "Borussia Dortmund",
    "home_rating": 2120,
    "away_rating": 1950,
    "home_advantage": 100,
    "sport": "football"
  }
]
```

---

## 🧪 Testing Requirements

### **File: `backend/app/tests/test_engine.py`**

**CRITICAL TESTS** (these MUST pass):

1. **`test_engine_determinism()`**
   ```python
   # Same seed → exact same results (bit-for-bit identical)
   result1 = simulate_event(event, SimulationConfig(n_simulations=1000, seed=42))
   result2 = simulate_event(event, SimulationConfig(n_simulations=1000, seed=42))
   assert result1 == result2
   ```

2. **`test_probabilities_sum_to_one()`**
   ```python
   # prob_home + prob_draw + prob_away ≈ 1.0 (within floating-point tolerance)
   ```

3. **`test_confidence_intervals()`**
   ```python
   # CI ranges are valid: 0 ≤ lower < upper ≤ 1
   # 99% CI should be wider than 95% CI
   ```

4. **`test_execution_time_reasonable()`**
   ```python
   # 1000 simulations should complete in < 5 seconds
   ```

---

### **File: `backend/app/tests/test_risk.py`**

**REQUIRED TESTS**:

1. **`test_risk_bands()`**
   ```python
   # Verify score < 33 → LOW, 33-67 → MEDIUM, ≥67 → HIGH
   ```

2. **`test_risk_rationale_no_forbidden_terms()`**
   ```python
   # Scan rationale for forbidden terms from GLOSSARY.md
   # Example forbidden: "bet", "pick", "guaranteed", "sure thing"
   ```

3. **`test_balanced_probabilities_higher_risk()`**
   ```python
   # [0.33, 0.33, 0.34] should have higher risk than [0.8, 0.1, 0.1]
   ```

---

## ✅ Definition of Done (DoD)

**Before creating the PR, ensure**:

- [ ] All files created in correct locations
- [ ] All functions have type hints
- [ ] All functions have comprehensive docstrings
- [ ] **Determinism test passes** (critical!)
- [ ] All tests in `test_engine.py` pass
- [ ] All tests in `test_risk.py` pass
- [ ] No forbidden gambling terms in any code/comments/docstrings
- [ ] Code follows Python best practices (PEP 8)
- [ ] No external API calls or network dependencies
- [ ] Execution time for 1000 sims < 5 seconds

---

## 📝 Deliverables Summary

1. `backend/app/core/model.py` - ELO probability calculations
2. `backend/app/core/engine.py` - Monte Carlo simulation (deterministic)
3. `backend/app/core/risk.py` - Risk scoring and banding
4. `backend/app/data/sample_events.json` - Sample event data
5. `backend/app/tests/test_engine.py` - Engine tests (especially determinism)
6. `backend/app/tests/test_risk.py` - Risk assessment tests

---

## 🚀 How to Proceed

1. **Create a feature branch**: `feature/phase1-monte-carlo-engine`
2. **Implement all files** according to specifications above
3. **Run all tests** and ensure they pass
4. **Create a Pull Request** with:
   - Title: `Phase 1: Monte Carlo Engine & Risk Assessment`
   - Description: Summary of implementation + test results
5. **Request review** from repository maintainer

---

## ⚠️ CRITICAL CONSTRAINTS

### **1. Anti-Gambling Policy** (NON-NEGOTIABLE)
- **NEVER** use terms: bet, pick, odds, guaranteed, profit, bankroll, stake, wager
- **ALWAYS** use terms: estimate, probability, statistical, uncertainty, analysis
- Check `GLOSSARY.md` for complete list

### **2. Determinism** (NON-NEGOTIABLE)
- Same `seed` parameter → exact same results (every time)
- Use `numpy.random.seed()` at start of simulation
- No system time, no external randomness sources

### **3. Performance**
- 1000 simulations must complete in < 5 seconds
- Use NumPy vectorization (not Python loops)

### **4. No External Dependencies**
- Do NOT add new pip packages beyond what's in `pyproject.toml`
- Use: NumPy, FastAPI, Pydantic (already installed)
- Do NOT call external APIs or databases

---

## 📚 Reference Files (Already in Repo)

You can read these for context:

- `GLOSSARY.md` - **READ THIS FIRST** for terminology rules
- `backend/app/api/schemas.py` - Pydantic models (EventInput, SimulationConfig, RiskInfo)
- `backend/app/core/explain.py` - Example of compliant, educational code
- `backend/pyproject.toml` - Available dependencies

---

## 🎯 Expected Outcome

After you complete this:
- The backend will have a working Monte Carlo simulation engine
- Risk assessment will quantify uncertainty
- All tests will pass
- The next phase (API integration) can proceed

---

**Thank you, Jules! Please create the feature branch and start implementing. Ask questions if any specification is unclear.**
```

---

## ✅ PASO 3: Añadir Labels (Opcional pero Recomendado)

Si ves la sección "Labels" en el lateral derecho, añade:
- `enhancement`
- `jules` (si existe)
- `phase-1` (si existe)

Si no hay labels disponibles, no te preocupes, no es crítico.

---

## ✅ PASO 4: Submit Issue

Click en el botón verde **"Submit new issue"**

---

## 🎯 ¿Qué Pasará Después?

1. **Inmediatamente**: Jules recibirá la notificación del `@google-jules` mention
2. **Dentro de minutos/horas**: Jules analizará el issue y las especificaciones
3. **Dentro de 1-4 horas**: Jules creará un branch `feature/phase1-monte-carlo-engine`
4. **Dentro de 2-6 horas**: Jules abrirá un Pull Request con el código implementado
5. **Tu acción**: Revisar el PR, aprobar si cumple el DoD, y hacer merge

---

## 📊 Cómo Monitorear el Progreso

### **Opción 1: GitHub Web (Recomendado)**
Ve a: https://github.com/Gahenax/TRIKSTER-ORACLE

- Pestaña **"Issues"** - Verás el issue que creaste
- Pestaña **"Pull Requests"** - Jules creará un PR aquí cuando termine
- Pestaña **"Code" → Branches"** - Verás el branch `feature/phase1-monte-carlo-engine` cuando Jules lo cree

### **Opción 2: Git Local**
Desde tu terminal:

```bash
cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE

# Actualizar info del remoto
git fetch origin

# Ver todos los branches (incluirá el de Jules cuando lo cree)
git branch -r

# Ver commits nuevos
git log origin/master --oneline -10
```

---

## ⚠️ Troubleshooting

### **Si Jules no responde en 24 horas**:
1. Verifica que escribiste `@google-jules` exactamente (con la @)
2. Asegúrate de que el repositorio es público
3. Revisa que el issue esté abierto (no cerrado accidentalmente)
4. Intenta crear un comment en el issue: `@google-jules ping`

### **Si Jules pide aclaraciones**:
Responde en el issue con la información solicitada. Jules puede hacer preguntas si algo no está claro.

### **Si quieres cancelar/modificar**:
- Puedes editar el issue en cualquier momento
- Puedes cerrar el issue si decides no continuar
- Jules entenderá updates en los comments del issue

---

## 🎉 Próximos Pasos Después de Jules

Una vez que Jules complete FASE 1:

1. **Revisar el PR de Jules**
2. **Ejecutar tests**: `cd backend && pytest`
3. **Mergear el PR** a master
4. **Continuar con FASE 3**: Implementar API endpoints + caching
5. **Integrar frontend con backend**: Probar simulaciones end-to-end
6. **Completar T4.2**: Añadir Chart.js para visualizaciones

---

## 📝 Notas Importantes

- **Jules trabaja de forma asíncrona** - No esperes respuesta instantánea
- **Jules es autónomo** - Clonará el repo, escribirá código, ejecutará tests, y creará PR automáticamente
- **Jules usa Google Cloud VMs** - Todo sucede en máquinas virtuales seguras
- **Puedes interactuar con Jules** - Responde a comments en issues/PRs

---

**¿Listo? Copia el texto del PASO 2 y créalo en GitHub ahora! 🚀**
