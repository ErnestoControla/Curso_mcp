#!/usr/bin/env python3
"""
Script para probar directamente la estructura de la base de datos
sin usar el cliente de IA
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def test_database_structure():
    """Probar directamente la estructura de la base de datos"""
    print("🔍 Probando estructura de base de datos directamente...")
    
    try:
        # Configurar parámetros del servidor MCP
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=None
        )
        
        # Crear cliente y sesión MCP
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Inicializar el servidor
                await session.initialize()
                print("✅ Sesión MCP inicializada")
                
                # Probar conexión
                result = await session.call_tool("test_connection", {})
                print(f"🔗 Conexión: {result.content[0].text}")
                
                # Listar bases de datos
                result = await session.call_tool("list_databases", {})
                databases = json.loads(result.content[0].text)
                print(f"📋 Bases de datos: {databases.get('databases', [])}")
                
                # Describir tabla core_registro
                result = await session.call_tool("describe_table", {
                    "database": "zapopan",
                    "table": "core_registro"
                })
                
                table_structure = json.loads(result.content[0].text)
                print("\n📊 Estructura de 'zapopan.core_registro':")
                print(json.dumps(table_structure, indent=2, ensure_ascii=False))
                
                # Probar una consulta simple
                print("\n🔍 Probando consulta de conteo...")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT COUNT(*) as total FROM core_registro"
                })
                
                count_result = json.loads(result.content[0].text)
                print(f"📊 Resultado: {count_result}")
                
                # Intentar listar los primeros 5 registros con todos los campos
                print("\n🔍 Probando consulta de muestra (primeros 5 registros)...")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan", 
                    "query": "SELECT * FROM core_registro LIMIT 5"
                })
                
                sample_result = json.loads(result.content[0].text)
                print(f"📊 Muestra: {sample_result}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_database_structure()) 