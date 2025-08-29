#!/usr/bin/env python3
"""
Diagnóstico simple de Redis
"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

async def simple_test():
    print("🔍 DIAGNÓSTICO REDIS SIMPLE")
    print("="*40)
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    
    try:
        await r.ping()
        print("✅ Conexión exitosa")
        
        # Buscar canales activos
        channels = await r.pubsub_channels("*")
        print(f"📡 Canales activos: {len(channels)}")
        
        if channels:
            print("Canales encontrados:")
            for i, ch in enumerate(channels[:10]):  # Solo primeros 10
                print(f"  {i+1}. {ch.decode()}")
        
        # Monitor simple
        pubsub = r.pubsub()
        await pubsub.psubscribe("*")
        
        print(f"\n👂 Monitoreando 30 segundos...")
        
        count = 0
        foreign_count = 0
        start = datetime.now()
        
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                count += 1
                channel = message["channel"].decode()
                data = message["data"].decode()
                
                # Detectar mensajes de otros
                if "nodo10" not in data and "monitor" not in data.lower():
                    foreign_count += 1
                    print(f"🎉 Mensaje de otro: {channel}")
                
                print(f"📨 {count}: {channel[-15:]} | {data[:30]}...")
                
                # Límites
                if count >= 20 or (datetime.now() - start).seconds > 30:
                    break
        
        print(f"\n📊 RESUMEN:")
        print(f"   Total: {count}")
        print(f"   De otros: {foreign_count}")
        
        if foreign_count == 0:
            print("❌ No se detectaron mensajes de otros estudiantes")
            print("💡 Puede que no estén enviando mensajes ahora")
        else:
            print("✅ Se detectó actividad de otros estudiantes")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        try:
            await pubsub.aclose()
            await r.aclose()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(simple_test())
