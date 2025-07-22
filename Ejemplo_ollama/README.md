# Sistema de Análisis de Base de Datos con IA (MCP + Ollama + MariaDB)

Este sistema combina un servidor MCP con Ollama para crear un asistente de análisis de base de datos impulsado por IA. Permite hacer consultas en lenguaje natural que se traducen automáticamente en análisis de datos y métricas.

## Configuración

### Credenciales de Base de Datos
- **Host:** 172.16.1.29
- **Usuario:** controla
- **Contraseña:** controla

### Requisitos Previos

1. **Ollama** ejecutándose con el modelo `llama3.1:8b`
2. **MariaDB** accesible en la red
3. **Python 3.8+**

### Instalación Automática

```bash
python setup.py
```

Este script:
- 📦 Instala todas las dependencias
- 🔍 Prueba la conexión a MariaDB
- 🦙 Verifica la conexión con Ollama
- ⚙️ Crea archivo de configuración

### Instalación Manual

```bash
pip install -r requirements.txt
```

### Ejecutar el Sistema

```bash
# Modo interactivo con IA
python client.py

# Solo servidor MCP (sin IA)
python server.py
```

## 🤖 Funcionalidades del Asistente IA

### Análisis en Lenguaje Natural
El sistema acepta preguntas en español y las convierte automáticamente en análisis de datos:

**Ejemplos de preguntas:**
- "¿Qué bases de datos hay disponibles?"
- "Analiza la tabla usuarios en la base de datos tienda"
- "Compara las tablas productos y categorías"
- "¿Cuáles son las métricas de la tabla ventas?"
- "Muéstrame los 10 productos más vendidos"
- "¿Cuál es la distribución de edades en la tabla clientes?"

### Capacidades de Análisis
- 📊 **Métricas automáticas**: Estadísticas, conteos, distribuciones
- 🔍 **Análisis comparativo**: Diferencias entre tablas y estructuras
- 📈 **Insights inteligentes**: Patrones y tendencias detectados por IA
- 📋 **Reportes detallados**: Análisis completos con recomendaciones

## 🛠️ Herramientas MCP Disponibles

### Herramientas de Conexión

### 1. `test_connection()`
Prueba la conexión a la base de datos MariaDB.

**Ejemplo de uso:**
```json
{
  "success": true,
  "connected": true,
  "server_version": "10.6.12-MariaDB",
  "server_time": "2024-01-15T10:30:00",
  "host": "172.16.1.29",
  "user": "controla"
}
```

### 2. `list_databases()`
Lista todas las bases de datos disponibles en el servidor.

**Retorna:**
- Lista de nombres de bases de datos
- Conteo total
- Timestamp

### 3. `list_tables(database: str)`
Lista todas las tablas en una base de datos específica.

**Parámetros:**
- `database`: Nombre de la base de datos

### 4. `describe_table(database: str, table: str)`
Obtiene la estructura completa de una tabla.

**Parámetros:**
- `database`: Nombre de la base de datos
- `table`: Nombre de la tabla

**Retorna:**
- Información de columnas (tipo, null, clave, default, extra)
- Número de columnas

### 5. `execute_query(database: str, query: str, limit: int = 100)`
Ejecuta consultas SELECT de forma segura.

**Parámetros:**
- `database`: Nombre de la base de datos
- `query`: Consulta SQL (solo SELECT)
- `limit`: Límite de resultados (por defecto 100)

**Características de seguridad:**
- Solo permite consultas SELECT
- Aplica límite automático si no se especifica
- Convierte fechas/tiempo a formato ISO

### 6. `insert_data(database: str, table: str, data: Dict[str, Any])`
Inserta un nuevo registro en una tabla.

**Parámetros:**
- `database`: Nombre de la base de datos
- `table`: Nombre de la tabla
- `data`: Diccionario con los datos a insertar

**Ejemplo:**
```python
data = {
    "nombre": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "edad": 30
}
```

### 7. `update_data(database: str, table: str, data: Dict[str, Any], where_clause: str)`
Actualiza registros existentes en una tabla.

**Parámetros:**
- `database`: Nombre de la base de datos
- `table`: Nombre de la tabla
- `data`: Diccionario con los nuevos valores
- `where_clause`: Condición WHERE (sin la palabra WHERE)

