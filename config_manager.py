"""
Configuración de topología y nodos
Formatos estándar para archivos de configuración
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class NodeConfig:
    """Configuración de un nodo individual"""
    node_id: str
    jid: str
    password: str
    resource: str = "routing"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NodeConfig':
        return cls(**data)

@dataclass
class TopologyConfig:
    """Configuración de topología de red"""
    nodes: List[str]
    connections: Dict[str, Dict[str, int]]  # {from_node: {to_node: cost}}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TopologyConfig':
        return cls(**data)
    
    def get_neighbors(self, node_id: str) -> Dict[str, int]:
        """Obtiene los vecinos de un nodo específico"""
        return self.connections.get(node_id, {})
    
    def get_cost(self, from_node: str, to_node: str) -> Optional[int]:
        """Obtiene el costo entre dos nodos"""
        return self.connections.get(from_node, {}).get(to_node)

class ConfigManager:
    """Gestor de configuraciones"""
    
    @staticmethod
    def create_sample_topology() -> TopologyConfig:
        """Crea una topología de ejemplo"""
        return TopologyConfig(
            nodes=["A", "B", "C", "D", "E", "F", "G", "H", "I"],
            connections={
                "A": {"B": 7, "I": 1, "C": 7},
                "B": {"A": 7, "F": 2},
                "C": {"A": 7, "D": 5},
                "D": {"I": 6, "C": 5, "F": 1, "E": 1},
                "E": {"D": 1, "G": 4},
                "F": {"B": 2, "D": 1, "G": 3, "H": 4},
                "G": {"F": 3, "E": 4},
                "H": {"F": 4},
                "I": {"A": 1, "D": 6}
            }
        )
    
    @staticmethod
    def create_sample_nodes() -> List[NodeConfig]:
        """Crea configuraciones de nodos de ejemplo"""
        nodes = []
        for node_id in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
            nodes.append(NodeConfig(
                node_id=node_id,
                jid=f"node_{node_id.lower()}@localhost",
                password=f"password_{node_id.lower()}",
                resource="routing"
            ))
        return nodes
    
    @staticmethod
    def save_topology(topology: TopologyConfig, filename: str):
        """Guarda topología en archivo JSON"""
        with open(filename, 'w') as f:
            json.dump(topology.to_dict(), f, indent=2)
        print(f"✅ Topología guardada en {filename}")
    
    @staticmethod
    def load_topology(filename: str) -> TopologyConfig:
        """Carga topología desde archivo JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return TopologyConfig.from_dict(data)
    
    @staticmethod
    def save_nodes(nodes: List[NodeConfig], filename: str):
        """Guarda configuración de nodos en archivo JSON"""
        nodes_data = [node.to_dict() for node in nodes]
        with open(filename, 'w') as f:
            json.dump(nodes_data, f, indent=2)
        print(f"✅ Configuración de nodos guardada en {filename}")
    
    @staticmethod
    def load_nodes(filename: str) -> List[NodeConfig]:
        """Carga configuración de nodos desde archivo JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return [NodeConfig.from_dict(node_data) for node_data in data]
    
    @staticmethod
    def create_config_files():
        """Crea archivos de configuración de ejemplo"""
        # Crear topología
        topology = ConfigManager.create_sample_topology()
        ConfigManager.save_topology(topology, "topology.json")
        
        # Crear nodos
        nodes = ConfigManager.create_sample_nodes()
        ConfigManager.save_nodes(nodes, "nodes.json")
        
        print("📁 Archivos de configuración creados:")
        print("   - topology.json")
        print("   - nodes.json")

# Validador de configuraciones
class ConfigValidator:
    """Validador para configuraciones"""
    
    @staticmethod
    def validate_topology(topology: TopologyConfig) -> List[str]:
        """Valida una configuración de topología"""
        errors = []
        
        # Verificar que todos los nodos en conexiones estén en la lista
        for from_node, connections in topology.connections.items():
            if from_node not in topology.nodes:
                errors.append(f"Nodo {from_node} en conexiones pero no en lista de nodos")
            
            for to_node in connections:
                if to_node not in topology.nodes:
                    errors.append(f"Nodo {to_node} en conexiones pero no en lista de nodos")
        
        # Verificar costos positivos
        for from_node, connections in topology.connections.items():
            for to_node, cost in connections.items():
                if cost <= 0:
                    errors.append(f"Costo inválido {cost} entre {from_node} y {to_node}")
        
        return errors
    
    @staticmethod
    def validate_nodes(nodes: List[NodeConfig]) -> List[str]:
        """Valida configuraciones de nodos"""
        errors = []
        
        # Verificar JIDs únicos
        jids = [node.jid for node in nodes]
        if len(jids) != len(set(jids)):
            errors.append("JIDs duplicados encontrados")
        
        # Verificar node_ids únicos
        node_ids = [node.node_id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Node IDs duplicados encontrados")
        
        # Verificar formato de JID básico
        for node in nodes:
            if "@" not in node.jid:
                errors.append(f"JID inválido para nodo {node.node_id}: {node.jid}")
        
        return errors

# Generador de configuraciones para diferentes escenarios
class ScenarioGenerator:
    """Generador de escenarios de prueba"""
    
    @staticmethod
    def linear_topology(num_nodes: int) -> TopologyConfig:
        """Genera topología lineal A-B-C-D-..."""
        nodes = [chr(65 + i) for i in range(num_nodes)]  # A, B, C, ...
        connections = {}
        
        for i in range(len(nodes)):
            connections[nodes[i]] = {}
            if i > 0:
                connections[nodes[i]][nodes[i-1]] = 1
            if i < len(nodes) - 1:
                connections[nodes[i]][nodes[i+1]] = 1
        
        return TopologyConfig(nodes=nodes, connections=connections)
    
    @staticmethod
    def ring_topology(num_nodes: int) -> TopologyConfig:
        """Genera topología en anillo"""
        nodes = [chr(65 + i) for i in range(num_nodes)]
        connections = {}
        
        for i in range(len(nodes)):
            connections[nodes[i]] = {
                nodes[(i-1) % len(nodes)]: 1,
                nodes[(i+1) % len(nodes)]: 1
            }
        
        return TopologyConfig(nodes=nodes, connections=connections)
    
    @staticmethod
    def star_topology(num_nodes: int, center_node: str = "A") -> TopologyConfig:
        """Genera topología en estrella"""
        nodes = [chr(65 + i) for i in range(num_nodes)]
        if center_node not in nodes:
            nodes[0] = center_node
        
        connections = {}
        
        # Nodo central conectado a todos
        connections[center_node] = {}
        for node in nodes:
            if node != center_node:
                connections[center_node][node] = 1
        
        # Otros nodos solo conectados al centro
        for node in nodes:
            if node != center_node:
                connections[node] = {center_node: 1}
        
        return TopologyConfig(nodes=nodes, connections=connections)
    
    @staticmethod
    def mesh_topology(num_nodes: int) -> TopologyConfig:
        """Genera topología de malla completa"""
        nodes = [chr(65 + i) for i in range(num_nodes)]
        connections = {}
        
        for i, node1 in enumerate(nodes):
            connections[node1] = {}
            for j, node2 in enumerate(nodes):
                if i != j:
                    connections[node1][node2] = 1
        
        return TopologyConfig(nodes=nodes, connections=connections)

# Ejemplo de uso
if __name__ == "__main__":
    print("=== GESTOR DE CONFIGURACIONES ===")
    
    # Crear archivos de configuración
    ConfigManager.create_config_files()
    
    # Cargar y validar
    topology = ConfigManager.load_topology("topology.json")
    nodes = ConfigManager.load_nodes("nodes.json")
    
    print(f"\n📊 Topología cargada: {len(topology.nodes)} nodos")
    print(f"🔗 Total conexiones: {sum(len(conns) for conns in topology.connections.values())}")
    
    # Validar configuraciones
    topo_errors = ConfigValidator.validate_topology(topology)
    node_errors = ConfigValidator.validate_nodes(nodes)
    
    if topo_errors:
        print(f"\n❌ Errores en topología: {topo_errors}")
    else:
        print("\n✅ Topología válida")
    
    if node_errors:
        print(f"❌ Errores en nodos: {node_errors}")
    else:
        print("✅ Configuración de nodos válida")
    
    # Generar escenarios de prueba
    print(f"\n🔬 Generando escenarios de prueba...")
    
    scenarios = {
        "linear_5": ScenarioGenerator.linear_topology(5),
        "ring_6": ScenarioGenerator.ring_topology(6),
        "star_7": ScenarioGenerator.star_topology(7),
        "mesh_4": ScenarioGenerator.mesh_topology(4)
    }
    
    for name, scenario in scenarios.items():
        ConfigManager.save_topology(scenario, f"scenario_{name}.json")
        print(f"   📁 {name}: {len(scenario.nodes)} nodos")
    
    print("\n✅ Configuraciones y escenarios creados")
