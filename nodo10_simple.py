#!/usr/bin/env python3
"""
Cliente LSR simplificado - Nodo configurable
Menú simple para comunicación con otros nodos
Permite seleccionar qué nodo ser y enviar mensajes a cualquier nodo
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

class NodelClient:
    def __init__(self, node_number=10):
        self.node_id = f"sec20.topologia2.nodo{node_number}"
        self.node_number = node_number
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
            
            print(f"✅ Nodo{self.node_number} conectado automáticamente")
            print(f"👂 Escuchando en: {self.node_id}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
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
        
        # Imprimir el JSON completo que se envía
        print(f"\n📤 ENVIANDO MENSAJE - Algoritmo: {self.algorithm}")
        print(f"JSON completo: {json.dumps(msg, indent=2)}")
        
        channel = f"sec20.topologia2.{target_node}"
        await self.redis_client.publish(channel, json.dumps(msg))
        print(f"✅ Mensaje enviado a {target_node}: {content}")
    
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
        print(f"🎯 Escuchando en: {self.node_id}")
        print("Time     | From     | Type    | Details")
        print("-" * 50)
        print("Presiona Ctrl+C para volver al menú")
        print("📝 Se mostrará el JSON completo de cada mensaje recibido")
        
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
                to_node = parsed.get("to", "")
                payload = parsed.get("payload", "")
                algorithm = parsed.get("algorithm", "N/A")
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                from_short = from_node.split(".")[-1] if "." in from_node else from_node
                to_short = to_node.split(".")[-1] if "." in to_node else to_node
                
                # Mostrar el JSON completo recibido
                print(f"\n📥 MENSAJE RECIBIDO - {timestamp}")
                print(f"JSON completo: {json.dumps(parsed, indent=2)}")
                
                if msg_type == "hello":
                    print(f"{timestamp} | {from_short:8} | HELLO   | Algoritmo: {algorithm}")
                    
                elif msg_type == "message":
                    if to_node == self.node_id:
                        print(f"{timestamp} | {from_short:8} | MESSAGE | Para: {to_short} | Algoritmo: {algorithm}")
                        print(f"🎉 MENSAJE PARA TI: {payload}")
                        print(f"📊 Detalles: De {from_short} usando {algorithm}")
                    else:
                        print(f"{timestamp} | {from_short:8} | TRANSIT | Para {to_short} | Algoritmo: {algorithm}")
                    
                elif msg_type == "info":
                    print(f"{timestamp} | {from_short:8} | INFO    | Tabla de rutas | Algoritmo: {algorithm}")
                    
        except json.JSONDecodeError:
            print(f"❌ Error: Mensaje no es JSON válido - {data}")
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    async def disconnect(self):
        """Desconectar"""
        self.running = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
        print("🔌 Desconectado")

def print_menu(client):
    """Mostrar menú simplificado"""
    print("\n" + "="*50)
    print(f"  🌐 NODO{client.node_number} - COMUNICACIÓN LSR")
    print("="*50)
    print()
    print("📡 COMUNICACIÓN:")
    print("  1. Enviar mensaje a nodo específico")
    print("  2. Modo escucha (Ctrl+C para salir)")
    print("  3. Seleccionar algoritmo")
    print("  4. Cambiar identidad de nodo")
    print()
    print("🎯 NODOS DISPONIBLES:")
    print("  nodo5, nodo6, nodo7, nodo8, nodo9, nodo10 (o el que elijas)")
    print()
    print("  0. Salir")
    print("-"*50)

async def main():
    """Función principal"""
    print("🚀 INICIANDO CLIENTE LSR...")
    
    # Seleccionar qué nodo ser
    print("\n🎯 SELECCIÓN DE NODO")
    print("¿Qué nodo quieres ser?")
    node_input = input("Ingresa el número del nodo (5-10): ").strip()
    
    try:
        node_number = int(node_input)
        if node_number < 5 or node_number > 10:
            print("❌ Número de nodo debe estar entre 5 y 10. Usando nodo10 por defecto.")
            node_number = 10
    except ValueError:
        print("❌ Número inválido. Usando nodo10 por defecto.")
        node_number = 10
    
    client = NodelClient(node_number)
    
    # Conectar automáticamente
    if not await client.connect():
        print("❌ No se pudo conectar. Saliendo...")
        return
    
    # Conexión exitosa
    print(f"🎯 Algoritmo actual: {client.algorithm}")
    
    try:
        while True:
            print_menu(client)
            choice = input("👉 Seleccione opción: ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
                
            elif choice == "1":
                # Enviar mensaje a nodo específico
                print("\n💌 ENVIAR MENSAJE")
                print("Nodos disponibles: nodo5, nodo6, nodo7, nodo8, nodo9, nodo10")
                print("(Puedes enviarte a ti mismo desde otra terminal)")
                
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
                
            elif choice == "2":
                # Modo escucha directo
                await client.listen_messages()
                    
            elif choice == "3":
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
            
            elif choice == "4":
                # Cambiar identidad de nodo
                print("\n🔄 CAMBIAR IDENTIDAD DE NODO")
                print(f"Actualmente eres: nodo{client.node_number}")
                new_node = input("¿Qué nodo quieres ser ahora? (5-10): ").strip()
                
                try:
                    new_node_number = int(new_node)
                    if 5 <= new_node_number <= 10:
                        # Desconectar del canal actual
                        if client.pubsub:
                            await client.pubsub.unsubscribe(client.node_id)
                        
                        # Cambiar identidad
                        client.node_number = new_node_number
                        client.node_id = f"sec20.topologia2.nodo{new_node_number}"
                        
                        # Suscribirse al nuevo canal
                        await client.pubsub.subscribe(client.node_id)
                        
                        print(f"✅ Ahora eres nodo{new_node_number}")
                        print(f"👂 Escuchando en: {client.node_id}")
                    else:
                        print("❌ Número de nodo debe estar entre 5 y 10")
                except ValueError:
                    print("❌ Número inválido")
                    
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
