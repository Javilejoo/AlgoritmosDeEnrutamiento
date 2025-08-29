#!/usr/bin/env python3
"""
Cliente Redis compatible con ambos formatos de canal
"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime

# Configuración
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

async def test_dual_format():
    """Probar comunicación con ambos formatos"""
    print("🔄 PRUEBA DE COMPATIBILIDAD DUAL")
    print("="*50)
    
    # Conectar a Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    
    try:
        await r.ping()
        print("✅ Conexión a Redis exitosa")
        
        # Crear pubsub
        pubsub = r.pubsub()
        
        # Suscribirse a AMBOS formatos para nodo10
        channels_to_listen = [
            "channel:sec20.topologia2.nodo10",  # Tu formato
            "sec20.topologia2.nodo10",          # Formato de otros
            "channel:sec20.topologia2.nodo2",   # Para tu compañera (tu formato)
            "sec20.topologia2.nodo2"            # Para tu compañera (formato otros)
        ]
        
        print(f"\n📡 Suscribiéndose a ambos formatos...")
        for channel in channels_to_listen:
            await pubsub.subscribe(channel)
            print(f"   📻 {channel}")
        
        print(f"\n🎯 ENVIANDO MENSAJES EN AMBOS FORMATOS...")
        
        test_message = {
            "type": "message",
            "origin": "nodo10",
            "destination": "nodo2",
            "content": "HOLA COMPAÑERA - Test dual format",
            "timestamp": datetime.now().isoformat(),
            "algorithm": "flooding"
        }
        
        # Enviar a AMBOS formatos para nodo2
        channels_to_send = [
            "channel:sec20.topologia2.nodo2",  # Tu formato
            "sec20.topologia2.nodo2"           # Formato que usan otros
        ]
        
        for channel in channels_to_send:
            await r.publish(channel, json.dumps(test_message))
            print(f"✅ Mensaje enviado a: {channel}")
        
        print(f"\n👂 ESCUCHANDO RESPUESTAS...")
        print("Presiona Ctrl+C para detener")
        
        message_count = 0
        async for message in pubsub.listen():
            if message["type"] == "message":
                message_count += 1
                channel = message["channel"].decode()
                data = message["data"].decode()
                
                print(f"\n📨 MENSAJE #{message_count}")
                print(f"   📻 Canal: {channel}")
                
                try:
                    parsed = json.loads(data)
                    origin = parsed.get('origin', 'Unknown')
                    content = parsed.get('content', 'No content')
                    
                    print(f"   👤 De: {origin}")
                    print(f"   💬 Mensaje: {content}")
                    
                    # Detectar si es de tu compañera
                    if origin != "nodo10" and origin != "Unknown":
                        print(f"🎉 ¡MENSAJE DE COMPAÑERA RECIBIDO!")
                        print(f"   🔍 Formato usado: {channel}")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️  Mensaje no JSON: {data[:50]}...")
                
                if message_count >= 20:
                    break
                    
    except KeyboardInterrupt:
        print("\n🛑 Prueba detenida")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            await pubsub.aclose()
            await r.aclose()
        except:
            pass
        print("🔚 Prueba completada")

if __name__ == "__main__":
    asyncio.run(test_dual_format())
