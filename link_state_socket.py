"""
Implementación distribuida del algoritmo Link State usando sockets
Cada nodo es un proceso independiente que se comunica con otros nodos via TCP
"""

import socket
import json
import threading
import time
import sys
import hashlib
from typing import Dict, List, Optional, Set
from dijkstra import dijkstra, first_hop
from grafo import grafo

class LSP:
    """Link State Packet para comunicación entre nodos"""
    def __init__(self, source: str, sequence_num: int, age: int, neighbors: Dict[str, int]):
        self.source = source
        self.sequence_num = sequence_num
        self.age = age
        self.neighbors = neighbors.copy()
        self.timestamp = time.time()
        
    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'sequence_num': self.sequence_num,
            'age': self.age,
            'neighbors': self.neighbors,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        lsp = cls(data['source'], data['sequence_num'], data['age'], data['neighbors'])
        lsp.timestamp = data['timestamp']
        return lsp

class LinkStateSocketNode:
    """Nodo Link State que se comunica via sockets"""
    
    def __init__(self, nombre: str, puerto: int, vecinos_iniciales: Dict[str, int], puertos_nodos: Dict[str, int]):
        self.nombre = nombre
        self.puerto = puerto
        self.host = '127.0.0.1'
        self.vecinos = vecinos_iniciales.copy()
        self.puertos_nodos = puertos_nodos.copy()
        
        # Estado Link State
        self.sequence_num = 0
        self.lsdb = {}  # {source: LSP}
        self.routing_table = {}
        self.topology_version = 0
        
        # Sockets y threading
        self.servidor_socket = None
        self.activo = True
        self.lock = threading.RLock()
        
        # Para tracking de LSPs enviados recientemente (evitar loops)
        self.lsp_cache = set()  # Set de hashes de LSPs enviados recientemente
        
        # Estadísticas
        self.lsps_enviados = 0
        self.lsps_recibidos = 0
        self.tablas_calculadas = 0
        
    def iniciar_servidor(self):
        """Inicia el servidor para recibir mensajes de otros nodos"""
        try:
            self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.servidor_socket.bind((self.host, self.puerto))
            self.servidor_socket.listen(10)
            print(f"[{self.nombre}] Servidor iniciado en puerto {self.puerto}")
            
            while self.activo:
                try:
                    cliente, direccion = self.servidor_socket.accept()
                    threading.Thread(target=self.manejar_cliente, args=(cliente, direccion), daemon=True).start()
                except Exception as e:
                    if self.activo:  # Solo mostrar error si no estamos cerrando
                        print(f"[{self.nombre}] Error aceptando conexión: {e}")
                    break
        except Exception as e:
            print(f"[{self.nombre}] Error iniciando servidor: {e}")
        finally:
            if self.servidor_socket:
                self.servidor_socket.close()
                
    def manejar_cliente(self, cliente, direccion):
        """Maneja mensajes entrantes de otros nodos"""
        try:
            # Recibir mensaje
            data = cliente.recv(4096).decode('utf-8')
            if not data:
                return
                
            mensaje = json.loads(data)
            tipo = mensaje.get('tipo')
            
            if tipo == 'lsp_flood':
                # Recibir LSP de otro nodo
                lsp_data = mensaje['lsp']
                lsp = LSP.from_dict(lsp_data)
                self.procesar_lsp_recibido(lsp, mensaje.get('sender'))
                
                # Confirmar recepción
                respuesta = {'tipo': 'ack', 'nodo': self.nombre}
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == 'hello':
                # Mensaje de saludo para verificar conectividad
                respuesta = {
                    'tipo': 'hello_response',
                    'nodo': self.nombre,
                    'timestamp': time.time()
                }
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == 'get_status':
                # Solicitud de estado del nodo
                estado = self.obtener_estado_completo()
                respuesta = {
                    'tipo': 'status_response',
                    'nodo': self.nombre,
                    'estado': estado
                }
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
        except Exception as e:
            print(f"[{self.nombre}] Error manejando cliente: {e}")
        finally:
            try:
                cliente.close()
            except:
                pass
                
    def generar_lsp(self) -> LSP:
        """Genera un nuevo LSP con la información local"""
        with self.lock:
            self.sequence_num += 1
            lsp = LSP(self.nombre, self.sequence_num, 0, self.vecinos)
            
            # Actualizar nuestra propia LSDB
            self.lsdb[self.nombre] = lsp
            
            print(f"[{self.nombre}] Generado LSP #{self.sequence_num} con vecinos: {self.vecinos}")
            return lsp
            
    def procesar_lsp_recibido(self, lsp: LSP, sender: str = None):
        """Procesa un LSP recibido de otro nodo"""
        with self.lock:
            self.lsps_recibidos += 1
            
            # No procesar nuestros propios LSPs
            if lsp.source == self.nombre:
                return
                
            print(f"[{self.nombre}] Recibido LSP de {lsp.source} (seq: {lsp.sequence_num}) via {sender}")
            
            # Verificar si es más reciente
            topology_changed = False
            
            if lsp.source not in self.lsdb:
                # Nuevo nodo
                self.lsdb[lsp.source] = lsp
                topology_changed = True
                print(f"[{self.nombre}] Nueva entrada LSDB para {lsp.source}")
            else:
                existing_lsp = self.lsdb[lsp.source]
                
                if lsp.sequence_num > existing_lsp.sequence_num:
                    # LSP más reciente
                    self.lsdb[lsp.source] = lsp
                    topology_changed = True
                    print(f"[{self.nombre}] Actualizada LSDB para {lsp.source} (seq: {existing_lsp.sequence_num} -> {lsp.sequence_num})")
                elif lsp.sequence_num == existing_lsp.sequence_num and lsp.neighbors != existing_lsp.neighbors:
                    # Mismo número de secuencia pero contenido diferente
                    self.lsdb[lsp.source] = lsp
                    topology_changed = True
                    print(f"[{self.nombre}] Contenido cambiado para {lsp.source}")
                    
            if topology_changed:
                self.topology_version += 1
                # Recalcular tabla de enrutamiento
                self.calcular_tabla_enrutamiento()
                # Retransmitir a vecinos (flooding)
                self.retransmitir_lsp(lsp, sender)
                
    def retransmitir_lsp(self, lsp: LSP, sender: str = None):
        """Retransmite un LSP a todos los vecinos excepto al sender"""
        lsp_hash = hashlib.md5(json.dumps(lsp.to_dict(), sort_keys=True).encode()).hexdigest()
        
        # Evitar retransmisiones duplicadas recientes
        if lsp_hash in self.lsp_cache:
            return
            
        self.lsp_cache.add(lsp_hash)
        
        # Limpiar cache viejo (mantener solo últimos 100)
        if len(self.lsp_cache) > 100:
            self.lsp_cache.clear()
            
        vecinos_a_enviar = []
        for vecino in self.vecinos.keys():
            if vecino != sender and vecino in self.puertos_nodos:
                vecinos_a_enviar.append(vecino)
                
        if vecinos_a_enviar:
            print(f"[{self.nombre}] Retransmitiendo LSP de {lsp.source} a: {vecinos_a_enviar}")
            for vecino in vecinos_a_enviar:
                threading.Thread(target=self.enviar_lsp_a_nodo, args=(lsp, vecino), daemon=True).start()
                
    def enviar_lsp_a_nodo(self, lsp: LSP, destino: str):
        """Envía un LSP a un nodo específico"""
        if destino not in self.puertos_nodos:
            return
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)  # Timeout de 5 segundos
                sock.connect((self.host, self.puertos_nodos[destino]))
                
                mensaje = {
                    'tipo': 'lsp_flood',
                    'sender': self.nombre,
                    'lsp': lsp.to_dict()
                }
                
                sock.send(json.dumps(mensaje).encode('utf-8'))
                
                # Esperar confirmación
                respuesta = sock.recv(1024).decode('utf-8')
                if respuesta:
                    ack = json.loads(respuesta)
                    if ack.get('tipo') == 'ack':
                        self.lsps_enviados += 1
                        
        except Exception as e:
            print(f"[{self.nombre}] Error enviando LSP a {destino}: {e}")
            
    def calcular_tabla_enrutamiento(self):
        """Calcula la tabla de enrutamiento usando Dijkstra sobre la LSDB"""
        with self.lock:
            print(f"[{self.nombre}] Recalculando tabla de enrutamiento (versión {self.topology_version})")
            self.tablas_calculadas += 1
            
            # Construir grafo desde LSDB
            grafo_topologia = grafo()
            
            for source, lsp in self.lsdb.items():
                for neighbor, cost in lsp.neighbors.items():
                    grafo_topologia.agregar_conexion(source, neighbor, cost, bidireccional=False)
                    
            # Verificar que estemos en la topología
            if self.nombre not in grafo_topologia.routers:
                print(f"[{self.nombre}] ERROR: Nodo no encontrado en topología construida")
                return
                
            # Calcular rutas más cortas
            try:
                distances, predecessors = dijkstra(grafo_topologia, self.nombre)
                
                # Construir tabla de enrutamiento
                nueva_tabla = {}
                
                for dest in grafo_topologia.routers:
                    if dest == self.nombre:
                        continue
                        
                    distance = distances[dest]
                    if distance == float('inf'):
                        continue
                        
                    next_hop = first_hop(self.nombre, dest, predecessors)
                    if next_hop:
                        nueva_tabla[dest] = {
                            'next_hop': next_hop,
                            'distance': distance,
                            'path': self._reconstruir_ruta(dest, predecessors)
                        }
                        
                # Detectar cambios en la tabla
                cambios = self._detectar_cambios_tabla(nueva_tabla)
                self.routing_table = nueva_tabla
                
                if cambios:
                    print(f"[{self.nombre}] Tabla de enrutamiento actualizada:")
                    self.imprimir_tabla_enrutamiento()
                    
            except Exception as e:
                print(f"[{self.nombre}] Error calculando tabla de enrutamiento: {e}")
                
    def _reconstruir_ruta(self, dest: str, predecessors: Dict[str, Optional[str]]) -> List[str]:
        """Reconstruye la ruta completa hacia un destino"""
        if self.nombre == dest:
            return [self.nombre]
        
        path = []
        current = dest
        
        while current is not None:
            path.append(current)
            if current == self.nombre:
                break
            current = predecessors.get(current)
        
        if not path or path[-1] != self.nombre:
            return []
        
        path.reverse()
        return path
        
    def _detectar_cambios_tabla(self, nueva_tabla: Dict) -> bool:
        """Detecta si hay cambios significativos en la tabla de enrutamiento"""
        if not self.routing_table:
            return bool(nueva_tabla)
            
        # Comparar destinos
        destinos_viejos = set(self.routing_table.keys())
        destinos_nuevos = set(nueva_tabla.keys())
        
        if destinos_viejos != destinos_nuevos:
            return True
            
        # Comparar rutas
        for dest in destinos_nuevos:
            vieja = self.routing_table.get(dest, {})
            nueva = nueva_tabla[dest]
            
            if (vieja.get('next_hop') != nueva.get('next_hop') or 
                abs(vieja.get('distance', 0) - nueva.get('distance', 0)) > 0.001):
                return True
                
        return False
        
    def actualizar_vecino(self, vecino: str, costo: int):
        """Actualiza el costo hacia un vecino y genera nuevo LSP"""
        with self.lock:
            cambio = False
            
            if costo <= 0:
                # Eliminar vecino
                if vecino in self.vecinos:
                    del self.vecinos[vecino]
                    cambio = True
                    print(f"[{self.nombre}] Eliminado enlace hacia {vecino}")
            else:
                # Agregar o actualizar vecino
                costo_anterior = self.vecinos.get(vecino)
                if costo_anterior != costo:
                    self.vecinos[vecino] = costo
                    cambio = True
                    if costo_anterior is None:
                        print(f"[{self.nombre}] Nuevo enlace hacia {vecino} con costo {costo}")
                    else:
                        print(f"[{self.nombre}] Actualizado enlace hacia {vecino}: {costo_anterior} -> {costo}")
                        
            if cambio:
                # Generar y propagar nuevo LSP
                lsp = self.generar_lsp()
                self.calcular_tabla_enrutamiento()
                self.propagar_lsp_inicial(lsp)
                
    def propagar_lsp_inicial(self, lsp: LSP):
        """Propaga un LSP generado localmente a todos los vecinos"""
        vecinos_destino = [v for v in self.vecinos.keys() if v in self.puertos_nodos]
        
        if vecinos_destino:
            print(f"[{self.nombre}] Propagando LSP inicial a vecinos: {vecinos_destino}")
            for vecino in vecinos_destino:
                threading.Thread(target=self.enviar_lsp_a_nodo, args=(lsp, vecino), daemon=True).start()
                
    def imprimir_tabla_enrutamiento(self):
        """Imprime la tabla de enrutamiento actual"""
        print(f"\n--- Tabla de Enrutamiento de {self.nombre} ---")
        print("Destino | Next-Hop | Distancia | Ruta")
        print("-" * 45)
        
        if not self.routing_table:
            print("  (tabla vacía)")
        else:
            for dest in sorted(self.routing_table.keys()):
                info = self.routing_table[dest]
                path_str = " -> ".join(info['path'])
                distance_str = str(int(info['distance'])) if info['distance'] != float('inf') else "∞"
                
                print(f"{dest:7} | {info['next_hop']:8} | {distance_str:9} | {path_str}")
        
        print("-" * 45)
        
    def imprimir_lsdb(self):
        """Imprime el contenido de la base de datos Link State"""
        print(f"\n--- LSDB de {self.nombre} (versión {self.topology_version}) ---")
        print("Nodo | Seq | Edad | Vecinos")
        print("-" * 40)
        
        for source in sorted(self.lsdb.keys()):
            lsp = self.lsdb[source]
            edad = int(time.time() - lsp.timestamp)
            vecinos_str = ", ".join(f"{v}:{c}" for v, c in sorted(lsp.neighbors.items()))
            print(f"{source:4} | {lsp.sequence_num:3} | {edad:4}s | {vecinos_str}")
            
        print("-" * 40)
        
    def obtener_estado_completo(self):
        """Obtiene el estado completo del nodo"""
        with self.lock:
            return {
                'nombre': self.nombre,
                'vecinos': self.vecinos,
                'sequence_num': self.sequence_num,
                'topology_version': self.topology_version,
                'routing_table': self.routing_table,
                'lsdb_size': len(self.lsdb),
                'estadisticas': {
                    'lsps_enviados': self.lsps_enviados,
                    'lsps_recibidos': self.lsps_recibidos,
                    'tablas_calculadas': self.tablas_calculadas
                }
            }
            
    def detener(self):
        """Detiene el nodo"""
        print(f"[{self.nombre}] Deteniendo nodo...")
        self.activo = False
        if self.servidor_socket:
            try:
                self.servidor_socket.close()
            except:
                pass
                
