# server.py
from mcp.server.fastmcp import FastMCP
import pymysql
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def get_db_connection(database: str = None):
    """Crear conexión a la base de datos"""
    config = DB_CONFIG.copy()
    if database:
        config['database'] = database
    try:
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
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
    try:
        # Validar que sea una consulta SELECT
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return {
                "success": False,
                "error": "Solo se permiten consultas SELECT por seguridad",
                "timestamp": datetime.now().isoformat()
            }
        
        # Agregar LIMIT si no existe
        if 'LIMIT' not in query_upper:
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
