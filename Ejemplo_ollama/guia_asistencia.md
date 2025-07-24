# 🏢 Guía Especializada: Análisis de Asistencia Laboral

## 🎯 Sistema Especializado para Control de Asistencia

Este sistema ha sido **optimizado específicamente** para el análisis de asistencia laboral con:
- **Base de datos:** zapopan 
- **Tabla de empleados:** core_usuario
- **Tabla de registros:** core_registro
- **Horario límite:** 08:10:00 AM (sin retardo)
- **Días laborales:** Lunes a Viernes

## 🚀 Inicio Rápido

### Comando Principal
```bash
python client.py
```

### Resumen Automático
Una vez iniciado el sistema, escribe:
```
resumen
```
Esto generará automáticamente un **resumen semanal completo** con:
- ✅ Métricas de puntualidad
- ⚠️ Top 5 retardos más grandes
- 🌟 Personas más puntuales
- 📊 Estadísticas generales

## 📋 Consultas Más Útiles (Copy & Paste)

### 🔥 **ANÁLISIS PRIORITARIOS**

#### Resumen Semanal Completo
```
Dame las métricas semanales de puntualidad
```

#### Identificar Retardos
```
¿Quién llegó tarde esta semana?
```

#### Control Diario
```
¿Quién se registró hoy?
```

#### Conteo de Asistencia
```
¿Cuántas personas vinieron esta semana?
```

### 📊 **ANÁLISIS DIARIOS**

#### Resumen del Día
```
¿Cuántos retardos hubo hoy?
```

#### Lista Ordenada
```
Lista de llegadas de hoy ordenadas por hora
```

#### Consulta Individual
```
¿A qué hora llegó [NOMBRE DE LA PERSONA]?
```
*Ejemplo: ¿A qué hora llegó María González?*

### 📈 **MÉTRICAS Y KPIs**

#### Porcentaje de Puntualidad
```
Porcentaje de puntualidad semanal
```

#### Hora Promedio
```
¿Cuál es el promedio de hora de llegada?
```

#### Análisis por Día
```
¿Qué día de la semana hay más retardos?
```

#### Estadísticas Individuales
```
Estadísticas de asistencia por persona
```

### 👤 **BÚSQUEDAS INDIVIDUALES**

#### Historial Personal
```
Historial de [NOMBRE]
```
*Ejemplo: Historial de Juan Pérez*

#### Conteo de Retardos
```
¿Cuántas veces llegó tarde [NOMBRE]?
```

#### Patrón de Asistencia
```
Patrón de asistencia de [NOMBRE]
```

### 📅 **COMPARACIONES TEMPORALES**

#### Comparación Semanal
```
Compara esta semana vs la semana pasada
```

#### Tendencias
```
¿Ha mejorado la puntualidad este mes?
```

#### Análisis de Tendencia
```
Tendencia de asistencia semanal
```

## 💡 **Tips para Mejores Resultados**

### ✅ **Búsquedas de Nombres**
- **Funciona con nombres parciales**: "María" encuentra "María José González"
- **No importa el orden**: "González María" = "María González" 
- **Maneja acentos**: "Jose" encuentra "José"

### ✅ **Análisis Temporales**
- **"Hoy"**: Automáticamente usa la fecha actual
- **"Esta semana"**: Desde el lunes actual
- **"Semana pasada"**: Semana completa anterior

### ✅ **Métricas Automáticas**
- **El sistema calcula automáticamente**:
  - % de puntualidad
  - Número de retardos vs puntuales
  - Promedios de hora de llegada
  - Comparaciones y tendencias

## 🎯 **Flujo de Trabajo Recomendado**

### Para Supervisores (Lunes):
1. `resumen` - Ver el resumen de la semana anterior
2. `¿Quién llegó tarde esta semana?` - Identificar patrones
3. `¿Quién es la persona más puntual?` - Reconocimiento

### Para RH (Diario):
1. `¿Quién se registró hoy?` - Control diario
2. `¿Cuántos retardos hubo hoy?` - Seguimiento
3. `Lista de llegadas de hoy ordenadas por hora` - Registro ordenado

### Para Análisis Mensual:
1. `Compara esta semana vs la semana pasada` - Tendencias
2. `¿Ha mejorado la puntualidad este mes?` - Progreso
3. `Estadísticas de asistencia por persona` - Evaluación individual

## 🔧 **Reglas del Sistema**

### ⏰ **Definiciones de Tiempo**
- **PUNTUAL**: Llegada hasta las 08:10:00 AM ✅
- **RETARDO**: Llegada después de las 08:10:00 AM ⚠️
- **SEMANA LABORAL**: Lunes a Viernes 📅

### 📊 **Cálculos Automáticos**
- **% Puntualidad**: (Llegadas puntuales / Total registros) × 100
- **Promedio hora**: Media aritmética de todas las horas de llegada
- **Evaluación**:
  - 90%+ = EXCELENTE 🌟
  - 80-89% = BUENA 👍  
  - 70-79% = REGULAR ⚠️
  - <70% = NECESITA MEJORA 🚨

## 🚨 **Solución de Problemas**

### No encuentra a una persona:
- Verifica la escritura del nombre
- Usa nombres parciales: "María" en lugar de "María José"
- Prueba solo el apellido

### No hay datos de una fecha:
- Confirma que sea día laboral (lunes-viernes)
- Verifica que haya registros en la base de datos
- Usa rangos más amplios ("esta semana" en lugar de "hoy")

### Resultados inesperados:
- El sistema está optimizado para semanas laborales
- Los fines de semana se excluyen automáticamente
- Las fechas se calculan dinámicamente

## 📞 **Comandos de Atajo**

| Comando | Resultado |
|---------|-----------|
| `resumen` | Resumen semanal completo automático |
| `salir` | Terminar sesión |
| `[nombre]` | Búsqueda rápida de persona |

---

**💼 Sistema optimizado para control de asistencia laboral - Base de datos zapopan** 