def main():
    """Función principal para ejecutar un nodo Link State"""
    if len(sys.argv) < 3:
        print("Uso: python link_state_socket.py <nombre> <puerto>")
        print("Ejemplo: python link_state_socket.py A 65001")
        sys.exit(1)
        
    nombre = sys.argv[1].upper()
    puerto = int(sys.argv[2])
    
    # Configuración de la red (misma topología que dijkstra.py)
    topologia = {
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
    
    # Puertos por defecto
    puertos_nodos = {
        'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
        'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
    }
    
    if nombre not in topologia:
        print(f"Error: Nodo {nombre} no está en la topología")
        print(f"Nodos disponibles: {list(topologia.keys())}")
        sys.exit(1)
        
    # Crear y iniciar nodo
    vecinos_iniciales = topologia[nombre]
    nodo = LinkStateSocketNode(nombre, puerto, vecinos_iniciales, puertos_nodos)
    
    # Iniciar servidor en hilo separado
    servidor_thread = threading.Thread(target=nodo.iniciar_servidor, daemon=True)
    servidor_thread.start()
    
    # Esperar a que otros nodos estén listos
    print(f"[{nombre}] Esperando inicialización de la red...")
    time.sleep(3)
    
    # Generar y propagar LSP inicial
    print(f"[{nombre}] Iniciando protocolo Link State...")
    lsp_inicial = nodo.generar_lsp()
    nodo.calcular_tabla_enrutamiento()
    nodo.propagar_lsp_inicial(lsp_inicial)
    
    print(f"[{nombre}] Nodo Link State iniciado correctamente")
    nodo.imprimir_tabla_enrutamiento()
    
    # Loop principal
    try:
        while nodo.activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[{nombre}] Recibido Ctrl+C")
    finally:
        nodo.detener()

if __name__ == "__main__":
    main()
