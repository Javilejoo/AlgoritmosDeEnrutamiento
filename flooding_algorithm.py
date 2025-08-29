"""
Implementación independiente del algoritmo de Flooding
Para cumplir completamente con los requerimientos del laboratorio
"""

import asyncio
import time
from typing import Dict, Set, Optional
from socket_routing_node import SocketRoutingNode, NeighborInfo
from protocolo import NetworkMessage, MessageFactory, MessageType

class FloodingNode(SocketRoutingNode):
    """Nodo que implementa el algoritmo de Flooding puro"""
    
    def __init__(self, node_id: str, port: int, topology_file: Optional[str] = None):
        super().__init__(node_id, port, topology_file)
        
        # Estado específico de Flooding
        self.seen_messages: Set[str] = set()  # Cache de mensajes ya procesados
        self.flood_sequence = 0
        self.ttl_default = 10  # TTL por defecto para flooding
        
        # Configurar handlers específicos de Flooding
        self.socket_client.register_handler("flood", self._handle_flood_message)
        
        self.logger.info(f"🌊 Nodo Flooding {node_id} inicializado")
    
    async def _routing_process(self):
        """Proceso de routing específico para Flooding - solo vecinos directos"""
        self.logger.info("🌊 Proceso Flooding iniciado")
        
        # En flooding puro, no hay cálculo de rutas
        # Solo se mantiene información de vecinos directos
        while self.state.name != "STOPPED":
            try:
                # Actualizar información de vecinos directos únicamente
                await self._update_direct_neighbors()
                
                # En flooding no se requiere cálculo de rutas
                # Cada mensaje se envía a todos los vecinos
                await asyncio.sleep(30)  # Verificación periódica de vecinos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en Flooding routing: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🔴 Proceso Flooding detenido")
    
    async def _update_direct_neighbors(self):
        """Actualiza solo información de vecinos directos"""
        # En flooding puro, solo se conoce a vecinos directos
        current_time = time.time()
        
        # Limpiar vecinos que no han respondido HELLO recientemente
        dead_neighbors = []
        for neighbor_jid, neighbor_info in list(self.neighbors.items()):
            if current_time - neighbor_info.last_hello > 60:  # 60 segundos timeout
                dead_neighbors.append(neighbor_jid)
        
        for neighbor_jid in dead_neighbors:
            del self.neighbors[neighbor_jid]
            self.logger.warning(f"🚫 Vecino {neighbor_jid} removido por timeout")
    
    async def send_user_message(self, destination: str, message: str):
        """Envía mensaje de usuario usando flooding"""
        # Crear ID único para el mensaje
        msg_id = f"{self.node_id}_{self.flood_sequence}_{int(time.time())}"
        self.flood_sequence += 1
        
        # Crear mensaje de flooding
        flood_message = MessageFactory.create_data_message(
            from_addr=self.socket_client.node_name,
            to_addr=destination,
            user_message=message,
            proto="flooding"
        )
        
        # Agregar headers específicos de flooding
        flood_message.add_header("flood_id", msg_id)
        flood_message.add_header("original_source", self.node_id)
        flood_message.ttl = self.ttl_default
        
        # Agregar a mensajes vistos para evitar loop
        self.seen_messages.add(msg_id)
        
        self.logger.info(f"🌊 Iniciando flooding de mensaje a {destination}")
        
        # Enviar a todos los vecinos
        await self._flood_to_all_neighbors(flood_message)
    
    async def _flood_to_all_neighbors(self, message: NetworkMessage):
        """Envía mensaje por flooding a todos los vecinos"""
        flooded_count = 0
        
        for neighbor_jid in self.neighbors:
            try:
                await self.socket_client.send_message_to(neighbor_jid, message)
                flooded_count += 1
                self.logger.debug(f"📡 Flooding enviado a {neighbor_jid}")
            except Exception as e:
                self.logger.error(f"Error flooding a {neighbor_jid}: {e}")
        
        if flooded_count > 0:
            self.logger.info(f"🌊 Mensaje enviado por flooding a {flooded_count} vecinos")
        else:
            self.logger.warning("⚠️ No se pudo enviar flooding a ningún vecino")
    
    async def _handle_flood_message(self, message: NetworkMessage, from_jid: str):
        """Maneja mensajes de flooding recibidos"""
        try:
            # Extraer ID del mensaje
            flood_id = None
            for header in message.headers:
                if "flood_id" in header:
                    flood_id = header["flood_id"]
                    break
            
            if not flood_id:
                self.logger.warning("⚠️ Mensaje flooding sin ID ignorado")
                return
            
            # Verificar si ya procesamos este mensaje
            if flood_id in self.seen_messages:
                self.logger.debug(f"🔄 Mensaje flooding duplicado ignorado: {flood_id}")
                return
            
            # Agregar a mensajes vistos
            self.seen_messages.add(flood_id)
            
            # Verificar TTL
            if message.ttl <= 0:
                self.logger.debug("⏰ Mensaje flooding expirado (TTL=0)")
                return
            
            # Si el mensaje es para nosotros
            if message.to_addr == self.node_id or message.to_addr == self.socket_client.node_name:
                self.logger.info(f"📥 MENSAJE RECIBIDO por flooding desde {message.from_addr}")
                self.logger.info(f"   Contenido: {message.payload.get('message', 'N/A')}")
                self.packets_received += 1
                return
            
            # Reenviar mensaje (decrementar TTL)
            message.ttl -= 1
            await self._forward_flood_message(message, from_jid)
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje flooding: {e}")
    
    async def _forward_flood_message(self, message: NetworkMessage, from_jid: str):
        """Reenvía mensaje de flooding a todos los vecinos excepto el origen"""
        forwarded_count = 0
        
        for neighbor_jid in self.neighbors:
            # No reenviar al nodo que nos envió el mensaje
            if neighbor_jid == from_jid:
                continue
            
            try:
                await self.socket_client.send_message_to(neighbor_jid, message)
                forwarded_count += 1
                self.packets_forwarded += 1
                self.logger.debug(f"📤 Flooding reenviado a {neighbor_jid}")
            except Exception as e:
                self.logger.error(f"Error reenviando flooding a {neighbor_jid}: {e}")
        
        if forwarded_count > 0:
            self.logger.info(f"🔄 Mensaje flooding reenviado a {forwarded_count} vecinos")
    
    def get_status(self) -> Dict[str, any]:
        """Retorna estado específico del nodo Flooding"""
        base_status = super().get_status()
        base_status.update({
            "algorithm": "flooding",
            "seen_messages": len(self.seen_messages),
            "flood_sequence": self.flood_sequence,
            "direct_neighbors_only": len(self.neighbors)
        })
        return base_status
    
    def print_status(self):
        """Imprime estado del nodo Flooding"""
        print(f"\n📊 ESTADO NODO FLOODING {self.node_id}")
        print(f"   Puerto: {self.port}")
        print(f"   Vecinos directos: {len(self.neighbors)}")
        print(f"   Mensajes vistos: {len(self.seen_messages)}")
        print(f"   Secuencia flooding: {self.flood_sequence}")
        print(f"   Paquetes reenviados: {self.packets_forwarded}")
        print(f"   Paquetes recibidos: {self.packets_received}")
        
        if self.neighbors:
            print("   Vecinos:")
            for neighbor_jid, neighbor_info in self.neighbors.items():
                print(f"     {neighbor_info.node_name}: costo {neighbor_info.cost}")

