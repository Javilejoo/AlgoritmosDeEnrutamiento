"""
Implementación específica de algoritmos de enrutamiento
Link State Routing (LSR) con XMPP
Solo incluye LSR ya que DVR no es requerido
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

# DistanceVector class removed - only LSR is implemented

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
    def create_node(algorithm: str, node_id: str, jid: str, password: str, 
                   use_xmpp: bool = True, topology_file: Optional[str] = None):
        """Crea un nodo según el algoritmo especificado"""
        algorithm = algorithm.lower()
        
        if algorithm == "flooding":
            if use_xmpp:
                from routing_node import RoutingNode
                node = RoutingNode(node_id, jid, password, use_xmpp)
                node.algorithm_type = "flooding"
                return node
            else:
                from flooding_algorithm import FloodingNode
                return FloodingNode(node_id, int(jid.split('@')[0][-1]) + 65000, topology_file)
        
        elif algorithm == "lsr":
            if use_xmpp:
                from routing_node import RoutingNode
                node = RoutingNode(node_id, jid, password, use_xmpp)
                node.algorithm_type = "lsr"
                return node
            else:
                return LSRNode(node_id, int(jid.split('@')[0][-1]) + 65000, topology_file)
        
        elif algorithm == "dijkstra" or algorithm == "basic":
            from routing_node import RoutingNode
            return RoutingNode(node_id, jid, password, use_xmpp)
        
        else:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")

# Ejemplo de uso
if __name__ == "__main__":
    async def test_lsr():
        # Crear nodo LSR para pruebas
        node = LSRNode("A", 65001)
        await node.start()
        
        print("Nodo LSR iniciado para pruebas")
        await asyncio.sleep(10)
        
        await node.stop()
    
    asyncio.run(test_lsr())

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== LINK STATE ROUTING DEMO ===")
        
        # Crear nodo LSR
        lsr_node = RoutingNodeFactory.create_node(
            "lsr", "B", 65002
        )
        
        # Simular vecino
        lsr_node.neighbors["A"] = NeighborInfo(
            node_name="A", cost=5.0, last_hello=time.time()
        )
        
        print("✅ Nodo LSR creado")
        
        # Iniciar nodo
        await lsr_node.start()
        
        print("🚀 Nodo LSR iniciado - Simulando 10 segundos...")
        await asyncio.sleep(10)
        
        # Mostrar estado
        print(f"\nEstado LSR: {lsr_node.get_status()}")
        
        # Detener nodo
        await lsr_node.stop()
        
        print("✅ Demo LSR completada")
    
    asyncio.run(main())
