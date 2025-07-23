#!/usr/bin/env python3
# client.py
import asyncio
import json
import requests
import subprocess
import sys
from typing import Dict, Any, List
import time

class OllamaMCPClient:
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434, model: str = "llama3.1:8b"):
        self.ollama_base_url = f"http://{ollama_host}:{ollama_port}"
        self.model = model
        self.mcp_process = None
        self.conversation_history = []
        self.debug_mode = True  # Activar debug para ver herramientas ejecutándose
        
    def start_mcp_server(self):
        """Iniciar el servidor MCP en un proceso separado"""
        try:
            print("🚀 Iniciando servidor MCP...")
            self.mcp_process = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(2)  # Dar tiempo al servidor para inicializar
            print("✅ Servidor MCP iniciado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error iniciando servidor MCP: {e}")
            return False
    
    def stop_mcp_server(self):
        """Detener el servidor MCP"""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            print("🛑 Servidor MCP detenido")
    
    def call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Llamar a Ollama con un prompt"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Agregar historial de conversación
            messages.extend(self.conversation_history[-6:])  # Últimas 6 interacciones
            
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
    
    def execute_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar una herramienta del servidor MCP"""
        try:
            # Simular llamada a herramienta MCP
            # En una implementación real, usarías el protocolo MCP
            
            if tool_name == "test_connection":
                from server import test_connection
                return test_connection()
            elif tool_name == "list_databases":
                from server import list_databases
                return list_databases()
            elif tool_name == "list_tables":
                from server import list_tables
                return list_tables(kwargs.get("database"))
            elif tool_name == "describe_table":
                from server import describe_table
                return describe_table(kwargs.get("database"), kwargs.get("table"))
            elif tool_name == "execute_query":
                from server import execute_query
                return execute_query(
                    kwargs.get("database"), 
                    kwargs.get("query"), 
                    kwargs.get("limit", 100)
                )
            elif tool_name == "get_table_metrics":
                from server import get_table_metrics
                return get_table_metrics(kwargs.get("database"), kwargs.get("table"))
            elif tool_name == "get_database_overview":
                from server import get_database_overview
                return get_database_overview(kwargs.get("database"))
            elif tool_name == "compare_tables":
                from server import compare_tables
                return compare_tables(
                    kwargs.get("database"), 
                    kwargs.get("table1"), 
                    kwargs.get("table2")
                )
            elif tool_name == "analyze_data_distribution":
                from server import analyze_data_distribution
                return analyze_data_distribution(
                    kwargs.get("database"), 
                    kwargs.get("table"), 
                    kwargs.get("column"),
                    kwargs.get("bins", 10)
                )
            elif tool_name == "smart_search_person":
                return self.smart_search_person(
                    kwargs.get("database"),
                    kwargs.get("search_term"),
                    kwargs.get("table_hint")
                )
            # === NUEVAS HERRAMIENTAS DE ASISTENCIA ===
            elif tool_name == "generate_attendance_query":
                from server import generate_attendance_query
                return generate_attendance_query(
                    kwargs.get("database"),
                    kwargs.get("analysis_type"),
                    kwargs.get("date_from"),
                    kwargs.get("date_to"),
                    kwargs.get("user_filter")
                )
            elif tool_name == "execute_attendance_analysis":
                from server import execute_attendance_analysis
                return execute_attendance_analysis(
                    kwargs.get("database"),
                    kwargs.get("analysis_type"),
                    kwargs.get("date_from"),
                    kwargs.get("date_to"),
                    kwargs.get("user_filter")
                )
            elif tool_name == "validate_attendance_data":
                from server import validate_attendance_data
                return validate_attendance_data(
                    kwargs.get("database"),
                    kwargs.get("data_issues")
                )
            elif tool_name == "create_attendance_kpis":
                from server import create_attendance_kpis
                return create_attendance_kpis(kwargs.get("database"))
            else:
                return {"success": False, "error": f"Herramienta '{tool_name}' no encontrada"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def smart_search_person(self, database: str, search_term: str, table_hint: str = None) -> Dict[str, Any]:
        """Búsqueda inteligente de personas usando múltiples estrategias"""
        try:
            from server import execute_query, list_tables, describe_table
            
            # Si no se especifica tabla, buscar tablas que puedan contener personas
            if not table_hint:
                tables_result = list_tables(database)
                if not tables_result.get("success"):
                    return {"success": False, "error": "No se pueden listar las tablas"}
                
                # Buscar tablas que probablemente contengan personas
                person_tables = []
                for table in tables_result.get("tables", []):
                    table_lower = table.lower()
                    if any(keyword in table_lower for keyword in ['usuario', 'persona', 'cliente', 'empleado', 'user', 'person', 'customer', 'employee']):
                        person_tables.append(table)
                
                if not person_tables:
                    person_tables = tables_result.get("tables", [])[:3]  # Usar las primeras 3 tablas
            else:
                person_tables = [table_hint]
            
            all_results = []
            search_strategies = []
            
            # Dividir el término de búsqueda en palabras
            words = [word.strip() for word in search_term.split() if word.strip()]
            
            for table in person_tables:
                # Obtener estructura de la tabla
                structure = describe_table(database, table)
                if not structure.get("success"):
                    continue
                
                columns = structure.get("columns", [])
                name_columns = []
                
                # Identificar columnas que puedan contener nombres
                for col in columns:
                    col_name = col["field"].lower()
                    if any(keyword in col_name for keyword in ['nombre', 'name', 'apellido', 'surname', 'firstname', 'lastname', 'fullname']):
                        name_columns.append(col["field"])
                
                if not name_columns:
                    # Si no hay columnas obvias, usar las primeras columnas de texto
                    for col in columns[:5]:
                        if 'varchar' in col["type"].lower() or 'text' in col["type"].lower():
                            name_columns.append(col["field"])
                
                # Estrategia 1: Búsqueda en cada palabra por separado
                for column in name_columns:
                    like_conditions = [f"{column} LIKE '%{word}%'" for word in words]
                    where_clause = " AND ".join(like_conditions)
                    
                    query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10"
                    result = execute_query(database, query)
                    
                    if result.get("success") and result.get("results"):
                        search_strategies.append(f"Búsqueda por palabras en {column}")
                        all_results.extend(result.get("results", []))
                
                # Estrategia 2: Búsqueda con CONCAT si hay múltiples columnas de nombre
                if len(name_columns) >= 2:
                    # Construir CONCAT con espacios entre columnas
                    concat_parts = [name_columns[0]]
                    for col in name_columns[1:]:
                        concat_parts.extend(["' '", col])
                    concat_cols = f"CONCAT({', '.join(concat_parts)})"
                    
                    like_conditions = [f"{concat_cols} LIKE '%{word}%'" for word in words]
                    where_clause = " AND ".join(like_conditions)
                    
                    query = f"SELECT *, {concat_cols} as nombre_completo FROM {table} WHERE {where_clause} LIMIT 10"
                    result = execute_query(database, query)
                    
                    if result.get("success") and result.get("results"):
                        search_strategies.append(f"Búsqueda en nombre completo concatenado")
                        all_results.extend(result.get("results", []))
                
                # Estrategia 3: Búsqueda fonética con SOUNDEX (si está disponible)
                if name_columns and len(words) > 0:
                    soundex_conditions = [f"SOUNDEX({name_columns[0]}) = SOUNDEX('{words[0]}')" for word in words[:2]]
                    where_clause = " OR ".join(soundex_conditions)
                    
                    query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 5"
                    result = execute_query(database, query)
                    
                    if result.get("success") and result.get("results"):
                        search_strategies.append(f"Búsqueda fonética con SOUNDEX")
                        all_results.extend(result.get("results", []))
            
            # Remover duplicados (comparación simple por primera columna)
            unique_results = []
            seen_keys = set()
            
            for result in all_results:
                if result:
                    first_value = list(result.values())[0] if result else None
                    if first_value not in seen_keys:
                        seen_keys.add(first_value)
                        unique_results.append(result)
            
            return {
                "success": True,
                "search_term": search_term,
                "database": database,
                "tables_searched": person_tables,
                "strategies_used": search_strategies,
                "results": unique_results[:15],  # Limitar a 15 resultados únicos
                "total_found": len(unique_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "search_term": search_term,
                "database": database,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_with_ai(self, question: str) -> str:
        """Analizar una pregunta y ejecutar las herramientas necesarias usando IA"""
        
        system_prompt = """Eres un ASISTENTE DE ANÁLISIS DE DATOS especializado que tiene ACCESO COMPLETO Y DIRECTO a una base de datos MariaDB. Tu misión es ayudar a los usuarios a interpretar, analizar y entender sus datos usando las herramientas disponibles.

