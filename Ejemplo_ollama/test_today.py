#!/usr/bin/env python3
"""
Script para probar consultas de fechas
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def test_date_queries():
    """Probar consultas de fechas"""
    print("🔍 Probando consultas de fechas...")
    
    try:
        server_params = StdioServerParameters(
            command="python", args=["server.py"], env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Consulta 1: Registros de hoy
                print("\n🗓️ Registros de hoy (CURRENT_DATE):")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT nombre, tiempo FROM core_registro WHERE DATE(tiempo) = CURRENT_DATE"
                })
                today_data = json.loads(result.content[0].text)
                print(f"📊 Resultado: {today_data}")
                
                # Consulta 2: Últimos 10 registros (cualquier fecha)
                print("\n📅 Últimos 10 registros (cualquier fecha):")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan", 
                    "query": "SELECT nombre, tiempo FROM core_registro ORDER BY tiempo DESC LIMIT 10"
                })
                recent_data = json.loads(result.content[0].text)
                print(f"📊 Resultado: {recent_data}")
                
                # Consulta 3: Registros de la última semana
                print("\n📅 Registros de la última semana:")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT nombre, tiempo FROM core_registro WHERE DATE(tiempo) >= CURRENT_DATE - INTERVAL 7 DAY"
                })
                week_data = json.loads(result.content[0].text)
                print(f"📊 Resultado: {week_data}")
                
                # Consulta 4: Fechas únicas disponibles
                print("\n📅 Fechas únicas disponibles:")
                result = await session.call_tool("execute_query", {
                    "database": "zapopan",
                    "query": "SELECT DISTINCT DATE(tiempo) as fecha FROM core_registro ORDER BY fecha DESC LIMIT 10"
                })
                dates_data = json.loads(result.content[0].text)
                print(f"📊 Fechas disponibles: {dates_data}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_date_queries()) 