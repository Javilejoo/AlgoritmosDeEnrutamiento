"""
Implementación específica de algoritmos de enrutamiento
Distance Vector Routing (DVR) y Link State Routing (LSR) con XMPP
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import copy

from socket_routing_node import SocketRoutingNode, NeighborInfo
from protocolo import NetworkMessage, MessageFactory, MessageType
from dijkstra import dijkstra
from grafo import grafo

@dataclass
class DistanceVector:
    """Representa un vector de distancias"""
    source: str
    destinations: Dict[str, float]  # {destination: distance}
    sequence: int
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "destinations": self.destinations,
            "sequence": self.sequence,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DistanceVector':
        return cls(
            source=data["source"],
            destinations=data["destinations"],
            sequence=data["sequence"],
            timestamp=data["timestamp"]
        )

class DVRNode(SocketRoutingNode):
    """Nodo que implementa Distance Vector Routing"""
    
    def __init__(self, node_id: str, port: int, 
                 topology_file: Optional[str] = None):
        super().__init__(node_id, port, topology_file)
        
        # Estado específico de DVR
        self.distance_vectors: Dict[str, DistanceVector] = {}  # {node_id: DV}
        self.sequence_number = 0
        self.convergence_count = 0
        
        # Configurar handlers específicos de DVR
        self.xmpp_client.register_handler("dv", self._handle_dv_message)
        
        self.logger.info(f"🎯 Nodo DVR {node_id} inicializado")
    
    async def _routing_process(self):
        """Proceso de routing específico para DVR"""
        self.logger.info("🗺️ Proceso DVR iniciado")
        
        # Inicializar vector de distancias propio
        await self._initialize_distance_vector()
        
        while self.state.name != "STOPPED":
            try:
                # Enviar vector de distancias a vecinos
                await self._send_distance_vectors()
                
                # Verificar convergencia
                if await self._check_convergence():
                    self.convergence_count += 1
                    if self.convergence_count > 3:
                        self.logger.info("✅ DVR convergido")
                        # Reducir frecuencia de actualizaciones
                        await asyncio.sleep(60)
                        continue
                
                # Esperar antes de siguiente actualización
                await asyncio.sleep(15)  # DVR típicamente actualiza cada 15-30s
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en DVR routing: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🔴 Proceso DVR detenido")
    
    async def _initialize_distance_vector(self):
        """Inicializa el vector de distancias propio"""
        destinations = {self.node_id: 0.0}  # Distancia a sí mismo es 0
        
        # Agregar vecinos directos
        for neighbor_jid, neighbor_info in self.neighbors.items():
            neighbor_id = self._extract_node_id(neighbor_jid)
            destinations[neighbor_id] = neighbor_info.cost
        
        # Crear vector de distancias inicial
        self.distance_vectors[self.node_id] = DistanceVector(
            source=self.node_id,
            destinations=destinations,
            sequence=self.sequence_number,
            timestamp=time.time()
        )
        
        self.logger.info(f"📊 Vector inicial: {destinations}")
    
    async def _send_distance_vectors(self):
        """Envía vector de distancias a todos los vecinos"""
        if self.node_id not in self.distance_vectors:
            return
        
        my_dv = self.distance_vectors[self.node_id]
        
        # Incrementar número de secuencia
        self.sequence_number += 1
        my_dv.sequence = self.sequence_number
        my_dv.timestamp = time.time()
        
        # Enviar a cada vecino
        for neighbor_jid in self.neighbors:
            try:
                await self.xmpp_client.send_distance_vector(
                    neighbor_jid, 
                    my_dv.to_dict()
                )
                self.logger.debug(f"📤 DV enviado a {neighbor_jid}")
            except Exception as e:
                self.logger.error(f"Error enviando DV a {neighbor_jid}: {e}")
    
    async def _handle_dv_message(self, message: NetworkMessage, from_jid: str):
        """Maneja mensajes de Distance Vector"""
        try:
            dv_data = message.payload.get("distance_vector", {})
            received_dv = DistanceVector.from_dict(dv_data)
            
            neighbor_id = self._extract_node_id(from_jid)
            self.logger.info(f"📥 DV recibido de {neighbor_id}")
            
            # Verificar si es más reciente
            if (neighbor_id not in self.distance_vectors or 
                received_dv.sequence > self.distance_vectors[neighbor_id].sequence):
                
                self.distance_vectors[neighbor_id] = received_dv
                
                # Recalcular rutas usando Bellman-Ford
                updated = await self._update_routing_table_dvr()
                
                if updated:
                    self.logger.info("🔄 Tabla de routing actualizada por DV")
                    # Resetear contador de convergencia
                    self.convergence_count = 0
                    
        except Exception as e:
            self.logger.error(f"Error procesando DV de {from_jid}: {e}")
    
    async def _update_routing_table_dvr(self) -> bool:
        """Actualiza tabla de routing usando algoritmo Bellman-Ford distribuido"""
        if self.node_id not in self.distance_vectors:
            return False
        
        old_distances = copy.deepcopy(self.distance_vectors[self.node_id].destinations)
        updated = False
        
        # Para cada destino, calcular mejor ruta
        all_destinations = set()
        for dv in self.distance_vectors.values():
            all_destinations.update(dv.destinations.keys())
        
        new_distances = {self.node_id: 0.0}
        
        for dest in all_destinations:
            if dest == self.node_id:
                continue
            
            best_distance = float('inf')
            best_next_hop = None
            
            # Verificar ruta directa
            for neighbor_jid, neighbor_info in self.neighbors.items():
                neighbor_id = self._extract_node_id(neighbor_jid)
                if neighbor_id == dest:
                    if neighbor_info.cost < best_distance:
                        best_distance = neighbor_info.cost
                        best_next_hop = neighbor_id
            
            # Verificar rutas a través de vecinos
            for neighbor_jid, neighbor_info in self.neighbors.items():
                neighbor_id = self._extract_node_id(neighbor_jid)
                
                if (neighbor_id in self.distance_vectors and 
                    dest in self.distance_vectors[neighbor_id].destinations):
                    
                    distance_via_neighbor = (neighbor_info.cost + 
                                           self.distance_vectors[neighbor_id].destinations[dest])
                    
                    if distance_via_neighbor < best_distance:
                        best_distance = distance_via_neighbor
                        best_next_hop = neighbor_id
            
            if best_distance != float('inf'):
                new_distances[dest] = best_distance
                if best_next_hop:
                    async with self.lock:
                        self.routing_table[dest] = (best_next_hop, best_distance)
        
        # Verificar si hubo cambios
        if new_distances != old_distances:
            self.distance_vectors[self.node_id].destinations = new_distances
            updated = True
            self.routing_updates += 1
        
        return updated
    
    async def _check_convergence(self) -> bool:
        """Verifica si el algoritmo ha convergido"""
        # DVR converge cuando no hay cambios en vectores de distancia
        # por un período determinado
        return len(self.distance_vectors) > 1  # Simplificado para demo

@dataclass
class LinkStatePacket:
    """Paquete de estado de enlace para LSR"""
    source: str
    sequence: int
    age: int
    neighbors: Dict[str, float]  # {neighbor: cost}
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "sequence": self.sequence,
            "age": self.age,
            "neighbors": self.neighbors,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LinkStatePacket':
        return cls(
            source=data["source"],
            sequence=data["sequence"],
            age=data["age"],
            neighbors=data["neighbors"],
            timestamp=data["timestamp"]
        )

class LSRNode(SocketRoutingNode):
    """Nodo que implementa Link State Routing"""
    
    def __init__(self, node_id: str, port: int, 
                 topology_file: Optional[str] = None):
        super().__init__(node_id, port, topology_file)
        
        # Estado específico de LSR
        self.lsdb: Dict[str, LinkStatePacket] = {}  # Link State Database
        self.sequence_number = 0
        self.topology_graph = grafo()
        
        # Configurar handlers específicos de LSR
        self.xmpp_client.register_handler("lsp", self._handle_lsp_message)
        
        self.logger.info(f"🌐 Nodo LSR {node_id} inicializado")
    
    async def _routing_process(self):
        """Proceso de routing específico para LSR"""
        self.logger.info("🗺️ Proceso LSR iniciado")
        
        # Generar LSP inicial
        await self._generate_initial_lsp()
        
        while self.state.name != "STOPPED":
            try:
                # Enviar LSP propio (flooding)
                await self._flood_lsp()
                
                # Actualizar tabla de routing con Dijkstra
                await self._update_routing_table_lsr()
                
                # Limpiar LSPs antiguos
                await self._cleanup_old_lsps()
                
                # Esperar antes de siguiente actualización
                await asyncio.sleep(30)  # LSR actualiza menos frecuentemente
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en LSR routing: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🔴 Proceso LSR detenido")
    
    async def _generate_initial_lsp(self):
        """Genera el LSP inicial con información de vecinos"""
        neighbors = {}
        for neighbor_jid, neighbor_info in self.neighbors.items():
            neighbor_id = self._extract_node_id(neighbor_jid)
            neighbors[neighbor_id] = neighbor_info.cost
        
        lsp = LinkStatePacket(
            source=self.node_id,
            sequence=self.sequence_number,
            age=0,
            neighbors=neighbors,
            timestamp=time.time()
        )
        
        self.lsdb[self.node_id] = lsp
        self.logger.info(f"📡 LSP inicial generado: {neighbors}")
    
    async def _flood_lsp(self):
        """Envía LSP a todos los vecinos (flooding)"""
        if self.node_id not in self.lsdb:
            return
        
        # Incrementar número de secuencia
        self.sequence_number += 1
        self.lsdb[self.node_id].sequence = self.sequence_number
        self.lsdb[self.node_id].timestamp = time.time()
        
        # Enviar LSP a todos los vecinos
        lsp_data = self.lsdb[self.node_id].to_dict()
        
        try:
            await self.xmpp_client.send_lsp(lsp_data)
            self.logger.debug(f"📡 LSP enviado (flooding)")
        except Exception as e:
            self.logger.error(f"Error en flooding LSP: {e}")
    
    async def _handle_lsp_message(self, message: NetworkMessage, from_jid: str):
        """Maneja mensajes LSP"""
        try:
            lsp_data = message.payload
            received_lsp = LinkStatePacket.from_dict(lsp_data)
            
            self.logger.info(f"📥 LSP recibido de {received_lsp.source}")
            
            # Verificar si es más reciente
            should_update = False
            
            if received_lsp.source not in self.lsdb:
                should_update = True
            elif received_lsp.sequence > self.lsdb[received_lsp.source].sequence:
                should_update = True
            
            if should_update:
                self.lsdb[received_lsp.source] = received_lsp
                self.logger.info(f"🔄 LSDB actualizada con LSP de {received_lsp.source}")
                
                # Reconstruir grafo de topología
                await self._rebuild_topology_graph()
                
                # Reenviar LSP a otros vecinos (flooding)
                await self._forward_lsp(message, from_jid)
                
        except Exception as e:
            self.logger.error(f"Error procesando LSP: {e}")
    
    async def _forward_lsp(self, lsp_message: NetworkMessage, from_jid: str):
        """Reenvía LSP a otros vecinos (excepto el origen)"""
        for neighbor_jid in self.neighbors:
            if neighbor_jid != from_jid:
                try:
                    # Decrementar TTL y reenviar
                    forwarded_msg = NetworkMessage(
                        proto=lsp_message.proto,
                        msg_type=lsp_message.type,
                        from_addr=lsp_message.from_addr,
                        to_addr=neighbor_jid,
                        payload=lsp_message.payload,
                        ttl=lsp_message.ttl - 1,
                        headers=lsp_message.headers + [{"forwarded_by": self.node_id}]
                    )
                    
                    if forwarded_msg.ttl > 0:
                        await self.xmpp_client.send_message(forwarded_msg)
                        
                except Exception as e:
                    self.logger.error(f"Error reenviando LSP a {neighbor_jid}: {e}")
    
    async def _rebuild_topology_graph(self):
        """Reconstruye el grafo de topología desde LSDB"""
        self.topology_graph = grafo()
        
        # Agregar todos los nodos y enlaces desde LSDB
        for source, lsp in self.lsdb.items():
            self.topology_graph.agregar_router(source)
            
            for neighbor, cost in lsp.neighbors.items():
                self.topology_graph.agregar_router(neighbor)
                self.topology_graph.agregar_conexion(source, neighbor, cost, bidireccional=False)
        
        self.logger.debug(f"🌐 Grafo reconstruido: {len(self.topology_graph.routers)} nodos")
    
    async def _update_routing_table_lsr(self):
        """Actualiza tabla de routing usando Dijkstra"""
        if len(self.topology_graph.routers) < 2:
            return
        
        try:
            # Ejecutar Dijkstra desde este nodo
            distances, predecessors = dijkstra(self.topology_graph, self.node_id)
            
            # Construir nueva tabla de routing
            new_table = {}
            for dest_node in self.topology_graph.routers:
                if dest_node != self.node_id and distances[dest_node] != float('inf'):
                    # Encontrar primer salto
                    path = []
                    current = dest_node
                    while current is not None:
                        path.append(current)
                        if current == self.node_id:
                            break
                        current = predecessors.get(current)
                    
                    if len(path) >= 2 and path[-1] == self.node_id:
                        path.reverse()
                        next_hop = path[1]
                        new_table[dest_node] = (next_hop, distances[dest_node])
            
            # Actualizar tabla
            async with self.lock:
                old_size = len(self.routing_table)
                self.routing_table = new_table
                self.routing_updates += 1
                
                if len(new_table) != old_size:
                    self.logger.info(f"🗺️ Tabla LSR actualizada: {len(new_table)} rutas")
                    
        except Exception as e:
            self.logger.error(f"Error actualizando tabla LSR: {e}")
    
    async def _cleanup_old_lsps(self):
        """Limpia LSPs antiguos de la LSDB"""
        current_time = time.time()
        max_age = 300  # 5 minutos
        
        to_remove = []
        for source, lsp in self.lsdb.items():
            if source != self.node_id and current_time - lsp.timestamp > max_age:
                to_remove.append(source)
        
        for source in to_remove:
            del self.lsdb[source]
            self.logger.info(f"🗑️ LSP antiguo removido: {source}")

# Factory para crear nodos según algoritmo
class RoutingNodeFactory:
    """Factory para crear nodos con diferentes algoritmos"""
    
    @staticmethod
    def create_node(algorithm: str, node_id: str, port: int,
                   topology_file: Optional[str] = None) -> SocketRoutingNode:
        """Crea un nodo con el algoritmo especificado"""
        
        if algorithm.lower() == "dvr":
            return DVRNode(node_id, port, topology_file)
        elif algorithm.lower() == "lsr":
            return LSRNode(node_id, port, topology_file)
        else:
            # Nodo básico con Dijkstra estático
            return SocketRoutingNode(node_id, port, topology_file)

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== ALGORITMOS DE ENRUTAMIENTO ===")
        
        # Crear nodos con diferentes algoritmos
        dvr_node = RoutingNodeFactory.create_node(
            "dvr", "A", 65001
        )
        
        lsr_node = RoutingNodeFactory.create_node(
            "lsr", "B", 65002
        )
        
        # Simular algunos vecinos
        dvr_node.neighbors["B"] = NeighborInfo(
            node_name="B", cost=5.0, last_hello=time.time()
        )
        
        lsr_node.neighbors["A"] = NeighborInfo(
            node_name="A", cost=5.0, last_hello=time.time()
        )
        
        print("✅ Nodos DVR y LSR creados")
        
        # Iniciar nodos
        await dvr_node.start()
        await lsr_node.start()
        
        print("🚀 Nodos iniciados - Simulando 15 segundos...")
        await asyncio.sleep(15)
        
        # Mostrar estado
        print(f"\nEstado DVR: {dvr_node.get_status()}")
        print(f"Estado LSR: {lsr_node.get_status()}")
        
        # Detener nodos
        await dvr_node.stop()
        await lsr_node.stop()
        
        print("✅ Demo completada")
    
    asyncio.run(main())
