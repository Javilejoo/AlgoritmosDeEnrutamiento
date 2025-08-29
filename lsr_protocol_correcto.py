#!/usr/bin/env python3
"""
Protocolo LSR correcto según especificación del laboratorio
"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuración Redis
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

class LSRMessage:
    """Clase base para mensajes LSR"""
    
    def __init__(self, from_node: str, to_node: str, ttl: int = 5, headers: List[str] = None):
        self.proto = "lsr"
        self.from_node = from_node
        self.to_node = to_node
        self.ttl = ttl
        self.headers = headers or []
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        raise NotImplementedError
    
    def to_json(self) -> str:
        """Convertir a JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

class HelloMessage(LSRMessage):
    """Mensaje HELLO para presentarse a vecinos"""
    
    def __init__(self, from_node: str, headers: List[str] = None):
        super().__init__(from_node, "broadcast", 5, headers)
        self.type = "hello"
        self.payload = ""
    
    def to_dict(self) -> Dict:
        return {
            "proto": self.proto,
            "type": self.type,
            "from": self.from_node,
            "to": self.to_node,
            "ttl": self.ttl,
            "headers": self.headers,
            "payload": self.payload
        }

class InfoMessage(LSRMessage):
    """Mensaje INFO con tabla de enrutamiento"""
    
    def __init__(self, from_node: str, routing_table: Dict[str, int], headers: List[str] = None):
        super().__init__(from_node, "broadcast", 5, headers)
        self.type = "info"
        self.payload = routing_table
    
    def to_dict(self) -> Dict:
        return {
            "proto": self.proto,
            "type": self.type,
            "from": self.from_node,
            "to": self.to_node,
            "ttl": self.ttl,
            "headers": self.headers,
            "payload": self.payload
        }

class MessageMessage(LSRMessage):
    """Mensaje MESSAGE personalizado"""
    
    def __init__(self, from_node: str, to_node: str, content: str, headers: List[str] = None):
        super().__init__(from_node, to_node, 5, headers)
        self.type = "message"
        self.payload = content
    
    def to_dict(self) -> Dict:
        return {
            "proto": self.proto,
            "type": self.type,
            "from": self.from_node,
            "to": self.to_node,
            "ttl": self.ttl,
            "headers": self.headers,
            "payload": self.payload
        }

class LSRNode:
    """Nodo LSR que implementa el protocolo correcto"""
    
    def __init__(self, node_number: int):
        self.node_id = f"sec20.topologia2.nodo{node_number}"
        self.node_number = node_number
        self.neighbours: Dict[str, int] = {}
        self.routing_table: Dict[str, int] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.running = False
        
        print(f"🆔 Nodo LSR creado: {self.node_id}")
    
    def set_neighbours(self, neighbours: Dict[str, int]):
        """Configurar vecinos directos"""
        self.neighbours = neighbours
        print(f"👥 Vecinos configurados: {neighbours}")
    
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
            await self.pubsub.subscribe(self.node_id)
            
            print(f"✅ Conectado a Redis: {self.node_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            return False
    
    async def send_hello(self):
        """Enviar mensaje HELLO a todos los vecinos"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        hello_msg = HelloMessage(self.node_id)
        
        print(f"📤 Enviando HELLO...")
        for neighbour in self.neighbours.keys():
            await self.redis_client.publish(neighbour, hello_msg.to_json())
            print(f"📤 HELLO enviado a {neighbour}")
    
    async def send_info(self):
        """Enviar mensaje INFO con tabla de enrutamiento"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        info_msg = InfoMessage(self.node_id, self.routing_table)
        
        print(f"📤 Enviando INFO...")
        for neighbour in self.neighbours.keys():
            await self.redis_client.publish(neighbour, info_msg.to_json())
            print(f"📤 INFO enviado a {neighbour}")
    
    async def send_message(self, to_node: str, content: str):
        """Enviar mensaje personalizado"""
        if not self.redis_client:
            print("❌ No conectado a Redis")
            return
        
        # Construir nombre completo del nodo destino si es necesario
        if not to_node.startswith("sec20.topologia2."):
            to_node = f"sec20.topologia2.{to_node}"
        
        message_msg = MessageMessage(self.node_id, to_node, content)
        
        print(f"📤 Enviando MESSAGE a {to_node}: {content}")
        await self.redis_client.publish(to_node, message_msg.to_json())
        print(f"✅ Mensaje enviado")
    
    async def listen(self):
        """Escuchar mensajes entrantes"""
        if not self.pubsub:
            print("❌ No hay conexión pubsub")
            return
        
        self.running = True
        print(f"👂 Escuchando en: {self.node_id}")
        
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
            from_node = msg.get("from")
            payload = msg.get("payload")
            
            print(f"\n📨 MENSAJE LSR RECIBIDO")
            print(f"   🔄 Tipo: {msg_type}")
            print(f"   👤 De: {from_node}")
            
            if msg_type == "hello":
                print(f"   👋 HELLO recibido de {from_node}")
                
            elif msg_type == "info":
                print(f"   📊 INFO recibido de {from_node}")
                print(f"   📄 Tabla: {payload}")
                
            elif msg_type == "message":
                to_node = msg.get("to")
                print(f"   🎯 Para: {to_node}")
                print(f"   💬 Mensaje: {payload}")
                
                # Verificar si es para nosotros
                if to_node == self.node_id:
                    print(f"🎉 ¡MENSAJE PARA MÍ!")
                    print(f"   De: {from_node}")
                    print(f"   Contenido: {payload}")
                
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

# Cliente interactivo para testing
class LSRClient:
    """Cliente interactivo para nodos LSR"""
    
    def __init__(self):
        self.node: Optional[LSRNode] = None
    
    def print_menu(self):
        """Mostrar menú principal"""
        print("\n" + "="*60)
        print("  🌐 PROTOCOLO LSR - LABORATORIO REDES")
        print("="*60)
        print()
        print("🔧 CONFIGURACIÓN:")
        print("  1. Crear nodo LSR")
        print("  2. Conectar a Redis")
        print("  3. Configurar vecinos")
        print()
        print("📡 COMUNICACIÓN LSR:")
        print("  4. Enviar HELLO")
        print("  5. Enviar INFO") 
        print("  6. Enviar MESSAGE")
        print("  7. Escuchar mensajes")
        print()
        print("  0. Salir")
        print("-"*60)
    
    async def create_node(self):
        """Crear nodo LSR"""
        print("\n🆔 CREAR NODO LSR")
        
        try:
            node_number = int(input("Número del nodo (ej: 10 para nodo10): ").strip())
            self.node = LSRNode(node_number)
            print(f"✅ Nodo creado: {self.node.node_id}")
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
        """Enviar HELLO"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        await self.node.send_hello()
    
    async def send_info(self):
        """Enviar INFO"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        await self.node.send_info()
    
    async def send_message(self):
        """Enviar MESSAGE"""
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
    
    async def run(self):
        """Ejecutar cliente"""
        print("🚀 Cliente LSR iniciado...")
        
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
    client = LSRClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
