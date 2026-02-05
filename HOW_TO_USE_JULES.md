# Cómo Asignar Tareas a Google Jules

## Opción 1: GitHub Issues (Recomendado)

1. Ve a: https://github.com/Gahenax/TRIKSTER-ORACLE/issues/new

2. **Título del Issue**:
   ```
   [JULES] Implement Monte Carlo Engine & Risk Assessment (FASE 1)
   ```

3. **Descripción del Issue**:
   ```markdown
   @jules-agent Please implement the Monte Carlo simulation engine and risk assessment module for FASE 1.
   
   ## Tasks
   See detailed specifications in: [TASKS_FOR_JULES.md](https://github.com/Gahenax/TRIKSTER-ORACLE/blob/master/TASKS_FOR_JULES.md)
   
   ## Summary
   - Implement `backend/app/core/model.py` (ELO probability model)
   - Implement `backend/app/core/engine.py` (Monte Carlo simulation)
   - Implement `backend/app/core/risk.py` (Risk scoring)
   - Create `backend/app/data/sample_events.json`
   - Write comprehensive unit tests (determinism, validation, risk bands)
   
   ## Critical Requirements
   - ✅ Deterministic with seed (same input → same output)
   - ✅ No gambling terminology (check GLOSSARY.md)
   - ✅ All tests must pass
   - ✅ Type hints and docstrings
   
   ## Branch
   Create PR from: `feature/phase1-monte-carlo-engine` to `master`
   
   ## Definition of Done
   - [ ] All pytest tests pass
   - [ ] `test_engine_determinism` verifies reproducibility
   - [ ] Risk rationale uses only permitted terms
   - [ ] Code formatted with black
   - [ ] Example output included in PR
   ```

4. **Labels**: Add `enhancement`, `jules-task`, `phase-1`

5. **Submit** y Jules comenzará a trabajar automáticamente

---

## Opción 2: Direct Mention (Alternativo)

Si tienes acceso a Jules via web:

1. Ve a: https://jules.ai/ (o Google Labs)
2. Menciona el repositorio: `@jules work on https://github.com/Gahenax/TRIKSTER-ORACLE`
3. Copia el contenido de `TASKS_FOR_JULES.md` en el prompt

---

## Opción 3: GitHub PR Comment (Si Jules ya está conectado)

Si Jules ya está configurado en el repo:

1. Crea un Draft PR vacío
2. Comenta: `@jules-agent Please see TASKS_FOR_JULES.md for implementation details`
3. Jules leerá las instrucciones y empezará a trabajar

---

## ⏱️ Tiempo Estimado de Jules

- **Lectura del contexto**: ~5 min
- **Implementación**: ~2-3 horas
- **Tests**: ~1 hora
- **PR Creation**: ~10 min

**Total**: Jules debería tener un PR listo en 3-4 horas

---

## 🔔 Notificaciones

Recibirás notificaciones de GitHub cuando:
- Jules cree la rama `feature/phase1-monte-carlo-engine`
- Jules haga commits
- Jules abra el Pull Request
- Jules solicite review o encuentre blockers

---

## ❓ Si Jules Pregunta

Jules puede hacer preguntas en el issue si encuentra ambigüedades. Respuestas típicas:

**Q**: "Should I use numpy or pure Python for simulations?"  
**A**: "Use numpy for performance. It's already in dependencies."

**Q**: "What draw probability should I use for equal-rated teams?"  
**A**: "Use ~25% for equal teams, scale based on rating difference."

**Q**: "Should I implement caching in this phase?"  
**A**: "No, caching is FASE 3 (T3.2). Focus only on engine + tests."

---

## 📊 Mientras Jules Trabaja

Yo puedo continuar con:
- **FASE 4**: Empezar el frontend (Vite + React setup)
- **FASE 2**: Preparar el módulo de explicabilidad (`explain.py`)
- **Documentación**: CONTRIBUTING.md, DEPLOY.md

¿Quieres que avance con algo específico mientras Jules trabaja en FASE 1?
