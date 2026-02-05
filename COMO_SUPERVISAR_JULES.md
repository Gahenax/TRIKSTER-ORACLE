# 👀 Cómo Supervisar a Jules Mientras Ves Tu Serie

## ⚠️ **IMPORTANTE: Primero Debes Activar a Jules**

Jules **NO** comenzará automáticamente. Necesitas:

1. Ir a: https://github.com/Gahenax/TRIKSTER-ORACLE/issues/new
2. Copiar el texto de `EJECUTAR_JULES.md` (PASO 2)
3. Crear el issue

**Sin esto, Jules NO trabajará.**

---

## 🎯 **Método Recomendado: Script Automático**

### **Opción 1: Script Completo con Interfaz**

Ejecuta esto cada 15-30 minutos (abre PowerShell):

```powershell
cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE
.\monitor_jules.ps1
```

**Qué hace**:
- ✅ Actualiza info del repositorio
- ✅ Verifica si Jules creó un branch
- ✅ Muestra commits de Jules
- ✅ Te dice si hay que revisar PRs
- ✅ Interfaz bonita con colores

---

### **Opción 2: Check Rápido (Una Línea)**

Desde PowerShell, ejecuta:

```powershell
.\quick_check.ps1
```

O directamente:

```powershell
cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE; git fetch origin; $branch = git branch -r | Select-String "feature/phase1"; if ($branch) { Write-Host "`n✅ JULES TRABAJANDO!`n" -ForegroundColor Green } else { Write-Host "`n⏳ Jules NO ha comenzado`n" -ForegroundColor Yellow }
```

---

### **Opción 3: Comando Git Manual**

```bash
cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE
git fetch origin
git branch -r
```

**Busca** una línea que diga:
```
origin/feature/phase1-monte-carlo-engine
```

Si la ves → **Jules está trabajando!** 🎉

---

## 📊 **Qué Esperar (Timeline)**

| Tiempo desde crear issue | Estado Esperado |
|---------------------------|-----------------|
| **0-30 min** | Jules recibe notificación, no verás cambios |
| **30-90 min** | Jules analiza specs, puede crear branch |
| **1-3 horas** | Branch creado: `feature/phase1-monte-carlo-engine` |
| **2-4 horas** | Jules hace commits al branch |
| **3-6 horas** | **PR abierto** (¡aquí debes revisarlo!) |

---

## 🔔 **Cómo Saber Cuando Jules Terminó**

### **1. Verás el Branch**
```powershell
.\monitor_jules.ps1
```

Output:
```
✅ ¡JULES HA CREADO UN BRANCH!
   Branch: origin/feature/phase1-monte-carlo-engine
```

### **2. Verás Commits**
```
[3/4] Commits de Jules:
abc1234 Add Monte Carlo engine implementation
def5678 Add risk assessment module
ghi9012 Add comprehensive tests for engine
```

### **3. Habrá un Pull Request**
Ve a: https://github.com/Gahenax/TRIKSTER-ORACLE/pulls

Verás un PR titulado algo como:
```
"Phase 1: Monte Carlo Engine & Risk Assessment"
```

---

## ✅ **Acción Cuando Jules Termine**

1. **Ve al PR**: https://github.com/Gahenax/TRIKSTER-ORACLE/pulls
2. **Revisa el código** (click en "Files changed")
3. **Verifica que cumple los requisitos**:
   - ✅ Archivos creados: `model.py`, `engine.py`, `risk.py`
   - ✅ Tests creados: `test_engine.py`, `test_risk.py`
   - ✅ Todos los tests pasan
   - ✅ No hay términos prohibidos

4. **Hacer merge local y probar**:
```bash
cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE

# Traer el branch de Jules
git fetch origin
git checkout feature/phase1-monte-carlo-engine

# Probar los tests
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
pytest app/tests/ -v

# Si todo pasa, hacer merge
git checkout master
git merge feature/phase1-monte-carlo-engine
git push origin master
```

5. **Cerrar el PR en GitHub** (o hacer merge desde la UI)

---

## 🚨 **Troubleshooting**

### **"Jules NO aparece después de 6 horas"**

Posibles causas:
1. **No creaste el issue** → Ve a GitHub y créalo ahora
2. **El repositorio es privado** → Jules solo trabaja en repos públicos
3. **No pusiste `@google-jules`** → Edita el issue y añádelo
4. **Jules está ocupado** → Puede tardar más en horarios pico

**Solución**: Crea un comment en el issue:
```
@google-jules ping - still waiting for your work on this phase
```

---

### **"Veo el branch pero no hay PR"**

Jules puede estar todavía trabajando. Espera 30-60 min más.

Si persiste, crea un comment en el issue pidiendo el PR.

---

### **"El PR tiene errores"**

Jules puede cometer errores. Opciones:
1. **Comentar en el PR** con feedback específico
2. **Hacer cambios tú mismo** y pushear al branch de Jules
3. **Cerrar el PR** y pedir a Jules que lo rehaga

---

## 📱 **Método Alternativo: Email/Notificaciones**

Si configuraste notificaciones de GitHub por email:
1. GitHub te enviará un email cuando Jules abra el PR
2. No necesitas checkear manualmente

**Configurar**:
1. Ve a: https://github.com/settings/notifications  
2. Activa "Pull requests" y "Issues" para el repo
3. Recibirás emails automáticamente

---

## 🎬 **Resumen: Disfruta Tu Serie**

**Antes de empezar la serie**:
1. ✅ Crea el GitHub Issue (2 minutos)
2. ✅ Deja este archivo abierto para referencia

**Durante la serie** (cada 15-30 min en comerciales):
1. Abre PowerShell
2. Ejecuta: `.\monitor_jules.ps1`
3. Si ves "Jules NO ha comenzado" → sigue viendo
4. Si ves "JULES TRABAJANDO" → seguimientomás frecuente (cada 15 min)
5. Si ves "¡Hay un PR!" → **¡hora de revisar!** 🎉

**Después de la serie**:
1. Revisa si hay PR
2. Si no hay, checkea mañana
3. Jules trabaja async, puede tardar más

---

**¡Disfruta tu serie! Jules trabajará mientras tanto.** 🍿📺
