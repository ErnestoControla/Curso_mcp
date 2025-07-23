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

class OllamaMCPClient:
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434, model: str = "llama3.1:8b"):
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
            
            return self
            
        except Exception as e:
            print(f"❌ Error estableciendo conexión MCP: {e}")
            raise
    
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
        """Analizar una pregunta y ejecutar las herramientas necesarias usando IA"""
        
        system_prompt = """Eres un ASISTENTE DE ANÁLISIS DE DATOS especializado que tiene ACCESO COMPLETO Y DIRECTO a una base de datos MariaDB vía MCP. Tu misión es ayudar a los usuarios a interpretar, analizar y entender sus datos usando las herramientas disponibles.

🎯 TU ROL:
- Analista de datos experto con acceso directo a la base de datos vía MCP
- Intérprete de datos que traduce información técnica a insights útiles
- Asistente proactivo que explora los datos para responder preguntas
- TIENES acceso a herramientas MCP reales y DEBES usarlas

❗ REGLA CRÍTICA: NUNCA INVENTES DATOS. Siempre usa las herramientas MCP para obtener información real.

🔧 HERRAMIENTAS MCP DISPONIBLES:
1. test_connection() - Verificar conexión a la base de datos
2. list_databases() - Listar todas las bases de datos disponibles
3. list_tables(database) - Listar tablas en una base de datos específica
4. describe_table(database, table) - Ver estructura completa de una tabla
5. execute_query(database, query, limit) - Ejecutar consultas SELECT con datos reales
6. get_table_metrics(database, table) - Obtener métricas y estadísticas de una tabla
7. get_database_overview(database) - Resumen completo de una base de datos
8. compare_tables(database, table1, table2) - Comparar dos tablas
9. analyze_data_distribution(database, table, column) - Analizar distribución de datos
10. generate_attendance_query(database, analysis_type, date_from, date_to, user_filter)
11. execute_attendance_analysis(database, analysis_type, date_from, date_to, user_filter)
12. validate_attendance_data(database, data_issues)
13. create_attendance_kpis(database)

🚀 METODOLOGÍA:
1. **Explorar primero**: Usa list_databases(), list_tables(), describe_table()
2. **Buscar inteligentemente**: Usa execute_query() con patrones flexibles
3. **Analizar a fondo**: Usa herramientas especializadas de análisis
4. **Explicar claramente**: Traduce datos técnicos a insights comprensibles

Formato EXACTO para usar herramientas MCP:
USAR_HERRAMIENTA_MCP: nombre_herramienta(parametro1="valor1", parametro2="valor2")

Ejemplos:
USAR_HERRAMIENTA_MCP: list_databases()
USAR_HERRAMIENTA_MCP: execute_attendance_analysis(database="asistencia", analysis_type="daily_summary")
USAR_HERRAMIENTA_MCP: execute_query(database="ventas", query="SELECT COUNT(*) FROM productos WHERE categoria = 'electronicos'")

Responde SIEMPRE en español y usa las herramientas MCP antes de responder sobre datos."""

        # Obtener respuesta de la IA
        ai_response = self.call_ollama(question, system_prompt)
        
        # Procesar respuesta para extraer comandos de herramientas MCP
        lines = ai_response.split('\n')
        result_parts = []
        
        for line in lines:
            line_clean = line.strip()
            
            # Detectar herramientas MCP
            if 'USAR_HERRAMIENTA_MCP:' in line_clean:
                tool_call = line_clean.split('USAR_HERRAMIENTA_MCP:', 1)[1].strip()
                tool_call = tool_call.replace('**', '').strip()
                
                try:
                    if self.debug_mode:
                        print(f"\n🔧 EJECUTANDO HERRAMIENTA MCP: {tool_call}")
                    
                    # Parsear y ejecutar la herramienta via MCP
                    tool_result = await self.parse_and_execute_mcp_tool(tool_call)
                    
                    if self.debug_mode:
                        print(f"✅ Herramienta MCP ejecutada exitosamente")
                        print(f"📊 Datos obtenidos: {len(str(tool_result))} caracteres")
                    
                    # Agregar resultado al contexto
                    result_parts.append(f"🔧 Ejecutando MCP: {tool_call}")
                    result_parts.append(f"📊 Resultado:")
                    result_parts.append(json.dumps(tool_result, indent=2, ensure_ascii=False))
                    
                    # Si la herramienta fue exitosa, continuar el análisis
                    if tool_result.get("success", False):
                        follow_up_prompt = f"""
La herramienta MCP {tool_call} se ejecutó exitosamente con este resultado:
{json.dumps(tool_result, indent=2, ensure_ascii=False)}

Basándote en este resultado real, proporciona una respuesta clara y útil al usuario. Si necesitas ejecutar más herramientas MCP para completar el análisis, hazlo.
"""
                        follow_up_response = self.call_ollama(follow_up_prompt)
                        result_parts.append(f"\n🤖 Análisis de resultados:")
                        result_parts.append(follow_up_response)
                    else:
                        result_parts.append(f"❌ Error en la herramienta MCP: {tool_result.get('error', 'Error desconocido')}")
                    
                except Exception as e:
                    result_parts.append(f"❌ Error ejecutando MCP {tool_call}: {e}")
                    print(f"Error detallado: {e}")
            else:
                # Solo agregar líneas que no sean de herramientas fallidas
                if (line_clean and 
                    not any(line_clean.startswith(prefix) for prefix in ['🔧', '📊', '🤖', '❌']) and
                    'USAR_HERRAMIENTA_MCP' not in line_clean):
                    result_parts.append(line)
        
        return '\n'.join(result_parts)
    
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
                        # Patrón mejorado que maneja strings con comas
                        param_pattern = r'(\w+)=(["\'])([^"\']*?)\2|(\w+)=([^,\s]+)'
                        matches = re.findall(param_pattern, params_str)
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
    
    async def interactive_session(self):
        """Sesión interactiva con el usuario usando MCP real"""
        print("=" * 60)
        print("🤖 ASISTENTE DE ANÁLISIS DE BASE DE DATOS CON IA + MCP")
        print("=" * 60)
        print("Conectado a:")
        print(f"  📊 MariaDB via MCP: 172.16.1.29")
        print(f"  🦙 Ollama: {self.ollama_base_url} ({self.model})")
        print("=" * 60)
        
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
            
            print("\n💡 Ejemplos de preguntas que puedes hacer:")
            print("   📊 General:")
            print("     - ¿Qué bases de datos tienes disponibles?")
            print("     - Muéstrame las tablas de la base de datos X")
            print("     - Analiza la tabla Y en la base de datos Z")
            print("   🎯 Análisis de Asistencia:")
            print("     - Muéstrame un resumen diario de asistencia")
            print("     - ¿Quiénes llegaron tarde esta semana?")
            print("     - Calcula los KPIs de asistencia")
            print("   🔍 Búsquedas:")
            print("     - Busca información de [nombre]")
            print("     - Encuentra todos los usuarios con nombre 'María'")
            print("\n" + "=" * 60)
            
            while True:
                try:
                    user_input = input("\n🤔 Tu pregunta (o 'salir' para terminar): ").strip()
                    
                    if user_input.lower() in ['salir', 'exit', 'quit']:
                        break
                    
                    if not user_input:
                        continue
                    
                    print("\n🤖 Analizando tu pregunta con MCP...")
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
    MODEL = "llama3.1:8b"
    
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