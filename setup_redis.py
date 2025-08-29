#!/usr/bin/env python3
"""
Script de instalación y verificación para el protocolo Redis
"""

import subprocess
import sys
import asyncio
import json

def install_dependencies():
    """Instalar dependencias de Redis"""
    print("🔧 INSTALANDO DEPENDENCIAS...")
    
    packages = [
        "redis[hiredis]",  # Redis con soporte optimizado
        "asyncio-mqtt"     # Para futuras extensiones MQTT
    ]
    
    for package in packages:
        print(f"📦 Instalando {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✅ {package} instalado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {package}: {e}")
            return False
    
    return True

async def test_redis_connection():
    """Probar conexión a Redis"""
    print("\n🔌 PROBANDO CONEXIÓN A REDIS...")
    
    try:
        import redis.asyncio as redis
        
        # Configuración
        host = "lab3.redesuvg.cloud"
        port = 6379
        password = "UVGRedis2025"
        
        print(f"Conectando a {host}:{port}...")
        
        # Crear cliente
        client = redis.Redis(host=host, port=port, password=password)
        
        # Probar ping
        pong = await client.ping()
        if pong:
            print("✅ Conexión exitosa a Redis")
            
            # Probar pub/sub
            pubsub = client.pubsub()
            await pubsub.subscribe("test_channel")
            
            # Enviar mensaje de prueba
            await client.publish("test_channel", "test_message")
            
            # Limpiar
            await pubsub.close()
            await client.close()
            
            print("✅ Pub/Sub funcionando")
            return True
        else:
            print("❌ No se recibió respuesta del servidor")
            return False
            
    except ImportError:
        print("❌ Redis no está instalado")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def create_example_scenarios():
    """Crear archivos de ejemplo"""
    print("\n📁 CREANDO ARCHIVOS DE EJEMPLO...")
    
    # Escenarios de ejemplo
    scenarios = {
        "topologias": {
            "simple": {
                "descripcion": "Red lineal A-B-C",
                "nodos": {
                    "A": {"vecinos": {"B": 5}},
                    "B": {"vecinos": {"A": 5, "C": 3}},
                    "C": {"vecinos": {"B": 3}}
                }
            },
            "estrella": {
                "descripcion": "Red en estrella con centro A",
                "nodos": {
                    "A": {"vecinos": {"B": 2, "C": 4, "D": 6}},
                    "B": {"vecinos": {"A": 2}},
                    "C": {"vecinos": {"A": 4}},
                    "D": {"vecinos": {"A": 6}}
                }
            },
            "mesh": {
                "descripcion": "Red parcialmente mallada",
                "nodos": {
                    "A": {"vecinos": {"B": 5, "C": 3}},
                    "B": {"vecinos": {"A": 5, "C": 2, "D": 4}},
                    "C": {"vecinos": {"A": 3, "B": 2, "D": 1}},
                    "D": {"vecinos": {"B": 4, "C": 1}}
                }
            }
        },
        "algoritmos": {
            "flooding": {
                "descripcion": "Algoritmo de inundación",
                "ttl_default": 5,
                "requiere_topologia": False
            },
            "link_state": {
                "descripcion": "Link State Routing con Dijkstra",
                "ttl_default": 10,
                "requiere_topologia": True
            }
        }
    }
    
    try:
        with open('redis_scenarios.json', 'w') as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)
        print("✅ redis_scenarios.json creado")
        
        # Crear script de ejemplo
        example_script = '''#!/usr/bin/env python3
"""
Ejemplo básico de uso del protocolo Redis
"""

import asyncio
from redis_protocol import RedisProtocolNode

async def ejemplo_basico():
    """Ejemplo básico de comunicación"""
    print("🌊 EJEMPLO: Nodo A enviando mensaje con Flooding")
    
    # Crear nodo A
    node_a = RedisProtocolNode("A", "sec20", "simple")
    node_a.set_neighbours({"B": 5})
    node_a.set_algorithm("flooding")
    
    if await node_a.connect():
        # Enviar init
        await node_a.send_init_message()
        
        # Enviar mensaje
        await node_a.send_message("C", "¡Hola desde A!")
        
        # Finalizar
        await node_a.send_done_message()
        await node_a.disconnect()
        
        print("✅ Ejemplo completado")
    else:
        print("❌ No se pudo conectar")

if __name__ == "__main__":
    asyncio.run(ejemplo_basico())
'''
        
        with open('ejemplo_redis.py', 'w') as f:
            f.write(example_script)
        print("✅ ejemplo_redis.py creado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando archivos: {e}")
        return False

def show_usage_guide():
    """Mostrar guía de uso"""
    print("\n" + "="*60)
    print("  📖 GUÍA DE USO - PROTOCOLO REDIS")
    print("="*60)
    print()
    print("🚀 ARCHIVOS PRINCIPALES:")
    print("  • redis_protocol.py     - Protocolo base")
    print("  • redis_client.py       - Cliente interactivo")
    print("  • redis_test_suite.py   - Suite de pruebas")
    print("  • ejemplo_redis.py      - Ejemplo básico")
    print()
    print("🎯 COMANDOS DE EJECUCIÓN:")
    print("  python redis_client.py       # Cliente interactivo")
    print("  python redis_test_suite.py   # Suite de pruebas")
    print("  python ejemplo_redis.py      # Ejemplo básico")
    print()
    print("📡 PROTOCOLO DE MENSAJES:")
    print("  • INIT: Inicialización con vecinos")
    print("  • MESSAGE: Envío de datos")
    print("  • DONE: Finalización")
    print()
    print("🎯 ALGORITMOS SOPORTADOS:")
    print("  • Flooding: Inundación de mensajes")
    print("  • Link State: Enrutamiento con Dijkstra")
    print()
    print("🌐 FORMATO DE CANALES:")
    print("  seccion.topologia.nodo")
    print("  Ejemplo: sec20.simple.A")
    print()

async def main():
    """Función principal de instalación"""
    print("🚀 CONFIGURACIÓN DEL PROTOCOLO REDIS")
    print("="*50)
    
    # Paso 1: Instalar dependencias
    if not install_dependencies():
        print("❌ Error en instalación de dependencias")
        return
    
    # Paso 2: Probar conexión
    if not await test_redis_connection():
        print("⚠️ Problema con conexión Redis")
        print("   Verificar conectividad de red")
    
    # Paso 3: Crear archivos de ejemplo
    if not create_example_scenarios():
        print("❌ Error creando archivos de ejemplo")
        return
    
    # Paso 4: Mostrar guía
    show_usage_guide()
    
    print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
    print("💡 Usar: python redis_client.py para empezar")

if __name__ == "__main__":
    asyncio.run(main())
