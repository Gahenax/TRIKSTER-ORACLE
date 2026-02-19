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

## 📊 Demo Scope (Versión 0.2.0-beta)

### Alcance
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
- ⚠️ Límite diario de simulaciones (demo gratuito)

---

## 🏗️ Arquitectura Técnica (Versión 0.3.0 - Grado Auditoría)

El sistema utiliza una **Arquitectura Dual** para garantizar la máxima integridad del motor matemático mientras permite una visualización web segura y monetizada.

### 1. Núcleo de Ejecución (Offline/Backend)
- **Engine**: Simulación Monte Carlo determinista (SHA-256 signatures).
- **Ledger L0**: Sistema *fail-closed* que registra cada simulación en un ledger inmutable antes de la ejecución.
- **Vocabulary Guard**: Escáner automático que bloquea exportaciones con lenguaje de apuestas.
- **Export Packs**: Generación de paquetes firmados (`report.json` + `manifest.json`) para verificación cruzada.

### 2. Web Companion Viewer (Cloud/Service)
- **FastAPI + Jinja2**: Visor de solo lectura diseñado para la interacción del usuario final.
- **Hardening G0**: 
  - **Rate Limiting**: 5 RPS / 20 Burst (Token Bucket).
  - **Traceability**: X-Request-ID propagation y Access Logs estructurados (JSON).
  - **Security**: CSP, HSTS ready, y firmas de integridad SHA-256 obligatorias.
- **Monetización**: Integración nativa con AdSense (Publisher: `ca-pub-8537336585034121`).

---

## 🚀 Despliegue de Producción

Para desplegar el visor en un entorno de producción (Docker), utiliza el pack de despliegue generado:

1. **Instalar Dependencias**: `pip install -e viewer[dev]`
2. **Configurar**: `cp deploy/PROD_ENV.template deploy/.env` (Edita las claves API y rutas).
3. **Ejecutar**: `python antigravity_execute_production.py`

El script realizará un despliegue automático con verificación de "Go-Live Gate".

---

## 📖 Glosario & Terminología

Ver [GLOSSARY.md](./GLOSSARY.md) para la lista completa de términos permitidos y prohibidos.
**Principio**: Usamos lenguaje **analítico y educativo**, no lenguaje de apuestas. Toda la data web es **determinista y auditable**.

---

## ⚖️ Disclaimer Legal

Este software se proporciona "tal cual" sin garantías de ningún tipo. El uso de TRICKSTER-ORACLE es bajo tu propio riesgo.

---

**Versión**: 0.3.0-stable (Production Ready)  
**Última actualización**: 11 Febrero 2026  
**Mantenido por**: [Gahenax](https://github.com/Gahenax)
