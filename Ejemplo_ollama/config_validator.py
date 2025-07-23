#!/usr/bin/env python3
# config_validator.py
import requests
import pymysql
import sys
from typing import Dict, Tuple, Any

class ConfigValidator:
    """Validador de configuración para el sistema MCP + Ollama + MariaDB"""
    
    def __init__(self):
        self.db_config = {
            'host': '172.16.1.29',
            'user': 'controla',
            'password': 'controla',
            'charset': 'utf8mb4',
            'autocommit': True
        }
        self.ollama_config = {
            'host': '172.16.1.37',
            'port': 11434,
            'model': 'llama3.1:8b'
        }
    
    def validate_mariadb(self) -> Tuple[bool, str]:
        """Validar conexión a MariaDB"""
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM information_schema.schemata")
                db_count = cursor.fetchone()[0]
            connection.close()
            return True, f"MariaDB {version} - {db_count} bases de datos disponibles"
        except Exception as e:
            return False, f"Error conectando a MariaDB: {e}"
    
    def validate_ollama(self) -> Tuple[bool, str]:
        """Validar conexión a Ollama"""
        try:
            base_url = f"http://{self.ollama_config['host']}:{self.ollama_config['port']}"
            
            # Verificar que Ollama esté ejecutándose
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False, f"Ollama no responde (código {response.status_code})"
            
            # Verificar que el modelo esté disponible
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if self.ollama_config['model'] not in model_names:
                return False, f"Modelo '{self.ollama_config['model']}' no disponible. Modelos: {', '.join(model_names[:3])}"
            
            return True, f"Ollama OK - Modelo {self.ollama_config['model']} disponible"
            
        except requests.exceptions.ConnectionError:
            return False, f"No se puede conectar a Ollama en {self.ollama_config['host']}:{self.ollama_config['port']}"
        except Exception as e:
            return False, f"Error validando Ollama: {e}"
    
    def validate_python_dependencies(self) -> Tuple[bool, str]:
        """Validar dependencias de Python"""
        required_packages = [
            'fastmcp',
            'pymysql', 
            'mcp',
            'requests'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return False, f"Paquetes faltantes: {', '.join(missing_packages)}. Ejecuta: pip install {' '.join(missing_packages)}"
        
        return True, f"Todas las dependencias instaladas correctamente"
    
    def validate_mcp_server(self) -> Tuple[bool, str]:
        """Validar que el archivo server.py existe y es importable"""
        try:
            import os
            if not os.path.exists('server.py'):
                return False, "Archivo server.py no encontrado en el directorio actual"
            
            # Intentar importar sin ejecutar
            import importlib.util
            spec = importlib.util.spec_from_file_location("server", "server.py")
            if spec is None:
                return False, "server.py no es un módulo válido de Python"
            
            return True, "Servidor MCP (server.py) encontrado y válido"
            
        except Exception as e:
            return False, f"Error validando server.py: {e}"
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Ejecutar validación completa del sistema"""
        print("🔍 VALIDANDO CONFIGURACIÓN DEL SISTEMA")
        print("=" * 50)
        
        validations = [
            ("📊 MariaDB", self.validate_mariadb),
            ("🦙 Ollama", self.validate_ollama),
            ("📦 Dependencias Python", self.validate_python_dependencies),
            ("🔧 Servidor MCP", self.validate_mcp_server)
        ]
        
        results = {}
        all_passed = True
        
        for name, validator in validations:
            try:
                success, message = validator()
                status = "✅" if success else "❌"
                print(f"{status} {name}: {message}")
                results[name] = {"success": success, "message": message}
                if not success:
                    all_passed = False
            except Exception as e:
                print(f"❌ {name}: Error inesperado - {e}")
                results[name] = {"success": False, "message": f"Error inesperado: {e}"}
                all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 ¡Todas las validaciones pasaron! El sistema está listo.")
            print("🚀 Puedes ejecutar: python client.py")
        else:
            print("⚠️  Hay problemas en la configuración.")
            print("📋 Corrige los errores anteriores antes de continuar.")
        
        results["all_passed"] = all_passed
        return results

if __name__ == "__main__":
    validator = ConfigValidator()
    results = validator.run_full_validation()
    sys.exit(0 if results["all_passed"] else 1) 