# Contrato de Output Limpio (Clean Output Contract) - V1.0

Este documento define el estándar obligatorio para todas las respuestas generadas por el motor del MVP. El objetivo es eliminar la complacencia del modelo y forzar el rigor estructural.

## Estructura Obligatoria

Toda respuesta final debe entregarse dividida exactamente en los siguientes 5 bloques:

### 1. Reencuadre de la Consulta (Reframing)
*   **Propósito:** Neutralizar lenguaje cargado, sesgos del usuario o ambigüedades.
*   **Contenido:** Una versión destilada y técnica de la pregunta original.
*   **Regla:** No usar adjetivos, solo variables y relaciones.

### 2. Hallazgos Rigurosos (Hechos)
*   **Propósito:** Listar lo que es demostrable o explícito.
*   **Contenido:** Puntos de datos, citas textuales o deducciones lógicas cerradas.
*   **Regla:** Si no hay evidencia directa, este bloque permanece vacío o dice "Ninguno detectado".

### 3. Exclusiones de Rigor (Lo que NO se puede concluir)
*   **Propósito:** Evitar saltos de fe o "wishful thinking".
*   **Contenido:** Inferencias comunes que el usuario podría hacer pero que no tienen sustento suficiente.
*   **Regla:** Ser agresivo en la negativa. "No hay datos para afirmar X".

### 4. Supuestos Críticos (Inferencias en Proceso)
*   **Propósito:** Identificar los "huecos" lógicos que impiden una conclusión definitiva.
*   **Contenido:** Inferencias necesarias para que el razonamiento avance, pero que aún no son hechos.
*   **Regla:** Cada supuesto debe estar vinculado a una conclusión potencial. "Inferencia: X -> Si se confirma, Conclusión: Y".

### 5. Interrogatorio de Validación (Mecanismo de Cierre)
*   **Propósito:** Transformar supuestos en hechos mediante la intervención del usuario.
*   **Contenido:** 1 a 3 preguntas de alta precisión diseñadas para despejar los supuestos del bloque anterior.
*   **Regla:** NO son preguntas abiertas. Deben ser orientadas a datos o decisiones binarias que permitan al sistema emitir un veredicto en el siguiente turno.

### 6. Próximos Pasos Verificables (Acción Fuera del Motor)
*   **Propósito:** Reducir la entropía en el mundo real.
*   **Contenido:** Acciones que el usuario puede ejecutar independientemente del software.

---

## Ejemplo de Aplicación

**Input del Usuario:**
> "¿Por qué mi equipo no está motivado si les pago bien y les doy fruta gratis?"

**Output Limpio:**

**1. Reencuadre:**
Análisis de la falta de correlación observada entre incentivos materiales (compensación y beneficios) y el rendimiento/compromiso percibido en un grupo de trabajo.

**2. Hallazgos Rigurosos:**
- Existen dos variables de incentivo implementadas: salario y beneficios tangibles ("fruta").
- El usuario reporta una percepción de "falta de motivación" (variable subjetiva).

**3. Lo que NO se puede concluir:**
- No se puede concluir que la causa sea el salario.
- No se puede concluir que el equipo esté realmente desmotivado (falta métrica de rendimiento).
- No se puede afirmar que los incentivos actuales sean los adecuados para el perfil demográfico del equipo.

**4. Supuestos:**
- Se asume que el salario es competitivo respecto al mercado (no verificado).
- Se asume que el equipo valora los incentivos materiales por encima de los culturales o de autonomía.

**5. Próximos pasos:**
1. Medir la rotación voluntaria de los últimos 6 meses.
2. Realizar una encuesta anónima de "Factores de Higiene" (Herzberg) enfocada en autonomía y propósito.
3. Comparar el salario actual con los benchmarks del sector para roles específicos.
