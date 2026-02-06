# 🚀 Quick Start Guide — Trickster Oracle

Este script te permite iniciar el backend y frontend rápidamente.

---

## 📦 Instalación (Primera Vez)

### **Backend**:
```bash
cd backend
pip install fastapi uvicorn numpy pydantic pytest httpx
```

### **Frontend** (Opcional — para desarrollo local):
```bash
cd frontend
npm install
```

---

## ▶️ Iniciar Aplicación

### **Opción 1: Solo Backend API** (Recomendado para testing)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Acceder a**:
- API Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### **Opción 2: Backend + Frontend**

**Terminal 1 — Backend**:
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend**:
```bash
cd frontend
npm run dev
```

**Acceder a**:
- Frontend UI: http://localhost:5173
- Backend API: http://localhost:8000

---

## 🧪 Testing Rápido

### **1. Test del Endpoint desde Browser**

Abre: http://localhost:8000/docs

Click en `/api/v1/simulate` → **Try it out**

Usa este JSON:
```json
{
  "event": {
    "home_team": "Barcelona",
    "away_team": "Real Madrid",
    "home_rating": 2100,
    "away_rating": 2050,
    "home_advantage": 100,
    "sport": "football"
  },
  "config": {
    "n_simulations": 1000,
    "seed": 42
  }
}
```

Click **Execute** → Verás resultados JSON completos

### **2. Test con curl**

```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "home_team": "Team A",
      "away_team": "Team B",
      "home_rating": 1500,
      "away_rating": 1500
    }
  }'
```

### **3. Ejecutar Tests Automatizados**

```bash
cd backend
pytest app/tests/ -v
```

---

## 📊 Demo Script

```bash
cd backend
python demo.py
```

Muestra:
- Output JSON de ejemplo
- Performance metrics (100, 1000, 10000 sims)

---

## 🛠️ Troubleshooting

### **Error: ModuleNotFoundError: No module named 'numpy'**

```bash
pip install numpy
```

### **Error: ModuleNotFoundError: No module named 'fastapi'**

```bash
pip install fastapi uvicorn pydantic
```

### **Error: Port 8000 already in use**

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Use otro puerto
uvicorn app.main:app --port 8001
```

### **Frontend no conecta con Backend**

Verifica que:
1. Backend esté corriendo en puerto 8000
2. `VITE_API_URL` en frontend/.env.local = `http://localhost:8000/api`
3. CORS está habilitado (ya está en main.py)

---

## 📝 Estructura de Directorios

```
TRICKSTER-ORACLE/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py       ← /simulate endpoint
│   │   │   └── schemas.py      ← Request/response models
│   │   ├── core/
│   │   │   ├── engine.py       ← Monte Carlo
│   │   │   ├── risk.py         ← Risk assessment
│   │   │   └── explain.py      ← Explainability
│   │   ├── tests/
│   │   │   ├── test_api.py     ← API tests
│   │   │   ├── test_engine.py  ← Engine tests
│   │   │   └── test_risk.py    ← Risk tests
│   │   └── main.py             ← FastAPI app
│   └── demo.py                 ← Demo script
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── lib/api.ts      ← API client
    │   │   └── pages/
    │   │       ├── Home.tsx
    │   │       ├── Simulator.tsx
    │   │       └── Result.tsx
    │   └── index.css           ← Design system
    └── vite.config.ts          ← Vite config (proxy /api)
```

---

## ✅ Verificar Estado

### **Backend Healthy**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"trickster-oracle-api","version":"0.1.0"}
```

### **API Funcional**:
```bash
curl http://localhost:8000/docs
# Expected: HTML de Swagger UI
```

### **Cache Funcional**:
```bash
curl http://localhost:8000/api/v1/cache/stats
# Expected: {"total_entries":0,"active_entries":0,...}
```

---

## 🎯 Próximos Pasos

1. ✅ Backend API funcionando
2. ✅ Frontend puede consumir API
3. ⏳ Integrar Chart.js para gráficos
4. ⏳ Implementar sistema de tokens (FASE 5)
5. ⏳ Deploy a producción (FASE 6)

---

**¡El stack está completo y listo para desarrollo!** 🎉
