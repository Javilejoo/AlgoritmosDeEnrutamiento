#!/usr/bin/env python3
"""
Script de diagnóstico para verificar comunicación Redis
"""

import asyncio
import redis.asyncio as redis
import json

# Configuración
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

async def test_communication():
    """Probar comunicación básica Redis"""
    print("🔍 DIAGNÓSTICO DE COMUNICACIÓN REDIS")
    print("="*50)
    
    # Conectar a Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    
    try:
        # Verificar conexión
        await r.ping()
        print("✅ Conexión a Redis exitosa")
        
        # Crear pubsub
        pubsub = r.pubsub()
        
        # Suscribirse a varios canales de prueba
        test_channels = [
            "channel:sec20.topologia2.nodo10",
            "channel:sec20.topologia2.nodo2", 
            "channel:sec20.topologia2.nodo6",
            "channel:sec20.topologia2.nodo7",
            "channel:sec20.topologia2.nodo8",
            "channel:sec20.topologia2.nodo9"
        ]
        
        print(f"\n📡 Suscribiéndose a {len(test_channels)} canales...")
        for channel in test_channels:
            await pubsub.subscribe(channel)
            print(f"   📻 {channel}")
        
        print("\n🎯 ENVIANDO MENSAJE DE PRUEBA...")
        test_message = {
            "type": "message",
            "origin": "nodo10",
            "destination": "nodo2", 
            "content": "PRUEBA DE DIAGNÓSTICO - Hola desde nodo10",
            "timestamp": "2025-08-28T10:00:00",
            "algorithm": "flooding"
        }
        
        # Enviar a canal de nodo2
        channel_nodo2 = "channel:sec20.topologia2.nodo2"
        await r.publish(channel_nodo2, json.dumps(test_message))
        print(f"✅ Mensaje enviado a: {channel_nodo2}")
        
        print(f"\n👂 ESCUCHANDO MENSAJES...")
        print("Presiona Ctrl+C para detener")
        
        message_count = 0
        async for message in pubsub.listen():
            if message["type"] == "message":
                message_count += 1
                channel = message["channel"].decode()
                data = message["data"].decode()
                
                print(f"\n MENSAJE RECIBIDO #{message_count}")
                print(f"    Canal: {channel}")
                print(f"    Datos: {data[:100]}...")
                
                try:
                    parsed = json.loads(data)
                    print(f"    Origen: {parsed.get('origin', 'N/A')}")
                    print(f"   🎯 Destino: {parsed.get('destination', 'N/A')}")
                    print(f"   💬 Contenido: {parsed.get('content', 'N/A')}")
                except:
                    print("   ⚠️  Mensaje no es JSON válido")
                
                if message_count >= 10:
                    print("\n🛑 Límite de mensajes alcanzado, deteniendo...")
                    break
                    
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico detenido por usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await pubsub.close()
        await r.close()
        print("🔚 Diagnóstico completado")

if __name__ == "__main__":
    asyncio.run(test_communication())
