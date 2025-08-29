#!/usr/bin/env python3
"""
Cliente universal que maneja múltiples protocolos
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

class UniversalClient:
    def __init__(self, node_number=10):
        self.node_id = f"sec20.topologia2.nodo{node_number}"
        self.redis_client = None
        self.pubsub = None
        
    async def connect(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        await self.redis_client.ping()
        
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(self.node_id)
        print(f"✅ Conectado y escuchando en: {self.node_id}")
        
    async def send_lsr_message(self, to_node, content):
        """Enviar mensaje LSR estándar"""
        msg = {
            "proto": "lsr",
            "type": "message",
            "from": self.node_id,
            "to": f"sec20.topologia2.{to_node}",
            "ttl": 5,
            "headers": [],
            "payload": content
        }
        
        channel = f"sec20.topologia2.{to_node}"
        await self.redis_client.publish(channel, json.dumps(msg))
        print(f"📤 LSR enviado a {channel}: {content}")
        
    async def send_hello(self):
        """Enviar HELLO LSR"""
        msg = {
            "proto": "lsr", 
            "type": "hello",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": 5,
            "headers": [],
            "payload": ""
        }
        
        # Enviar a nodos conocidos
        targets = ["nodo2", "nodo6", "nodo7", "nodo8", "nodo9"]
        for target in targets:
            channel = f"sec20.topologia2.{target}"
            await self.redis_client.publish(channel, json.dumps(msg))
            print(f"📤 HELLO enviado a {channel}")
    
    async def listen(self):
        """Escuchar todos los mensajes"""
        print(f"👂 Escuchando mensajes...")
        print("Time     | From          | Type    | Content")
        print("-" * 50)
        
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = message["data"].decode()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                try:
                    parsed = json.loads(data)
                    
                    # Detectar tipo de protocolo
                    if parsed.get("proto") == "lsr":
                        from_node = parsed.get("from", "Unknown")
                        msg_type = parsed.get("type", "unknown")
                        payload = parsed.get("payload", "")
                        
                        print(f"{timestamp} | {from_node[-12:]:12} | {msg_type:7} | {str(payload)[:20]}")
                        
                        if msg_type == "message" and parsed.get("to") == self.node_id:
                            print(f"🎉 ¡MENSAJE PARA MÍ! De: {from_node}")
                            print(f"   💬: {payload}")
                            
                    else:
                        # Otros protocolos
                        from_node = parsed.get("from", parsed.get("origin", "Unknown"))
                        msg_type = parsed.get("type", "unknown")
                        content = parsed.get("payload", parsed.get("content", ""))
                        
                        print(f"{timestamp} | {str(from_node)[-12:]:12} | {msg_type:7} | {str(content)[:20]}")
                        
                except json.JSONDecodeError:
                    print(f"{timestamp} | RAW           | data    | {data[:20]}...")

async def main():
    print("🌐 CLIENTE UNIVERSAL LSR")
    print("="*40)
    
    client = UniversalClient(10)  # nodo10
    await client.connect()
    
    print("\nOpciones:")
    print("1. Enviar HELLO")
    print("2. Enviar mensaje a nodo2")
    print("3. Escuchar mensajes")
    print("4. Prueba completa")
    
    choice = input("\nSeleccione opción (1-4): ").strip()
    
    if choice == "1":
        await client.send_hello()
        
    elif choice == "2":
        message = input("Mensaje para nodo2: ")
        await client.send_lsr_message("nodo2", message)
        
    elif choice == "3":
        print("Presione Ctrl+C para detener")
        try:
            await client.listen()
        except KeyboardInterrupt:
            print("\n🛑 Detenido")
            
    elif choice == "4":
        print("🧪 Ejecutando prueba completa...")
        await client.send_hello()
        await asyncio.sleep(1)
        await client.send_lsr_message("nodo2", "Hola compañera! ¿Me puedes responder?")
        
        print("👂 Escuchando respuestas por 30 segundos...")
        try:
            start = datetime.now()
            async for message in client.pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode()
                    try:
                        parsed = json.loads(data)
                        if parsed.get("proto") == "lsr" and parsed.get("type") == "message":
                            from_node = parsed.get("from", "")
                            if "nodo2" in from_node:
                                print(f"🎉 ¡RESPUESTA DE NODO2!")
                                print(f"   💬: {parsed.get('payload', '')}")
                                break
                    except:
                        pass
                    
                    if (datetime.now() - start).seconds > 30:
                        print("⏱️ Tiempo agotado")
                        break
        except KeyboardInterrupt:
            print("\n🛑 Detenido")
    
    # Cleanup
    await client.pubsub.aclose()
    await client.redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
