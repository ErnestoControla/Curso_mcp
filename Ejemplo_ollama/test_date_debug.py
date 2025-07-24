#!/usr/bin/env python3
"""
Script para debuggear el problema de fechas
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def debug_date_issue():
    """Debuggear el problema de fechas"""
    print("🔍 Debuggeando problema de fechas...")
    
    try:
        server_params = StdioServerParameters(
            command="python", args=["server.py"], env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 1. Ver qué vale CURRENT_DATE
                print("\n📅 Verificando CURRENT_DATE:")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT CURRENT_DATE as fecha_actual, NOW() as fecha_hora_actual"
                })
                current_date_data = json.loads(result.content[0].text)
                print(f"📊 CURRENT_DATE: {current_date_data}")
                
                # 2. Ver fechas reales en la tabla hoy
                print("\n📅 Fechas reales en la tabla (formato completo):")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT tiempo, DATE(tiempo) as solo_fecha FROM core_registro WHERE tiempo >= '2025-07-23 00:00:00' ORDER BY tiempo DESC LIMIT 5"
                })
                real_dates_data = json.loads(result.content[0].text)
                print(f"📊 Fechas reales: {real_dates_data}")
                
                # 3. Comparar directamente
                print("\n📅 Comparación directa:")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT DATE(tiempo) = CURRENT_DATE as coincide, DATE(tiempo) as fecha_registro, CURRENT_DATE as fecha_actual FROM core_registro WHERE tiempo >= '2025-07-23 00:00:00' LIMIT 3"
                })
                comparison_data = json.loads(result.content[0].text)
                print(f"📊 Comparación: {comparison_data}")
                
                # 4. Probar consulta con fecha específica
                print("\n📅 Consulta con fecha específica '2025-07-23':")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT nombre, tiempo FROM core_registro WHERE DATE(tiempo) = '2025-07-23'"
                })
                specific_date_data = json.loads(result.content[0].text)
                print(f"📊 Resultados: {specific_date_data}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_date_issue()) 