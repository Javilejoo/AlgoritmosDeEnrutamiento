"""
Script de instalación y configuración automática
Para preparar el entorno del laboratorio de XMPP
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(title):
    """Imprime un header estilizado"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step, description):
    """Imprime un paso del proceso"""
    print(f"\n🔧 PASO {step}: {description}")
    print("-" * 40)

def run_command(command, description=""):
    """Ejecuta un comando y maneja errores"""
    try:
        print(f"   Ejecutando: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description or 'Comando exitoso'}")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        return False

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} no compatible")
        print("   📋 Se requiere Python 3.7 o superior")
        return False

def install_dependencies():
    """Instala las dependencias necesarias"""
    dependencies = [
        "slixmpp",      # Para XMPP
        "asyncio",      # Async support (ya incluido en Python 3.7+)
        "dataclasses",  # Para estructuras de datos (incluido en 3.7+)
    ]
    
    print("   📦 Instalando dependencias...")
    
    for dep in dependencies:
        if dep in ["asyncio", "dataclasses"]:
            print(f"   ✅ {dep} (incluido en Python 3.7+)")
            continue
            
        print(f"   📥 Instalando {dep}...")
        success = run_command(f"pip install {dep}", f"{dep} instalado")
        if not success:
            print(f"   ⚠️ Error instalando {dep}, continuando...")

def create_project_structure():
    """Crea la estructura de directorios del proyecto"""
    directories = [
        "configs",
        "logs", 
        "results",
        "scenarios",
        "reports"
    ]
    
    print("   📁 Creando estructura de directorios...")
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}/")

def generate_sample_configs():
    """Genera archivos de configuración de ejemplo"""
    # Ejecutar el generador de configuraciones
    try:
        print("   📝 Generando configuraciones de ejemplo...")
        from config_manager import ConfigManager
        ConfigManager.create_config_files()
        print("   ✅ Configuraciones creadas")
    except Exception as e:
        print(f"   ❌ Error generando configuraciones: {e}")

def create_batch_scripts():
    """Crea scripts batch para inicio rápido"""
    
    # Script para Windows
    batch_content = """@echo off
echo ========================================
echo   LABORATORIO ALGORITMOS DE ENRUTAMIENTO
echo ========================================
echo.
echo Iniciando interfaz principal...
python main_xmpp.py
pause
"""
    
    with open("start_lab.bat", "w") as f:
        f.write(batch_content)
    
    print("   ✅ start_lab.bat creado")
    
    # Script para Linux/Mac
    shell_content = """#!/bin/bash
echo "========================================"
echo "  LABORATORIO ALGORITMOS DE ENRUTAMIENTO"
echo "========================================"
echo ""
echo "Iniciando interfaz principal..."
python3 main_xmpp.py
"""
    
    with open("start_lab.sh", "w") as f:
        f.write(shell_content)
    
    # Hacer ejecutable en sistemas Unix
    try:
        run_command("chmod +x start_lab.sh", "Script shell ejecutable")
    except:
        pass
    
    print("   ✅ start_lab.sh creado")

def create_development_config():
    """Crea configuración para desarrollo"""
    dev_config = {
        "mode": "development",
        "use_xmpp": False,
        "log_level": "DEBUG",
        "test_nodes": ["A", "B", "C", "D"],
        "default_topology": "topology.json",
        "auto_start": True,
        "simulation_speed": 1.0
    }
    
    with open("configs/development.json", "w") as f:
        json.dump(dev_config, f, indent=2)
    
    print("   ✅ configs/development.json creado")

def create_production_config():
    """Crea configuración para producción"""
    prod_config = {
        "mode": "production", 
        "use_xmpp": True,
        "log_level": "INFO",
        "xmpp_server": "localhost",
        "xmpp_port": 5222,
        "test_nodes": ["A", "B", "C", "D", "E", "F", "G", "H", "I"],
        "default_topology": "topology.json",
        "auto_start": False,
        "simulation_speed": 1.0,
        "timeout": 30
    }
    
    with open("configs/production.json", "w") as f:
        json.dump(prod_config, f, indent=2)
    
    print("   ✅ configs/production.json creado")

def create_test_scenarios():
    """Crea escenarios de prueba predefinidos"""
    try:
        print("   🎬 Generando escenarios de prueba...")
        from config_manager import ScenarioGenerator, ConfigManager
        
        scenarios = {
            "linear_4": ScenarioGenerator.linear_topology(4),
            "ring_5": ScenarioGenerator.ring_topology(5), 
            "star_6": ScenarioGenerator.star_topology(6),
            "mesh_4": ScenarioGenerator.mesh_topology(4)
        }
        
        for name, scenario in scenarios.items():
            ConfigManager.save_topology(scenario, f"scenarios/{name}.json")
            print(f"   ✅ scenarios/{name}.json")
            
    except Exception as e:
        print(f"   ❌ Error creando escenarios: {e}")

