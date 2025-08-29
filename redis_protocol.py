"""
Protocolo Redis para comunicación entre nodos
Implementa los mensajes: init, message, done
"""

import asyncio
import json
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

# Configuración del servidor Redis
REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

@dataclass
class InitMessage:
    """Mensaje de inicialización"""
    type: str = "init"
    whoAmI: str = ""
    neighbours: Dict[str, int] = None
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "whoAmI": self.whoAmI,
            "neighbours": self.neighbours or {}
        })
    
    @classmethod
    def from_json(cls, data: str) -> 'InitMessage':
        parsed = json.loads(data)
        return cls(
            type=parsed["type"],
            whoAmI=parsed["whoAmI"],
            neighbours=parsed["neighbours"]
        )

@dataclass
class DataMessage:
    """Mensaje de datos entre nodos"""
    type: str = "message"
    origin: str = ""
    destination: str = ""
    ttl: int = 5
    content: str = ""
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "origin": self.origin,
            "destination": self.destination,
            "ttl": self.ttl,
            "content": self.content
        })
    
    @classmethod
    def from_json(cls, data: str) -> 'DataMessage':
        parsed = json.loads(data)
        return cls(
            type=parsed["type"],
            origin=parsed["origin"],
            destination=parsed["destination"],
            ttl=parsed["ttl"],
            content=parsed["content"]
        )

@dataclass
class DoneMessage:
    """Mensaje de finalización"""
    type: str = "done"
    whoAmI: str = ""
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "whoAmI": self.whoAmI
        })
    
    @classmethod
    def from_json(cls, data: str) -> 'DoneMessage':
        parsed = json.loads(data)
        return cls(
            type=parsed["type"],
            whoAmI=parsed["whoAmI"]
        )