# Factory actualizado para incluir Flooding
class RoutingNodeFactory:
    """Factory para crear nodos con diferentes algoritmos"""
    
    @staticmethod
    def create_node(algorithm: str, node_id: str, port: int, 
                   topology_file: Optional[str] = None):
        """Crea un nodo según el algoritmo especificado"""
        algorithm = algorithm.lower()
        
        if algorithm == "flooding":
            return FloodingNode(node_id, port, topology_file)
        elif algorithm == "lsr":
            from routing_algorithms import LSRNode
            return LSRNode(node_id, port, topology_file)
        elif algorithm == "dijkstra" or algorithm == "basic":
            return SocketRoutingNode(node_id, port, topology_file)
        else:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")

# Demo del algoritmo de Flooding
async def demo_flooding_algorithm():
    """Demo específico del algoritmo de Flooding"""
    print("🌊 === DEMO ALGORITMO DE FLOODING PURO ===\n")
    
    # Crear nodos flooding
    nodes = {}
    for i, node_id in enumerate(["A", "B", "C", "D"], 1):
        nodes[node_id] = FloodingNode(node_id, 65000 + i)
    
    # Configurar topología simple (cadena lineal)
    # A - B - C - D
    nodes["A"].neighbors["B"] = NeighborInfo("B", 1, time.time())
    nodes["B"].neighbors["A"] = NeighborInfo("A", 1, time.time())
    nodes["B"].neighbors["C"] = NeighborInfo("C", 1, time.time())
    nodes["C"].neighbors["B"] = NeighborInfo("B", 1, time.time())
    nodes["C"].neighbors["D"] = NeighborInfo("D", 1, time.time())
    nodes["D"].neighbors["C"] = NeighborInfo("C", 1, time.time())
    
    try:
        # Iniciar todos los nodos
        print("🚀 Iniciando nodos flooding...")
        for node in nodes.values():
            await node.start()
        
        print("✅ Todos los nodos iniciados")
        await asyncio.sleep(2)
        
        # Enviar mensaje desde A hacia D
        print("\n📤 Enviando mensaje de A hacia D usando flooding...")
        await nodes["A"].send_user_message("D", "¡Hola desde A usando flooding puro!")
        
        # Esperar propagación
        await asyncio.sleep(5)
        
        # Mostrar estadísticas
        print("\n📊 ESTADÍSTICAS FINALES:")
        for node_id, node in nodes.items():
            status = node.get_status()
            print(f"   {node_id}: {status['packets_forwarded']} reenviados, {status['packets_received']} recibidos")
        
        # Probar flooding en dirección opuesta
        print("\n📤 Enviando mensaje de D hacia A...")
        await nodes["D"].send_user_message("A", "¡Respuesta desde D!")
        
        await asyncio.sleep(5)
        
        print("\n📊 ESTADÍSTICAS DESPUÉS DE SEGUNDO MENSAJE:")
        for node_id, node in nodes.items():
            node.print_status()
        
    finally:
        # Detener todos los nodos
        print("\n🛑 Deteniendo nodos...")
        for node in nodes.values():
            await node.stop()

if __name__ == "__main__":
    asyncio.run(demo_flooding_algorithm())
