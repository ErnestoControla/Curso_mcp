# client_fixed.py - Versión corregida con parsing mejorado
import json
import requests
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import re

class OllamaMCPClient:
    def __init__(self, ollama_url: str = "http://172.16.1.37:11434", model: str = "gemma3:12b"):
        self.ollama_url = ollama_url
        self.model = model
        self.mcp_session = None
        self.mcp_read = None
        self.mcp_write = None
        self.context_loaded = False
        self.debug_mode = True  # Temporal para debugging
        
    async def __aenter__(self):
        """Configurar MCP al entrar al contexto"""
        await self.setup_mcp()
        if not self.context_loaded:
            await self.load_attendance_context()
            self.context_loaded = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup al salir del contexto"""
        if self.mcp_read and self.mcp_write:
            self.mcp_read.close()
            await self.mcp_write.wait_closed()
    
    async def setup_mcp(self):
        """Configurar la conexión MCP"""
        print("🚀 Iniciando conexión MCP...")
        server_params = StdioServerParameters(command="python", args=["server.py"], env=None)
        
        self.mcp_read, self.mcp_write = await stdio_client(server_params)
        self.mcp_session = ClientSession(self.mcp_read, self.mcp_write)
        await self.mcp_session.initialize()
        
        print("✅ Conexión MCP establecida correctamente")
        
        # Listar herramientas disponibles
        list_tools_result = await self.mcp_session.list_tools()
        print(f"🔧 Herramientas disponibles: {len(list_tools_result.tools)}")
        for tool in list_tools_result.tools:
            description = tool.description or ""
            if description:
                description_lines = description.split('\n')
                main_desc = description_lines[0]
                print(f"   - {tool.name}: {main_desc}")
                
                if len(description_lines) > 1:
                    for line in description_lines[1:5]:  # Máximo 4 líneas adicionales
                        if line.strip():
                            print(f"    {line.strip()}")
                    if len(description_lines) > 5:
                        print("    ...")
            else:
                print(f"   - {tool.name}")
        print()
        
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
    
    async def parse_and_execute_mcp_tool(self, tool_call: str) -> Dict[str, Any]:
        """Parsear y ejecutar herramienta MCP con parsing mejorado"""
        try:
            if "(" in tool_call and tool_call.endswith(")"):
                tool_name = tool_call[:tool_call.find("(")]
                params_str = tool_call[tool_call.find("(")+1:-1]
                
                if self.debug_mode:
                    print(f"🔧 Tool: {tool_name}")
                    print(f"🔧 Params raw: {params_str}")
                
                # Usar parser robusto para execute_query
                if tool_name == 'execute_query' and 'query=' in params_str:
                    kwargs = self._parse_mcp_params_robust(params_str)
                    if self.debug_mode:
                        print(f"🔧 Parsed query length: {len(kwargs.get('query', ''))} chars")
                else:
                    # Parsing estándar para otras herramientas
                    try:
                        kwargs = eval(f'dict({params_str})')
                    except:
                        kwargs = {}
                
                return await self.execute_mcp_tool(tool_name, **kwargs)
            else:
                return await self.execute_mcp_tool(tool_call)
                
        except Exception as e:
            return {"success": False, "error": f"Error parseando herramienta MCP: {e}"}
            
    async def execute_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar una herramienta usando MCP real"""
        try:
            if not self.mcp_session:
                return {"success": False, "error": "Sesión MCP no inicializada"}
            
            # DEBUG: Capturar exactamente qué se envía al MCP
            if tool_name == 'execute_query' and 'query' in kwargs:
                print(f"🔍 DEBUG - MCP Tool Call:")
                print(f"   Tool: {tool_name}")
                print(f"   Query enviada: '{kwargs['query'][:100]}{'...' if len(kwargs['query']) > 100 else ''}'")
                print(f"   Query length: {len(kwargs['query'])} chars")
                print(f"   Database: {kwargs.get('database', 'None')}")
            
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

# Función de prueba
async def test_conteo_fix():
    """Probar que el conteo de retardos ahora funciona"""
    client = OllamaMCPClient()
    async with client:
        print('🔍 PROBANDO CONTEO CORREGIDO')
        print('='*50)
        
        # Probar específicamente el conteo que fallaba
        result = await client.analyze_with_ai('puedes hacer un conteo por nombres?')
        print(f'Resultado: {result}')

if __name__ == "__main__":
    # Solo testing básico aquí
    asyncio.run(test_conteo_fix()) 