class RedisProtocolNode:
    """Nodo que implementa el protocolo Redis con algoritmos de enrutamiento"""
    
    def __init__(self, node_id: str, seccion: str = "sec20", topologia: str = "topologia1"):
        self.node_id = node_id
        self.seccion = seccion
        self.topologia = topologia
        
        # Canal oficial para recibir mensajes
        self.channel_name = f"{seccion}.{topologia}.{node_id}"
        
        # Estado del nodo
        self.neighbours: Dict[str, int] = {}
        self.algorithm = "flooding"  # Por defecto
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.running = False
        
        # Para algoritmos específicos
        self.routing_table: Dict[str, str] = {}  # destino -> next_hop
        self.link_state_db: Dict[str, Dict[str, int]] = {}  # nodo -> {vecino: costo}
        self.seen_messages: set = set()  # Para evitar loops en flooding
        
        print(f"🆔 Nodo {node_id} creado en canal: {self.channel_name}")
    
    async def connect(self):
        """Conectar al servidor Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                password=REDIS_PASSWORD
            )
            
            # Probar conexión
            await self.redis_client.ping()
            print(f"✅ Conectado a Redis: {self.node_id}")
            
            # Configurar pub/sub
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(f"channel:{self.channel_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            return False
    
    async def disconnect(self):
        """Desconectar del servidor Redis"""
        self.running = False
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        print(f"🔌 Desconectado: {self.node_id}")
    
    def set_algorithm(self, algorithm: str):
        """Configurar el algoritmo de enrutamiento"""
        if algorithm in ["flooding", "link_state"]:
            self.algorithm = algorithm
            print(f"🎯 Algoritmo configurado: {algorithm}")
        else:
            print(f"❌ Algoritmo no válido: {algorithm}")
    
    def set_neighbours(self, neighbours: Dict[str, int]):
        """Configurar vecinos del nodo"""
        self.neighbours = neighbours.copy()
        print(f"👥 Vecinos configurados: {self.neighbours}")
    
    async def send_init_message(self):
        """Enviar mensaje de inicialización"""
        init_msg = InitMessage(
            whoAmI=self.node_id,
            neighbours=self.neighbours
        )
        
        # Enviar a todos los vecinos
        for neighbour in self.neighbours.keys():
            channel = f"channel:{self.seccion}.{self.topologia}.{neighbour}"
            await self.redis_client.publish(channel, init_msg.to_json())
            print(f"📤 INIT enviado a {neighbour}")
    
    async def send_message(self, destination: str, content: str):
        """Enviar mensaje usando el algoritmo configurado"""
        msg = DataMessage(
            origin=self.node_id,
            destination=destination,
            content=content
        )
        
        if self.algorithm == "flooding":
            await self._send_with_flooding(msg)
        elif self.algorithm == "link_state":
            await self._send_with_link_state(msg)
    
    async def _send_with_flooding(self, msg: DataMessage):
        """Enviar mensaje usando flooding"""
        msg_id = f"{msg.origin}-{msg.destination}-{hash(msg.content)}"
        
        if msg_id in self.seen_messages:
            print(f"🔄 Mensaje ya procesado: {msg_id}")
            return
        
        self.seen_messages.add(msg_id)
        
        # Enviar a todos los vecinos
        for neighbour in self.neighbours.keys():
            if neighbour != msg.origin:  # No devolver al origen
                channel = f"channel:{self.seccion}.{self.topologia}.{neighbour}"
                msg.ttl -= 1
                
                if msg.ttl > 0:
                    await self.redis_client.publish(channel, msg.to_json())
                    print(f"🌊 FLOODING a {neighbour}: {msg.content[:20]}...")
    
    async def _send_with_link_state(self, msg: DataMessage):
        """Enviar mensaje usando Link State Routing"""
        # Calcular ruta usando tabla de enrutamiento
        next_hop = self.routing_table.get(msg.destination)
        
        if next_hop:
            channel = f"channel:{self.seccion}.{self.topologia}.{next_hop}"
            await self.redis_client.publish(channel, msg.to_json())
            print(f"🗺️ LSR a {next_hop} (destino: {msg.destination}): {msg.content[:20]}...")
        else:
            print(f"❌ No hay ruta a {msg.destination}")
    
    async def send_done_message(self):
        """Enviar mensaje de finalización"""
        done_msg = DoneMessage(whoAmI=self.node_id)
        
        # Enviar a todos los vecinos
        for neighbour in self.neighbours.keys():
            channel = f"channel:{self.seccion}.{self.topologia}.{neighbour}"
            await self.redis_client.publish(channel, done_msg.to_json())
            print(f"✅ DONE enviado a {neighbour}")
    
    async def _handle_message(self, message_data: str):
        """Manejar mensaje recibido"""
        try:
            parsed = json.loads(message_data)
            msg_type = parsed.get("type")
            
            if msg_type == "init":
                await self._handle_init(InitMessage.from_json(message_data))
            elif msg_type == "message":
                await self._handle_data(DataMessage.from_json(message_data))
            elif msg_type == "done":
                await self._handle_done(DoneMessage.from_json(message_data))
            else:
                print(f"❓ Tipo de mensaje desconocido: {msg_type}")
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    async def _handle_init(self, msg: InitMessage):
        """Manejar mensaje INIT"""
        print(f"📥 INIT recibido de {msg.whoAmI}: {msg.neighbours}")
        
        if self.algorithm == "link_state":
            # Actualizar base de datos de estado de enlaces
            self.link_state_db[msg.whoAmI] = msg.neighbours
            self._calculate_routing_table()
    
    async def _handle_data(self, msg: DataMessage):
        """Manejar mensaje DATA"""
        if msg.destination == self.node_id:
            print(f"📩 MENSAJE RECIBIDO de {msg.origin}: {msg.content}")
        else:
            # Reenviar mensaje
            if self.algorithm == "flooding":
                await self._send_with_flooding(msg)
            elif self.algorithm == "link_state":
                await self._send_with_link_state(msg)
    
    async def _handle_done(self, msg: DoneMessage):
        """Manejar mensaje DONE"""
        print(f"✅ DONE recibido de {msg.whoAmI}")
    
    def _calculate_routing_table(self):
        """Calcular tabla de enrutamiento usando Dijkstra"""
        # Implementación simple de Dijkstra
        from dijkstra import dijkstra
        from grafo import grafo
        
        # Construir grafo
        g = grafo()
        for nodo, vecinos in self.link_state_db.items():
            g.agregar_router(nodo)
            for vecino, costo in vecinos.items():
                g.agregar_conexion(nodo, vecino, costo)
        
        # Agregar nodo actual si no está
        if self.node_id not in g.routers:
            g.agregar_router(self.node_id)
            for vecino, costo in self.neighbours.items():
                g.agregar_conexion(self.node_id, vecino, costo)
        
        # Calcular distancias
        try:
            dist, prev = dijkstra(g, self.node_id)
            
            # Construir tabla de enrutamiento
            self.routing_table = {}
            for destino in g.routers:
                if destino != self.node_id and prev[destino] is not None:
                    # Encontrar primer salto
                    current = destino
                    while prev[current] != self.node_id:
                        current = prev[current]
                        if current is None:
                            break
                    if current:
                        self.routing_table[destino] = current
            
            print(f"🗺️ Tabla de enrutamiento actualizada: {self.routing_table}")
            
        except Exception as e:
            print(f"❌ Error calculando tabla: {e}")
    
    async def listen(self):
        """Escuchar mensajes del canal"""
        if not self.pubsub:
            print("❌ No hay conexión pub/sub")
            return
        
        self.running = True
        print(f"👂 Escuchando en {self.channel_name}...")
        
        try:
            while self.running:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True, 
                    timeout=1.0
                )
                
                if message is not None:
                    data = message["data"].decode()
                    if data == "STOP":
                        print("🛑 Comando STOP recibido")
                        break
                    await self._handle_message(data)
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error en listener: {e}")
        finally:
            self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del nodo"""
        return {
            "node_id": self.node_id,
            "channel": self.channel_name,
            "algorithm": self.algorithm,
            "neighbours": self.neighbours,
            "routing_table": self.routing_table,
            "link_state_db": self.link_state_db,
            "running": self.running
        }

# Función de demostración
async def demo_redis_protocol():
    """Demo del protocolo Redis"""
    print("=== DEMO PROTOCOLO REDIS ===")
    
    # Crear nodo
    node = RedisProtocolNode("A")
    
    # Configurar
    node.set_neighbours({"B": 5, "C": 3})
    node.set_algorithm("flooding")
    
    # Conectar
    if await node.connect():
        # Enviar mensaje init
        await node.send_init_message()
        
        # Simular escucha por unos segundos
        listen_task = asyncio.create_task(node.listen())
        
        # Esperar un poco
        await asyncio.sleep(2)
        
        # Enviar mensaje de prueba
        await node.send_message("B", "Hola desde A!")
        
        # Esperar más
        await asyncio.sleep(3)
        
        # Enviar done
        await node.send_done_message()
        
        # Detener
        await node.disconnect()
        listen_task.cancel()
    
    print("✅ Demo completado")

if __name__ == "__main__":
    asyncio.run(demo_redis_protocol())