🎯 TU ROL:
- Analista de datos experto con acceso directo a la base de datos
- Intérprete de datos que traduce información técnica a insights útiles
- Asistente proactivo que explora los datos para responder preguntas
- NO eres solo un consultor, TIENES y DEBES usar las herramientas disponibles

❗ REGLA CRÍTICA: NUNCA INVENTES DATOS. Siempre usa las herramientas para obtener información real.

🔧 HERRAMIENTAS DISPONIBLES (úsalas activamente):

📊 HERRAMIENTAS GENERALES:
1. test_connection() - Verificar conexión a la base de datos
2. list_databases() - Listar todas las bases de datos disponibles
3. list_tables(database) - Listar tablas en una base de datos específica
4. describe_table(database, table) - Ver estructura completa de una tabla
5. execute_query(database, query, limit) - Ejecutar consultas SELECT con datos reales
6. get_table_metrics(database, table) - Obtener métricas y estadísticas de una tabla
7. get_database_overview(database) - Resumen completo de una base de datos
8. compare_tables(database, table1, table2) - Comparar dos tablas
9. analyze_data_distribution(database, table, column) - Analizar distribución de datos
10. smart_search_person(database, search_term, table_hint) - Búsqueda inteligente de personas

🎯 HERRAMIENTAS ESPECIALIZADAS DE ASISTENCIA:
11. generate_attendance_query(database, analysis_type, date_from, date_to, user_filter) - Genera consultas SQL para análisis de asistencia
12. execute_attendance_analysis(database, analysis_type, date_from, date_to, user_filter) - Ejecuta análisis completos de asistencia
13. validate_attendance_data(database, data_issues) - Valida calidad de datos de asistencia
14. create_attendance_kpis(database) - Calcula KPIs de asistencia organizacionales

