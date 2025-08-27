"""
Nodo de red distribuida que implementa el protocolo específico
Compatible con algoritmos Flooding y LSR
"""

import asyncio
import json
import time
import socket
import threading
from typing import Dict, List, Optional, Set, Callable
from network_protocol import NetworkMessage, NetworkMessageFactory, NetworkProtocolValidator

class DistributedNode:
    """Nodo que implementa el protocolo de red distribuida"""
    
    def __init__(self, node_id: str, port: int, algorithm: str = "flooding"):
        self.node_id = node_id
        self.port = port
        self.algorithm = algorithm.lower()  # "flooding" o "lsr"
        
        # Información del nodo
        self.neighbours = {}  # {neighbor_id: cost}
        self.neighbor_connections = {}  # {neighbor_id: (ip, port)}
        
        # Estado del algoritmo
        self.routing_table = {}
        self.lsdb = {}  # Para LSR
        self.sequence_number = 0
        self.calculation_done = False
        
        # Control de mensajes
        self.seen_messages = set()  # Para flooding
        self.message_handlers = {}
        
        # Servidor socket
        self.server_socket = None
        self.running = False
        self.server_thread = None
        
        # Estadísticas
        self.messages_sent = 0
        self.messages_received = 0
        self.init_messages_received = 0
        self.done_messages_received = 0
        
        print(f"🌐 Nodo de Red {node_id} creado (Algoritmo: {algorithm})")
    
    async def start(self):
        """Inicia el nodo de red distribuida"""
        self.running = True
        await self._start_server()
        print(f"🚀 Nodo {self.node_id} iniciado en puerto {self.port}")
    
    async def stop(self):
        """Detiene el nodo"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"🛑 Nodo {self.node_id} detenido")
    
    async def _start_server(self):
        """Inicia el servidor socket"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen(10)
        
        # Iniciar thread para manejar conexiones
        self.server_thread = threading.Thread(target=self._handle_connections)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def _handle_connections(self):
        """Maneja conexiones entrantes"""
        while self.running:
            try:
                if self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    # Manejar cada cliente en un thread separado
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
            except:
                break
    
    def _handle_client(self, client_socket, addr):
        """Maneja un cliente específico"""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                message_str = data.decode('utf-8')
                asyncio.create_task(self._process_message(message_str, addr))
                
        except Exception as e:
            print(f"❌ Error manejando cliente {addr}: {e}")
        finally:
            client_socket.close()
    
    def add_neighbour(self, neighbor_id: str, cost: int, ip: str = "localhost", port: int = None):
        """Agrega un vecino según protocolo de red distribuida"""
        self.neighbours[neighbor_id] = cost
        if port:
            self.neighbor_connections[neighbor_id] = (ip, port)
        print(f"👥 Vecino agregado: {neighbor_id} (costo: {cost})")
    
    async def send_init_message(self):
        """Envía mensaje INIT a todos los vecinos"""
        init_msg = NetworkMessageFactory.create_init_message(
            self.node_id,
            self.neighbours
        )
        
        await self._broadcast_to_neighbours(init_msg)
        print(f"📢 Mensaje INIT enviado desde {self.node_id}")
    
    async def send_user_message(self, destination: str, content: str):
        """Envía mensaje de usuario"""
        message_msg = NetworkMessageFactory.create_message(
            self.node_id,
            destination,
            content
        )
        
        if self.algorithm == "flooding":
            await self._flood_message(message_msg)
        else:  # LSR
            await self._route_message(message_msg)
        
        print(f"📤 Mensaje enviado a {destination}: {content[:20]}...")
    
    async def send_done_message(self):
        """Envía mensaje DONE cuando termina cálculos"""
        done_msg = NetworkMessageFactory.create_done_message(self.node_id)
        
        await self._broadcast_to_neighbours(done_msg)
        self.calculation_done = True
        print(f"✅ Mensaje DONE enviado desde {self.node_id}")
    
    async def _broadcast_to_neighbours(self, message: NetworkMessage):
        """Envía mensaje a todos los vecinos"""
        for neighbor_id in self.neighbours:
            if neighbor_id in self.neighbor_connections:
                await self._send_to_node(neighbor_id, message)
    
    async def _send_to_node(self, node_id: str, message: NetworkMessage):
        """Envía mensaje a un nodo específico"""
        if node_id not in self.neighbor_connections:
            print(f"❌ No hay conexión a {node_id}")
            return
        
        ip, port = self.neighbor_connections[node_id]
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(message.to_json().encode('utf-8'))
            sock.close()
            
            self.messages_sent += 1
            
        except Exception as e:
            print(f"❌ Error enviando a {node_id}: {e}")
    
    async def _process_message(self, message_str: str, from_addr):
        """Procesa mensaje entrante"""
        try:
            message = NetworkMessage.from_json(message_str)
            
            if not NetworkProtocolValidator.validate_network_message(message):
                print(f"⚠️ Mensaje inválido de {from_addr}")
                return
            
            self.messages_received += 1
            print(f"📥 Mensaje {message.type} recibido de {from_addr}")
            
            # Procesar según tipo
            if message.type == "init":
                await self._handle_init_message(message)
            elif message.type == "message":
                await self._handle_user_message(message)
            elif message.type == "done":
                await self._handle_done_message(message)
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    async def _handle_init_message(self, message: NetworkMessage):
        """Maneja mensaje INIT"""
        data = message.data
        neighbor_id = data["whoAmI"]
        neighbor_neighbours = data["neighbours"]
        
        self.init_messages_received += 1
        print(f"🤝 INIT de {neighbor_id}: {neighbor_neighbours}")
        
        # Actualizar información de vecinos
        if self.algorithm == "lsr":
            # Para LSR, usar esta info para construir LSDB
            self.lsdb[neighbor_id] = neighbor_neighbours
            await self._update_lsr_tables()
        
        # Responder con nuestro INIT si no lo hemos hecho
        if not hasattr(self, '_init_sent'):
            await self.send_init_message()
            self._init_sent = True
    
    async def _handle_user_message(self, message: NetworkMessage):
        """Maneja mensaje de usuario"""
        data = message.data
        origin = data["origin"]
        destination = data["destination"]
        content = data["content"]
        ttl = data["ttl"]
        
        # Crear ID único para el mensaje
        msg_id = f"{origin}_{destination}_{content[:10]}_{int(time.time())}"
        
        if destination == self.node_id:
            # Mensaje para nosotros
            print(f"📨 MENSAJE ENTREGADO:")
            print(f"   De: {origin}")
            print(f"   Contenido: {content}")
            return
        
        # Verificar TTL
        if ttl <= 0:
            print(f"⏰ TTL expirado para mensaje {msg_id}")
            return
        
        # Decrementar TTL
        data["ttl"] = ttl - 1
        
        if self.algorithm == "flooding":
            await self._flood_user_message(message, msg_id)
        else:  # LSR
            await self._route_user_message(message)
    
    async def _handle_done_message(self, message: NetworkMessage):
        """Maneja mensaje DONE"""
        neighbor_id = message.data["whoAmI"]
        self.done_messages_received += 1
        print(f"✅ {neighbor_id} terminó sus cálculos")
    
    async def _flood_message(self, message: NetworkMessage):
        """Implementa flooding del mensaje"""
        msg_id = f"{message.data['origin']}_{message.data['destination']}_{int(time.time())}"
        
        if msg_id in self.seen_messages:
            return
        
        self.seen_messages.add(msg_id)
        await self._broadcast_to_neighbours(message)
    
    async def _flood_user_message(self, message: NetworkMessage, msg_id: str):
        """Flooding para mensaje de usuario"""
        if msg_id in self.seen_messages:
            print(f"🔄 Mensaje duplicado ignorado: {msg_id}")
            return
        
        self.seen_messages.add(msg_id)
        
        # Reenviar a todos los vecinos excepto el origen
        updated_message = NetworkMessage(
            type="message",
            data=message.data
        )
        
        await self._broadcast_to_neighbours(updated_message)
        print(f"🌊 Mensaje flooding reenviado: {msg_id}")
    
    async def _route_message(self, message: NetworkMessage):
        """Implementa enrutamiento LSR"""
        destination = message.data["destination"]
        
        if destination in self.routing_table:
            next_hop = self.routing_table[destination]["next_hop"]
            if next_hop in self.neighbor_connections:
                await self._send_to_node(next_hop, message)
                print(f"📍 Mensaje enrutado a {destination} via {next_hop}")
            else:
                print(f"❌ Next hop {next_hop} no disponible")
        else:
            print(f"❌ No hay ruta a {destination}")
    
    async def _route_user_message(self, message: NetworkMessage):
        """Enrutamiento para mensaje de usuario"""
        await self._route_message(message)
    
    async def _update_lsr_tables(self):
        """Actualiza tablas usando LSR (Dijkstra)"""
        if not self.lsdb:
            return
        
        # Implementación simplificada de Dijkstra
        distances = {self.node_id: 0}
        previous = {}
        unvisited = set(self.lsdb.keys())
        unvisited.add(self.node_id)
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances.get(x, float('inf')))
            if distances.get(current, float('inf')) == float('inf'):
                break
            
            unvisited.remove(current)
            
            # Obtener vecinos del nodo actual
            current_neighbors = self.lsdb.get(current, {})
            if current == self.node_id:
                current_neighbors = self.neighbours
            
            for neighbor, cost in current_neighbors.items():
                if neighbor in unvisited:
                    new_distance = distances[current] + cost
                    if new_distance < distances.get(neighbor, float('inf')):
                        distances[neighbor] = new_distance
                        previous[neighbor] = current
        
        # Construir tabla de enrutamiento
        self.routing_table = {}
        for dest, distance in distances.items():
            if dest != self.node_id and distance < float('inf'):
                # Encontrar next hop
                current = dest
                while previous.get(current) != self.node_id:
                    current = previous.get(current)
                    if current is None:
                        break
                
                if current:
                    self.routing_table[dest] = {
                        "distance": distance,
                        "next_hop": current
                    }
        
        print(f"📋 Tabla LSR actualizada: {len(self.routing_table)} rutas")
    
    async def calculate_routes(self):
        """Calcula rutas y envía DONE"""
        print(f"🔄 Calculando rutas con algoritmo {self.algorithm}...")
        
        if self.algorithm == "lsr":
            await self._update_lsr_tables()
        
        # Simular tiempo de cálculo
        await asyncio.sleep(2)
        
        await self.send_done_message()
    
    def print_status(self):
        """Imprime estado actual del nodo"""
        print(f"\n📊 ESTADO NODO {self.node_id}")
        print(f"   Algoritmo: {self.algorithm}")
        print(f"   Puerto: {self.port}")
        print(f"   Vecinos: {len(self.neighbours)}")
        print(f"   Mensajes enviados: {self.messages_sent}")
        print(f"   Mensajes recibidos: {self.messages_received}")
        print(f"   INIT recibidos: {self.init_messages_received}")
        print(f"   DONE recibidos: {self.done_messages_received}")
        print(f"   Cálculos terminados: {self.calculation_done}")
        
        if self.routing_table:
            print(f"   Tabla de enrutamiento: {len(self.routing_table)} entradas")
            for dest, info in self.routing_table.items():
                print(f"     {dest}: {info}")

