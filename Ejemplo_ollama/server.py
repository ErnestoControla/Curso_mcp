# server.py
from mcp.server.fastmcp import FastMCP
import pymysql
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configurar logging mejorado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Log de inicio del servidor
logger.info("🚀 Iniciando servidor MCP de análisis de base de datos")

# Decorator para manejo de errores consistente
def handle_mcp_errors(func):
    """Decorator para manejo consistente de errores en herramientas MCP"""
    def wrapper(*args, **kwargs):
        try:
            logger.debug(f"🔧 Ejecutando herramienta MCP: {func.__name__} con args: {args[:2]}")
            result = func(*args, **kwargs)
            if isinstance(result, dict) and result.get("success", True):
                logger.debug(f"✅ Herramienta {func.__name__} ejecutada exitosamente")
            else:
                logger.warning(f"⚠️  Herramienta {func.__name__} retornó error: {result.get('error', 'Error desconocido')}")
            return result
        except Exception as e:
            logger.error(f"❌ Error en herramienta {func.__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"Error interno en {func.__name__}: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    return wrapper

# Create an MCP server
mcp = FastMCP("MariaDB_Analytics_Server")

# Configuración de la base de datos
DB_CONFIG = {
    'host': '172.16.1.29',
    'user': 'controla',
    'password': 'controla',
    'charset': 'utf8mb4',
    'autocommit': True
}

def validate_sql_query(query: str) -> tuple[bool, str]:
    """Validar consulta SQL para prevenir inyección y comandos peligrosos"""
    query_upper = query.strip().upper()
    
    # Lista de comandos prohibidos (más específica)
    forbidden_commands = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL',
        'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE'
    ]
    
    # Patrones de UNION peligrosos (permite UNION en subconsultas legítimas)
    dangerous_patterns = [
        'UNION ALL SELECT', 'UNION SELECT', ') UNION', '/* UNION'
    ]
    
    # Verificar comandos prohibidos
    for cmd in forbidden_commands:
        if cmd in query_upper:
            return False, f"Comando prohibido detectado: {cmd}"
    
    # Verificar patrones peligrosos de UNION
    for pattern in dangerous_patterns:
        if pattern in query_upper:
            return False, f"Patrón peligroso detectado: {pattern}"
    
    # Debe empezar con SELECT
    if not query_upper.startswith('SELECT'):
        return False, "Solo se permiten consultas SELECT"
    
    # Validar caracteres peligrosos específicos
    dangerous_chars = [';', '--', 'xp_', 'sp_']
    for char in dangerous_chars:
        if char in query.lower():
            return False, f"Caracter o patrón peligroso detectado: {char}"
    
    # Permitir comentarios SQL básicos pero no en posiciones peligrosas
    if query.strip().endswith('--') or query.strip().startswith('--'):
        return False, "Comentarios SQL en posiciones peligrosas no permitidos"
    
    return True, "Consulta válida"

def get_db_connection(database: str = None):
    """Crear conexión a la base de datos"""
    config = DB_CONFIG.copy()
    if database:
        config['database'] = database
        logger.debug(f"Conectando a base de datos específica: {database}")
    else:
        logger.debug("Conectando a servidor MariaDB sin seleccionar base de datos")
    
    try:
        connection = pymysql.connect(**config)
        logger.debug(f"✅ Conexión exitosa a {config['host']}")
        return connection
    except Exception as e:
        logger.error(f"❌ Error conectando a base de datos {config['host']}: {e}")
        raise


