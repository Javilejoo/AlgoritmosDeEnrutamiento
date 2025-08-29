#!/usr/bin/env python3
"""
Diagnóstico completo de comunicación Redis
Verifica si realmente hay mensajes de otros estudiantes
"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime

# Configuración
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

async def full_diagnosis():
    """Diagnóstico completo del estado de Redis"""
    print("🔍 DIAGNÓSTICO COMPLETO DE REDIS")
    print("="*60)
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    
    try:
        # 1. Verificar conexión
        await r.ping()
        print("✅ Conexión a Redis exitosa")
        
        # 2. Obtener información del servidor
        print(f"\n📊 INFORMACIÓN DEL SERVIDOR:")
        info = await r.info()
        print(f"   📡 Versión Redis: {info.get('redis_version', 'N/A')}")
        print(f"   🔗 Clientes conectados: {info.get('connected_clients', 'N/A')}")
        print(f"   📨 Comandos procesados: {info.get('total_commands_processed', 'N/A')}")
        
        # 3. Buscar TODOS los canales activos
        print(f"\n🔎 BUSCANDO CANALES ACTIVOS...")
        
        # Patrones diferentes para buscar canales
        patterns = ["*", "sec20*", "*nodo*", "*topologia*", "channel:*"]
        all_channels = set()
        
        for pattern in patterns:
            try:
                channels = await r.pubsub_channels(pattern)
                for channel in channels:
                    channel_name = channel.decode() if isinstance(channel, bytes) else channel
                    all_channels.add(channel_name)
            except Exception as e:
                print(f"   ⚠️  Error buscando patrón {pattern}: {e}")
        
        if all_channels:
            print(f"📡 Encontrados {len(all_channels)} canales activos:")
            sorted_channels = sorted(all_channels)
            for i, channel in enumerate(sorted_channels):
                print(f"   {i+1:2d}. {channel}")
        else:
            print("❌ No se encontraron canales activos")
            print("   Esto podría indicar que nadie está publicando mensajes")
        
        # 4. Crear monitor universal
        print(f"\n👂 INICIANDO MONITOR UNIVERSAL...")
        pubsub = r.pubsub()
        
        # Suscribirse a patrones amplios
        monitor_patterns = [
            "*",                    # Todo
            "sec20.*",             # Sección 20
            "*nodo*",              # Cualquier nodo
            "*topologia*"          # Cualquier topología
        ]
        
        for pattern in monitor_patterns:
            await pubsub.psubscribe(pattern)
            print(f"   🔍 Patrón: {pattern}")
        
        # También suscribirse a canales específicos conocidos
        specific_channels = [
            "sec20.topologia2.nodo1",
            "sec20.topologia2.nodo2", 
            "sec20.topologia2.nodo3",
            "sec20.topologia2.nodo4",
            "sec20.topologia2.nodo5",
            "sec20.topologia2.nodo6",
            "sec20.topologia2.nodo7",
            "sec20.topologia2.nodo8",
            "sec20.topologia2.nodo9",
            "sec20.topologia2.nodo10"
        ]
        
        for channel in specific_channels:
            await pubsub.subscribe(channel)
        
        # 5. Enviar mensaje de prueba
        print(f"\n🎯 ENVIANDO MENSAJE DE PRUEBA...")
        test_msg = {
            "proto": "lsr",
            "type": "message",
            "from": "sec20.topologia2.nodo10",
            "to": "sec20.topologia2.nodo2", 
            "ttl": 5,
            "headers": [],
            "payload": f"PRUEBA DIAGNÓSTICO - {datetime.now().isoformat()}"
        }
        
        # Enviar a múltiples formatos de canal
        test_channels = [
            "sec20.topologia2.nodo2",      # Formato estándar
            "channel:sec20.topologia2.nodo2",  # Con prefijo channel
            "sec20.topologia2.nodo10"      # Nuestro propio canal
        ]
        
        for channel in test_channels:
            await r.publish(channel, json.dumps(test_msg))
            print(f"✅ Mensaje enviado a: {channel}")
        
        # 6. Monitorear actividad
        print(f"\n📻 MONITOREANDO ACTIVIDAD (60 segundos)...")
        print("⏰ Time  | 🔄 Type | 📻 Channel | 👤 From | 🎯 To | 💬 Content")
        print("-" * 80)
        
        message_count = 0
        foreign_messages = 0
        start_time = datetime.now()
        
        try:
            async for message in pubsub.listen():
                if message["type"] in ["message", "pmessage"]:
                    message_count += 1
                    
                    # Obtener detalles del mensaje
                    if message["type"] == "pmessage":
                        channel = message["channel"].decode()
                        pattern = message["pattern"].decode()
                    else:
                        channel = message["channel"].decode()
                        pattern = "direct"
                    
                    data = message["data"].decode()
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Intentar parsear como JSON LSR
                    try:
                        parsed = json.loads(data)
                        proto = parsed.get("proto", "")
                        msg_type = parsed.get("type", "")
                        from_node = parsed.get("from", "Unknown")
                        to_node = parsed.get("to", "Unknown") 
                        payload = str(parsed.get("payload", ""))[:20]
                        
                        # Detectar si es de otro usuario
                        is_foreign = from_node != "sec20.topologia2.nodo10" and "nodo10" not in from_node
                        if is_foreign:
                            foreign_messages += 1
                            marker = "🎉"
                        else:
                            marker = "📤"
                        
                        print(f"{timestamp} | {msg_type:7} | {channel[-20:]:20} | {from_node[-8:]:8} | {to_node[-8:]:8} | {payload}")
                        
                        if is_foreign:
                            print(f"{marker} ¡MENSAJE DE OTRO ESTUDIANTE!")
                            print(f"    📄 Mensaje completo: {data}")
                            print("-" * 50)
                        
                    except json.JSONDecodeError:
                        # Mensaje no JSON
                        print(f"{timestamp} | RAW     | {channel[-20:]:20} | N/A      | N/A      | {data[:20]}")
                    
                    # Límites de tiempo y mensajes
                    elapsed = (datetime.now() - start_time).seconds
                    if elapsed > 60:  # 60 segundos
                        print(f"\n⏱️  Tiempo límite alcanzado (60s)")
                        break
                    
                    if message_count >= 100:  # Máximo 100 mensajes
                        print(f"\n📊 Límite de mensajes alcanzado (100)")
                        break
        
        except asyncio.TimeoutError:
            print(f"\n⏱️  Timeout en escucha")
        
        # 7. Resumen final
        print(f"\n📊 RESUMEN DEL DIAGNÓSTICO:")
        print(f"   📨 Total mensajes monitoreados: {message_count}")
        print(f"   🎉 Mensajes de otros estudiantes: {foreign_messages}")
        print(f"   📡 Canales activos encontrados: {len(all_channels)}")
        
        if foreign_messages == 0:
            print(f"\n❌ PROBLEMA IDENTIFICADO:")
            print(f"   No se detectaron mensajes de otros estudiantes")
            print(f"   Posibles causas:")
            print(f"   1. Otros estudiantes no están enviando mensajes ahora")
            print(f"   2. Están usando canales diferentes")
            print(f"   3. Problema de configuración de Redis")
            print(f"   4. Están usando formato de mensaje diferente")
        else:
            print(f"\n✅ COMUNICACIÓN DETECTADA:")
            print(f"   Se encontraron {foreign_messages} mensajes de otros estudiantes")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
    
    finally:
        try:
            await pubsub.aclose()
            await r.aclose()
        except:
            pass
        print("🔚 Diagnóstico completado")

if __name__ == "__main__":
    asyncio.run(full_diagnosis())