🚀 ESTRATEGIA DE TRABAJO:
1. SIEMPRE comienza explorando la estructura (list_databases, list_tables, describe_table)
2. Para búsquedas de personas/entidades, usa búsquedas parciales inteligentes:
   - Busca por partes del nombre: LIKE '%Sergio%' AND LIKE '%Saucedo%'
   - Usa SOUNDEX para nombres similares fonéticamente
   - Prueba variaciones: nombres, apellidos, iniciales
3. Si no encuentras algo inmediatamente, EXPLORA más:
   - Revisa diferentes tablas relacionadas
   - Usa wildcards y patrones de búsqueda
   - Analiza la estructura de datos disponible

📝 BÚSQUEDAS INTELIGENTES DE PERSONAS:
Para buscar personas por nombre, usa la herramienta smart_search_person que:
- Busca automáticamente en tablas relevantes (usuarios, personas, clientes, etc.)
- Usa múltiples estrategias: palabras parciales, nombres concatenados, SOUNDEX
- Maneja variaciones: "José Luis" vs "Jose Luis" vs "J.L."
- Encuentra coincidencias incluso con nombres incompletos como "Sergio Saucedo" → "Sergio Ivan Saucedo"
- Si hay múltiples resultados, muestra opciones al usuario

💡 METODOLOGÍA:
1. **Explorar primero**: Entiende qué datos tienes disponibles
2. **Buscar inteligentemente**: Usa patrones flexibles para encontrar información
3. **Analizar a fondo**: Proporciona estadísticas, métricas y contexto
4. **Explicar claramente**: Traduce datos técnicos a insights comprensibles
5. **Sugerir acciones**: Recomienda próximos pasos basados en los hallazgos

🔍 EJEMPLOS DE CONSULTAS INTELIGENTES:
- Buscar persona: SELECT * FROM usuarios WHERE CONCAT(nombre, ' ', apellido) LIKE '%Sergio%' AND CONCAT(nombre, ' ', apellido) LIKE '%Saucedo%'
- Explorar estructura: SHOW COLUMNS FROM tabla_nombre
- Búsqueda fonética: SELECT * FROM usuarios WHERE SOUNDEX(nombre) = SOUNDEX('Sergio')

🎯 REGLAS IMPORTANTES:
- ❗ NUNCA INVENTES DATOS - Siempre usa herramientas para obtener información real
- ❗ NO digas nombres de bases de datos o tablas si no las has consultado primero
- NUNCA digas "no puedo acceder" - SÍ PUEDES usar las herramientas
- SIEMPRE usa las herramientas antes de responder sobre datos
- Si no sabes qué base de datos usar, ejecuta list_databases() primero
- Para nombres parciales, usa búsquedas flexibles con LIKE
- Explica QUÉ encontraste y QUÉ significa para el usuario
- Responde SIEMPRE en español