@mcp.tool()
def list_databases() -> Dict[str, Any]:
    """Listar todas las bases de datos disponibles en el servidor MariaDB"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                databases = [row[0] for row in cursor.fetchall()]
                return {
                    "success": True,
                    "databases": databases,
                    "count": len(databases),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def list_tables(database: str) -> Dict[str, Any]:
    """Listar todas las tablas en una base de datos específica"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                return {
                    "success": True,
                    "database": database,
                    "tables": tables,
                    "count": len(tables),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def describe_table(database: str, table: str) -> Dict[str, Any]:
    """Obtener la estructura de una tabla específica"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table}")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "field": row[0],
                        "type": row[1],
                        "null": row[2],
                        "key": row[3],
                        "default": row[4],
                        "extra": row[5]
                    })
                return {
                    "success": True,
                    "database": database,
                    "table": table,
                    "columns": columns,
                    "column_count": len(columns),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "table": table,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def execute_query(database: str, query: str, limit: int = 100) -> Dict[str, Any]:
    """Ejecutar una consulta SELECT en la base de datos con límite de resultados"""
    logger.info(f"🔍 Ejecutando consulta en base de datos '{database}': {query[:100]}...")
    try:
        # Validación de seguridad SQL
        is_valid, validation_msg = validate_sql_query(query)
        if not is_valid:
            logger.warning(f"⚠️  Consulta SQL rechazada por seguridad: {validation_msg}")
            return {
                "success": False,
                "error": f"Consulta rechazada por seguridad: {validation_msg}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Agregar LIMIT si no existe (detección mejorada)
        query_clean = query.strip()
        query_upper = query_clean.upper()
        
        # Verificar más robustamente si ya tiene LIMIT
        has_limit = (
            'LIMIT' in query_upper or 
            query_clean.endswith(';') or
            query_upper.endswith('LIMIT') or
            ' LIMIT ' in query_upper or
            query_upper.endswith('LIMIT 1') or
            query_upper.endswith('LIMIT 5') or
            query_upper.endswith('LIMIT 10') or
            query_upper.endswith('LIMIT 20') or
            query_upper.endswith('LIMIT 50') or
            query_upper.endswith('LIMIT 100')
        )
        
        if not has_limit:
            query += f" LIMIT {limit}"
        
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir resultados a formato JSON serializable
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif hasattr(value, 'isoformat'):  # Para dates, times, etc.
                            value = value.isoformat()
                        row_dict[col] = value
                    results.append(row_dict)
                
                return {
                    "success": True,
                    "database": database,
                    "query": query,
                    "columns": columns,
                    "results": results,
                    "row_count": len(results),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """Probar la conexión a la base de datos MariaDB"""
    logger.info("🔍 Probando conexión a la base de datos MariaDB")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.execute("SELECT NOW()")
                server_time = cursor.fetchone()[0]
                
                return {
                    "success": True,
                    "connected": True,
                    "server_version": version,
                    "server_time": server_time.isoformat(),
                    "host": DB_CONFIG['host'],
                    "user": DB_CONFIG['user'],
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "host": DB_CONFIG['host'],
            "user": DB_CONFIG['user'],
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def get_table_metrics(database: str, table: str) -> Dict[str, Any]:
    """Obtener métricas completas de una tabla"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                # Información básica de la tabla
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
                table_status = cursor.fetchone()
                
                # Índices
                cursor.execute(f"SHOW INDEX FROM {table}")
                indexes = cursor.fetchall()
                
                # Conteo de registros
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Obtener información de columnas numéricas para estadísticas
                cursor.execute(f"DESCRIBE {table}")
                columns_info = cursor.fetchall()
                
                numeric_stats = {}
                for col_info in columns_info:
                    col_name = col_info[0]
                    col_type = col_info[1].upper()
                    
                    # Verificar si es columna numérica
                    if any(num_type in col_type for num_type in ['INT', 'DECIMAL', 'FLOAT', 'DOUBLE', 'NUMERIC']):
                        try:
                            cursor.execute(f"""
                                SELECT 
                                    MIN({col_name}) as min_val,
                                    MAX({col_name}) as max_val,
                                    AVG({col_name}) as avg_val,
                                    COUNT(DISTINCT {col_name}) as distinct_count
                                FROM {table}
                                WHERE {col_name} IS NOT NULL
                            """)
                            stats = cursor.fetchone()
                            if stats:
                                numeric_stats[col_name] = {
                                    "min": float(stats[0]) if stats[0] is not None else None,
                                    "max": float(stats[1]) if stats[1] is not None else None,
                                    "avg": float(stats[2]) if stats[2] is not None else None,
                                    "distinct_count": stats[3]
                                }
                        except:
                            continue
                
                return {
                    "success": True,
                    "database": database,
                    "table": table,
                    "row_count": row_count,
                    "engine": table_status[1] if table_status else None,
                    "collation": table_status[14] if table_status else None,
                    "data_length_bytes": table_status[6] if table_status else None,
                    "index_length_bytes": table_status[8] if table_status else None,
                    "auto_increment": table_status[10] if table_status else None,
                    "indexes": [{"key_name": idx[2], "column_name": idx[4], "non_unique": idx[1]} for idx in indexes],
                    "numeric_statistics": numeric_stats,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "table": table,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def get_database_overview(database: str) -> Dict[str, Any]:
    """Obtener un resumen completo de una base de datos"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                # Listar todas las tablas
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                tables_info = []
                total_rows = 0
                total_size = 0
                
                for table in tables:
                    # Información básica de cada tabla
                    cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
                    table_status = cursor.fetchone()
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    table_size = (table_status[6] or 0) + (table_status[8] or 0)  # data + index length
                    
                    tables_info.append({
                        "name": table,
                        "rows": row_count,
                        "size_bytes": table_size,
                        "engine": table_status[1] if table_status else None
                    })
                    
                    total_rows += row_count
                    total_size += table_size
                
                return {
                    "success": True,
                    "database": database,
                    "total_tables": len(tables),
                    "total_rows": total_rows,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "tables": tables_info,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def compare_tables(database: str, table1: str, table2: str) -> Dict[str, Any]:
    """Comparar dos tablas en términos de estructura y métricas básicas"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                # Información de tabla 1
                cursor.execute(f"DESCRIBE {table1}")
                cols1 = cursor.fetchall()
                cursor.execute(f"SELECT COUNT(*) FROM {table1}")
                count1 = cursor.fetchone()[0]
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table1}'")
                status1 = cursor.fetchone()
                
                # Información de tabla 2
                cursor.execute(f"DESCRIBE {table2}")
                cols2 = cursor.fetchall()
                cursor.execute(f"SELECT COUNT(*) FROM {table2}")
                count2 = cursor.fetchone()[0]
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table2}'")
                status2 = cursor.fetchone()
                
                # Comparar estructura
                cols1_names = set(col[0] for col in cols1)
                cols2_names = set(col[0] for col in cols2)
                
                common_columns = cols1_names & cols2_names
                only_in_table1 = cols1_names - cols2_names
                only_in_table2 = cols2_names - cols1_names
                
                size1 = (status1[6] or 0) + (status1[8] or 0) if status1 else 0
                size2 = (status2[6] or 0) + (status2[8] or 0) if status2 else 0
                
                return {
                    "success": True,
                    "database": database,
                    "table1": {
                        "name": table1,
                        "columns": len(cols1),
                        "rows": count1,
                        "size_bytes": size1,
                        "engine": status1[1] if status1 else None
                    },
                    "table2": {
                        "name": table2,
                        "columns": len(cols2),
                        "rows": count2,
                        "size_bytes": size2,
                        "engine": status2[1] if status2 else None
                    },
                    "comparison": {
                        "common_columns": list(common_columns),
                        "common_columns_count": len(common_columns),
                        "only_in_table1": list(only_in_table1),
                        "only_in_table2": list(only_in_table2),
                        "row_difference": count2 - count1,
                        "size_difference_bytes": size2 - size1,
                        "structure_similarity": len(common_columns) / max(len(cols1_names), len(cols2_names)) * 100
                    },
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "table1": table1,
            "table2": table2,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def analyze_data_distribution(database: str, table: str, column: str, bins: int = 10) -> Dict[str, Any]:
    """Analizar la distribución de datos en una columna específica"""
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                # Verificar que la columna existe
                cursor.execute(f"DESCRIBE {table}")
                columns = [row[0] for row in cursor.fetchall()]
                
                if column not in columns:
                    return {
                        "success": False,
                        "error": f"La columna '{column}' no existe en la tabla '{table}'",
                        "available_columns": columns,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Estadísticas básicas
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT({column}) as non_null_count,
                        COUNT(DISTINCT {column}) as distinct_count,
                        MIN({column}) as min_val,
                        MAX({column}) as max_val
                    FROM {table}
                """)
                basic_stats = cursor.fetchone()
                
                # Top valores más frecuentes
                cursor.execute(f"""
                    SELECT {column}, COUNT(*) as frequency
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    GROUP BY {column}
                    ORDER BY frequency DESC
                    LIMIT 10
                """)
                top_values = cursor.fetchall()
                
                result = {
                    "success": True,
                    "database": database,
                    "table": table,
                    "column": column,
                    "basic_statistics": {
                        "total_rows": basic_stats[0],
                        "non_null_count": basic_stats[1],
                        "null_count": basic_stats[0] - basic_stats[1],
                        "distinct_count": basic_stats[2],
                        "null_percentage": round((basic_stats[0] - basic_stats[1]) / basic_stats[0] * 100, 2),
                        "uniqueness_ratio": round(basic_stats[2] / basic_stats[1] * 100, 2) if basic_stats[1] > 0 else 0
                    },
                    "top_values": [{"value": val[0], "frequency": val[1], "percentage": round(val[1] / basic_stats[1] * 100, 2)} for val in top_values],
                    "timestamp": datetime.now().isoformat()
                }
                
                # Si es numérico, agregar estadísticas adicionales
                if basic_stats[3] is not None and basic_stats[4] is not None:
                    try:
                        cursor.execute(f"""
                            SELECT AVG({column}), STDDEV({column})
                            FROM {table}
                            WHERE {column} IS NOT NULL
                        """)
                        avg_std = cursor.fetchone()
                        
                        result["basic_statistics"].update({
                            "min_value": float(basic_stats[3]),
                            "max_value": float(basic_stats[4]),
                            "average": float(avg_std[0]) if avg_std[0] else None,
                            "std_deviation": float(avg_std[1]) if avg_std[1] else None
                        })
                    except:
                        pass
                
                return result
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "table": table,
            "column": column,
            "timestamp": datetime.now().isoformat()
        }


# ===== HERRAMIENTAS ESPECIALIZADAS PARA ANÁLISIS DE ASISTENCIA =====

@mcp.tool()
def generate_attendance_query(database: str, analysis_type: str, date_from: str = None, date_to: str = None, user_filter: str = None) -> Dict[str, Any]:
    """
    Genera consultas SQL optimizadas para análisis de asistencia específicos.
    
    database: Base de datos que contiene la tabla core_registro
    analysis_type: 'daily_summary', 'late_arrivals', 'missing_exits', 'user_pattern', 'device_usage', 'hourly_distribution'
    date_from: Fecha inicio en formato YYYY-MM-DD
    date_to: Fecha fin en formato YYYY-MM-DD  
    user_filter: Filtro por nombre o código de usuario
    """
    try:
        base_conditions = []
        if date_from:
            base_conditions.append(f"tiempo >= '{date_from} 00:00:00'")
        if date_to:
            base_conditions.append(f"tiempo <= '{date_to} 23:59:59'")
        if user_filter:
            base_conditions.append(f"(nombre LIKE '%{user_filter}%' OR codigo_usuario LIKE '%{user_filter}%')")
        
        where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
        
        queries = {
            "daily_summary": f"""
                SELECT 
                    DATE(tiempo) as fecha,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT usuario_id) as usuarios_unicos,
                    COUNT(CASE WHEN estado_id = 1 THEN 1 END) as entradas,
                    COUNT(CASE WHEN estado_id = 2 THEN 1 END) as salidas
                FROM core_registro 
                WHERE {where_clause}
                GROUP BY DATE(tiempo)
                ORDER BY fecha DESC;
            """,
            
            "late_arrivals": f"""
                SELECT 
                    nombre, codigo_usuario, 
                    DATE(tiempo) as fecha,
                    TIME(tiempo) as hora_llegada,
                    lugar, dispositivo
                FROM core_registro 
                WHERE estado_id = 1 
                    AND TIME(tiempo) > '08:10:00'
                    AND {where_clause}
                ORDER BY tiempo DESC;
            """,
            
            "missing_exits": f"""
                SELECT DISTINCT
                    r1.nombre, r1.codigo_usuario,
                    DATE(r1.tiempo) as fecha,
                    TIME(r1.tiempo) as hora_entrada
                FROM core_registro r1
                WHERE r1.estado_id = 1 
                    AND {where_clause.replace('tiempo', 'r1.tiempo')}
                    AND NOT EXISTS (
                        SELECT 1 FROM core_registro r2 
                        WHERE r2.usuario_id = r1.usuario_id 
                            AND r2.estado_id = 2
                            AND DATE(r2.tiempo) = DATE(r1.tiempo)
                            AND r2.tiempo > r1.tiempo
                    )
                ORDER BY r1.tiempo DESC;
            """,
            
            "user_pattern": f"""
                SELECT 
                    nombre, codigo_usuario,
                    COUNT(*) as total_registros,
                    MIN(tiempo) as primer_registro,
                    MAX(tiempo) as ultimo_registro,
                    COUNT(DISTINCT DATE(tiempo)) as dias_activos,
                    AVG(CASE WHEN estado_id = 1 THEN HOUR(tiempo) + MINUTE(tiempo)/60.0 END) as hora_promedio_entrada
                FROM core_registro 
                WHERE {where_clause}
                GROUP BY usuario_id, nombre, codigo_usuario
                ORDER BY total_registros DESC;
            """,
            
            "device_usage": f"""
                SELECT 
                    dispositivo,
                    lugar,
                    COUNT(*) as total_usos,
                    COUNT(DISTINCT usuario_id) as usuarios_distintos,
                    DATE(MIN(tiempo)) as primer_uso,
                    DATE(MAX(tiempo)) as ultimo_uso
                FROM core_registro 
                WHERE {where_clause}
                GROUP BY dispositivo, lugar
                ORDER BY total_usos DESC;
            """,
            
            "hourly_distribution": f"""
                SELECT 
                    HOUR(tiempo) as hora,
                    evento,
                    COUNT(*) as cantidad,
                    COUNT(DISTINCT usuario_id) as usuarios_unicos
                FROM core_registro 
                WHERE {where_clause}
                GROUP BY HOUR(tiempo), evento
                ORDER BY hora, evento;
            """
        }
        
        if analysis_type not in queries:
            return {
                "success": False,
                "error": f"Tipo de análisis no válido. Opciones: {', '.join(queries.keys())}",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "database": database,
            "query": queries[analysis_type].strip(),
            "description": f"Consulta para {analysis_type}",
            "filters_applied": {
                "date_from": date_from,
                "date_to": date_to, 
                "user_filter": user_filter
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def execute_attendance_analysis(database: str, analysis_type: str, date_from: str = None, date_to: str = None, user_filter: str = None) -> Dict[str, Any]:
    """
    Ejecuta directamente un análisis de asistencia y devuelve los resultados.
    
    database: Base de datos que contiene la tabla core_registro
    analysis_type: Tipo de análisis a ejecutar
    date_from, date_to, user_filter: Filtros opcionales
    """
    try:
        # Primero obtenemos la consulta
        query_result = generate_attendance_query(database, analysis_type, date_from, date_to, user_filter)
        
        if not query_result.get("success"):
            return query_result
        
        query = query_result["query"]
        
        # Ejecutamos la consulta
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir resultados a formato JSON serializable
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[col] = value
                    results.append(row_dict)
                
                return {
                    "success": True,
                    "database": database,
                    "analysis_type": analysis_type,
                    "filters_applied": query_result["filters_applied"],
                    "columns": columns,
                    "results": results,
                    "row_count": len(results),
                    "executed_query": query,
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def validate_attendance_data(database: str, data_issues: str) -> Dict[str, Any]:
    """
    Ejecuta validaciones para identificar problemas en los datos de asistencia.
    
    database: Base de datos que contiene la tabla core_registro
    data_issues: 'duplicates', 'same_time_events', 'invalid_sequences', 'time_gaps'
    """
    try:
        validation_queries = {
            "duplicates": """
                SELECT usuario_id, nombre, tiempo, evento, COUNT(*) as duplicados
                FROM core_registro 
                GROUP BY usuario_id, tiempo, evento
                HAVING COUNT(*) > 1
                ORDER BY duplicados DESC;
            """,
            
            "same_time_events": """
                SELECT r1.nombre, r1.tiempo, r1.evento as evento1, r2.evento as evento2,
                       r1.lugar, r1.dispositivo
                FROM core_registro r1
                JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id 
                    AND r1.tiempo = r2.tiempo 
                    AND r1.id != r2.id
                ORDER BY r1.tiempo DESC;
            """,
            
            "invalid_sequences": """
                SELECT r1.nombre, r1.codigo_usuario,
                       r1.tiempo as evento1_tiempo, r1.evento as evento1,
                       r2.tiempo as evento2_tiempo, r2.evento as evento2
                FROM core_registro r1
                JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id
                WHERE r1.evento = r2.evento 
                    AND r2.tiempo > r1.tiempo
                    AND NOT EXISTS (
                        SELECT 1 FROM core_registro r3 
                        WHERE r3.usuario_id = r1.usuario_id 
                            AND r3.tiempo > r1.tiempo 
                            AND r3.tiempo < r2.tiempo
                    )
                ORDER BY r1.tiempo DESC
                LIMIT 50;
            """,
            
            "time_gaps": """
                SELECT 
                    r1.nombre, r1.codigo_usuario,
                    DATE(r1.tiempo) as fecha,
                    r1.tiempo as entrada,
                    r2.tiempo as salida,
                    TIMESTAMPDIFF(HOUR, r1.tiempo, r2.tiempo) as horas_diferencia
                FROM core_registro r1
                JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id
                    AND DATE(r1.tiempo) = DATE(r2.tiempo)
                    AND r1.estado_id = 1 
                    AND r2.estado_id = 2
                    AND r2.tiempo > r1.tiempo
                WHERE TIMESTAMPDIFF(HOUR, r1.tiempo, r2.tiempo) > 12
                    OR TIMESTAMPDIFF(MINUTE, r1.tiempo, r2.tiempo) < 30
                ORDER BY horas_diferencia DESC
                LIMIT 50;
            """
        }
        
        if data_issues not in validation_queries:
            return {
                "success": False,
                "error": f"Tipo de validación no válido. Opciones: {', '.join(validation_queries.keys())}",
                "timestamp": datetime.now().isoformat()
            }
        
        query = validation_queries[data_issues]
        
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir resultados
                results = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[col] = value
                    results.append(row_dict)
                
                return {
                    "success": True,
                    "database": database,
                    "validation_type": data_issues,
                    "columns": columns,
                    "issues_found": results,
                    "issue_count": len(results),
                    "executed_query": query.strip(),
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "validation_type": data_issues,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
def create_attendance_kpis(database: str) -> Dict[str, Any]:
    """
    Calcula KPIs (indicadores clave) de asistencia para los últimos 30 días.
    
    database: Base de datos que contiene la tabla core_registro
    """
    try:
        kpi_results = {}
        
        with get_db_connection(database) as conn:
            with conn.cursor() as cursor:
                
                # 1. Tasa de puntualidad
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN TIME(tiempo) <= '08:10:00' THEN 1 END) as puntuales,
                        COUNT(CASE WHEN estado_id = 1 THEN 1 END) as total_entradas
                    FROM core_registro 
                    WHERE tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        AND estado_id = 1;
                """)
                punctuality = cursor.fetchone()
                
                if punctuality and punctuality[1] > 0:
                    punctuality_rate = round((punctuality[0] / punctuality[1]) * 100, 2)
                    kpi_results["punctuality_rate"] = {
                        "percentage": punctuality_rate,
                        "punctual_arrivals": punctuality[0],
                        "total_arrivals": punctuality[1]
                    }
                
                # 2. Promedio de horas trabajadas
                cursor.execute("""
                    SELECT AVG(horas_trabajadas) as promedio_horas
                    FROM (
                        SELECT 
                            TIMESTAMPDIFF(MINUTE, r1.tiempo, r2.tiempo) / 60.0 as horas_trabajadas
                        FROM core_registro r1
                        JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id
                            AND DATE(r1.tiempo) = DATE(r2.tiempo)
                            AND r1.estado_id = 1 
                            AND r2.estado_id = 2
                            AND r2.tiempo > r1.tiempo
                        WHERE r1.tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ) horas_diarias;
                """)
                avg_hours = cursor.fetchone()
                
                if avg_hours and avg_hours[0]:
                    kpi_results["average_work_hours"] = round(float(avg_hours[0]), 2)
                
                # 3. Días con registros de asistencia
                cursor.execute("""
                    SELECT COUNT(DISTINCT DATE(tiempo)) as dias_activos
                    FROM core_registro 
                    WHERE tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        AND estado_id = 1;
                """)
                active_days = cursor.fetchone()
                
                if active_days:
                    kpi_results["active_days_last_30"] = active_days[0]
                
                # 4. Usuarios únicos activos
                cursor.execute("""
                    SELECT COUNT(DISTINCT usuario_id) as usuarios_activos
                    FROM core_registro 
                    WHERE tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
                """)
                active_users = cursor.fetchone()
                
                if active_users:
                    kpi_results["active_users_last_30"] = active_users[0]
                
                return {
                    "success": True,
                    "database": database,
                    "period": "Últimos 30 días",
                    "kpis": kpi_results,
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": database,
            "timestamp": datetime.now().isoformat()
        }


