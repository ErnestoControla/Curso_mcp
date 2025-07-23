#!/usr/bin/env python3
# test_integration.py
import asyncio
import json
import sys
from config_validator import ConfigValidator
from client import OllamaMCPClient

class IntegrationTester:
    """Tester de integración completa cliente-servidor MCP"""
    
    def __init__(self):
        self.client = None
        self.test_results = []
        
    async def setup(self):
        """Configurar el entorno de testing"""
        print("🔧 Configurando entorno de testing...")
        
        # Validar configuración primero
        validator = ConfigValidator()
        results = validator.run_full_validation()
        
        if not results["all_passed"]:
            print("❌ La configuración no es válida. No se pueden ejecutar tests.")
            return False
        
        # Crear cliente MCP
        self.client = OllamaMCPClient("172.16.1.37", 11434, "llama3.1:8b")
        
        return True
    
    async def test_mcp_connection(self) -> tuple[bool, str]:
        """Test: Conectar al servidor MCP"""
        try:
            async with self.client:
                if self.client.mcp_session:
                    tools = await self.client.mcp_session.list_tools()
                    return True, f"Conexión MCP exitosa - {len(tools.tools)} herramientas disponibles"
                else:
                    return False, "Sesión MCP no establecida"
        except Exception as e:
            return False, f"Error de conexión MCP: {e}"
    
    async def test_basic_tools(self) -> tuple[bool, str]:
        """Test: Herramientas básicas MCP"""
        try:
            async with self.client:
                # Test test_connection
                result = await self.client.execute_mcp_tool("test_connection")
                if not result.get("success"):
                    return False, f"test_connection falló: {result.get('error')}"
                
                # Test list_databases
                result = await self.client.execute_mcp_tool("list_databases")
                if not result.get("success"):
                    return False, f"list_databases falló: {result.get('error')}"
                
                db_count = result.get("count", 0)
                return True, f"Herramientas básicas funcionan - {db_count} bases de datos encontradas"
        except Exception as e:
            return False, f"Error en herramientas básicas: {e}"
    
    async def test_ai_integration(self) -> tuple[bool, str]:
        """Test: Integración con IA (Ollama)"""
        try:
            async with self.client:
                # Test simple de análisis con IA
                response = await self.client.analyze_with_ai("¿Qué bases de datos tienes disponibles?")
                
                if not response:
                    return False, "No se obtuvo respuesta de la IA"
                
                # Verificar que se ejecutaron herramientas MCP
                if "USAR_HERRAMIENTA_MCP" in response or "Ejecutando MCP" in response:
                    return True, "Integración IA-MCP funcionando correctamente"
                else:
                    return False, "La IA no está usando herramientas MCP correctamente"
        except Exception as e:
            return False, f"Error en integración IA: {e}"
    
    async def test_security_features(self) -> tuple[bool, str]:
        """Test: Características de seguridad"""
        try:
            async with self.client:
                # Test consulta peligrosa - debe ser rechazada
                dangerous_query = "DROP TABLE usuarios; SELECT * FROM datos"
                result = await self.client.execute_mcp_tool("execute_query", 
                                                           database="test", 
                                                           query=dangerous_query)
                
                if result.get("success"):
                    return False, "Consulta peligrosa fue permitida - FALLO DE SEGURIDAD"
                
                if "seguridad" in result.get("error", "").lower():
                    return True, "Validación de seguridad SQL funcionando correctamente"
                else:
                    return False, f"Consulta rechazada pero no por seguridad: {result.get('error')}"
        except Exception as e:
            return False, f"Error en test de seguridad: {e}"
    
    async def test_error_handling(self) -> tuple[bool, str]:
        """Test: Manejo de errores"""
        try:
            async with self.client:
                # Test herramienta inexistente
                result = await self.client.execute_mcp_tool("herramienta_inexistente")
                if result.get("success"):
                    return False, "Herramienta inexistente reportó éxito"
                
                # Test con parámetros inválidos
                result = await self.client.execute_mcp_tool("list_tables")  # Sin database requerido
                if result.get("success"):
                    return False, "Parámetros faltantes no detectados"
                
                return True, "Manejo de errores funcionando correctamente"
        except Exception as e:
            return False, f"Error en test de manejo de errores: {e}"
    
    async def run_all_tests(self):
        """Ejecutar todos los tests de integración"""
        print("🧪 INICIANDO TESTS DE INTEGRACIÓN COMPLETA")
        print("=" * 60)
        
        if not await self.setup():
            print("❌ Setup falló - abortando tests")
            return False
        
        tests = [
            ("🔗 Conexión MCP", self.test_mcp_connection),
            ("🛠️  Herramientas Básicas", self.test_basic_tools),
            ("🤖 Integración IA", self.test_ai_integration),
            ("🛡️  Seguridad", self.test_security_features),
            ("⚠️  Manejo de Errores", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Ejecutando {test_name}...")
            try:
                success, message = await test_func()
                status = "✅" if success else "❌"
                print(f"{status} {test_name}: {message}")
                
                self.test_results.append({
                    "name": test_name,
                    "success": success,
                    "message": message
                })
                
                if success:
                    passed += 1
                    
            except Exception as e:
                print(f"❌ {test_name}: Error inesperado - {e}")
                self.test_results.append({
                    "name": test_name,
                    "success": False,
                    "message": f"Error inesperado: {e}"
                })
        
        # Resumen final
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN DE TESTS: {passed}/{total} pasaron")
        
        if passed == total:
            print("🎉 ¡TODOS LOS TESTS PASARON!")
            print("✅ El sistema cliente-servidor está completamente funcional")
            print("\n🚀 Sistema listo para producción")
        elif passed > total // 2:
            print("⚠️  La mayoría de tests pasaron")
            print("📋 Revisa los fallos para optimización")
        else:
            print("❌ Múltiples tests fallaron")
            print("🔧 Requiere correcciones antes de usar")
        
        print("=" * 60)
        return passed == total

async def main():
    """Función principal"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 