#!/usr/bin/env python3
"""
Monitor completo de Redis - Ve TODOS los canales activos
"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime

# Configuración
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

async def monitor_all_channels():
    """Monitorear todos los canales activos en Redis"""
    print("🔍 MONITOR COMPLETO DE REDIS")
    print("="*60)
    
    # Conectar a Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    
    try:
        # Verificar conexión
        await r.ping()
        print("✅ Conexión a Redis exitosa")
        
        # Obtener todos los canales con patrón
        print("\n🔎 Buscando canales activos...")
        
        # Buscar diferentes patrones de canales
        patterns = [
            "channel:*",
            "sec20.*",
            "*nodo*",
            "*topologia*"
        ]
        
        all_channels = set()
        for pattern in patterns:
            channels = await r.pubsub_channels(pattern)
            for channel in channels:
                all_channels.add(channel.decode() if isinstance(channel, bytes) else channel)
        
        if all_channels:
            print(f"📡 Encontrados {len(all_channels)} canales activos:")
            for channel in sorted(all_channels):
                print(f"   📻 {channel}")
        else:
            print("⚠️  No se encontraron canales activos")
            print("   Esto podría significar que nadie está conectado")
        
        # Crear pubsub y suscribirse a patrones amplios
        pubsub = r.pubsub()
        
        # Suscribirse a patrones que capturen todo
        patterns_to_subscribe = [
            "channel:sec20.*",
            "sec20.*",
            "*"  # Captura TODO
        ]
        
        print(f"\n📡 Suscribiéndose a patrones amplios...")
        for pattern in patterns_to_subscribe:
            await pubsub.psubscribe(pattern)
            print(f"   🔍 Patrón: {pattern}")
        
        # También suscribirse a canales específicos conocidos
        specific_channels = [
            "channel:sec20.topologia2.nodo1",
            "channel:sec20.topologia2.nodo2",
            "channel:sec20.topologia2.nodo6",
            "channel:sec20.topologia2.nodo7",
            "channel:sec20.topologia2.nodo8",
            "channel:sec20.topologia2.nodo9",
            "channel:sec20.topologia2.nodo10",
            # Variaciones posibles
            "sec20.topologia2.nodo2",
            "sec20.topologia2.nodo10"
        ]
        
        for channel in specific_channels:
            await pubsub.subscribe(channel)
        
        print(f"\n🎯 ENVIANDO MENSAJE DE PRUEBA AMPLIO...")
        test_message = {
            "type": "message",
            "origin": "monitor_test",
            "destination": "broadcast",
            "content": "MENSAJE DE PRUEBA DESDE MONITOR - ¿Alguien me escucha?",
            "timestamp": datetime.now().isoformat(),
            "algorithm": "monitor"
        }
        
        # Enviar a múltiples canales posibles
        test_channels = [
            "channel:sec20.topologia2.nodo2",
            "channel:sec20.topologia2.nodo10",
            "sec20.topologia2.nodo2",
            "sec20.topologia2.nodo10"
        ]
        
        for channel in test_channels:
            await r.publish(channel, json.dumps(test_message))
            print(f"✅ Mensaje enviado a: {channel}")
        
        print(f"\n👂 MONITOREANDO TODOS LOS MENSAJES...")
        print("⏰ Timestamp | 📻 Canal | 👤 Origen | 🎯 Destino | 💬 Contenido")
        print("-" * 80)
        
        message_count = 0
        start_time = datetime.now()
        
        async for message in pubsub.listen():
            if message["type"] in ["message", "pmessage"]:
                message_count += 1
                
                # Obtener canal
                if message["type"] == "pmessage":
                    channel = message["channel"].decode()
                    pattern = message["pattern"].decode()
                else:
                    channel = message["channel"].decode()
                    pattern = "direct"
                
                data = message["data"].decode()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Intentar parsear JSON
                try:
                    parsed = json.loads(data)
                    origin = parsed.get('origin', 'N/A')
                    destination = parsed.get('destination', 'N/A')
                    content = parsed.get('content', 'N/A')[:30] + "..." if len(parsed.get('content', '')) > 30 else parsed.get('content', 'N/A')
                    
                    print(f"{timestamp} | {channel[:20]:20} | {origin[:8]:8} | {destination[:8]:8} | {content}")
                    
                    # Si es de otro usuario, mostrar detalles completos
                    if origin not in ['nodo10', 'monitor_test'] and origin != 'N/A':
                        print(f"🎉 ¡MENSAJE DE OTRO USUARIO DETECTADO!")
                        print(f"   📻 Canal: {channel}")
                        print(f"   📄 Mensaje completo: {data}")
                        print(f"   🔍 Patrón usado: {pattern}")
                        print("-" * 40)
                        
                except json.JSONDecodeError:
                    print(f"{timestamp} | {channel[:20]:20} | RAW_DATA | N/A | {data[:30]}...")
                
                # Límite de mensajes para no sobrecargar
                if message_count >= 50:
                    print(f"\n🛑 Límite de {message_count} mensajes alcanzado")
                    break
                    
                # Timeout después de 2 minutos
                if (datetime.now() - start_time).seconds > 120:
                    print(f"\n⏱️  Timeout de 2 minutos alcanzado")
                    break
                    
    except KeyboardInterrupt:
        print("\n🛑 Monitor detenido por usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            await pubsub.aclose()
            await r.aclose()
        except:
            pass
        print("🔚 Monitor completado")

if __name__ == "__main__":
    asyncio.run(monitor_all_channels())
