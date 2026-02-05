# TRICKSTER-ORACLE

**Plataforma de Análisis Probabilístico para Eventos Deportivos**

---

## 🎯 ¿Qué es TRICKSTER-ORACLE?

TRICKSTER-ORACLE es una **herramienta educativa y analítica** diseñada para:
- Analizar escenarios probabilísticos en eventos deportivos usando simulaciones Monte Carlo
- Visualizar distribuciones de probabilidad, intervalos de confianza y análisis de riesgo
- Explorar sensibilidad de variables y factores que impactan los resultados
- Proporcionar explicaciones interpretables de modelos estadísticos

Este proyecto es una **demostración técnica** de métodos cuantitativos aplicados al análisis deportivo.

---

## ❌ ¿Qué NO es TRICKSTER-ORACLE?

TRICKSTER-ORACLE **NO**:
- ❌ Predice resultados con certeza
- ❌ Recomienda apuestas ni "picks ganadores"
- ❌ Vende pronósticos ni servicios de gambling
- ❌ Garantiza ganancias ni retornos financieros
- ❌ Es una herramienta de inversión

**IMPORTANTE**: Este sistema genera **estimaciones probabilísticas** basadas en modelos estadísticos con limitaciones inherentes. Los resultados deben interpretarse como **análisis educativos**, no como predicciones absolutas.

---

## 🧠 Promesa Central

TRICKSTER-ORACLE te permite:

1. **Explorar escenarios**: Simula miles de posibles resultados para entender la distribución de probabilidades
2. **Cuantificar incertidumbre**: Visualiza intervalos de confianza y bandas de riesgo
3. **Entender factores**: Analiza qué variables impactan más en las probabilidades
4. **Aprender probabilística**: Comprende conceptos como varianza, CI, distribución, sesgo

Este es un **laboratorio educativo**, no una bola de cristal.

---

## 📊 Demo Scope (Versión 1.0)

### Alcance Inicial
- **Deporte**: Fútbol (Soccer)
- **Mercado**: Match Winner (Home/Draw/Away)
- **Modelo**: ELO Rating System simplificado
- **Simulaciones**: Máximo 1,000 corridas en modo demo
- **Datos**: Eventos históricos de muestra (no datos en vivo)

### Limitaciones del Demo
- ⚠️ Dataset limitado (histórico estático)
- ⚠️ Modelo básico (no considera lesiones, clima, motivación, etc.)
- ⚠️ Sin integración en tiempo real
- ⚠️ Sin tracking de precisión histórica del modelo
- ⚠️ Máximo 5 simulaciones diarias (demo gratuito)

---

## 🏗️ Arquitectura Técnica

```
Backend:  Python 3.11+ | FastAPI | NumPy
Engine:   Monte Carlo Simulation (deterministic with seed)
Frontend: Vite + React + TypeScript
Charts:   Chart.js / Recharts
Cache:    In-memory (demo) → Redis (producción)
```

### Componentes Clave
1. **Core Engine** (`backend/app/core/engine.py`): Motor de simulación Monte Carlo
2. **Risk Module** (`backend/app/core/risk.py`): Cálculo de volatilidad y bandas de riesgo
3. **Explainer** (`backend/app/core/explain.py`): Generación de narrativas interpretables
4. **API** (`backend/app/api/routes.py`): Endpoints REST con validación estricta
5. **UI** (`frontend/src/`): Interfaz responsiva con visualizaciones interactivas

---

## 🚀 Roadmap

Ver [ROADMAP.py](./ROADMAP.py) para el plan de ejecución completo por fases.

**Fases**:
- ✅ **FASE 0**: Fundaciones (identidad, alcance, scaffolding)
- ⏳ **FASE 1**: Núcleo Analítico (Monte Carlo + Risk)
- ⏳ **FASE 2**: Interpretación & Explicabilidad
- ⏳ **FASE 3**: API lista para demo
- ⏳ **FASE 4**: UI Demo
- ⏳ **FASE 5**: Tokens + Control de uso
- ⏳ **FASE 6**: Escalabilidad

---

## 📖 Glosario & Terminología

Ver [GLOSSARY.md](./GLOSSARY.md) para la lista completa de términos permitidos y prohibidos.

**Principio**: Usamos lenguaje **analítico y educativo**, no lenguaje de apuestas.

---

## ⚖️ Disclaimer Legal

Este software se proporciona "tal cual" sin garantías de ningún tipo. El uso de TRICKSTER-ORACLE es bajo tu propio riesgo. Los creadores no se responsabilizan por:
- Pérdidas financieras derivadas del uso de este sistema
- Decisiones tomadas basándose en los análisis generados
- Exactitud de las probabilidades calculadas

**Si decides usar información de este sistema para apuestas, hazlo bajo tu total responsabilidad y cumpliendo las leyes de tu jurisdicción.**

---

## 📝 Licencia

MIT License - Ver [LICENSE](./LICENSE) para más detalles.

---

## 🙏 Contribuciones

Este es un proyecto educativo. Las contribuciones son bienvenidas siguiendo las [guías de contribución](./CONTRIBUTING.md).

---

**Versión**: 0.1.0-alpha (Demo)  
**Última actualización**: Febrero 2026  
**Mantenido por**: [Gahenax](https://github.com/Gahenax)
