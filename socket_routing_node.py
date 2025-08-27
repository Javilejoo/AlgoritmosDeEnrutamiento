"""
Nodo de enrutamiento usando sockets TCP (sin XMPP)
Implementa forwarding y routing como procesos separados
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from protocolo import NetworkMessage, MessageFactory, ProtocolType, MessageType
from socket_client import SocketRoutingClient
from dijkstra import dijkstra, first_hop
from grafo import grafo

class NodeState(Enum):
    """Estados del nodo"""
    INITIALIZING = "initializing"
    DISCOVERING = "discovering"
    RUNNING = "running"
    STOPPED = "stopped"

@dataclass
class NeighborInfo:
    """Información de un vecino"""
    node_name: str
    cost: float
    last_hello: float
    alive: bool = True

@dataclass
class TopologyEntry:
    """Entrada en la tabla de topología"""
    nodes: List[str]
    connections: Dict[str, Dict[str, int]]  # {from_node: {to_node: cost}}

class SocketRoutingNode:
    """Nodo de enrutamiento con sockets TCP - sin XMPP"""
    
    def __init__(self, node_id: str, port: int, topology_file: Optional[str] = None):
        self.node_id = node_id
        self.port = port
        self.state = NodeState.INITIALIZING
        
        # Cliente socket (reemplaza XMPP)
        self.socket_client = SocketRoutingClient(node_id, port)
        
        # Información de vecinos y topología
        self.neighbors: Dict[str, NeighborInfo] = {}
        self.topology: Optional[TopologyEntry] = None
        self.routing_table: Dict[str, Tuple[str, float]] = {}  # {dest: (next_hop, cost)}
        
        # Procesos
        self.forwarding_task = None
        self.routing_task = None
        self.discovery_task = None
        
        # Colas para comunicación entre procesos
        self.incoming_queue = asyncio.Queue()
        self.outgoing_queue = asyncio.Queue()
        
        # Estadísticas
        self.packets_forwarded = 0
        self.packets_received = 0
        self.routing_updates = 0
        
        # Lock para thread safety
        self.lock = asyncio.Lock()
        
        # Cargar topología si se proporciona
        if topology_file:
            self.load_topology(topology_file)
        
        # Configurar handlers
        self._setup_message_handlers()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Node-{node_id}")
    
    def load_topology(self, topology_file: str):
        """Carga la topología desde archivo"""
        try:
            with open(topology_file, 'r') as f:
                topo_data = json.load(f)
            
            self.topology = TopologyEntry(
                nodes=topo_data.get("nodes", []),
                connections=topo_data.get("connections", {})
            )
            
            # Identificar vecinos directos
            if self.node_id in self.topology.connections:
                for neighbor, cost in self.topology.connections[self.node_id].items():
                    self.neighbors[neighbor] = NeighborInfo(
                        node_name=neighbor,
                        cost=float(cost),
                        last_hello=0
                    )
            
            self.logger.info(f"Topología cargada: {len(self.neighbors)} vecinos")
            
        except Exception as e:
            self.logger.error(f"Error cargando topología: {e}")
    
    def _setup_message_handlers(self):
        """Configura los handlers para diferentes tipos de mensajes"""
        self.socket_client.register_handler("hello", self._handle_hello)
        self.socket_client.register_handler("echo", self._handle_ping)
        self.socket_client.register_handler("data", self._handle_data_message)
        self.socket_client.register_handler("lsp", self._handle_lsp)
        self.socket_client.register_handler("dv", self._handle_distance_vector)
        self.socket_client.register_handler("info", self._handle_info)
    
    async def start(self):
        """Inicia el nodo y todos sus procesos"""
        self.logger.info(f"Iniciando nodo {self.node_id}")
        
        # Conectar socket client
        await self.socket_client.connect()
        
        # Iniciar procesos
        self.forwarding_task = asyncio.create_task(self._forwarding_process())
        self.routing_task = asyncio.create_task(self._routing_process())
        self.discovery_task = asyncio.create_task(self._discovery_process())
        
        self.state = NodeState.DISCOVERING
        self.logger.info("✅ Nodo iniciado - Descubriendo vecinos...")
        
        # Enviar HELLO inicial a vecinos conocidos
        await self._send_initial_hellos()
    
    async def stop(self):
        """Detiene el nodo y sus procesos"""
        self.logger.info("Deteniendo nodo...")
        self.state = NodeState.STOPPED
        
        # Cancelar tareas
        for task in [self.forwarding_task, self.routing_task, self.discovery_task]:
            if task:
                task.cancel()
        
        # Desconectar socket
        await self.socket_client.disconnect()
        
        self.logger.info("🔴 Nodo detenido")
    
    async def _forwarding_process(self):
        """Proceso de forwarding - Maneja paquetes entrantes y salientes"""
        self.logger.info("🔄 Proceso de forwarding iniciado")
        
        while self.state != NodeState.STOPPED:
            try:
                # Procesar colas con timeout para permitir checking de estado
                try:
                    # El socket_client ya maneja mensajes entrantes automáticamente
                    await asyncio.sleep(0.1)  # Yield control
                    
                    # Procesar cola de salida si hay mensajes pendientes
                    try:
                        message = await asyncio.wait_for(
                            self.outgoing_queue.get(), 
                            timeout=0.1
                        )
                        await self._forward_message(message)
                    except asyncio.TimeoutError:
                        pass  # Normal, continúa el loop
                        
                except Exception as e:
                    self.logger.error(f"Error en forwarding: {e}")
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
        
        self.logger.info("🔴 Proceso de forwarding detenido")
    
    async def _routing_process(self):
        """Proceso de routing - Mantiene tablas de enrutamiento"""
        self.logger.info("🗺️ Proceso de routing iniciado")
        
        while self.state != NodeState.STOPPED:
            try:
                # Actualizar tablas de enrutamiento periódicamente
                await self._update_routing_table()
                
                # Enviar información de routing a vecinos (si corresponde)
                await self._send_routing_updates()
                
                # Esperar antes de siguiente actualización
                await asyncio.sleep(30)  # Cada 30 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en routing: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🔴 Proceso de routing detenido")
    
    async def _discovery_process(self):
        """Proceso de descubrimiento - Mantiene descubrimiento de vecinos"""
        self.logger.info("🔍 Proceso de descubrimiento iniciado")
        
        while self.state != NodeState.STOPPED:
            try:
                # Enviar HELLO a vecinos
                await self._send_hello_to_neighbors()
                
                # Verificar vecinos vivos
                await self._check_neighbor_liveness()
                
                # Esperar antes de siguiente round
                await asyncio.sleep(10)  # Cada 10 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en discovery: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🔴 Proceso de descubrimiento detenido")
    
    async def _forward_message(self, message: NetworkMessage):
        """Reenvía un mensaje según la tabla de enrutamiento"""
        try:
            # Si el mensaje es para nosotros, procesarlo
            if self._is_message_for_me(message.to_addr):
                await self._process_local_message(message)
                return
            
            # Si es broadcast y somos el origen, enviarlo a vecinos
            if message.to_addr == "broadcast" and self._is_from_me(message.from_addr):
                for neighbor_name in self.neighbors:
                    # El socket_client maneja el broadcast automáticamente
                    pass
                return
            
            # Buscar ruta en tabla de enrutamiento
            dest_node = self._extract_node_id(message.to_addr)
            if dest_node in self.routing_table:
                next_hop_node, _ = self.routing_table[dest_node]
                
                # Reenviar mensaje al next hop
                await self.socket_client.send_data(
                    next_hop_node, 
                    json.dumps(message.to_json()), 
                    message.proto
                )
                
                self.packets_forwarded += 1
                self.logger.info(f"📤 Reenviado {message.type} hacia {dest_node} via {next_hop_node}")
            else:
                self.logger.warning(f"⚠️ No hay ruta hacia {dest_node}")
                
        except Exception as e:
            self.logger.error(f"Error reenviando mensaje: {e}")
    
    async def _process_local_message(self, message: NetworkMessage):
        """Procesa un mensaje destinado a este nodo"""
        self.packets_received += 1
        
        if message.type == MessageType.DATA.value:
            # Mensaje de usuario - mostrarlo
            user_msg = message.payload.get("message", "")
            print(f"\n📨 MENSAJE RECIBIDO de {message.from_addr}:")
            print(f"   {user_msg}")
            print(f"   Ruta: {[h.get('forwarded_by', '') for h in message.headers if 'forwarded_by' in h]}")
        
        self.logger.info(f"📥 Procesado mensaje {message.type} de {message.from_addr}")
    
    # Handlers para diferentes tipos de mensajes
    async def _handle_hello(self, message: NetworkMessage, from_addr: str):
        """Maneja mensajes HELLO"""
        neighbor_info = message.payload
        neighbor_name = neighbor_info.get("node_id", self._extract_node_id(from_addr))
        
        async with self.lock:
            if neighbor_name not in self.neighbors:
                # Nuevo vecino descubierto
                self.neighbors[neighbor_name] = NeighborInfo(
                    node_name=neighbor_name,
                    cost=1.0,  # Costo por defecto
                    last_hello=time.time()
                )
                self.logger.info(f"🤝 Nuevo vecino: {neighbor_name}")
            else:
                # Actualizar timestamp
                self.neighbors[neighbor_name].last_hello = time.time()
                self.neighbors[neighbor_name].alive = True
        
        # Responder con nuestro HELLO
        await self.socket_client.send_hello(neighbor_name, {
            "node_id": self.node_id,
            "neighbors": list(self.neighbors.keys())
        })
    
    async def _handle_ping(self, message: NetworkMessage, from_addr: str):
        """Maneja mensajes PING/ECHO"""
        ping_data = message.payload
        from_node = self._extract_node_id(from_addr)
        
        # Responder con PONG
        pong_data = {
            "ping_id": ping_data.get("ping_id"),
            "original_timestamp": ping_data.get("timestamp"),
            "reply_timestamp": time.time()
        }
        
        # Crear mensaje de respuesta manualmente
        pong_message = NetworkMessage(
            proto=message.proto,
            msg_type="echo_reply",
            from_addr=f"node_{self.node_id}@localhost:{self.port}",
            to_addr=from_addr,
            payload=pong_data
        )
        
        await self.socket_client.send_message(pong_message)
    
    async def _handle_data_message(self, message: NetworkMessage, from_addr: str):
        """Maneja mensajes de datos"""
        # Si es para nosotros, procesarlo; si no, reenviarlo
        if self._is_message_for_me(message.to_addr):
            await self._process_local_message(message)
        else:
            await self.outgoing_queue.put(message)
    
    async def _handle_lsp(self, message: NetworkMessage, from_addr: str):
        """Maneja Link State Packets"""
        lsp_data = message.payload
        self.logger.info(f"📡 LSP recibido de {from_addr}: {lsp_data}")
        
        # Procesar LSP y actualizar topología
        await self._process_lsp(lsp_data)
        
        # Reenviar LSP a otros vecinos (flooding)
        for neighbor_name in self.neighbors:
            if neighbor_name != self._extract_node_id(from_addr):  # No reenviar al origen
                await self.socket_client.send_lsp(lsp_data)
    
    async def _handle_distance_vector(self, message: NetworkMessage, from_addr: str):
        """Maneja mensajes Distance Vector"""
        dv_data = message.payload
        self.logger.info(f"📊 DV recibido de {from_addr}")
        
        # Procesar distance vector
        await self._process_distance_vector(dv_data, from_addr)
    
    async def _handle_info(self, message: NetworkMessage, from_addr: str):
        """Maneja mensajes de información general"""
        info_data = message.payload
        self.logger.info(f"ℹ️ INFO recibido de {from_addr}: {info_data}")
    
    # Métodos auxiliares
    async def _send_initial_hellos(self):
        """Envía HELLO inicial a vecinos conocidos"""
        for neighbor_name in self.neighbors:
            await self.socket_client.send_hello(neighbor_name, {
                "node_id": self.node_id,
                "neighbors": list(self.neighbors.keys())
            })
    
    async def _send_hello_to_neighbors(self):
        """Envía HELLO periódico a vecinos"""
        for neighbor_name in self.neighbors:
            await self.socket_client.send_hello(neighbor_name, {
                "node_id": self.node_id,
                "timestamp": time.time()
            })
    
    async def _check_neighbor_liveness(self):
        """Verifica que los vecinos estén vivos"""
        current_time = time.time()
        dead_neighbors = []
        
        for name, neighbor in self.neighbors.items():
            if current_time - neighbor.last_hello > 30:  # 30 segundos timeout
                neighbor.alive = False
                dead_neighbors.append(name)
        
        for name in dead_neighbors:
            self.logger.warning(f"💀 Vecino {name} no responde")
    
    async def _update_routing_table(self):
        """Actualiza la tabla de enrutamiento usando Dijkstra"""
        if not self.topology:
            return
        
        try:
            # Crear grafo desde topología
            g = grafo()
            for node in self.topology.nodes:
                g.agregar_router(node)
            
            for from_node, connections in self.topology.connections.items():
                for to_node, cost in connections.items():
                    g.agregar_conexion(from_node, to_node, cost)
            
            # Calcular rutas con Dijkstra
            distances, predecessors = dijkstra(g, self.node_id)
            
            # Actualizar tabla de enrutamiento
            new_table = {}
            for dest_node in g.routers:
                if dest_node != self.node_id and distances[dest_node] != float('inf'):
                    next_hop = first_hop(self.node_id, dest_node, predecessors)
                    if next_hop:
                        new_table[dest_node] = (next_hop, distances[dest_node])
            
            async with self.lock:
                self.routing_table = new_table
                self.routing_updates += 1
            
            self.logger.info(f"🗺️ Tabla de enrutamiento actualizada: {len(new_table)} rutas")
            
        except Exception as e:
            self.logger.error(f"Error actualizando routing table: {e}")
    
    async def _send_routing_updates(self):
        """Envía actualizaciones de routing a vecinos"""
        # Implementar según algoritmo específico (LSR, DVR, etc.)
        pass
    
    async def _process_lsp(self, lsp_data: Dict):
        """Procesa un Link State Packet"""
        # Implementar procesamiento de LSP
        pass
    
    async def _process_distance_vector(self, dv_data: Dict, from_addr: str):
        """Procesa un Distance Vector"""
        # Implementar procesamiento de DV
        pass
    
    def _extract_node_id(self, address: str) -> str:
        """Extrae node_id de una dirección"""
        # Ejemplo: node_A@localhost:65001 -> A
        if "node_" in address:
            return address.split("node_")[1].split("@")[0]
        return address.split("@")[0]
    
    def _is_message_for_me(self, to_addr: str) -> bool:
        """Verifica si un mensaje es para este nodo"""
        return f"node_{self.node_id}" in to_addr or str(self.port) in to_addr
    
    def _is_from_me(self, from_addr: str) -> bool:
        """Verifica si un mensaje es de este nodo"""
        return f"node_{self.node_id}" in from_addr or str(self.port) in from_addr
    
    # Métodos públicos para interacción
    async def send_user_message(self, dest_node: str, message: str):
        """Envía un mensaje de usuario a otro nodo"""
        await self.socket_client.send_data(dest_node, message)
    
    def get_status(self) -> Dict:
        """Obtiene el estado del nodo"""
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "neighbors": len(self.neighbors),
            "routing_entries": len(self.routing_table),
            "packets_forwarded": self.packets_forwarded,
            "packets_received": self.packets_received,
            "routing_updates": self.routing_updates,
            "socket_stats": self.socket_client.get_stats()
        }
    
    def get_routing_table(self) -> Dict:
        """Obtiene la tabla de enrutamiento"""
        return self.routing_table.copy()
    
    def get_neighbors(self) -> Dict:
        """Obtiene información de vecinos"""
        return {name: {
            "cost": info.cost,
            "alive": info.alive,
            "last_hello": info.last_hello
        } for name, info in self.neighbors.items()}

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== NODO DE ENRUTAMIENTO CON SOCKETS TCP ===")
        
        # Crear nodo
        node = SocketRoutingNode("A", 65001, "topology.json")
        
        # Iniciar nodo
        await node.start()
        
        # Simular funcionamiento
        print("✅ Nodo iniciado - Simulando 10 segundos...")
        await asyncio.sleep(10)
        
        # Mostrar estado
        print(f"\nEstado final: {node.get_status()}")
        
        # Detener nodo
        await node.stop()
    
    asyncio.run(main())