# Demo del nodo de red distribuida
async def demo_distributed_nodes():
    """Demo de nodos de red distribuida"""
    print("=== DEMO NODOS DE RED DISTRIBUIDA ===\n")
    
    # Crear nodos
    node_a = DistributedNode("A", 65401, "flooding")
    node_b = DistributedNode("B", 65402, "lsr")
    node_c = DistributedNode("C", 65403, "flooding")
    
    # Configurar topología
    node_a.add_neighbour("B", 5, "localhost", 65402)
    node_a.add_neighbour("C", 10, "localhost", 65403)
    
    node_b.add_neighbour("A", 5, "localhost", 65401)
    node_b.add_neighbour("C", 3, "localhost", 65403)
    
    node_c.add_neighbour("A", 10, "localhost", 65401)
    node_c.add_neighbour("B", 3, "localhost", 65402)
    
    try:
        # Iniciar nodos
        await node_a.start()
        await node_b.start()
        await node_c.start()
        
        await asyncio.sleep(1)
        
        # Enviar mensajes INIT
        await node_a.send_init_message()
        await asyncio.sleep(1)
        
        # Calcular rutas
        await node_a.calculate_routes()
        await node_b.calculate_routes()
        await node_c.calculate_routes()
        
        await asyncio.sleep(2)
        
        # Enviar mensajes de usuario
        await node_a.send_user_message("C", "Mensaje desde A para C")
        await asyncio.sleep(1)
        
        await node_c.send_user_message("A", "Respuesta desde C para A")
        await asyncio.sleep(2)
        
        # Mostrar estado
        node_a.print_status()
        node_b.print_status()
        node_c.print_status()
        
    finally:
        await node_a.stop()
        await node_b.stop()
        await node_c.stop()

if __name__ == "__main__":
    asyncio.run(demo_distributed_nodes())
