#!/usr/bin/env python3
"""
Protocolo LSR exacto según las funciones de la clase
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuración Redis
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

# ===== FUNCIONES EXACTAS DE LA CLASE =====

def make_base_msg(type_: str, from_: str, to: str, ttl: int, headers: List[str], payload: Any) -> dict:
    return {
        "proto": "lsr",
        "type": type_,
        "from": from_,
        "to": to,
        "ttl": ttl,
        "headers": headers,
        "payload": payload
    }

# HELLO -> equivalente a "init"
def make_hello_msg(who_am_i: str, ttl: int = 5) -> dict:
    return make_base_msg(
        "hello",
        from_=who_am_i,
        to="broadcast",
        ttl=ttl,
        headers=[],
        payload=""  # opcional: vecinos iniciales si quieres
    )

# INFO -> equivalente a "done"/tablas
def make_info_msg(who_am_i: str, routing_table: Dict[str, int], headers: List[str] = None, ttl: int = 5) -> dict:
    if headers is None:
        headers = []
    return make_base_msg(
        "info",
        from_=who_am_i,
        to="broadcast",
        ttl=ttl,
        headers=headers,
        payload=routing_table
    )

# MESSAGE -> equivalente a "message" de usuario
def make_message(origin: str, destination: str, content: str, headers: List[str] = None,
                 ttl: int = 5, msg_id: str = None) -> dict:
    if headers is None:
        headers = []
    if msg_id is None:
        msg_id = str(uuid.uuid4())
    return make_base_msg(
        "message",
        from_=origin,
        to=destination,
        ttl=ttl,
        headers=headers,
        payload=content
    )

def channel_name(node_id: str) -> str:
    return f"{node_id}"

# ===== CLIENTE LSR CON FUNCIONES DE LA CLASE =====

class LSRNode:
    """Nodo LSR usando las funciones exactas de la clase"""
    
    def __init__(self, node_number: int):
        self.node_id = f"sec20.topologia2.nodo{node_number}"
        self.node_number = node_number
        self.neighbours: Dict[str, int] = {}
        self.routing_table: Dict[str, int] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.running = False
        
        print(f"🆔 Nodo LSR creado: {self.node_id}")
        print(f"📻 Canal: {channel_name(self.node_id)}")
    
    def set_neighbours(self, neighbours: Dict[str, int]):
        """Configurar vecinos directos"""
        self.neighbours = neighbours
        # Actualizar tabla de enrutamiento con vecinos directos
        self.routing_table.update(neighbours)
        print(f"👥 Vecinos configurados: {neighbours}")
        print(f"📊 Tabla de enrutamiento actualizada: {self.routing_table}")
    
    async def connect(self) -> bool:
        """Conectar a Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD
            )
            
            # Verificar conexión
            await self.redis_client.ping()
            
            # Crear pubsub y suscribirse a nuestro canal
            self.pubsub = self.redis_client.pubsub()
            my_channel = channel_name(self.node_id)
            await self.pubsub.subscribe(my_channel)
            
            print(f"✅ Conectado a Redis")
            print(f"👂 Escuchando en canal: {my_channel}")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            return False
    
    async def send_hello(self):
        """Enviar mensaje HELLO a todos los vecinos"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        hello_msg = make_hello_msg(self.node_id)
        
        print(f"📤 Enviando HELLO...")
        print(f"📄 Mensaje: {json.dumps(hello_msg, indent=2, ensure_ascii=False)}")
        
        for neighbour in self.neighbours.keys():
            neighbour_channel = channel_name(neighbour)
            await self.redis_client.publish(neighbour_channel, json.dumps(hello_msg))
            print(f"📤 HELLO enviado a {neighbour} en canal {neighbour_channel}")
    
    async def send_info(self):
        """Enviar mensaje INFO con tabla de enrutamiento"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        info_msg = make_info_msg(self.node_id, self.routing_table)
        
        print(f"📤 Enviando INFO...")
        print(f"📄 Mensaje: {json.dumps(info_msg, indent=2, ensure_ascii=False)}")
        
        for neighbour in self.neighbours.keys():
            neighbour_channel = channel_name(neighbour)
            await self.redis_client.publish(neighbour_channel, json.dumps(info_msg))
            print(f"📤 INFO enviado a {neighbour} en canal {neighbour_channel}")
    
    async def send_message(self, to_node: str, content: str):
        """Enviar mensaje personalizado"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        # Construir nombre completo del nodo destino si es necesario
        if not to_node.startswith("sec20.topologia2."):
            to_node = f"sec20.topologia2.{to_node}"
        
        message_msg = make_message(self.node_id, to_node, content)
        
        print(f"📤 Enviando MESSAGE...")
        print(f"🎯 A: {to_node}")
        print(f"💬 Contenido: {content}")
        print(f"📄 Mensaje: {json.dumps(message_msg, indent=2, ensure_ascii=False)}")
        
        destination_channel = channel_name(to_node)
        await self.redis_client.publish(destination_channel, json.dumps(message_msg))
        print(f"✅ Mensaje enviado a canal: {destination_channel}")
    
    async def listen(self):
        """Escuchar mensajes entrantes"""
        if not self.pubsub:
            print("❌ No hay conexión pubsub")
            return
        
        self.running = True
        my_channel = channel_name(self.node_id)
        print(f"👂 Escuchando en: {my_channel}")
        print("⏰ Timestamp | 🔄 Tipo | 👤 De | 🎯 Para | 💬 Contenido")
        print("-" * 70)
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self.handle_message(message["data"].decode())
        except Exception as e:
            print(f"❌ Error en listen: {e}")
        finally:
            self.running = False
    
    async def handle_message(self, data: str):
        """Procesar mensaje recibido"""
        try:
            msg = json.loads(data)
            
            # Verificar que es un mensaje LSR
            if msg.get("proto") != "lsr":
                print(f"⚠️  Mensaje no LSR ignorado")
                return
            
            msg_type = msg.get("type")
            from_node = msg.get("from", "Unknown")
            to_node = msg.get("to", "Unknown")
            payload = msg.get("payload", "")
            ttl = msg.get("ttl", 0)
            headers = msg.get("headers", [])
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"{timestamp} | {msg_type:7} | {from_node[-5:]:5} | {to_node[-5:]:5} | {str(payload)[:20]}")
            
            if msg_type == "hello":
                print(f"📢 HELLO recibido de {from_node}")
                
            elif msg_type == "info":
                print(f"📊 INFO recibido de {from_node}")
                print(f"   📋 Tabla de enrutamiento: {payload}")
                
            elif msg_type == "message":
                # Verificar si es para nosotros
                if to_node == self.node_id:
                    print(f"\n🎉 ¡MENSAJE PARA MÍ!")
                    print(f"   👤 De: {from_node}")
                    print(f"   💬 Contenido: {payload}")
                    print(f"   🆔 TTL: {ttl}")
                    print(f"   📋 Headers: {headers}")
                    print("-" * 50)
                else:
                    print(f"📬 Mensaje en tránsito de {from_node} para {to_node}")
                
        except json.JSONDecodeError:
            print(f"⚠️  Mensaje no JSON válido: {data[:50]}...")
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    async def disconnect(self):
        """Desconectar de Redis"""
        self.running = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
        print(f"🔌 Desconectado: {self.node_id}")
    
    def get_status(self) -> Dict:
        """Obtener estado del nodo"""
        return {
            "node_id": self.node_id,
            "channel": channel_name(self.node_id),
            "neighbours": self.neighbours,
            "routing_table": self.routing_table,
            "running": self.running,
            "connected": self.redis_client is not None
        }

# ===== CLIENTE INTERACTIVO =====

class LSRClassClient:
    """Cliente interactivo usando las funciones exactas de la clase"""
    
    def __init__(self):
        self.node: Optional[LSRNode] = None
    
    def print_menu(self):
        """Mostrar menú principal"""
        print("\n" + "="*70)
        print("  🌐 PROTOCOLO LSR - FUNCIONES EXACTAS DE LA CLASE")
        print("="*70)
        print()
        print("🔧 CONFIGURACIÓN:")
        print("  1. Crear nodo LSR")
        print("  2. Conectar a Redis")
        print("  3. Configurar vecinos")
        print()
        print("📡 COMUNICACIÓN LSR:")
        print("  4. Enviar HELLO (make_hello_msg)")
        print("  5. Enviar INFO (make_info_msg)") 
        print("  6. Enviar MESSAGE (make_message)")
        print("  7. Escuchar mensajes")
        print("  8. Ver estado del nodo")
        print()
        print("🧪 PRUEBAS:")
        print("  9. Prueba rápida (HELLO + MESSAGE)")
        print()
        print("  0. Salir")
        print("-"*70)
    
    async def create_node(self):
        """Crear nodo LSR"""
        print("\n🆔 CREAR NODO LSR")
        
        try:
            node_number = int(input("Número del nodo (ej: 10 para nodo10): ").strip())
            self.node = LSRNode(node_number)
            print(f"✅ Nodo creado exitosamente")
        except ValueError:
            print("❌ Número inválido")
    
    async def connect_redis(self):
        """Conectar a Redis"""
        if not self.node:
            print("❌ Primero cree un nodo")
            return
        
        if await self.node.connect():
            print("✅ Conexión exitosa")
        else:
            print("❌ Error en conexión")
    
    async def configure_neighbours(self):
        """Configurar vecinos"""
        if not self.node:
            print("❌ Primero cree un nodo")
            return
        
        print("\n👥 CONFIGURAR VECINOS")
        print("Formato: nodo2:1, nodo6:2 (número:costo)")
        print("Terminar con línea vacía")
        
        neighbours = {}
        while True:
            vecino_input = input("Vecino: ").strip()
            if not vecino_input:
                break
            
            try:
                nodo, costo = vecino_input.split(":")
                nodo_full = f"sec20.topologia2.{nodo.strip()}"
                neighbours[nodo_full] = int(costo.strip())
            except ValueError:
                print("❌ Formato inválido. Use: nodo2:1")
        
        if neighbours:
            self.node.set_neighbours(neighbours)
    
    async def send_hello(self):
        """Enviar HELLO usando make_hello_msg"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        await self.node.send_hello()
    
    async def send_info(self):
        """Enviar INFO usando make_info_msg"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        await self.node.send_info()
    
    async def send_message(self):
        """Enviar MESSAGE usando make_message"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n💌 ENVIAR MESSAGE")
        destination = input("Nodo destino (ej: nodo2): ").strip()
        content = input("Mensaje: ").strip()
        
        if destination and content:
            await self.node.send_message(destination, content)
    
    async def listen_mode(self):
        """Modo escucha"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n👂 MODO ESCUCHA ACTIVADO")
        print("Presione Ctrl+C para detener")
        
        try:
            await self.node.listen()
        except KeyboardInterrupt:
            print("\n🛑 Modo escucha detenido")
    
    def show_status(self):
        """Mostrar estado del nodo"""
        if not self.node:
            print("❌ No hay nodo creado")
            return
        
        print("\n📊 ESTADO DEL NODO")
        status = self.node.get_status()
        
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
    
    async def quick_test(self):
        """Prueba rápida: HELLO + MESSAGE"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n🧪 PRUEBA RÁPIDA")
        
        # Enviar HELLO
        print("1. Enviando HELLO...")
        await self.node.send_hello()
        
        await asyncio.sleep(1)
        
        # Enviar MESSAGE a nodo2
        print("2. Enviando MESSAGE a nodo2...")
        await self.node.send_message("nodo2", "Hola compañera! Prueba rápida desde el protocolo correcto")
        
        print("✅ Prueba rápida completada")
    
    async def run(self):
        """Ejecutar cliente"""
        print("🚀 Cliente LSR con funciones de clase iniciado...")
        
        try:
            while True:
                self.print_menu()
                choice = input("👉 Seleccione una opción: ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    await self.create_node()
                elif choice == "2":
                    await self.connect_redis()
                elif choice == "3":
                    await self.configure_neighbours()
                elif choice == "4":
                    await self.send_hello()
                elif choice == "5":
                    await self.send_info()
                elif choice == "6":
                    await self.send_message()
                elif choice == "7":
                    await self.listen_mode()
                elif choice == "8":
                    self.show_status()
                elif choice == "9":
                    await self.quick_test()
                else:
                    print("❌ Opción inválida")
                
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Cliente interrumpido")
        finally:
            if self.node:
                await self.node.disconnect()

async def main():
    """Función principal"""
    client = LSRClassClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
