# server.py - Servidor MCP para Análisis de Registros de Asistencia
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
import json

# Crear servidor MCP especializado en registros de asistencia
mcp = FastMCP("Attendance Analysis Server")

# Configuración de la base de datos de asistencia
DB_SCHEMA = {
    "core_registro": {
        "id": "BIGINT PRIMARY KEY",
        "tiempo": "DATETIME - Fecha y hora del registro",
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

@mcp.tool()
def generate_attendance_query(analysis_type: str, date_from: str = None, date_to: str = None, user_filter: str = None) -> dict:
    """
    Genera consultas SQL optimizadas para análisis de asistencia específicos.
    
    analysis_type: 'daily_summary', 'late_arrivals', 'early_departures', 'missing_exits', 'user_pattern', 'device_usage'
    date_from: Fecha inicio en formato YYYY-MM-DD
    date_to: Fecha fin en formato YYYY-MM-DD  
    user_filter: Filtro por nombre o código de usuario
    """
    
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
                COUNT(CASE WHEN evento = 'entrada' THEN 1 END) as entradas,
                COUNT(CASE WHEN evento = 'salida' THEN 1 END) as salidas
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
            WHERE evento = 'entrada' 
                AND TIME(tiempo) > '08:30:00'  -- Ajustar hora según política
                AND {where_clause}
            ORDER BY tiempo DESC;
        """,
        
        "missing_exits": f"""
            SELECT DISTINCT
                r1.nombre, r1.codigo_usuario,
                DATE(r1.tiempo) as fecha,
                TIME(r1.tiempo) as hora_entrada
            FROM core_registro r1
            WHERE r1.evento = 'entrada' 
                AND {where_clause.replace('tiempo', 'r1.tiempo')}
                AND NOT EXISTS (
                    SELECT 1 FROM core_registro r2 
                    WHERE r2.usuario_id = r1.usuario_id 
                        AND r2.evento = 'salida'
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
                AVG(CASE WHEN evento = 'entrada' THEN HOUR(tiempo) + MINUTE(tiempo)/60.0 END) as hora_promedio_entrada
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
            "error": f"Tipo de análisis no válido. Opciones: {', '.join(queries.keys())}"
        }
    
    return {
        "query": queries[analysis_type].strip(),
        "description": f"Consulta para {analysis_type}",
        "filters_applied": {
            "date_from": date_from,
            "date_to": date_to, 
            "user_filter": user_filter
        }
    }

@mcp.tool()
def validate_attendance_data(data_issues: str) -> dict:
    """
    Proporciona consultas para validar e identificar problemas en los datos de asistencia.
    
    data_issues: 'duplicates', 'same_time_events', 'invalid_sequences', 'orphan_records', 'time_gaps'
    """
    
    validation_queries = {
        "duplicates": """
            -- Registros duplicados (mismo usuario, tiempo, evento)
            SELECT usuario_id, nombre, tiempo, evento, COUNT(*) as duplicados
            FROM core_registro 
            GROUP BY usuario_id, tiempo, evento
            HAVING COUNT(*) > 1
            ORDER BY duplicados DESC;
        """,
        
        "same_time_events": """
            -- Eventos simultáneos del mismo usuario (posible error)
            SELECT r1.nombre, r1.tiempo, r1.evento as evento1, r2.evento as evento2,
                   r1.lugar, r1.dispositivo
            FROM core_registro r1
            JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id 
                AND r1.tiempo = r2.tiempo 
                AND r1.id != r2.id
            ORDER BY r1.tiempo DESC;
        """,
        
        "invalid_sequences": """
            -- Secuencias inválidas (dos entradas seguidas sin salida)
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
            ORDER BY r1.tiempo DESC;
        """,
        
        "time_gaps": """
            -- Identificar gaps de tiempo inusuales entre entrada y salida
            SELECT 
                r1.nombre, r1.codigo_usuario,
                DATE(r1.tiempo) as fecha,
                r1.tiempo as entrada,
                r2.tiempo as salida,
                TIMESTAMPDIFF(HOUR, r1.tiempo, r2.tiempo) as horas_diferencia
            FROM core_registro r1
            JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id
                AND DATE(r1.tiempo) = DATE(r2.tiempo)
                AND r1.evento = 'entrada' 
                AND r2.evento = 'salida'
                AND r2.tiempo > r1.tiempo
            WHERE TIMESTAMPDIFF(HOUR, r1.tiempo, r2.tiempo) > 12  -- Más de 12 horas
                OR TIMESTAMPDIFF(MINUTE, r1.tiempo, r2.tiempo) < 30  -- Menos de 30 minutos
            ORDER BY horas_diferencia DESC;
        """
    }
    
    if data_issues not in validation_queries:
        return {
            "error": f"Tipo de validación no válido. Opciones: {', '.join(validation_queries.keys())}"
        }
    
    return {
        "query": validation_queries[data_issues].strip(),
        "description": f"Validación para detectar: {data_issues}",
        "purpose": "Identificar inconsistencias en los datos de asistencia"
    }

@mcp.tool()
def create_attendance_kpis() -> dict:
    """
    Genera consultas para KPIs (indicadores clave) de asistencia comunes en organizaciones.
    """
    
    kpi_queries = {
        "punctuality_rate": """
            -- Tasa de puntualidad (llegadas antes de las 8:30)
            SELECT 
                'Puntualidad' as kpi,
                ROUND(
                    (COUNT(CASE WHEN TIME(tiempo) <= '08:30:00' THEN 1 END) * 100.0 / 
                     COUNT(CASE WHEN evento = 'entrada' THEN 1 END)), 2
                ) as porcentaje,
                COUNT(CASE WHEN evento = 'entrada' THEN 1 END) as total_entradas
            FROM core_registro 
            WHERE tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
        """,
        
        "attendance_rate": """
            -- Tasa de asistencia (días con al menos una entrada)
            SELECT 
                'Asistencia' as kpi,
                COUNT(DISTINCT DATE(tiempo)) as dias_con_registros,
                (SELECT COUNT(*) FROM (
                    SELECT DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 30 DAY), INTERVAL n DAY) as fecha
                    FROM (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION 
                          SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1
                    CROSS JOIN (SELECT 0 as n UNION SELECT 10 UNION SELECT 20) t2
                    WHERE WEEKDAY(DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 30 DAY), INTERVAL (t1.n + t2.n) DAY)) < 5
                    AND DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 30 DAY), INTERVAL (t1.n + t2.n) DAY) <= CURDATE()
                ) dias_laborales) as dias_laborales_totales
            FROM core_registro 
            WHERE tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                AND evento = 'entrada';
        """,
        
        "average_work_hours": """
            -- Promedio de horas trabajadas por día
            SELECT 
                'Horas Promedio' as kpi,
                ROUND(AVG(horas_trabajadas), 2) as promedio_horas_diarias
            FROM (
                SELECT 
                    DATE(r1.tiempo) as fecha,
                    r1.usuario_id,
                    TIMESTAMPDIFF(MINUTE, r1.tiempo, r2.tiempo) / 60.0 as horas_trabajadas
                FROM core_registro r1
                JOIN core_registro r2 ON r1.usuario_id = r2.usuario_id
                    AND DATE(r1.tiempo) = DATE(r2.tiempo)
                    AND r1.evento = 'entrada' 
                    AND r2.evento = 'salida'
                    AND r2.tiempo > r1.tiempo
                WHERE r1.tiempo >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ) horas_diarias;
        """
    }
    
    return {
        "kpi_queries": kpi_queries,
        "description": "Consultas para indicadores clave de asistencia",
        "period": "Últimos 30 días"
    }

# Recursos específicos para información del sistema de asistencia
@mcp.resource("schema://attendance")
def get_attendance_schema() -> str:
    """Obtiene el esquema completo de la base de datos de asistencia"""
    return json.dumps(DB_SCHEMA, indent=2)

@mcp.resource("help://queries")
def get_query_help() -> str:
    """Guía de uso para las herramientas de consulta de asistencia"""
    help_text = """
    GUÍA DE HERRAMIENTAS DE ASISTENCIA
    
    1. generate_attendance_query: Análisis principales
       - daily_summary: Resumen diario de registros
       - late_arrivals: Llegadas tardías
       - missing_exits: Entradas sin salida
       - user_pattern: Patrones por usuario
       - device_usage: Uso de dispositivos
       
    2. validate_attendance_data: Validación de datos
       - duplicates: Registros duplicados
       - same_time_events: Eventos simultáneos
       - invalid_sequences: Secuencias inválidas
       - time_gaps: Gaps de tiempo inusuales
       
    3. create_attendance_kpis: KPIs organizacionales
       - Tasa de puntualidad
       - Tasa de asistencia
       - Promedio de horas trabajadas
    
    FILTROS DISPONIBLES:
    - date_from/date_to: Rango de fechas (YYYY-MM-DD)
    - user_filter: Filtro por nombre o código de usuario
    """
    return help_text

# Entry point para ejecutar el servidor
if __name__ == "__main__":
    mcp.run() 