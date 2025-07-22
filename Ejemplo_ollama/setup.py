#!/usr/bin/env python3
# setup.py
import subprocess
import sys
import requests
import json

def install_requirements():
    """Instalar dependencias de requirements.txt"""
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def test_mariadb_connection():
    """Probar conexión a MariaDB"""
    print("🔍 Probando conexión a MariaDB...")
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
            print(f"✅ Conexión a MariaDB exitosa - Versión: {version}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a MariaDB: {e}")
        print("Verifica que:")
        print("  1. La IP 172.16.1.29 sea accesible")
        print("  2. El usuario 'controla' tenga permisos")
        print("  3. El puerto 3306 esté abierto")
        return False

def test_ollama_connection(host="localhost", port=11434):
    """Probar conexión a Ollama"""
    print(f"🦙 Probando conexión a Ollama en {host}:{port}...")
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            print(f"✅ Conexión a Ollama exitosa")
            print(f"   Modelos disponibles: {', '.join(model_names)}")
            
            if "llama3.1:8b" in model_names:
                print("✅ Modelo llama3.1:8b encontrado")
                return True
            else:
                print("⚠️  Modelo llama3.1:8b no encontrado")
                print("   Ejecuta: ollama pull llama3.1:8b")
                return False
        else:
            print(f"❌ Error en respuesta de Ollama: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a Ollama en {host}:{port}")
        print("Verifica que:")
        print("  1. Ollama esté ejecutándose")
        print("  2. El host y puerto sean correctos")
        print("  3. El firewall permita las conexiones")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def create_config_file(ollama_host="localhost", ollama_port=11434):
    """Crear archivo de configuración"""
    config = {
        "mariadb": {
            "host": "172.16.1.29",
            "user": "controla",
            "password": "controla",
            "charset": "utf8mb4"
        },
        "ollama": {
            "host": ollama_host,
            "port": ollama_port,
            "model": "llama3.1:8b"
        }
    }
    
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Archivo config.json creado")
        return True
    except Exception as e:
        print(f"❌ Error creando config.json: {e}")
        return False

def main():
    print("🚀 CONFIGURACIÓN DEL SISTEMA MCP + OLLAMA + MARIADB")
    print("=" * 55)
    
    # Paso 1: Instalar dependencias
    if not install_requirements():
        print("❌ No se pudieron instalar las dependencias. Abortando.")
        return
    
    print("\n" + "=" * 55)
    
    # Paso 2: Probar MariaDB
    mariadb_ok = test_mariadb_connection()
    
    print("\n" + "=" * 55)
    
    # Paso 3: Configurar Ollama
    ollama_host = input("🦙 IP de Ollama (Enter para localhost): ").strip() or "localhost"
    ollama_port = input("🦙 Puerto de Ollama (Enter para 11434): ").strip() or "11434"
    
    try:
        ollama_port = int(ollama_port)
    except ValueError:
        print("❌ Puerto inválido, usando 11434")
        ollama_port = 11434
    
    ollama_ok = test_ollama_connection(ollama_host, ollama_port)
    
    print("\n" + "=" * 55)
    
    # Paso 4: Crear configuración
    create_config_file(ollama_host, ollama_port)
    
    print("\n" + "=" * 55)
    
    # Resumen final
    print("📋 RESUMEN DE CONFIGURACIÓN:")
    print(f"  📊 MariaDB: {'✅ OK' if mariadb_ok else '❌ Error'}")
    print(f"  🦙 Ollama: {'✅ OK' if ollama_ok else '❌ Error'}")
    
    if mariadb_ok and ollama_ok:
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n🚀 Para usar el sistema ejecuta:")
        print("   python client.py")
    else:
        print("\n⚠️  Hay problemas en la configuración.")
        print("   Revisa los errores anteriores antes de continuar.")
    
    print("\n" + "=" * 55)

if __name__ == "__main__":
    main() 