📝 PARA ANÁLISIS DE ASISTENCIA específicamente:
- Usa execute_attendance_analysis() para análisis completos
- Tipos disponibles: daily_summary, late_arrivals, missing_exits, user_pattern, device_usage, hourly_distribution
- Para KPIs organizacionales usa create_attendance_kpis()
- Para validar datos usa validate_attendance_data()

Formato EXACTO para usar herramientas:
USAR_HERRAMIENTA: nombre_herramienta(parametro1="valor1", parametro2="valor2")

Ejemplos:
USAR_HERRAMIENTA: list_databases()
USAR_HERRAMIENTA: execute_attendance_analysis(database="asistencia", analysis_type="daily_summary")
USAR_HERRAMIENTA: smart_search_person(database="usuarios", search_term="Sergio Saucedo")
USAR_HERRAMIENTA: execute_query(database="ventas", query="SELECT COUNT(*) FROM productos WHERE categoria = 'electronicos'")"""

        # Obtener respuesta de la IA
        ai_response = self.call_ollama(question, system_prompt)
        
        # Procesar respuesta para extraer comandos de herramientas
        lines = ai_response.split('\n')
        result_parts = []
        
        for line in lines:
            # Detectar herramientas con múltiples formatos posibles
            line_clean = line.strip()
            tool_call = None
            
            # Patrón 1: USAR_HERRAMIENTA: function()
            if 'USAR_HERRAMIENTA:' in line_clean:
                tool_call = line_clean.split('USAR_HERRAMIENTA:', 1)[1].strip()
                # Remover markdown si existe
                tool_call = tool_call.replace('**', '').strip()
                
            # Patrón 2: **USAR_HERRAMIENTA: function()**
            elif line_clean.startswith('**USAR_HERRAMIENTA:') and line_clean.endswith('**'):
                tool_call = line_clean.replace('**USAR_HERRAMIENTA:', '').replace('**', '').strip()
            
            if tool_call:
                try:
                    if self.debug_mode:
                        print(f"\n🔧 EJECUTANDO HERRAMIENTA: {tool_call}")
                    
                    # Parsear y ejecutar la herramienta
                    tool_result = self.parse_and_execute_tool(tool_call)
                    
                    if self.debug_mode:
                        print(f"✅ Herramienta ejecutada exitosamente")
                        print(f"📊 Datos obtenidos: {len(str(tool_result))} caracteres")
                    
                    # Agregar resultado al contexto
                    result_parts.append(f"🔧 Ejecutando: {tool_call}")
                    result_parts.append(f"📊 Resultado:")
                    result_parts.append(json.dumps(tool_result, indent=2, ensure_ascii=False))
                    
                    # Si la herramienta fue exitosa, continuar el análisis
                    if tool_result.get("success", False):
                        follow_up_prompt = f"""
La herramienta {tool_call} se ejecutó exitosamente con este resultado:
{json.dumps(tool_result, indent=2, ensure_ascii=False)}