# Recursos para información del servidor
@mcp.resource("mariadb://connection_info")
def get_connection_info() -> str:
    """Obtener información de configuración de conexión (sin contraseña)"""
    safe_config = {
        "host": DB_CONFIG['host'],
        "user": DB_CONFIG['user'],
        "charset": DB_CONFIG['charset'],
        "autocommit": DB_CONFIG['autocommit'],
        "password": "***"
    }
    return json.dumps(safe_config, indent=2)


@mcp.resource("attendance://schema")
def get_attendance_schema() -> str:
    """Obtiene el esquema de la tabla core_registro para análisis de asistencia"""
    schema = {
        "core_registro": {
            "id": "BIGINT PRIMARY KEY AUTO_INCREMENT",
            "tiempo": "DATETIME(6) - Fecha y hora del registro",
            "lugar": "VARCHAR(100) - Ubicación del registro",
            "dispositivo": "VARCHAR(100) - Dispositivo usado para el registro",
            "punto_evento": "VARCHAR(100) - Punto donde ocurrió el evento",
            "verificacion": "VARCHAR(100) - Método de verificación usado",
            "evento": "VARCHAR(100) - Tipo de evento (entrada/salida)",
            "estado_id": "BIGINT FK - Referencia a core_estado",
            "usuario_id": "BIGINT FK - Referencia a core_usuario", 
            "nombre": "VARCHAR(255) - Nombre del usuario",
            "codigo_usuario": "VARCHAR(100) - Código identificador del usuario"
        }
    }
    return json.dumps(schema, indent=2)


