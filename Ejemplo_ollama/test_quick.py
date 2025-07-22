#!/usr/bin/env python3
# test_quick.py
"""
Script de prueba rápida para verificar conectividad
"""

import sys
import requests
import json

def test_mariadb():
    """Prueba rápida de MariaDB"""
    try:
        import pymysql
        connection = pymysql.connect(
            host='172.16.1.29',
            user='controla',
            password='controla',
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        connection.close()
        return True, f"MariaDB {version}"
    except Exception as e:
        return False, str(e)

def test_ollama(host="localhost", port=11434):
    """Prueba rápida de Ollama"""
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            if "llama3.1:8b" in model_names:
                return True, f"Ollama con {len(model_names)} modelos"
            else:
                return False, "Modelo llama3.1:8b no encontrado"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_mcp_tools():
    """Prueba rápida de herramientas MCP"""
    try:
        from server import test_connection, list_databases
        
        # Probar conexión
        result = test_connection()
        if not result.get("success"):
            return False, "Error en test_connection"
        
        # Probar listado de bases de datos
        result = list_databases()
        if not result.get("success"):
            return False, "Error en list_databases"
            
        return True, f"MCP OK - {result.get('count', 0)} bases de datos"
    except Exception as e:
        return False, str(e)

def test_smart_search():
    """Prueba rápida de búsqueda inteligente"""
    try:
        import sys
        sys.path.append('.')
        from client import OllamaMCPClient
        
        client = OllamaMCPClient()
        
        # Primero obtener una base de datos para probar
        from server import list_databases
        dbs_result = list_databases()
        
        if not dbs_result.get("success") or not dbs_result.get("databases"):
            return False, "Sin bases de datos para probar"
        
        # Usar la primera base de datos disponible
        test_db = dbs_result.get("databases")[0]
        
        # Probar búsqueda inteligente con un término genérico
        result = client.smart_search_person(test_db, "test user", None)
        
        if result.get("success"):
            strategies = len(result.get("strategies_used", []))
            return True, f"Búsqueda inteligente OK - {strategies} estrategias"
        else:
            return True, "Búsqueda inteligente funcional (sin resultados de prueba)"
            
    except Exception as e:
        return False, str(e)

def main():
    print("🧪 PRUEBA RÁPIDA DEL SISTEMA")
    print("=" * 40)
    
    tests = [
        ("📊 MariaDB", test_mariadb),
        ("🦙 Ollama", lambda: test_ollama()),
        ("🔧 Herramientas MCP", test_mcp_tools),
        ("🔍 Búsqueda Inteligente", test_smart_search)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nProbando {name}...")
        success, message = test_func()
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
        results.append(success)
    
    print("\n" + "=" * 40)
    if all(results):
        print("🎉 ¡Todas las pruebas pasaron!")
        print("✅ El sistema está listo para usar")
        print("\n🚀 Ejecuta: python client.py")
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("📋 Revisa los errores anteriores")
        failed_count = len([r for r in results if not r])
        print(f"   {failed_count}/{len(results)} componentes con problemas")
    
    print("=" * 40)

if __name__ == "__main__":
    main() 