Basándote en este resultado real, proporciona una respuesta clara y útil al usuario. Si necesitas ejecutar más herramientas para completar el análisis, hazlo.
"""
                        follow_up_response = self.call_ollama(follow_up_prompt)
                        result_parts.append(f"\n🤖 Análisis de resultados:")
                        result_parts.append(follow_up_response)
                    else:
                        result_parts.append(f"❌ Error en la herramienta: {tool_result.get('error', 'Error desconocido')}")
                    
                except Exception as e:
                    result_parts.append(f"❌ Error ejecutando {tool_call}: {e}")
                    print(f"Error detallado: {e}")
            else:
                # Solo agregar líneas que no sean de herramientas fallidas
                if (line_clean and 
                    not any(line_clean.startswith(prefix) for prefix in ['🔧', '📊', '🤖', '❌']) and
                    'USAR_HERRAMIENTA' not in line_clean):
                    result_parts.append(line)
        
        return '\n'.join(result_parts)
    
    def parse_and_execute_tool(self, tool_call: str) -> Dict[str, Any]:
        """Parsear y ejecutar una llamada a herramienta"""
        try:
            # Extraer nombre de la función y parámetros
            if '(' in tool_call:
                tool_name = tool_call.split('(')[0].strip()
                params_str = tool_call.split('(', 1)[1].rsplit(')', 1)[0]
                
                # Parsear parámetros simples
                kwargs = {}
                if params_str.strip():
                    # Parseo básico de parámetros key="value"
                    import re
                    param_pattern = r'(\w+)=(["\']?)([^,"\']+)\2'
                    matches = re.findall(param_pattern, params_str)
                    for key, quote, value in matches:
                        # Convertir tipos básicos
                        if value.isdigit():
                            kwargs[key] = int(value)
                        elif value.replace('.', '').isdigit():
                            kwargs[key] = float(value)
                        elif value.lower() in ['true', 'false']:
                            kwargs[key] = value.lower() == 'true'
                        else:
                            kwargs[key] = value
                
                return self.execute_mcp_tool(tool_name, **kwargs)
            else:
                return self.execute_mcp_tool(tool_call)
                
        except Exception as e:
            return {"success": False, "error": f"Error parseando herramienta: {e}"}
    
    def interactive_session(self):
        """Sesión interactiva con el usuario"""
        print("=" * 60)
        print("🤖 ASISTENTE DE ANÁLISIS DE BASE DE DATOS CON IA")
        print("=" * 60)
        print("Conectado a:")
        print(f"  📊 MariaDB: 172.16.1.29")
        print(f"  🦙 Ollama: {self.ollama_base_url} ({self.model})")
        print("=" * 60)
        
        # Probar conexión inicial
        print("🔍 Probando conexión a la base de datos...")
        connection_test = self.execute_mcp_tool("test_connection")
        if connection_test.get("success"):
            print("✅ Conexión a MariaDB exitosa")
            print(f"   Versión: {connection_test.get('server_version', 'Desconocida')}")
        else:
            print("❌ Error conectando a MariaDB")
            print(f"   {connection_test.get('error', 'Error desconocido')}")
        
        print("\n💡 Ejemplos de preguntas que puedes hacer:")
        print("   📊 General:")
        print("     - ¿Qué bases de datos tienes disponibles?")
        print("     - Muéstrame las tablas de la base de datos X")
        print("     - Analiza la tabla Y en la base de datos Z")
        print("   🎯 Análisis de Asistencia:")
        print("     - Muéstrame un resumen diario de asistencia")
        print("     - ¿Quiénes llegaron tarde esta semana?")
        print("     - Calcula los KPIs de asistencia")
        print("     - Encuentra registros duplicados en asistencia")
        print("     - Analiza el patrón de asistencia por usuario")
        print("   🔍 Búsquedas:")
        print("     - Busca información de [nombre] (búsqueda inteligente)")
        print("     - Encuentra todos los usuarios con nombre 'María'")
        print("\n" + "=" * 60)
        
        while True:
            try:
                user_input = input("\n🤔 Tu pregunta (o 'salir' para terminar): ").strip()
                
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 Analizando tu pregunta...")
                response = self.analyze_with_ai(user_input)
                print(f"\n📋 Respuesta:\n{response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
        
        print("\n👋 ¡Hasta luego!")

def main():
    # Configuración
    OLLAMA_HOST = "172.16.1.37"  # Cambia esto por la IP de tu servidor Ollama si es diferente
    OLLAMA_PORT = 11434
    MODEL = "llama3.1:8b"
    
    client = OllamaMCPClient(OLLAMA_HOST, OLLAMA_PORT, MODEL)
    
    try:
        print("🔧 Verificando conexión con Ollama...")
        test_response = requests.get(f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags", timeout=5)
        if test_response.status_code != 200:
            print(f"❌ No se puede conectar a Ollama en {OLLAMA_HOST}:{OLLAMA_PORT}")
            print("Asegúrate de que Ollama esté ejecutándose y sea accesible")
            return
        
        print("✅ Conexión con Ollama establecida")
        
        # Verificar que el modelo existe
        models = test_response.json().get("models", [])
        model_names = [model["name"] for model in models]
        if MODEL not in model_names:
            print(f"❌ El modelo '{MODEL}' no está disponible")
            print(f"Modelos disponibles: {', '.join(model_names)}")
            return
        
        print(f"✅ Modelo '{MODEL}' disponible")
        
        # Iniciar sesión interactiva
        client.interactive_session()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a Ollama en {OLLAMA_HOST}:{OLLAMA_PORT}")
        print("Verifica que:")
        print("  1. Ollama esté ejecutándose")
        print("  2. El host y puerto sean correctos")
        print("  3. El firewall permita las conexiones")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        client.stop_mcp_server()

if __name__ == "__main__":
    main() 