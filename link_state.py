"""
Implementación del algoritmo de Link State Routing
Utiliza Dijkstra para calcular las rutas más cortas cuando cambia la topología de red
"""

import json
import time
import copy
import hashlib
from typing import Dict, List, Set, Tuple, Optional
from dijkstra import dijkstra, construir_tablas_para_todos, first_hop
from grafo import grafo

class LSP:
    """Link State Packet - Paquete de Estado de Enlace"""
    def __init__(self, source: str, sequence_num: int, age: int, neighbors: Dict[str, int]):
        self.source = source  # Nodo origen del LSP
        self.sequence_num = sequence_num  # Número de secuencia
        self.age = age  # Edad del paquete (TTL)
        self.neighbors = neighbors.copy()  # Vecinos y costos: {vecino: costo}
        self.timestamp = time.time()  # Marca de tiempo de creación
        
    def to_dict(self) -> dict:
        """Convierte el LSP a diccionario para serialización"""
        return {
            'source': self.source,
            'sequence_num': self.sequence_num,
            'age': self.age,
            'neighbors': self.neighbors,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Crea un LSP desde un diccionario"""
        lsp = cls(data['source'], data['sequence_num'], data['age'], data['neighbors'])
        lsp.timestamp = data['timestamp']
        return lsp
    
    def get_hash(self) -> str:
        """Genera un hash único para el LSP basado en su contenido"""
        content = f"{self.source}-{self.sequence_num}-{json.dumps(self.neighbors, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

class LinkStateDB:
    """Base de datos de estados de enlace"""
    def __init__(self):
        self.lsp_db: Dict[str, LSP] = {}  # {source: LSP_más_reciente}
        self.topology_version = 0
        
    def update_lsp(self, lsp: LSP) -> bool:
        """
        Actualiza la base de datos con un nuevo LSP.
        Retorna True si hubo cambios en la topología.
        """
        source = lsp.source
        updated = False
        
        if source not in self.lsp_db:
            # Nuevo nodo
            self.lsp_db[source] = lsp
            updated = True
            print(f"[LSDB] Nuevo LSP de {source}: {lsp.neighbors}")
        else:
            existing_lsp = self.lsp_db[source]
            
            # Verificar si es más reciente
            if lsp.sequence_num > existing_lsp.sequence_num:
                self.lsp_db[source] = lsp
                updated = True
                print(f"[LSDB] Actualizado LSP de {source} (seq: {existing_lsp.sequence_num} -> {lsp.sequence_num})")
            elif lsp.sequence_num == existing_lsp.sequence_num:
                # Mismo número de secuencia, verificar contenido
                if lsp.neighbors != existing_lsp.neighbors:
                    self.lsp_db[source] = lsp
                    updated = True
                    print(f"[LSDB] Contenido cambiado en LSP de {source}")
        
        if updated:
            self.topology_version += 1
            
        return updated
    
    def get_topology_graph(self) -> grafo:
        """
        Construye el grafo de topología completa desde la LSDB
        """
        g = grafo()
        
        # Agregar todos los enlaces desde cada LSP
        for source, lsp in self.lsp_db.items():
            for neighbor, cost in lsp.neighbors.items():
                g.agregar_conexion(source, neighbor, cost, bidireccional=False)
                
        return g
    
    def cleanup_old_lsps(self, max_age: int = 300):
        """Elimina LSPs antiguos (mayor a max_age segundos)"""
        current_time = time.time()
        to_remove = []
        
        for source, lsp in self.lsp_db.items():
            if current_time - lsp.timestamp > max_age:
                to_remove.append(source)
                
        for source in to_remove:
            del self.lsp_db[source]
            print(f"[LSDB] LSP de {source} eliminado por antigüedad")
            self.topology_version += 1
    
    def print_database(self):
        """Imprime el contenido de la base de datos"""
        print("\n=== LINK STATE DATABASE ===")
        print(f"Versión de topología: {self.topology_version}")
        print(f"Total de LSPs: {len(self.lsp_db)}")
        print("-" * 40)
        
        for source, lsp in sorted(self.lsp_db.items()):
            age = int(time.time() - lsp.timestamp)
            print(f"Nodo {source} (seq: {lsp.sequence_num}, edad: {age}s)")
            for neighbor, cost in sorted(lsp.neighbors.items()):
                print(f"  -> {neighbor}: costo {cost}")
        print("=" * 40)

class LinkStateNode:
    """Nodo que implementa el protocolo Link State"""
    
    def __init__(self, name: str, initial_neighbors: Dict[str, int]):
        self.name = name
        self.neighbors = initial_neighbors.copy()
        self.sequence_num = 0
        self.lsdb = LinkStateDB()
        self.routing_table = {}
        self.topology_version = 0
        
        # Crear y agregar nuestro LSP inicial
        self.generate_and_flood_lsp()
        
    def generate_and_flood_lsp(self) -> LSP:
        """Genera un nuevo LSP con la información local y lo propaga"""
        self.sequence_num += 1
        lsp = LSP(self.name, self.sequence_num, 0, self.neighbors)
        
        print(f"\n[{self.name}] Generando LSP #{self.sequence_num}")
        print(f"[{self.name}] Vecinos: {self.neighbors}")
        
        # Actualizar nuestra propia LSDB
        self.lsdb.update_lsp(lsp)
        
        return lsp
    
    def receive_lsp(self, lsp: LSP) -> bool:
        """
        Recibe un LSP de otro nodo.
        Retorna True si debe retransmitir el LSP.
        """
        # No procesar nuestros propios LSPs
        if lsp.source == self.name:
            return False
            
        print(f"[{self.name}] Recibido LSP de {lsp.source} (seq: {lsp.sequence_num})")
        
        # Actualizar LSDB
        topology_changed = self.lsdb.update_lsp(lsp)
        
        if topology_changed:
            # Recalcular tabla de enrutamiento
            self.calculate_routing_table()
            return True  # Retransmitir a otros vecinos
            
        return False
    
    def calculate_routing_table(self):
        """Recalcula la tabla de enrutamiento usando Dijkstra sobre la topología completa"""
        print(f"\n[{self.name}] Recalculando tabla de enrutamiento...")
        
        # Obtener grafo de topología desde LSDB
        topology_graph = self.lsdb.get_topology_graph()
        
        # Verificar que nuestro nodo esté en la topología
        if self.name not in topology_graph.routers:
            print(f"[{self.name}] ERROR: Nodo no encontrado en topología")
            return
        
        # Calcular rutas más cortas desde nuestro nodo
        distances, predecessors = dijkstra(topology_graph, self.name)
        
        # Construir tabla de enrutamiento
        self.routing_table = {}
        
        for dest in topology_graph.routers:
            if dest == self.name:
                continue
                
            distance = distances[dest]
            if distance == float('inf'):
                continue
                
            next_hop = first_hop(self.name, dest, predecessors)
            if next_hop:
                self.routing_table[dest] = {
                    'next_hop': next_hop,
                    'distance': distance,
                    'path': self._reconstruct_path(dest, predecessors)
                }
        
        # Actualizar versión
        self.topology_version = self.lsdb.topology_version
        
        print(f"[{self.name}] Tabla actualizada (versión {self.topology_version})")
        self.print_routing_table()
    
    def _reconstruct_path(self, dest: str, predecessors: Dict[str, Optional[str]]) -> List[str]:
        """Reconstruye el camino completo hacia un destino"""
        if self.name == dest:
            return [self.name]
        
        path = []
        current = dest
        
        while current is not None:
            path.append(current)
            if current == self.name:
                break
            current = predecessors.get(current)
        
        if not path or path[-1] != self.name:
            return []
        
        path.reverse()
        return path
    
    def update_neighbor(self, neighbor: str, cost: int):
        """Actualiza el costo hacia un vecino"""
        old_cost = self.neighbors.get(neighbor, None)
        
        if cost <= 0:
            # Eliminar vecino
            if neighbor in self.neighbors:
                del self.neighbors[neighbor]
                print(f"[{self.name}] Eliminado enlace hacia {neighbor}")
        else:
            # Agregar o actualizar vecino
            self.neighbors[neighbor] = cost
            if old_cost is None:
                print(f"[{self.name}] Nuevo enlace hacia {neighbor} con costo {cost}")
            elif old_cost != cost:
                print(f"[{self.name}] Actualizado enlace hacia {neighbor}: {old_cost} -> {cost}")
        
        # Generar nuevo LSP solo si hubo cambios
        if old_cost != cost or (cost <= 0 and old_cost is not None):
            self.generate_and_flood_lsp()
            self.calculate_routing_table()
    
    def remove_neighbor(self, neighbor: str):
        """Elimina un vecino"""
        self.update_neighbor(neighbor, 0)
    
    def print_routing_table(self):
        """Imprime la tabla de enrutamiento"""
        print(f"\n--- Tabla de Enrutamiento de {self.name} ---")
        print("Destino | Next-Hop | Distancia | Ruta Completa")
        print("-" * 50)
        
        for dest in sorted(self.routing_table.keys()):
            info = self.routing_table[dest]
            path_str = " -> ".join(info['path'])
            distance_str = str(int(info['distance'])) if info['distance'] != float('inf') else "∞"
            
            print(f"{dest:7} | {info['next_hop']:8} | {distance_str:9} | {path_str}")
        
        print("-" * 50)
    
    def get_next_hop(self, destination: str) -> Optional[str]:
        """Obtiene el siguiente salto hacia un destino"""
        if destination in self.routing_table:
            return self.routing_table[destination]['next_hop']
        return None
    
    def print_status(self):
        """Imprime el estado completo del nodo"""
        print(f"\n{'='*60}")
        print(f"Estado del Nodo {self.name}")
        print(f"{'='*60}")
        print(f"Secuencia LSP: {self.sequence_num}")
        print(f"Versión topología: {self.topology_version}")
        print(f"Vecinos directos: {self.neighbors}")
        
        self.lsdb.print_database()
        self.print_routing_table()

def simulacion_link_state():
    """Simulación del protocolo Link State con la red de ejemplo"""
    
    print("=== SIMULACIÓN ALGORITMO LINK STATE ===\n")
    
    # Definir la topología inicial (misma que en dijkstra.py)
    initial_topology = {
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
    
    # Crear nodos
    nodes = {}
    for name, neighbors in initial_topology.items():
        nodes[name] = LinkStateNode(name, neighbors)
        print(f"Nodo {name} creado")
    
    print("\n" + "="*80)
    print("FASE 1: CONVERGENCIA INICIAL")
    print("="*80)
    
    # Simular intercambio de LSPs entre todos los nodos
    all_lsps = []
    
    # Recolectar todos los LSPs generados
    for node in nodes.values():
        lsp = node.lsdb.lsp_db[node.name]  # Su propio LSP
        all_lsps.append(lsp)
    
    # Distribuir LSPs a todos los nodos
    for node in nodes.values():
        print(f"\n[FLOODING] Enviando LSPs a nodo {node.name}")
        for lsp in all_lsps:
            if lsp.source != node.name:  # No enviar su propio LSP
                node.receive_lsp(lsp)
    
    print("\n" + "="*80)
    print("ESTADO DESPUÉS DE LA CONVERGENCIA INICIAL")
    print("="*80)
    
    # Mostrar estado de algunos nodos representativos
    for node_name in ['A', 'D', 'F']:
        nodes[node_name].print_status()
    
    print("\n" + "="*80)
    print("FASE 2: SIMULACIÓN DE CAMBIO EN LA RED")
    print("="*80)
    
    # Simular falla del enlace F-H (costo 4)
    print("\n🔥 SIMULANDO FALLA DEL ENLACE F-H 🔥")
    print("-" * 40)
    
    # El nodo F detecta que perdió conectividad con H
    nodes['F'].remove_neighbor('H')
    # El nodo H detecta que perdió conectividad con F
    nodes['H'].remove_neighbor('F')
    
    # Obtener los nuevos LSPs
    new_lsps = [
        nodes['F'].lsdb.lsp_db['F'],
        nodes['H'].lsdb.lsp_db['H']
    ]
    
    # Propagar los cambios
    print("\n[FLOODING] Propagando cambios por falla de enlace...")
    for node in nodes.values():
        if node.name not in ['F', 'H']:  # Los nodos afectados ya se actualizaron
            for lsp in new_lsps:
                node.receive_lsp(lsp)
    
    print("\n" + "="*80)
    print("ESTADO DESPUÉS DEL CAMBIO DE TOPOLOGÍA")
    print("="*80)
    
    # Mostrar cómo cambió el enrutamiento
    for node_name in ['A', 'G']:  # Nodos que podrían verse afectados por la falla F-H
        print(f"\n--- Impacto en nodo {node_name} ---")
        nodes[node_name].print_routing_table()
    
    print("\n" + "="*80)
    print("FASE 3: RECUPERACIÓN DE ENLACE")
    print("="*80)
    
    # Simular recuperación del enlace F-H con costo diferente
    print("\n✅ SIMULANDO RECUPERACIÓN DEL ENLACE F-H CON COSTO 6 ✅")
    print("-" * 50)
    
    nodes['F'].update_neighbor('H', 6)  # Costo mayor que antes (era 4)
    nodes['H'].update_neighbor('F', 6)
    
    # Propagar recuperación
    recovery_lsps = [
        nodes['F'].lsdb.lsp_db['F'],
        nodes['H'].lsdb.lsp_db['H']
    ]
    
    for node in nodes.values():
        if node.name not in ['F', 'H']:
            for lsp in recovery_lsps:
                node.receive_lsp(lsp)
    
    print("\n" + "="*80)
    print("ESTADO FINAL DESPUÉS DE LA RECUPERACIÓN")
    print("="*80)
    
    # Estado final
    nodes['A'].print_status()
    
    print("\n" + "="*80)
    print("COMPARACIÓN: RUTAS HACIA H DESDE DIFERENTES NODOS")
    print("="*80)
    
    for source in ['A', 'B', 'C', 'E']:
        if 'H' in nodes[source].routing_table:
            route_info = nodes[source].routing_table['H']
            path = " -> ".join(route_info['path'])
            print(f"{source} hacia H: {path} (distancia: {route_info['distance']})")
        else:
            print(f"{source} hacia H: SIN RUTA")
    
    return nodes

if __name__ == "__main__":
    # Ejecutar simulación
    nodos_finales = simulacion_link_state()
    
    print("\n" + "="*80)
    print("SIMULACIÓN COMPLETADA")
    print("="*80)
    print("\nEl algoritmo Link State ha demostrado:")
    print("✓ Convergencia inicial con información completa de topología")
    print("✓ Detección y propagación de fallas de enlaces")
    print("✓ Recálculo automático de rutas óptimas")
    print("✓ Recuperación ante restauración de enlaces")
    print("✓ Mantenimiento de consistencia en toda la red")
