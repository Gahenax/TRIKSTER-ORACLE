# GLOSSARY — Terminología TRICKSTER-ORACLE

**Principio**: Este proyecto usa lenguaje **analítico, educativo y científico**. Evitamos terminología de gambling para mantener credibilidad y compliance.

---

## ✅ Términos PERMITIDOS (Usar siempre)

### Análisis y Métodos
- **Probabilidad** / Probability
- **Distribución** / Distribution
- **Simulación** / Simulation
- **Escenario** / Scenario
- **Modelo** / Model
- **Análisis** / Analysis
- **Estimación** / Estimate
- **Inferencia** / Inference
- **Incertidumbre** / Uncertainty
- **Varianza** / Variance
- **Desviación estándar** / Standard Deviation
- **Intervalo de confianza (CI)** / Confidence Interval
- **Monte Carlo**
- **Riesgo** / Risk
- **Volatilidad** / Volatility
- **Sensibilidad** / Sensitivity
- **Factor** / Factor
- **Variable** / Variable
- **Métrica** / Metric

### Resultados y Outputs
- **Resultado estimado** / Estimated outcome
- **Resultado más probable** / Most likely outcome
- **Resultado esperado** / Expected outcome
- **Rango de resultados** / Outcome range
- **Escenario probable** / Likely scenario
- **Escenario sorpresa** / Surprise scenario
- **Banda de confianza** / Confidence band
- **Score de riesgo** / Risk score
- **Nivel de certeza** / Certainty level (siempre con caveats)

### Eventos y Dominio
- **Evento** / Event
- **Partido** / Match
- **Competidor** / Competitor
- **Equipo** / Team
- **Desempeño** / Performance
- **Forma reciente** / Recent form
- **Historial** / History
- **Estadística** / Statistic
- **Rating** (ELO, Glicko, etc.)

### UI y Experiencia
- **Explorar** / Explore
- **Analizar** / Analyze
- **Simular** / Simulate
- **Comparar** / Compare
- **Visualizar** / Visualize
- **Interpretar** / Interpret
- **Entender** / Understand

---

## ❌ Términos PROHIBIDOS (Nunca usar)

### Lenguaje de Apuestas
- ❌ **Bet** / Apuesta
- ❌ **Pick** / Pronóstico ganador
- ❌ **Odd** / Cuota (usar "probabilidad" en su lugar)
- ❌ **Line** / Línea de apuesta
- ❌ **Spread** / Hándicap
- ❌ **Parlays** / Combinadas
- ❌ **Bookmaker** / Casa de apuestas
- ❌ **Stake** / Inversión
- ❌ **Bankroll** / Fondos de apuesta
- ❌ **Units** / Unidades de apuesta
- ❌ **Sharp** / Apostador profesional
- ❌ **Lock** / Apuesta segura
- ❌ **Sure bet** / Apuesta garantizada
- ❌ **Arbitrage** (en contexto de apuestas)
- ❌ **Tipster** / Pronosticador

### Lenguaje de Certeza Absoluta
- ❌ **Garantizado** / Guaranteed
- ❌ **Seguro** / Sure thing
- ❌ **Certeza** / Certainty (sin caveats)
- ❌ **Infalible** / Foolproof
- ❌ **Predicción exacta** / Exact prediction
- ❌ **Va a ganar** / Will win
- ❌ **No puede perder** / Can't lose

### Lenguaje Financiero Engañoso
- ❌ **Ganancia** / Profit
- ❌ **Retorno de inversión (ROI)** (en contexto de apuestas)
- ❌ **Rentabilidad** / Profitability (en contexto de apuestas)
- ❌ **Ganar dinero** / Make money
- ❌ **Inversión segura** / Safe investment

---

## 🔄 Sustituciones Recomendadas

| ❌ NO usar | ✅ Usar en su lugar |
|-----------|-------------------|
| Odd de 2.5 | Probabilidad de 40% |
| Este pick es seguro | Este escenario tiene alta probabilidad (CI: 80-90%) |
| Vas a ganar | El resultado estimado favorece a... |
| Apuesta por X | Analiza el escenario donde X gana |
| Ganancia esperada | Valor esperado (EV) del escenario |
| Lock / Sure thing | Alta confianza (con riesgo bajo) |
| Bankroll management | Gestión de límites de uso |

---

## ✍️ Ejemplos de Copy Correcto

### ✅ CORRECTO
> "El modelo estima una probabilidad de 65% (CI: 58-72%) para que el Equipo A gane. El análisis de sensibilidad muestra que la forma reciente es el factor más influyente (+12% de impacto). **Importante**: Esta es una estimación basada en datos históricos limitados, no una predicción garantizada."

### ❌ INCORRECTO
> "Este pick tiene odd de 1.5, es un lock seguro. Apuesta todo tu bankroll en el Equipo A, vas a ganar 100%."

---

## 🎯 Filosofía de Comunicación

1. **Siempre incluir caveats**: Nunca presentar resultados sin mencionar limitaciones
2. **Usar rangos, no puntos**: Probabilidades con CI, no números exactos
3. **Explicar el método**: Dejar claro que es Monte Carlo, no magia
4. **Enfatizar educación**: "Aprende cómo funciona la probabilidad"
5. **Evitar imperatives**: No "Apuesta X", sino "Explora el escenario X"

---

## 📚 Referencias y Justificación

Este glosario está diseñado para:
- ✅ Cumplir con estándares de comunicación científica
- ✅ Evitar problemas legales relacionados con promoción de gambling
- ✅ Mantener credibilidad académica y profesional
- ✅ Diferenciar el producto de "servicios de picks"
- ✅ Proteger al usuario de expectativas irreales

---

**Versión**: 1.0  
**Última actualización**: Febrero 2026  
**Enforcement**: Este glosario se aplica a:
- UI (todos los textos visibles)
- Documentación (README, CONTRIBUTING, etc.)
- API Responses (campos `explanation`, `summary`, etc.)
- Marketing Materials (si aplica)
- Código (nombres de variables cuando sean user-facing)