def verify_installation():
    """Verifica que todo esté instalado correctamente"""
    print("   🔍 Verificando instalación...")
    
    # Verificar archivos críticos
    critical_files = [
        "protocolo.py",
        "xmpp_client.py", 
        "routing_node.py",
        "routing_algorithms.py",
        "config_manager.py",
        "test_coordinator.py",
        "main_xmpp.py"
    ]
    
    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"   ✅ {file}")
    
    if missing_files:
        print(f"   ❌ Archivos faltantes: {missing_files}")
        return False
    
    # Verificar que se pueden importar los módulos
    try:
        print("   🧪 Probando imports...")
        import protocolo
        import config_manager
        print("   ✅ Módulos importados correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error importando módulos: {e}")
        return False

def create_readme_quick():
    """Crea un README rápido de referencia"""
    quick_readme = """# INICIO RÁPIDO - LABORATORIO ALGORITMOS DE ENRUTAMIENTO

## 🚀 Comandos Esenciales

### Interfaz Principal:
```bash
python main_xmpp.py
```

### Desarrollo Local (sin XMPP):
1. Ejecutar interfaz principal
2. Seleccionar opción 1 (crear configuraciones)
3. Seleccionar opción 7-10 (pruebas)

### Producción con XMPP:
1. Instalar: `pip install slixmpp`
2. Configurar servidor XMPP
3. Editar nodes.json con JIDs reales
4. Cambiar use_xmpp=True en código

## 📁 Estructura Importante

- `main_xmpp.py` - Interfaz principal
- `topology.json` - Configuración de red
- `nodes.json` - Configuración de nodos
- `configs/` - Configuraciones adicionales
- `scenarios/` - Escenarios de prueba
- `results/` - Resultados de pruebas

## 🆘 Solución de Problemas

1. **Error de imports**: Verificar Python 3.7+
2. **Error XMPP**: Usar modo offline (use_xmpp=False)
3. **Configuración**: Regenerar con opción 1 del menú

## 🎯 Algoritmos Disponibles

- **Dijkstra**: Centralizado
- **DVR**: Distance Vector Routing
- **LSR**: Link State Routing
- **Flooding**: Para propagación

¡Listo para el laboratorio! 🎉
"""
    
    with open("INICIO_RAPIDO.md", "w") as f:
        f.write(quick_readme)
    
    print("   ✅ INICIO_RAPIDO.md creado")

def main():
    """Función principal de instalación"""
    print_header("INSTALADOR DEL LABORATORIO DE ALGORITMOS DE ENRUTAMIENTO")
    
    print("Este script configurará tu entorno para el laboratorio de XMPP")
    print("y algoritmos de enrutamiento distribuidos.")
    
    # Paso 1: Verificar Python
    print_step(1, "Verificando versión de Python")
    if not check_python_version():
        print("\n❌ INSTALACIÓN ABORTADA: Versión de Python no compatible")
        return False
    
    # Paso 2: Instalar dependencias
    print_step(2, "Instalando dependencias")
    install_dependencies()
    
    # Paso 3: Crear estructura
    print_step(3, "Creando estructura del proyecto")
    create_project_structure()
    
    # Paso 4: Generar configuraciones
    print_step(4, "Generando configuraciones")
    generate_sample_configs()
    create_development_config()
    create_production_config()
    
    # Paso 5: Crear escenarios
    print_step(5, "Creando escenarios de prueba")
    create_test_scenarios()
    
    # Paso 6: Scripts de inicio
    print_step(6, "Creando scripts de inicio")
    create_batch_scripts()
    create_readme_quick()
    
    # Paso 7: Verificación
    print_step(7, "Verificando instalación")
    if verify_installation():
        print("\n🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Ejecutar: python main_xmpp.py")
        print("   2. Seleccionar opción 1 para configurar")
        print("   3. Probar algoritmos con opciones 7-10")
        print("   4. Para XMPP real, editar configs/production.json")
        print("\n💡 Consulta INICIO_RAPIDO.md para más información")
        return True
    else:
        print("\n❌ INSTALACIÓN INCOMPLETA")
        print("   Revisa los errores anteriores y ejecuta nuevamente")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            input("\n⏎ Presiona Enter para cerrar...")
        else:
            input("\n⏎ Revisa los errores y presiona Enter...")
    except KeyboardInterrupt:
        print("\n\n👋 Instalación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\n⏎ Presiona Enter para cerrar...")