**Ejemplo:**
```python
data = {"email": "nuevo@ejemplo.com"}
where_clause = "id = 123"
```

### 8. `delete_data(database: str, table: str, where_clause: str)`
Elimina registros de una tabla.

**Parámetros:**
- `database`: Nombre de la base de datos
- `table`: Nombre de la tabla
- `where_clause`: Condición WHERE (sin la palabra WHERE)

### 6. `get_table_metrics(database: str, table: str)`
Obtiene métricas completas de una tabla incluyendo estadísticas numéricas.

**Retorna:**
- Número de registros y estructura
- Estadísticas de columnas numéricas (min, max, avg, distinct)
- Información de índices y almacenamiento

### 7. `get_database_overview(database: str)`
Obtiene un resumen completo de una base de datos.

**Retorna:**
- Total de tablas y registros
- Tamaño total de la base de datos
- Información detallada de cada tabla

### 8. `compare_tables(database: str, table1: str, table2: str)`
Compara dos tablas en términos de estructura y métricas.

**Retorna:**
- Columnas comunes y diferentes
- Diferencias en tamaño y registros
- Porcentaje de similaridad estructural

### 9. `analyze_data_distribution(database: str, table: str, column: str)`
Analiza la distribución de datos en una columna específica.

**Retorna:**
- Estadísticas básicas (conteos, nulos, únicos)
- Top valores más frecuentes
- Estadísticas numéricas (si aplica)

## Recursos Disponibles

### 1. `mariadb://connection_info`
Información de configuración de conexión (sin mostrar contraseña).

### 2. `mariadb://status`
Estado actual del servidor MariaDB incluyendo:
- Tiempo de actividad
- Conexiones activas
- Total de consultas

## Características de Seguridad

1. **Solo consultas SELECT**: La herramienta `execute_query` solo permite consultas SELECT para evitar modificaciones accidentales.

2. **Límites automáticos**: Se aplican límites automáticos a las consultas para evitar resultados excesivamente grandes.

3. **Manejo de errores**: Todas las herramientas incluyen manejo robusto de errores.

4. **Logging**: Se registra información importante para debugging.

5. **Sanitización**: Los parámetros se pasan de forma segura usando placeholders.

## 🚀 Configuración de Ollama

### Instalar y Configurar Ollama

```bash
# Instalar Ollama (si no lo tienes)
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar el modelo
ollama pull llama3.1:8b

# Ejecutar Ollama (permitir conexiones externas)
OLLAMA_HOST=0.0.0.0 ollama serve
```

### Verificar que Ollama esté ejecutándose
```bash
curl http://localhost:11434/api/tags
```

## 💬 Ejemplos de Conversación con IA

### Ejemplo 1: Exploración Inicial
```
Usuario: ¿Qué bases de datos hay disponibles?

Asistente: 🔧 Ejecutando: list_databases()
📊 Resultado: {
  "success": true,
  "databases": ["tienda", "usuarios", "logs", "analytics"],
  "count": 4
}

🤖 Análisis: Encontré 4 bases de datos disponibles:
- tienda: Probablemente contiene datos de e-commerce
- usuarios: Sistema de gestión de usuarios
- logs: Registros del sistema
- analytics: Datos para análisis y reportes

¿Te gustaría explorar alguna en particular?
```

### Ejemplo 2: Análisis de Tabla
```
Usuario: Analiza la tabla productos en la base tienda

Asistente: 🔧 Ejecutando: get_table_metrics(database="tienda", table="productos")
📊 Resultado: {
  "success": true,
  "row_count": 1250,
  "numeric_statistics": {
    "precio": {"min": 9.99, "max": 1299.99, "avg": 145.67},
    "stock": {"min": 0, "max": 500, "avg": 45.2}
  }
}

🤖 Análisis: La tabla productos contiene 1,250 productos con:
• Precios desde $9.99 hasta $1,299.99 (promedio: $145.67)
• Stock desde 0 hasta 500 unidades (promedio: 45.2)
• Hay productos sin stock (valor mínimo 0)

Recomendaciones:
- Revisar productos con stock 0
- El rango de precios es amplio, considera categorización
```

## 🔧 Flujo de Trabajo Técnico (MCP)

Para desarrollo o uso directo de las herramientas MCP:

1. **Probar conexión:**
   ```python
   test_connection()
   ```

