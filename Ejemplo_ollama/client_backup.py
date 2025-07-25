#!/usr/bin/env python3
# fixed_client.py
import asyncio
import json
import requests
import subprocess
import sys
from typing import Dict, Any, List
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import re

class OllamaMCPClient:
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434, model: str = "gemma3:12b"):
        self.ollama_base_url = f"http://{ollama_host}:{ollama_port}"
        self.model = model
        self.mcp_session = None
        self.mcp_read = None
        self.mcp_write = None
        self._stdio_client = None
        self._client_session = None
        self.conversation_history = []
        self.debug_mode = True
        
    async def __aenter__(self):
        """Context manager para gestionar la sesión MCP"""
        try:
            print("🚀 Iniciando conexión MCP...")
            
            # Configurar parámetros del servidor MCP
            server_params = StdioServerParameters(
                command="python",
                args=["server.py"],
                env=None
            )
            
            # Crear cliente y sesión que permanecerán activos
            self._stdio_client = stdio_client(server_params)
            self.mcp_read, self.mcp_write = await self._stdio_client.__aenter__()
            self._client_session = ClientSession(self.mcp_read, self.mcp_write)
            self.mcp_session = await self._client_session.__aenter__()
            
            # Inicializar el servidor
            await self.mcp_session.initialize()
            
            print("✅ Conexión MCP establecida correctamente")
            
            # Listar herramientas disponibles
            tools = await self.mcp_session.list_tools()
            print(f"🔧 Herramientas disponibles: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            
            # Cargar contexto automático de la base de datos de asistencia
            await self.load_attendance_context()
            
            return self
            
        except Exception as e:
            print(f"❌ Error estableciendo conexión MCP: {e}")
            raise

    async def load_attendance_context(self):
        """Cargar automáticamente el contexto de la base de datos de asistencia"""
        try:
            print("📊 Cargando contexto de base de datos de asistencia...")
            
            # Obtener estructura de las tablas principales
            usuarios_structure = await self.execute_mcp_tool("describe_table", database="zapopan", table="core_usuario")
            registro_structure = await self.execute_mcp_tool("describe_table", database="zapopan", table="core_registro")
            
            # Obtener métricas básicas
            usuarios_metrics = await self.execute_mcp_tool("get_table_metrics", database="zapopan", table="core_usuario")
            registro_metrics = await self.execute_mcp_tool("get_table_metrics", database="zapopan", table="core_registro")
            
            # Almacenar contexto para uso en consultas
            self.attendance_context = {
                "database": "zapopan",
                "users_table": "core_usuario",
                "attendance_table": "core_registro", 
                "users_structure": usuarios_structure,
                "attendance_structure": registro_structure,
                "users_count": usuarios_metrics.get("row_count", 0),
                "attendance_records": registro_metrics.get("row_count", 0),
                "business_rules": {
                    "late_threshold": "08:10:00",
                    "workdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "week_start": "Monday"
                }
            }
            
            print(f"✅ Contexto cargado: {self.attendance_context['users_count']} usuarios, {self.attendance_context['attendance_records']} registros")
            
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo cargar contexto de asistencia: {e}")
            self.attendance_context = None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cerrar conexión MCP"""
        try:
            if hasattr(self, '_client_session') and self._client_session:
                await self._client_session.__aexit__(exc_type, exc_val, exc_tb)
            if hasattr(self, '_stdio_client') and self._stdio_client:
                await self._stdio_client.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            print(f"⚠️  Error cerrando conexión MCP: {e}")
    
    def call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Llamar a Ollama con un prompt"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Agregar historial de conversación
            messages.extend(self.conversation_history[-6:])
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result["message"]["content"]
                
                # Agregar al historial
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                return assistant_response
            else:
                return f"Error en Ollama: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error conectando con Ollama: {e}"
    
    async def execute_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar una herramienta usando MCP real"""
        try:
            if not self.mcp_session:
                return {"success": False, "error": "Sesión MCP no inicializada"}
            
            # DEBUG: Capturar exactamente qué se envía al MCP
            if tool_name == 'execute_query' and 'query' in kwargs:
                print(f"🔍 DEBUG - MCP Tool Call:")
                print(f"   Tool: {tool_name}")
                print(f"   Query enviada: '{kwargs['query']}'")
                print(f"   Query length: {len(kwargs['query'])} chars")
                print(f"   Database: {kwargs.get('database', 'None')}")
                # Verificar caracteres no imprimibles
                clean_query = ''.join(c if ord(c) >= 32 and ord(c) < 127 else f'\\x{ord(c):02x}' for c in kwargs['query'])
                if clean_query != kwargs['query']:
                    print(f"   Query with non-printable chars: '{clean_query}'")
            
            # Usar la sesión MCP para llamar a la herramienta
            result = await self.mcp_session.call_tool(tool_name, kwargs)
            
            # Convertir el resultado a dict si es necesario
            if hasattr(result, 'content'):
                # Extraer contenido del resultado MCP
                tool_result = result.content[0].text if result.content else {}
                try:
                    return json.loads(tool_result)
                except json.JSONDecodeError:
                    return {"success": True, "data": tool_result}
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_with_ai(self, question: str) -> str:
        """Analizar una pregunta y ejecutar las herramientas necesarias usando IA con contexto de asistencia laboral"""
        
        # System prompt especializado para análisis de asistencia laboral
        system_prompt = f"""ERES UN SISTEMA AUTOMATIZADO DE CONSULTAS SQL. DEBES RESPONDER SOLO CON COMANDOS EJECUTABLES.

IMPORTANTE: Para CUALQUIER pregunta sobre asistencia, responde ÚNICAMENTE con comandos USAR_HERRAMIENTA_MCP.

BASE DE DATOS: zapopan - Tabla: core_registro
CAMPOS: id, tiempo, nombre, estado_id, usuario_id
REGLAS: estado_id=1 (Entrada), estado_id=2 (Salida), Retardo >08:10:00, Solo días laborales WEEKDAY<5

RESPUESTAS OBLIGATORIAS:

Para "¿Quién se registró hoy?" o "¿Quién vino hoy?":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre FROM core_registro WHERE DATE(tiempo) = CURDATE() AND estado_id = 1 LIMIT 20")

Para "¿Quién llegó tarde hoy?":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre FROM core_registro WHERE estado_id = 1 AND TIME(tiempo) > '08:10:00' AND TIME(tiempo) < '12:00:00' AND DATE(tiempo) = CURDATE() LIMIT 20")

Para "¿Cuántos retardos hubo hoy?":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT COUNT(*) as total_retardos FROM core_registro WHERE estado_id = 1 AND TIME(tiempo) > '08:10:00' AND TIME(tiempo) < '12:00:00' AND DATE(tiempo) = CURDATE() LIMIT 1")

Para "¿Quién llegó tarde esta semana?" o "última semana":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre FROM core_registro WHERE estado_id = 1 AND tiempo > CONCAT(DATE(tiempo), ' 08:10:00') AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) LIMIT 20")

Para "¿Quiénes se registraron esta semana?" o "última semana":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT DISTINCT nombre FROM core_registro WHERE estado_id = 1 AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) LIMIT 20")

Para análisis de "[nombre]":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre, DATE(tiempo) as fecha, HOUR(tiempo) as hora, MINUTE(tiempo) as minuto, CASE WHEN TIME(tiempo) <= '08:10:00' THEN 'Puntual' WHEN TIME(tiempo) > '08:10:00' AND TIME(tiempo) < '12:00:00' THEN 'Retardo' ELSE 'Entrada tardía' END as estado FROM core_registro WHERE nombre LIKE '%[nombre]%' AND estado_id = 1 ORDER BY tiempo DESC LIMIT 10")

Para "conteo" o "cuántos registros":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre, COUNT(*) as total FROM core_registro GROUP BY nombre ORDER BY total DESC LIMIT 10")

Para "conteo de entradas":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT nombre, COUNT(*) as total FROM core_registro WHERE estado_id = 1 GROUP BY nombre ORDER BY total DESC LIMIT 10")

Para "cuántos retardos":
USAR_HERRAMIENTA_MCP: execute_query(database="zapopan", query="SELECT COUNT(*) as retardos FROM core_registro WHERE estado_id = 1 AND TIME(tiempo) > '08:10:00' AND TIME(tiempo) < '12:00:00' AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) LIMIT 1")

NO DES EXPLICACIONES. NO ESCRIBAS SQL MANUAL. SOLO RESPONDE CON USAR_HERRAMIENTA_MCP.

FECHAS IMPORTANTES:
- Los datos están en 2025, NO en 2024
- Para "julio" usa: BETWEEN '2025-07-01' AND '2025-07-31'
- Para "esta semana" usa: DATE_SUB(CURDATE(), INTERVAL 7 DAY)
- Para "hoy" usa: CURDATE()

EJEMPLOS ADICIONALES:
- "resumen" → Usa get_weekly_attendance_summary 
- "métricas" → Usa consultas de conteo y promedios
- Nombres parciales → Usa LIKE '%nombre%'
- Fechas específicas → SIEMPRE usa año 2025"""

        # Obtener respuesta de la IA
        ai_response = self.call_ollama(question, system_prompt)
        
        # Filtrar bloques de thinking y texto irrelevante
        ai_response = ai_response.replace('<think>', '').replace('</think>', '')
        # Eliminar cualquier texto antes de la primera herramienta MCP
        if 'USAR_HERRAMIENTA_MCP:' in ai_response:
            parts = ai_response.split('USAR_HERRAMIENTA_MCP:', 1)
            ai_response = 'USAR_HERRAMIENTA_MCP:' + parts[1]
        
        # Procesar respuesta para extraer comandos de herramientas MCP
        lines = ai_response.split('\n')
        result_parts = []
        found_mcp_tool = False
        
        for line in lines:
            line_clean = line.strip()
            
            # Detectar herramientas MCP
            if 'USAR_HERRAMIENTA_MCP:' in line_clean:
                found_mcp_tool = True
                tool_call = line_clean.split('USAR_HERRAMIENTA_MCP:', 1)[1].strip()
                tool_call = tool_call.replace('**', '').strip()
                
                try:
                    if self.debug_mode:
                        print(f"\n🔧 Ejecutando: {tool_call}")
                    
                    # DEBUG: Imprimir consulta SQL exacta
                    if 'execute_query' in tool_call and 'query=' in tool_call:
                        query_start = tool_call.find('query="') + 7
                        query_end = tool_call.rfind('")')
                        if query_start > 6 and query_end > query_start:
                            extracted_query = tool_call[query_start:query_end]
                            print(f"🔍 DEBUG - SQL exacto generado por Gemma:")
                            print(f"   Query: {extracted_query}")
                            print(f"   Longitud: {len(extracted_query)} caracteres")
                    
                    # Parsear y ejecutar la herramienta via MCP
                    tool_result = await self.parse_and_execute_mcp_tool(tool_call)
                    
                    if self.debug_mode:
                        print(f"✅ Completado exitosamente")
                    
                    # Si la herramienta fue exitosa, presentar directamente los datos con contexto de asistencia
                    if tool_result.get("success", False):
                        # Formatear resultados con contexto laboral
                        if 'results' in tool_result and tool_result['results']:
                            # Es una consulta SQL con resultados - formatear para asistencia
                            result_parts.append(f"\n**📊 Datos de Asistencia Encontrados:**")
                            for i, row in enumerate(tool_result['results'], 1):
                                formatted_row = []
                                for key, value in row.items():
                                    # Formateo especial para datos de asistencia
                                    if 'tiempo' in key.lower() or 'hora' in key.lower():
                                        if isinstance(value, str) and ':' in value:
                                            # Es una hora - verificar si es retardo
                                            try:
                                                if len(value.split(':')) >= 2:
                                                    hour_min = value.split(':')[:2]
                                                    if int(hour_min[0]) > 8 or (int(hour_min[0]) == 8 and int(hour_min[1]) > 10):
                                                        formatted_row.append(f"{key}: {value} ⚠️ (RETARDO)")
                                                    else:
                                                        formatted_row.append(f"{key}: {value} ✅ (PUNTUAL)")
                                                else:
                                                    formatted_row.append(f"{key}: {value}")
                                            except:
                                                formatted_row.append(f"{key}: {value}")
                                        else:
                                            formatted_row.append(f"{key}: {value}")
                                    else:
                                        formatted_row.append(f"{key}: {value}")
                                result_parts.append(f"{i}. {' | '.join(formatted_row)}")
                            
                            # Agregar métricas automáticas si hay datos de tiempo
                            if any('tiempo' in str(row) or 'hora' in str(row) for row in tool_result['results']):
                                total_registros = len(tool_result['results'])
                                retardos = sum(1 for row in tool_result['results'] 
                                             for key, value in row.items() 
                                             if ('tiempo' in key.lower() or 'hora' in key.lower()) and isinstance(value, str) and ':' in value
                                             and self._is_late(value))
                                puntuales = total_registros - retardos
                                puntualidad_pct = (puntuales / total_registros * 100) if total_registros > 0 else 0
                                
                                result_parts.append(f"\n**📈 Métricas de Puntualidad:**")
                                result_parts.append(f"• Total registros: {total_registros}")
                                result_parts.append(f"• Llegadas puntuales: {puntuales} ✅")
                                result_parts.append(f"• Retardos: {retardos} ⚠️")
                                result_parts.append(f"• % Puntualidad: {puntualidad_pct:.1f}%")
                            
                            result_parts.append(f"\n**📋 Total encontrado:** {tool_result.get('row_count', len(tool_result['results']))} registros")
                        elif 'columns' in tool_result and isinstance(tool_result['columns'], list) and len(tool_result['columns']) > 0 and isinstance(tool_result['columns'][0], dict):
                            # Es describe_table con estructura de columnas
                            result_parts.append(f"\n**🏗️ Estructura de tabla encontrada:**")
                            for col in tool_result['columns']:
                                col_desc = f"- {col.get('field', 'campo')}: {col.get('type', 'tipo')}"
                                if col.get('field') == 'tiempo':
                                    col_desc += " 🕐 (Campo de hora de registro)"
                                elif 'usuario' in col.get('field', '').lower():
                                    col_desc += " 👤 (Referencia a usuario)"
                                result_parts.append(col_desc)
                        elif 'results' in tool_result and not tool_result['results']:
                            # Consulta SQL sin resultados
                            result_parts.append(f"\n**❌ No se encontraron registros de asistencia** para la consulta realizada.")
                            result_parts.append("💡 Sugerencias:")
                            result_parts.append("• Verifica que haya registros en el período consultado")
                            result_parts.append("• Confirma que los nombres estén escritos correctamente")
                            result_parts.append("• Prueba con rangos de fechas más amplios")
                        else:
                            result_parts.append(f"\n**📋 Resultado:** {json.dumps(tool_result, indent=2, ensure_ascii=False)}")
                    else:
                        result_parts.append(f"❌ Error en la herramienta MCP: {tool_result.get('error', 'Error desconocido')}")
                    
                except Exception as e:
                    result_parts.append(f"❌ Error ejecutando MCP {tool_call}: {e}")
                    print(f"Error detallado: {e}")
            else:
                # Si no hemos encontrado herramientas MCP, incluir texto normal
                # Si ya encontramos herramientas MCP, ignorar texto adicional de Ollama para evitar alucinaciones
                if not found_mcp_tool and line_clean:
                    # Solo incluir líneas que no sean prefijos técnicos
                    if not any(line_clean.startswith(prefix) for prefix in ['🔧', '📊', '🤖', '❌', 'USAR_HERRAMIENTA_MCP']):
                        result_parts.append(line)
        
        return '\n'.join(result_parts)
    
    def _is_late(self, time_str: str) -> bool:
        """Verificar si una hora representa un retardo (después de 08:10)"""
        try:
            if ':' in time_str:
                hour_min = time_str.split(':')[:2]
                hour = int(hour_min[0])
                minute = int(hour_min[1])
                return hour > 8 or (hour == 8 and minute > 10)
        except:
            pass
        return False
    
    async def get_weekly_attendance_summary(self) -> str:
        """Obtener un resumen automático de asistencia semanal"""
        try:
            print("\n📊 Generando resumen semanal de asistencia...")
            
            # Métricas generales de la semana (CORREGIDO con estado_id)
            metrics_query = """
            SELECT 
                COUNT(*) as total_entradas,
                COUNT(DISTINCT usuario_id) as empleados_distintos,
                SUM(CASE WHEN TIME(tiempo) <= '08:10:00' THEN 1 ELSE 0 END) as llegadas_puntuales,
                SUM(CASE WHEN TIME(tiempo) > '08:10:00' AND TIME(tiempo) < '12:00:00' THEN 1 ELSE 0 END) as retardos,
                MIN(DATE(tiempo)) as primer_dia,
                MAX(DATE(tiempo)) as ultimo_dia,
                AVG(TIME_TO_SEC(TIME(tiempo))) as promedio_segundos,
                AVG(TIMESTAMPDIFF(MINUTE, TIME('08:10:00'), TIME(tiempo))) as promedio_minutos_retardo
            FROM core_registro 
            WHERE estado_id = 1 
                AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
                AND WEEKDAY(tiempo) < 5
                AND TIME(tiempo) < '12:00:00'
            """
            
            # Top llegadas más tardías (CORREGIDO con estado_id)
            late_arrivals_query = """
            SELECT 
                nombre, 
                DATE(tiempo) as fecha,
                TIME(tiempo) as hora,
                TIMESTAMPDIFF(MINUTE, TIME('08:10:00'), TIME(tiempo)) as minutos_retardo
            FROM core_registro 
            WHERE estado_id = 1
                AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) 
                AND TIME(tiempo) > '08:10:00'
                AND TIME(tiempo) < '12:00:00'
                AND WEEKDAY(tiempo) < 5
            ORDER BY TIME(tiempo) DESC 
            LIMIT 5
            """
            
            # Personas más puntuales (CORREGIDO con estado_id)
            punctual_people_query = """
            SELECT 
                nombre,
                COUNT(*) as total_entradas,
                SUM(CASE WHEN TIME(tiempo) <= '08:10:00' THEN 1 ELSE 0 END) as dias_puntuales,
                ROUND(SUM(CASE WHEN TIME(tiempo) <= '08:10:00' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as porcentaje_puntualidad
            FROM core_registro 
            WHERE estado_id = 1
                AND DATE(tiempo) >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
                AND WEEKDAY(tiempo) < 5
                AND TIME(tiempo) < '12:00:00'
            GROUP BY usuario_id, nombre
            HAVING COUNT(*) >= 2
            ORDER BY porcentaje_puntualidad DESC, dias_puntuales DESC
            LIMIT 5
            """
            
            # Ejecutar consultas
            metrics_result = await self.execute_mcp_tool("execute_query", 
                                                        database="zapopan", 
                                                        query=metrics_query)
            
            late_result = await self.execute_mcp_tool("execute_query", 
                                                     database="zapopan", 
                                                     query=late_arrivals_query)
            
            punctual_result = await self.execute_mcp_tool("execute_query", 
                                                         database="zapopan", 
                                                         query=punctual_people_query)
            
            # Formatear respuesta
            summary_parts = []
            summary_parts.append("📊 **RESUMEN SEMANAL DE ASISTENCIA**")
            summary_parts.append("=" * 50)
            
            if metrics_result.get("success") and metrics_result.get("results"):
                metrics = metrics_result["results"][0]
                total_entradas = metrics.get("total_entradas", 0)
                empleados_distintos = metrics.get("empleados_distintos", 0)
                puntuales = metrics.get("llegadas_puntuales", 0)
                retardos = metrics.get("retardos", 0)
                promedio_seg = metrics.get("promedio_segundos", 0)
                promedio_min_retardo = metrics.get("promedio_minutos_retardo", 0)
                
                # Convertir promedio de segundos a formato hora
                if promedio_seg:
                    horas = int(promedio_seg // 3600)
                    minutos = int((promedio_seg % 3600) // 60)
                    promedio_hora = f"{horas:02d}:{minutos:02d}"
                else:
                    promedio_hora = "N/A"
                
                porcentaje_puntualidad = (puntuales / total_entradas * 100) if total_entradas > 0 else 0
                
                summary_parts.append(f"\n📈 **MÉTRICAS SEMANALES (SOLO ENTRADAS):**")
                summary_parts.append(f"• Total de entradas registradas: {total_entradas}")
                summary_parts.append(f"• Empleados que asistieron: {empleados_distintos}")
                summary_parts.append(f"• Llegadas puntuales (≤08:10): {puntuales} ✅")
                summary_parts.append(f"• Retardos (>08:10 y <12:00): {retardos} ⚠️")
                summary_parts.append(f"• % Puntualidad general: {porcentaje_puntualidad:.1f}%")
                summary_parts.append(f"• Hora promedio de llegada: {promedio_hora}")
                if promedio_min_retardo and promedio_min_retardo > 0:
                    summary_parts.append(f"• Promedio minutos de retardo: {promedio_min_retardo:.1f} min")
                
                # Evaluación de rendimiento
                if porcentaje_puntualidad >= 90:
                    summary_parts.append(f"• **Evaluación: EXCELENTE** 🌟")
                elif porcentaje_puntualidad >= 80:
                    summary_parts.append(f"• **Evaluación: BUENA** 👍")
                elif porcentaje_puntualidad >= 70:
                    summary_parts.append(f"• **Evaluación: REGULAR** ⚠️")
                else:
                    summary_parts.append(f"• **Evaluación: NECESITA MEJORA** 🚨")
            
            # Top retardos (ACTUALIZADO con minutos de retardo)
            if late_result.get("success") and late_result.get("results"):
                summary_parts.append(f"\n⚠️ **TOP 5 LLEGADAS MÁS TARDÍAS:**")
                for i, late in enumerate(late_result["results"], 1):
                    nombre = late.get('nombre', '')
                    fecha = late.get('fecha', '')
                    hora = late.get('hora', '')
                    minutos_retardo = late.get('minutos_retardo', 0)
                    if minutos_retardo:
                        summary_parts.append(f"{i}. {nombre} - {fecha} a las {hora} (+{minutos_retardo:.0f} min)")
                    else:
                        summary_parts.append(f"{i}. {nombre} - {fecha} a las {hora}")
            
            # Top puntuales (ACTUALIZADO con nombres de campos corregidos)
            if punctual_result.get("success") and punctual_result.get("results"):
                summary_parts.append(f"\n✅ **TOP 5 EMPLEADOS MÁS PUNTUALES:**")
                for i, person in enumerate(punctual_result["results"], 1):
                    nombre = person.get('nombre', '')
                    porcentaje = person.get('porcentaje_puntualidad', 0)
                    dias_puntuales = person.get('dias_puntuales', 0)
                    total_entradas = person.get('total_entradas', 0)
                    summary_parts.append(f"{i}. {nombre} - {porcentaje}% ({dias_puntuales}/{total_entradas} entradas)")
            
            summary_parts.append("\n" + "=" * 50)
            return '\n'.join(summary_parts)
            
        except Exception as e:
            return f"❌ Error generando resumen semanal: {e}"
    
    async def parse_and_execute_mcp_tool(self, tool_call: str) -> Dict[str, Any]:
        """Parsear y ejecutar una llamada a herramienta MCP de forma robusta"""
        try:
            # Extraer nombre de la función y parámetros
            if '(' in tool_call:
                tool_name = tool_call.split('(')[0].strip()
                params_str = tool_call.split('(', 1)[1].rsplit(')', 1)[0].strip()
                
                # Parsear parámetros usando eval seguro para casos simples
                kwargs = {}
                if params_str:
                    try:
                        # Parsing seguro usando ast.literal_eval para casos simples
                        import ast
                        # Intentar evaluar como diccionario literal
                        if params_str.startswith('{') and params_str.endswith('}'):
                            kwargs = ast.literal_eval(params_str)
                        else:
                            # Construir diccionario seguro manualmente
                            kwargs = {}
                            for param in params_str.split(','):
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    key = key.strip()
                                    value = value.strip().strip('\'"')
                                    # Validación de tipos segura
                                    if value.isdigit():
                                        kwargs[key] = int(value)
                                    elif value.replace('.', '', 1).isdigit():
                                        kwargs[key] = float(value)
                                    elif value.lower() in ['true', 'false']:
                                        kwargs[key] = value.lower() == 'true'
                                    elif value.lower() == 'none':
                                        kwargs[key] = None
                                    else:
                                        kwargs[key] = value
                    except:
                        # Fallback al parsing manual si eval falla
                        import re
                        # Patrón corregido que maneja strings SQL complejos con comas
                        param_pattern = r'(\w+)=(["\'])([^"\']*?)\2(?=\s*[,)]|$)|(\w+)=([^,\s)]+)'
                        matches = re.findall(param_pattern, params_str)
                        
                        # Si el regex falla, usar método manual más robusto
                        if not matches and 'query=' in params_str:
                            # Parsing manual específico para query con strings SQL complejos
                            parts = {}
                            query_start = params_str.find('query="')
                            if query_start != -1:
                                query_start += 7  # len('query="')
                                quote_count = 0
                                query_end = query_start
                                for i, char in enumerate(params_str[query_start:], query_start):
                                    if char == '"' and (i == query_start or params_str[i-1] != '\\'):
                                        quote_count += 1
                                        if quote_count == 1:  # Encontramos el cierre
                                            query_end = i
                                            break
                                
                                if query_end > query_start:
                                    parts['query'] = params_str[query_start:query_end]
                                    
                                    # Extraer database también
                                    db_match = re.search(r'database=(["\'])([^"\']*?)\1', params_str)
                                    if db_match:
                                        parts['database'] = db_match.group(2)
                                    
                                                                                                          # Usar parts como kwargs
                                 kwargs = parts
                         
                         # Solo procesar matches si no usamos el parsing manual
                         if not ('query' in kwargs and len(kwargs) >= 1):
                             for match in matches:
                            if match[0]:  # String quoted
                                key, _, value = match[0], match[1], match[2]
                            else:  # Unquoted value
                                key, value = match[3], match[4]
                            
                            # Convertir tipos básicos
                            if value.isdigit():
                                kwargs[key] = int(value)
                            elif value.replace('.', '', 1).isdigit():
                                kwargs[key] = float(value)
                            elif value.lower() in ['true', 'false']:
                                kwargs[key] = value.lower() == 'true'
                            elif value.lower() == 'none':
                                kwargs[key] = None
                            else:
                                kwargs[key] = value
                
                return await self.execute_mcp_tool(tool_name, **kwargs)
            else:
                return await self.execute_mcp_tool(tool_call)
                
        except Exception as e:
            return {"success": False, "error": f"Error parseando herramienta MCP: {e}"}
    
    def _parse_mcp_params_robust(self, params_str: str) -> Dict[str, Any]:
        """Parser robusto para parámetros MCP que maneja strings SQL complejos"""
        params = {}
        
        # Parsing específico para execute_query con query SQL
        if 'query=' in params_str:
            # Encontrar database
            db_match = re.search(r'database=(["\'])(.*?)\1', params_str)
            if db_match:
                params['database'] = db_match.group(2)
            
            # Encontrar query (más complejo porque puede tener comas)
            query_match = re.search(r'query=(["\'])(.*)\1(?:\s*\)|$)', params_str, re.DOTALL)
            if query_match:
                params['query'] = query_match.group(2)
            
            # Encontrar limit si existe
            limit_match = re.search(r'limit=(\d+)', params_str)
            if limit_match:
                params['limit'] = int(limit_match.group(1))
        
        return params
    
    async def interactive_session(self):
        """Sesión interactiva con el usuario usando MCP real con contexto de asistencia laboral"""
        print("=" * 70)
        print("🏢 ASISTENTE ESPECIALIZADO EN ANÁLISIS DE ASISTENCIA LABORAL")
        print("=" * 70)
        print("Conectado a:")
        print(f"  📊 Base de datos: zapopan (MariaDB 172.16.1.29)")
        print(f"  🦙 IA: Ollama {self.ollama_base_url} ({self.model})")
        print(f"  🔧 Protocolo: MCP (Model Context Protocol)")
        print("=" * 70)
        
        # Conectar a MCP
        async with self: # Usar el context manager para la conexión MCP
            if not self.mcp_session:
                print("❌ No se pudo establecer conexión MCP")
                return
            
            # Probar conexión inicial via MCP
            print("🔍 Probando conexión a la base de datos via MCP...")
            connection_test = await self.execute_mcp_tool("test_connection")
            if connection_test.get("success"):
                print("✅ Conexión a MariaDB via MCP exitosa")
                print(f"   Versión: {connection_test.get('server_version', 'Desconocida')}")
            else:
                print("❌ Error conectando a MariaDB via MCP")
                print(f"   {connection_test.get('error', 'Error desconocido')}")
            
            # Mostrar información del contexto cargado
            if hasattr(self, 'attendance_context') and self.attendance_context:
                print("\n📋 CONTEXTO DE ASISTENCIA CARGADO:")
                print(f"   👥 Usuarios registrados: {self.attendance_context['users_count']}")
                print(f"   📊 Registros de asistencia: {self.attendance_context['attendance_records']}")
                print(f"   🕐 Horario límite sin retardo: {self.attendance_context['business_rules']['late_threshold']}")
                print(f"   📅 Días laborales: Lunes a Viernes")
            
            print("\n💡 EJEMPLOS DE CONSULTAS ESPECIALIZADAS:")
            
            print("\n   🔥 ANÁLISIS PRIORITARIOS (Más Útiles):")
            print("     • ¿Quién llegó tarde esta semana?")
            print("     • Dame las métricas semanales de puntualidad")
            print("     • ¿Cuántas personas vinieron hoy?")
            print("     • Resumen de asistencia de esta semana")
            print("     • ¿Quién es la persona más puntual esta semana?")
            
            print("\n   📊 ANÁLISIS DIARIOS:")
            print("     • ¿Quién se registró hoy?")
            print("     • ¿Cuántos retardos hubo hoy?")
            print("     • ¿A qué hora llegó [nombre de persona]?")
            print("     • Lista de llegadas de hoy ordenadas por hora")
            
            print("\n   📈 MÉTRICAS Y ESTADÍSTICAS:")
            print("     • Porcentaje de puntualidad semanal")
            print("     • ¿Cuál es el promedio de hora de llegada?")
            print("     • ¿Qué día de la semana hay más retardos?")
            print("     • Estadísticas de asistencia por persona")
            
            print("\n   👤 BÚSQUEDAS INDIVIDUALES:")
            print("     • Historial de [nombre de persona]")
            print("     • ¿Cuántas veces llegó tarde [nombre]?")
            print("     • Patrón de asistencia de [nombre]")
            
            print("\n   📅 COMPARACIONES TEMPORALES:")
            print("     • Compara esta semana vs la semana pasada")
            print("     • ¿Ha mejorado la puntualidad este mes?")
            print("     • Tendencia de asistencia semanal")
            
            print(f"\n{'='*20} CONFIGURACIÓN DEL SISTEMA {'='*20}")
            print("🕐 REGLAS DE NEGOCIO:")
            print("   • Horario sin retardo: Hasta las 08:10:00 AM")
            print("   • Retardo: Después de las 08:10:00 AM")
            print("   • Semana laboral: Lunes a Viernes")
            print("   • Base de datos: zapopan (core_usuario + core_registro)")
            print("=" * 70)
            
            while True:
                try:
                    user_input = input("\n🤔 Tu pregunta (o 'salir'/'resumen' para opciones): ").strip()
                    
                    if user_input.lower() in ['salir', 'exit', 'quit']:
                        break
                    
                    if user_input.lower() in ['resumen', 'resumen semanal', 'summary']:
                        # Generar resumen automático semanal
                        print("🚀 Generando resumen semanal automático...")
                        summary = await self.get_weekly_attendance_summary()
                        print(f"\n{summary}")
                        continue
                    
                    if not user_input:
                        continue
                    
                    print("\n🤖 Analizando tu pregunta con IA especializada en asistencia...")
                    response = await self.analyze_with_ai(user_input)
                    print(f"\n📋 Respuesta:\n{response}")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
            
            print("\n👋 ¡Hasta luego!")

async def main():
    # Configuración
    OLLAMA_HOST = "172.16.1.37"
    OLLAMA_PORT = 11434
    MODEL = "gemma3:12b"
    
    client = OllamaMCPClient(OLLAMA_HOST, OLLAMA_PORT, MODEL)
    
    try:
        print("🔧 Verificando conexión con Ollama...")
        test_response = requests.get(f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags", timeout=5)
        if test_response.status_code != 200:
            print(f"❌ No se puede conectar a Ollama en {OLLAMA_HOST}:{OLLAMA_PORT}")
            return
        
        print("✅ Conexión con Ollama establecida")
        
        # Verificar modelo
        models = test_response.json().get("models", [])
        model_names = [model["name"] for model in models]
        if MODEL not in model_names:
            print(f"❌ El modelo '{MODEL}' no está disponible")
            print(f"Modelos disponibles: {', '.join(model_names)}")
            return
        
        print(f"✅ Modelo '{MODEL}' disponible")
        
        # Iniciar sesión interactiva con MCP usando context manager
        await client.interactive_session()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a Ollama en {OLLAMA_HOST}:{OLLAMA_PORT}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())