# 🔍 FRASES PARA PROBAR CONTEO DE RETARDOS

## 📋 **INSTRUCCIONES DE USO:**
1. Ejecuta: `python client.py`
2. Copia y pega estas frases exactas
3. Verifica que los conteos funcionen correctamente

---

## 🔥 **TEST BÁSICOS DE CONTEO**

### ✅ Test 1: Conteo diario
```
¿Cuántos retardos hubo hoy?
```
**Esperado:** Número de retardos del día actual

### ✅ Test 2: Conteo semanal
```
¿Cuántos retardos hubo esta semana?
```
**Esperado:** Suma de retardos de lunes a viernes en los últimos 7 días

### ✅ Test 3: Conteo mensual
```
¿Cuántos retardos hubo este mes?
```
**Esperado:** Total de retardos del mes actual

### ✅ Test 4: Conteo en julio
```
¿Cuántos retardos hubo en julio?
```
**Esperado:** Total de retardos de julio 2025

---

## 👥 **TEST DE CONTEO POR PERSONA**

### ✅ Test 5: Top retardos por persona
```
¿Quién tiene más retardos este mes?
```
**Esperado:** Lista ordenada de personas con más retardos

### ✅ Test 6: Conteo individual
```
¿Cuántos retardos tiene Ernesto Sanchez?
```
**Esperado:** Número específico de retardos de esa persona

### ✅ Test 7: Conteo con detalles
```
¿Cuántas veces llegó tarde María Leticia esta semana?
```
**Esperado:** Conteo específico con nombre completo

---

## 📊 **TEST DE CONTEOS AVANZADOS**

### ✅ Test 8: Conteo con porcentajes
```
¿Cuál es el porcentaje de retardos esta semana?
```
**Esperado:** Cálculo de porcentaje basado en total de entradas

### ✅ Test 9: Promedio de retardos
```
¿Cuál es el promedio de retardos por día?
```
**Esperado:** Cálculo de promedio diario

### ✅ Test 10: Comparación temporal
```
¿Hubo más retardos esta semana que la semana pasada?
```
**Esperado:** Comparación numérica entre períodos

---

## 📅 **TEST DE RANGOS ESPECÍFICOS**

### ✅ Test 11: Período específico
```
¿Cuántos retardos hubo entre el 15 y 20 de julio?
```
**Esperado:** Conteo en rango de fechas específico

### ✅ Test 12: Días de la semana
```
¿Qué día de la semana hay más retardos?
```
**Esperado:** Análisis por día de la semana

### ✅ Test 13: Conteo por horarios
```
¿Cuántas personas llegan tarde después de las 9 AM?
```
**Esperado:** Conteo filtrado por hora específica

---

## 🎯 **RESULTADOS ESPERADOS**

### ✅ **Lo que DEBE funcionar:**
- Números exactos de retardos
- Conteos por persona correctos  
- Rangos de fechas precisos
- Cálculos de porcentajes
- Comparaciones temporales

### ❌ **Errores que NO deben aparecer:**
- `Unknown column 'nombre'`
- `You have an error in your SQL syntax`
- `LIMIT 100` duplicado
- Fechas de 2024 en lugar de 2025
- Conteos en cero cuando hay datos

---

## 📋 **CHECKLIST DE VERIFICACIÓN**

Marca ✅ si funciona, ❌ si falla:

- [ ] Conteo básico diario
- [ ] Conteo semanal
- [ ] Conteo mensual  
- [ ] Conteo por persona
- [ ] Rangos de fechas específicos
- [ ] Cálculos de minutos de retardo
- [ ] Comparaciones temporales
- [ ] Porcentajes de puntualidad

---

## 🔧 **EN CASO DE ERRORES:**

Si alguna consulta falla:
1. **Anota el error exacto**
2. **Copia la consulta SQL generada**
3. **Prueba la consulta directamente en `test_conteo_retardos.sql`**
4. **Reporta el problema específico** 