2. **Análisis completo de base de datos:**
   ```python
   get_database_overview("mi_base_datos")
   ```

3. **Comparar estructuras:**
   ```python
   compare_tables("mi_base_datos", "usuarios", "clientes")
   ```

4. **Análisis de distribución:**
   ```python
   analyze_data_distribution("mi_base_datos", "ventas", "precio")
   ```

## Notas Importantes

- **Codificación**: Se usa UTF8MB4 para soporte completo de Unicode
- **Autocommit**: Está habilitado por defecto
- **Conexiones**: Se abren y cierran automáticamente para cada operación
- **Timestamps**: Todos los resultados incluyen timestamps ISO 8601

## 🔧 Troubleshooting

### Error de Conexión a MariaDB
Si no puedes conectarte a la base de datos:
1. Verifica que la IP 172.16.1.29 sea accesible
2. Confirma que el usuario "controla" tenga permisos
3. Asegúrate de que el puerto 3306 esté abierto
4. Verifica que PyMySQL esté instalado correctamente

### Error de Conexión a Ollama
Si el cliente no puede conectarse a Ollama:
1. **Verificar que Ollama esté ejecutándose:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Ollama en red local:**
   ```bash
   # Ejecutar Ollama permitiendo conexiones externas
   OLLAMA_HOST=0.0.0.0 ollama serve
   ```

3. **Verificar modelo disponible:**
   ```bash
   ollama list
   # Si no está: ollama pull llama3.1:8b
   ```

4. **Firewall/Puertos:**
   - Puerto 11434 debe estar abierto
   - Verificar configuración de firewall

### Error de Permisos en MariaDB
El usuario "controla" necesita estos permisos:
- **SELECT**: Para consultas y análisis
- **SHOW DATABASES**: Para listar bases de datos  
- **SHOW TABLES**: Para explorar estructuras

### Problemas de Rendimiento
Si las consultas son lentas:
1. Limita los resultados usando el parámetro `limit`
2. Considera usar índices en las columnas consultadas
3. El sistema aplica límites automáticos para proteger el rendimiento

### Errores Comunes

**Error: "Modelo no disponible"**
```bash
ollama pull llama3.1:8b
```

**Error: "Connection refused" (Ollama)**
```bash
# Verificar que Ollama esté ejecutándose
ps aux | grep ollama
# Si no está: ollama serve
```

**Error: "Access denied" (MariaDB)**
```sql
-- Verificar permisos del usuario
SHOW GRANTS FOR 'controla'@'%';
```

## 📦 Dependencias

### Librerías Python
- `fastmcp`: Framework MCP para herramientas de base de datos
- `pymysql`: Conector MySQL/MariaDB
- `requests`: Cliente HTTP para comunicación con Ollama
- `typing-extensions`: Extensiones de tipado para Python

### Servicios Externos
- **Ollama**: Servidor de LLM local (llama3.1:8b)
- **MariaDB**: Base de datos (172.16.1.29)

### Instalación Completa
```bash
# Opción 1: Instalación automática
python setup.py

# Opción 2: Instalación manual
pip install -r requirements.txt
```

## 🎯 Arquitectura del Sistema

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│                 │◄──────────────► │                 │
│     Ollama      │                 │   Cliente MCP   │
│   (llama3.1)    │                 │   (client.py)   │
│                 │                 │                 │
└─────────────────┘                 └─────────────────┘
                                             │
                                             │ MCP Protocol
                                             ▼
                                    ┌─────────────────┐
                                    │                 │
                                    │  Servidor MCP   │
                                    │   (server.py)   │
                                    │                 │
                                    └─────────────────┘
                                             │
                                             │ MySQL Protocol
                                             ▼
                                    ┌─────────────────┐
                                    │                 │
                                    │    MariaDB      │
                                    │  172.16.1.29    │
                                    │                 │
                                    └─────────────────┘
```

## 📈 Próximas Funcionalidades

- 📊 Generación automática de gráficos
- 📝 Exportación de reportes en PDF/Excel
- 🔄 Monitoreo en tiempo real
- 🎯 Alertas inteligentes basadas en patrones
- 🔗 Integración con más LLMs (GPT, Claude, etc.)

## 🤝 Contribuir

¿Quieres mejorar el sistema? ¡Las contribuciones son bienvenidas!

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request 