# server.py
from mcp.server.fastmcp import FastMCP
import math
import json
from datetime import datetime
import os

# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Herramienta de multiplicación
@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


# Herramienta de calculadora avanzada
@mcp.tool()
def calculate_area_circle(radius: float) -> dict:
    """Calculate the area and circumference of a circle given its radius"""
    if radius < 0:
        return {"error": "Radius cannot be negative"}
    
    area = math.pi * radius ** 2
    circumference = 2 * math.pi * radius
    
    return {
        "radius": radius,
        "area": round(area, 2),
        "circumference": round(circumference, 2)
    }


# Herramienta de fecha y hora
@mcp.tool()
def get_current_time(timezone: str = "UTC") -> dict:
    """Get current date and time information"""
    now = datetime.now()
    return {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": timezone,
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B")
    }


# Herramienta de manipulación de texto
@mcp.tool()
def text_analyzer(text: str) -> dict:
    """Analyze text and return statistics"""
    words = text.split()
    sentences = text.count('.') + text.count('!') + text.count('?')
    
    return {
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(' ', '')),
        "word_count": len(words),
        "sentence_count": sentences,
        "average_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0,
        "longest_word": max(words, key=len) if words else "",
        "shortest_word": min(words, key=len) if words else ""
    }


# Herramienta de conversión de temperatura
@mcp.tool()
def convert_temperature(temperature: float, from_unit: str, to_unit: str) -> dict:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin"""
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    # Convertir todo a Celsius primero
    if from_unit == "fahrenheit" or from_unit == "f":
        celsius = (temperature - 32) * 5/9
    elif from_unit == "kelvin" or from_unit == "k":
        celsius = temperature - 273.15
    elif from_unit == "celsius" or from_unit == "c":
        celsius = temperature
    else:
        return {"error": "Invalid from_unit. Use 'celsius', 'fahrenheit', or 'kelvin'"}
    
    # Convertir de Celsius a la unidad deseada
    if to_unit == "fahrenheit" or to_unit == "f":
        result = (celsius * 9/5) + 32
    elif to_unit == "kelvin" or to_unit == "k":
        result = celsius + 273.15
    elif to_unit == "celsius" or to_unit == "c":
        result = celsius
    else:
        return {"error": "Invalid to_unit. Use 'celsius', 'fahrenheit', or 'kelvin'"}
    
    return {
        "original": f"{temperature}° {from_unit}",
        "converted": f"{round(result, 2)}° {to_unit}",
        "celsius_equivalent": f"{round(celsius, 2)}° C"
    }


# Herramienta de generación de contraseñas
@mcp.tool()
def generate_password(length: int = 12, include_symbols: bool = True) -> dict:
    """Generate a random password"""
    import random
    import string
    
    if length < 4:
        return {"error": "Password length must be at least 4 characters"}
    
    characters = string.ascii_letters + string.digits
    if include_symbols:
        characters += "!@#$%^&*"
    
    password = ''.join(random.choice(characters) for _ in range(length))
    
    return {
        "password": password,
        "length": length,
        "includes_symbols": include_symbols,
        "strength_tips": [
            "Use a mix of uppercase and lowercase letters",
            "Include numbers and symbols",
            "Make it at least 12 characters long",
            "Avoid common words or personal information"
        ]
    }


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Agregar recurso de información del sistema
@mcp.resource("system://info")
def get_system_info() -> str:
    """Get basic system information"""
    info = {
        "current_directory": os.getcwd(),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.name,
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(info, indent=2)


# Entry point to run the server
if __name__ == "__main__":
    mcp.run()