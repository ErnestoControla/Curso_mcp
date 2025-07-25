#!/usr/bin/env python3
"""
Script para probar la corrección del parsing de consultas SQL
"""
import re

def parse_mcp_params_robust(params_str: str):
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

def test_parsing():
    """Probar el parsing con la consulta problemática"""
    
    # Esta es la llamada exacta que genera Gemma
    test_call = 'execute_query(database="zapopan", query="SELECT nombre, COUNT(*) as total FROM core_registro GROUP BY nombre ORDER BY total DESC LIMIT 10")'
    
    # Extraer parámetros
    if '(' in test_call and test_call.endswith(')'):
        params_str = test_call[test_call.find('(')+1:-1]
        print(f"Parámetros extraídos: {params_str}")
        
        # Usar nuestro parser robusto
        result = parse_mcp_params_robust(params_str)
        
        print("\n🔍 RESULTADO DEL PARSING:")
        print(f"Database: {result.get('database', 'NO ENCONTRADO')}")
        print(f"Query: {result.get('query', 'NO ENCONTRADO')}")
        print(f"Query length: {len(result.get('query', ''))} chars")
        
        # Verificar que la query está completa
        expected_query = "SELECT nombre, COUNT(*) as total FROM core_registro GROUP BY nombre ORDER BY total DESC LIMIT 10"
        actual_query = result.get('query', '')
        
        if actual_query == expected_query:
            print("✅ PARSING CORRECTO - Query completa!")
            return True
        else:
            print("❌ PARSING INCORRECTO")
            print(f"Esperado: {expected_query}")
            print(f"Obtenido: {actual_query}")
            return False

if __name__ == "__main__":
    print("🔧 PROBANDO CORRECCIÓN DE PARSING")
    print("="*50)
    
    success = test_parsing()
    
    if success:
        print("\n🎉 ¡CORRECCIÓN EXITOSA!")
        print("El parsing ahora maneja correctamente las consultas SQL complejas")
    else:
        print("\n❌ La corrección necesita más trabajo") 