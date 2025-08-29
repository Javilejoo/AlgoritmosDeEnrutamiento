#!/usr/bin/env python3
"""
Cliente LSR simplificado - Nodo10 automático
Menú simple para comunicación con otros nodos
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

class Nodo10Client:
    def __init__(self):
        self.node_id = "sec20.topologia2.nodo10"
        self.redis_client = None
        self.pubsub = None
        self.algorithm = "flooding"  # Algoritmo por defecto
        
    async def connect(self):
        """Conectar automáticamente"""
        try:
            self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(self.node_id)
            
            print(f"✅ Nodo10 conectado automáticamente")
            print(f"👂 Escuchando en: {self.node_id}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    async def send_hello(self, target_nodes=None):
        """Enviar HELLO a nodos específicos o todos"""
        if target_nodes is None:
            target_nodes = ["nodo5", "nodo6", "nodo7", "nodo8", "nodo9"]
        
        msg = {
            "proto": "lsr",
            "type": "hello",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": 5,
            "headers": [],
            "payload": ""
        }
        
        print(f"📤 Enviando HELLO...")
        for target in target_nodes:
            channel = f"sec20.topologia2.{target}"
            await self.redis_client.publish(channel, json.dumps(msg))
            print(f"   👋 HELLO → {target}")
    
    async def send_message(self, target_node, content):
        """Enviar mensaje a nodo específico"""
        msg = {
            "proto": "lsr",
            "type": "message", 
            "from": self.node_id,
            "to": f"sec20.topologia2.{target_node}",
            "ttl": 5,
            "headers": [],
            "payload": content,
            "algorithm": self.algorithm  # Incluir algoritmo en el mensaje
        }
        
        channel = f"sec20.topologia2.{target_node}"
        await self.redis_client.publish(channel, json.dumps(msg))
        print(f"📤 Mensaje enviado a {target_node} usando {self.algorithm}: {content}")
    
    def set_algorithm(self, algorithm):
        """Cambiar algoritmo de enrutamiento"""
        self.algorithm = algorithm
        print(f"🎯 Algoritmo cambiado a: {algorithm}")
    
    async def listen_messages(self):
        """Modo escucha directo (bloquea hasta Ctrl+C)"""
        if not self.pubsub:
            print("❌ No hay conexión pubsub")
            return
        
        print(f"👂 MODO ESCUCHA ACTIVADO")
        print(f"� Escuchando en: {self.node_id}")
        print("Time     | From     | Type    | Content")
        print("-" * 45)
        print("Presiona Ctrl+C para volver al menú")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message["data"].decode())
        except KeyboardInterrupt:
            print("\n🛑 Modo escucha detenido - Volviendo al menú")
        except Exception as e:
            print(f"❌ Error en escucha: {e}")
    
    async def _handle_message(self, data):
        """Procesar mensaje recibido"""
        try:
            parsed = json.loads(data)
            
            if parsed.get("proto") == "lsr":
                msg_type = parsed.get("type")
                from_node = parsed.get("from", "Unknown")
                payload = parsed.get("payload", "")
                
                # Solo mostrar mensajes de otros nodos
                if from_node != self.node_id:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    from_short = from_node.split(".")[-1] if "." in from_node else from_node
                    
                    if msg_type == "hello":
                        print(f"{timestamp} | {from_short:8} | HELLO   | Saludo recibido")
                        
                    elif msg_type == "message":
                        to_node = parsed.get("to", "")
                        if to_node == self.node_id:
                            print(f"{timestamp} | {from_short:8} | MESSAGE | {str(payload)[:20]}")
                            print(f"🎉 MENSAJE PARA TI: {payload}")
                        else:
                            print(f"{timestamp} | {from_short:8} | TRANSIT | Para {parsed.get('to', 'N/A').split('.')[-1]}")
                        
                    elif msg_type == "info":
                        print(f"{timestamp} | {from_short:8} | INFO    | Tabla de rutas")
                        
        except json.JSONDecodeError:
            pass  # Ignorar mensajes no JSON
        except Exception as e:
            pass  # Ignorar errores
    
    async def disconnect(self):
        """Desconectar"""
        self.running = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
        print("🔌 Desconectado")

def print_menu():
    """Mostrar menú simplificado"""
    print("\n" + "="*50)
    print("  🌐 NODO10 - COMUNICACIÓN LSR")
    print("="*50)
    print()
    print("📡 COMUNICACIÓN:")
    print("  1. Enviar HELLO a todos")
    print("  2. Enviar mensaje a nodo específico")
    print("  3. Modo escucha (Ctrl+C para salir)")
    print("  4. Seleccionar algoritmo")
    print()
    print("🎯 NODOS DISPONIBLES:")
    print("  nodo5, nodo6, nodo7, nodo8, nodo9")
    print()
    print("  0. Salir")
    print("-"*50)

async def main():
    """Función principal"""
    print("🚀 INICIANDO NODO10...")
    
    client = Nodo10Client()
    
    # Conectar automáticamente
    if not await client.connect():
        print("❌ No se pudo conectar. Saliendo...")
        return
    
    # Conexión exitosa - NO activar escucha automática
    print(f"🎯 Algoritmo actual: {client.algorithm}")
    
    try:
        while True:
            print_menu()
            choice = input("👉 Seleccione opción: ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
                
            elif choice == "1":
                # Enviar HELLO a todos
                await client.send_hello()
                
            elif choice == "2":
                # Enviar mensaje a nodo específico
                print("\n💌 ENVIAR MENSAJE")
                print("Nodos disponibles: nodo5, nodo6, nodo7, nodo8, nodo9")
                
                target = input("¿A qué nodo? (ej: nodo5): ").strip()
                if not target:
                    print("❌ Debe especificar un nodo")
                    continue
                
                # Agregar 'nodo' si solo pusieron el número
                if target.isdigit():
                    target = f"nodo{target}"
                
                message = input("Mensaje: ").strip()
                if not message:
                    print("❌ Debe escribir un mensaje")
                    continue
                
                await client.send_message(target, message)
                
            elif choice == "3":
                # Modo escucha directo
                await client.listen_messages()
                    
            elif choice == "4":
                # Seleccionar algoritmo
                print("\n🎯 SELECCIONAR ALGORITMO")
                print("1. Flooding (inundación)")
                print("2. Link State Routing (LSR)")
                
                algo_choice = input("Seleccione algoritmo (1-2): ").strip()
                
                if algo_choice == "1":
                    client.set_algorithm("flooding")
                elif algo_choice == "2":
                    client.set_algorithm("link_state")
                else:
                    print("❌ Opción inválida")
                    
            else:
                print("❌ Opción inválida")
            
            # Pausa pequeña
            await asyncio.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
