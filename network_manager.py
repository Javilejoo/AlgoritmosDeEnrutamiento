"""
Gestor de red distribuida
Maneja múltiples nodos con el protocolo específico
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from distributed_node import DistributedNode
from network_protocol import NetworkMessageFactory

class NetworkManager:
    """Gestor para redes distribuidas"""
    
    def __init__(self):
        self.nodes = {}  # {node_id: DistributedNode}
        self.topology = {}  # {node_id: {neighbor_id: cost}}
        self.all_done = set()  # Nodos que han terminado cálculos
        
    def add_node(self, node_id: str, port: int, algorithm: str = "flooding"):
        """Agrega un nodo a la red"""
        node = DistributedNode(node_id, port, algorithm)
        self.nodes[node_id] = node
        self.topology[node_id] = {}
        print(f"➕ Nodo {node_id} agregado al gestor")
    
    def add_connection(self, node1: str, node2: str, cost: int):
        """Agrega conexión bidireccional entre nodos"""
        if node1 in self.nodes and node2 in self.nodes:
            # Configurar topología
            self.topology[node1][node2] = cost
            self.topology[node2][node1] = cost
            
            # Configurar nodos
            port1 = self.nodes[node1].port
            port2 = self.nodes[node2].port
            
            self.nodes[node1].add_neighbour(node2, cost, "localhost", port2)
            self.nodes[node2].add_neighbour(node1, cost, "localhost", port1)
            
            print(f"🔗 Conexión agregada: {node1} <-> {node2} (costo: {cost})")
    
    async def start_network(self):
        """Inicia todos los nodos de la red"""
        print("🚀 Iniciando red distribuida...")
        
        for node in self.nodes.values():
            await node.start()
        
        await asyncio.sleep(1)
        print("✅ Todos los nodos iniciados")
    
    async def stop_network(self):
        """Detiene todos los nodos"""
        print("🛑 Deteniendo red distribuida...")
        
        for node in self.nodes.values():
            await node.stop()
        
        print("✅ Todos los nodos detenidos")
    
    async def initialize_network(self):
        """Envía mensajes INIT desde todos los nodos"""
        print("📢 Enviando mensajes INIT...")
        
        for node in self.nodes.values():
            await node.send_init_message()
            await asyncio.sleep(0.5)  # Pequeña pausa entre INITs
        
        print("✅ Mensajes INIT enviados")
    
    async def calculate_all_routes(self):
        """Hace que todos los nodos calculen sus rutas"""
        print("🔄 Iniciando cálculo de rutas en todos los nodos...")
        
        # Iniciar cálculos en paralelo
        tasks = []
        for node in self.nodes.values():
            tasks.append(node.calculate_routes())
        
        await asyncio.gather(*tasks)
        
        print("✅ Todos los nodos terminaron cálculos")
    
    async def send_test_messages(self):
        """Envía mensajes de prueba entre nodos"""
        print("📤 Enviando mensajes de prueba...")
        
        node_ids = list(self.nodes.keys())
        
        for i, sender_id in enumerate(node_ids):
            for j, receiver_id in enumerate(node_ids):
                if i != j:  # No enviarse a sí mismo
                    message = f"Mensaje de {sender_id} para {receiver_id} - {int(time.time())}"
                    await self.nodes[sender_id].send_user_message(receiver_id, message)
                    await asyncio.sleep(0.5)
        
        print("✅ Mensajes de prueba enviados")
    
    async def wait_for_convergence(self, timeout: int = 30):
        """Espera a que todos los nodos terminen sus cálculos"""
        print("⏳ Esperando convergencia de la red...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_done = all(node.calculation_done for node in self.nodes.values())
            
            if all_done:
                print("✅ Red convergida - todos los nodos terminaron")
                return True
            
            await asyncio.sleep(1)
        
        print("⚠️ Timeout - no todos los nodos convergieron")
        return False
    
    def print_network_status(self):
        """Imprime estado de toda la red"""
        print("\n" + "="*50)
        print("📊 ESTADO DE LA RED DISTRIBUIDA")
        print("="*50)
        
        for node_id, node in self.nodes.items():
            node.print_status()
        
        print("\n📈 ESTADÍSTICAS GLOBALES:")
        total_sent = sum(node.messages_sent for node in self.nodes.values())
        total_received = sum(node.messages_received for node in self.nodes.values())
        total_init = sum(node.init_messages_received for node in self.nodes.values())
        total_done = sum(node.done_messages_received for node in self.nodes.values())
        
        print(f"   Total mensajes enviados: {total_sent}")
        print(f"   Total mensajes recibidos: {total_received}")
        print(f"   Total INIT recibidos: {total_init}")
        print(f"   Total DONE recibidos: {total_done}")
        print(f"   Nodos activos: {len(self.nodes)}")
        
        # Mostrar topología
        print(f"\n🌐 TOPOLOGÍA:")
        for node_id, neighbors in self.topology.items():
            neighbor_str = ", ".join([f"{n}({c})" for n, c in neighbors.items()])
            print(f"   {node_id}: {neighbor_str}")
    
    def save_network_config(self, filename: str):
        """Guarda configuración de la red"""
        config = {
            "nodes": {
                node_id: {
                    "port": node.port,
                    "algorithm": node.algorithm
                }
                for node_id, node in self.nodes.items()
            },
            "topology": self.topology,
            "timestamp": time.time()
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuración guardada en {filename}")
    
    @classmethod
    def load_network_config(cls, filename: str) -> 'NetworkManager':
        """Carga configuración de la red"""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        manager = cls()
        
        # Cargar nodos
        for node_id, node_config in config["nodes"].items():
            manager.add_node(
                node_id,
                node_config["port"],
                node_config["algorithm"]
            )
        
        # Cargar topología
        for node_id, neighbors in config["topology"].items():
            for neighbor_id, cost in neighbors.items():
                if node_id < neighbor_id:  # Evitar duplicados
                    manager.add_connection(node_id, neighbor_id, cost)
        
        print(f"📁 Configuración cargada desde {filename}")
        return manager

# Demo completo
async def demo_distributed_network():
    """Demo completo de red distribuida"""
    print("=== DEMO RED DISTRIBUIDA COMPLETA ===\n")
    
    # Crear gestor
    manager = NetworkManager()
    
    # Agregar nodos (mezcla de algoritmos)
    manager.add_node("A", 65501, "flooding")
    manager.add_node("B", 65502, "lsr")  
    manager.add_node("C", 65503, "flooding")
    manager.add_node("D", 65504, "lsr")
    
    # Configurar topología en cuadrado
    manager.add_connection("A", "B", 5)
    manager.add_connection("B", "C", 3)
    manager.add_connection("C", "D", 7)
    manager.add_connection("D", "A", 4)
    manager.add_connection("A", "C", 10)  # Diagonal
    
    try:
        # Ejecutar protocolo completo
        await manager.start_network()
        await asyncio.sleep(2)
        
        await manager.initialize_network()
        await asyncio.sleep(3)
        
        await manager.calculate_all_routes()
        await manager.wait_for_convergence()
        await asyncio.sleep(2)
        
        await manager.send_test_messages()
        await asyncio.sleep(5)
        
        # Mostrar resultados
        manager.print_network_status()
        
        # Guardar configuración
        manager.save_network_config("distributed_network_config.json")
        
    finally:
        await manager.stop_network()

if __name__ == "__main__":
    asyncio.run(demo_distributed_network())