@mcp.resource("attendance://help")
def get_attendance_help() -> str:
    """Guía de uso para las herramientas de análisis de asistencia"""
    help_text = """
    HERRAMIENTAS DE ANÁLISIS DE ASISTENCIA
    
    1. generate_attendance_query: Genera consultas SQL para análisis específicos
       - daily_summary: Resumen diario de registros
       - late_arrivals: Llegadas tardías (después de 8:30 AM)
       - missing_exits: Entradas sin salida correspondiente
       - user_pattern: Patrones de comportamiento por usuario
       - device_usage: Análisis de uso de dispositivos/lugares
       - hourly_distribution: Distribución por horas del día
       
    2. execute_attendance_analysis: Ejecuta análisis y devuelve resultados
       - Combina generate_attendance_query + execute_query
       - Devuelve datos formateados listos para usar
       
    3. validate_attendance_data: Validación de calidad de datos
       - duplicates: Registros duplicados
       - same_time_events: Eventos simultáneos (posibles errores)
       - invalid_sequences: Secuencias inválidas (doble entrada, etc.)
       - time_gaps: Gaps de tiempo inusuales
       
    4. create_attendance_kpis: Calcula KPIs organizacionales
       - Tasa de puntualidad
       - Promedio de horas trabajadas
       - Días activos y usuarios únicos
    
    FILTROS DISPONIBLES:
    - date_from/date_to: Rango de fechas (YYYY-MM-DD)
    - user_filter: Filtro por nombre o código de usuario
    
    EJEMPLOS DE USO:
    - execute_attendance_analysis("mi_db", "daily_summary", "2024-01-01", "2024-01-31")
    - validate_attendance_data("mi_db", "duplicates")
    - create_attendance_kpis("mi_db")
    """
    return help_text


@mcp.resource("mariadb://status")
def get_server_status() -> str:
    """Obtener estado actual del servidor MariaDB"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW STATUS LIKE 'Uptime'")
                uptime = cursor.fetchone()
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                connections = cursor.fetchone()
                cursor.execute("SHOW STATUS LIKE 'Questions'")
                questions = cursor.fetchone()
                
                status = {
                    "uptime_seconds": uptime[1] if uptime else "unknown",
                    "active_connections": connections[1] if connections else "unknown",
                    "total_questions": questions[1] if questions else "unknown",
                    "timestamp": datetime.now().isoformat()
                }
                return json.dumps(status, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()}, indent=2)


# Entry point to run the server
if __name__ == "__main__":
    mcp.run()
