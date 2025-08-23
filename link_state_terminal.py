"""
Nodo terminal para probar el algoritmo Link State de forma interactiva
Similar a nodo_terminal.py pero usando Link State distribuido
"""

import socket
import json
import threading
import time
import sys
from typing import Dict, List, Optional
from dijkstra import dijkstra, first_hop
from grafo import grafo

class LSP:
    """Link State Packet"""
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

class LinkStateTerminal:
    """Nodo Link State interactivo para terminal"""
    
    def __init__(self, nombre: str, puerto: int):
        self.nombre = nombre
        self.puerto = puerto
        self.host = '127.0.0.1'
        
        # Topología inicial
        self.topologia_inicial = {
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
        
        self.vecinos = self.topologia_inicial.get(nombre, {}).copy()
        
        # Estado Link State
        self.sequence_num = 0
        self.lsdb = {}  # {source: LSP}
        self.routing_table = {}
        self.topology_version = 0
        
        # Sockets y threading
        self.servidor_socket = None
        self.activo = True
        self.lock = threading.RLock()
        
        # Puertos de otros nodos
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        
        # Estadísticas
        self.lsps_enviados = 0
        self.lsps_recibidos = 0
        self.mensajes_enviados = 0
        self.mensajes_recibidos = 0
        
    def iniciar_servidor(self):
        """Inicia el servidor para recibir LSPs y mensajes"""
        self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.servidor_socket.bind((self.host, self.puerto))
            self.servidor_socket.listen(10)
            print(f"🟢 NODO LINK STATE {self.nombre} ACTIVO en puerto {self.puerto}")
            
            while self.activo:
                try:
                    cliente, direccion = self.servidor_socket.accept()
                    threading.Thread(target=self.manejar_conexion, args=(cliente, direccion), daemon=True).start()
                except:
                    if self.activo:
                        break
                        
        except Exception as e:
            print(f"❌ Error iniciando nodo {self.nombre}: {e}")
            
    def manejar_conexion(self, cliente, direccion):
        """Maneja conexiones entrantes"""
        try:
            cliente.settimeout(10.0)
            data = cliente.recv(4096).decode('utf-8')
            
            if not data:
                return
                
            mensaje = json.loads(data)
            tipo = mensaje.get('tipo')
            
            if tipo == 'lsp_flood':
                # Recibir LSP
                lsp_data = mensaje['lsp']
                lsp = LSP.from_dict(lsp_data)
                sender = mensaje.get('sender')
                self.procesar_lsp(lsp, sender)
                
                # Confirmar recepción
                respuesta = {'tipo': 'ack_lsp', 'nodo': self.nombre}
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == 'mensaje_usuario':
                # Recibir mensaje de usuario (como los paquetes en Dijkstra)
                self.procesar_mensaje_usuario(mensaje, cliente)
                
            elif tipo == 'ping':
                # Ping de conectividad
                respuesta = {'tipo': 'pong', 'nodo': self.nombre, 'timestamp': time.time()}
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
            elif tipo == 'get_estado':
                # Solicitud de estado
                estado = self.obtener_estado()
                respuesta = {'tipo': 'estado', 'datos': estado}
                cliente.send(json.dumps(respuesta).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Error manejando conexión: {e}")
        finally:
            try:
                cliente.close()
            except:
                pass
                
    def procesar_lsp(self, lsp: LSP, sender: str = None):
        """Procesa un LSP recibido"""
        with self.lock:
            self.lsps_recibidos += 1
            
            # No procesar nuestros propios LSPs
            if lsp.source == self.nombre:
                return
                
            print(f"📡 LSP recibido de {lsp.source} (seq: {lsp.sequence_num}) vía {sender}")
            
            topology_changed = False
            
            if lsp.source not in self.lsdb:
                # Nuevo nodo
                self.lsdb[lsp.source] = lsp
                topology_changed = True
                print(f"   ➕ Nuevo nodo en LSDB: {lsp.source}")
            else:
                existing_lsp = self.lsdb[lsp.source]
                
                if lsp.sequence_num > existing_lsp.sequence_num:
                    # LSP más reciente
                    self.lsdb[lsp.source] = lsp
                    topology_changed = True
                    print(f"   🔄 LSDB actualizada para {lsp.source} (seq: {existing_lsp.sequence_num} -> {lsp.sequence_num})")
                elif lsp.sequence_num == existing_lsp.sequence_num and lsp.neighbors != existing_lsp.neighbors:
                    # Mismo número de secuencia pero contenido diferente
                    self.lsdb[lsp.source] = lsp
                    topology_changed = True
                    print(f"   📝 Contenido cambiado para {lsp.source}")
                    
            if topology_changed:
                self.topology_version += 1
                print(f"   🔥 TOPOLOGÍA CAMBIÓ - Recalculando rutas...")
                self.calcular_tabla_enrutamiento()
                # Retransmitir a otros vecinos
                self.retransmitir_lsp(lsp, sender)
                
    def procesar_mensaje_usuario(self, mensaje: dict, cliente):
        """Procesa mensajes de usuario (similar a paquetes en Dijkstra)"""
        try:
            origen = mensaje['origen']
            destino = mensaje['destino'] 
            contenido = mensaje['contenido']
            ruta = mensaje['ruta']
            saltos_recorridos = mensaje.get('saltos_recorridos', [])
            
            # Agregar este nodo a los saltos
            saltos_recorridos.append(self.nombre)
            self.mensajes_recibidos += 1
            
            if self.nombre == destino:
                # Somos el destino final
                print(f"\n📦 MENSAJE RECIBIDO!")
                print(f"   De: {origen}")
                print(f"   Para: {destino}")  
                print(f"   Contenido: {contenido}")
                print(f"   Ruta planificada: {' -> '.join(ruta)}")
                print(f"   Saltos realizados: {' -> '.join(saltos_recorridos)}")
                print(f"   ✅ ENTREGADO AL DESTINO FINAL\n")
                
                respuesta = {'estado': 'entregado', 'nodo': self.nombre}
                cliente.send(json.dumps(respuesta).encode())
                
            else:
                # Reenviar mensaje
                print(f"🔄 Mensaje en tránsito: {origen} -> {destino} (pasando por {self.nombre})")
                
                # Encontrar siguiente salto usando nuestra tabla Link State
                if destino in self.routing_table:
                    siguiente_nodo = self.routing_table[destino]['next_hop']
                    print(f"   🚀 Reenviando a: {siguiente_nodo}")
                    
                    mensaje['saltos_recorridos'] = saltos_recorridos
                    self.reenviar_mensaje(siguiente_nodo, mensaje)
                    
                    respuesta = {'estado': 'reenviado', 'via': siguiente_nodo}
                    cliente.send(json.dumps(respuesta).encode())
                else:
                    print(f"   ❌ No hay ruta hacia {destino}")
                    respuesta = {'estado': 'sin_ruta', 'destino': destino}
                    cliente.send(json.dumps(respuesta).encode())
                    
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            respuesta = {'estado': 'error', 'mensaje': str(e)}
            cliente.send(json.dumps(respuesta).encode())
            
    def reenviar_mensaje(self, siguiente_nodo: str, mensaje: dict):
        """Reenvía un mensaje al siguiente nodo"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.host, self.puertos_nodos[siguiente_nodo]))
                
                mensaje['tipo'] = 'mensaje_usuario'
                sock.send(json.dumps(mensaje).encode('utf-8'))
                
                # Esperar confirmación
                respuesta = sock.recv(1024).decode('utf-8')
                if respuesta:
                    confirmacion = json.loads(respuesta)
                    print(f"   ✅ Mensaje reenviado a {siguiente_nodo}: {confirmacion.get('estado', 'ok')}")
                    
        except Exception as e:
            print(f"   ❌ Error reenviando a {siguiente_nodo}: {e}")
            
    def generar_lsp(self) -> LSP:
        """Genera un nuevo LSP"""
        with self.lock:
            self.sequence_num += 1
            lsp = LSP(self.nombre, self.sequence_num, 0, self.vecinos)
            
            # Actualizar nuestra LSDB
            self.lsdb[self.nombre] = lsp
            
            print(f"📋 LSP #{self.sequence_num} generado con vecinos: {self.vecinos}")
            return lsp
            
    def propagar_lsp(self, lsp: LSP):
        """Propaga un LSP a todos los vecinos"""
        for vecino in self.vecinos.keys():
            if vecino in self.puertos_nodos:
                threading.Thread(target=self.enviar_lsp_a_nodo, args=(lsp, vecino), daemon=True).start()
                
    def retransmitir_lsp(self, lsp: LSP, sender: str = None):
        """Retransmite un LSP a vecinos (excepto sender)"""
        for vecino in self.vecinos.keys():
            if vecino != sender and vecino in self.puertos_nodos:
                threading.Thread(target=self.enviar_lsp_a_nodo, args=(lsp, vecino), daemon=True).start()
                
    def enviar_lsp_a_nodo(self, lsp: LSP, destino: str):
        """Envía un LSP a un nodo específico"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3.0)
                sock.connect((self.host, self.puertos_nodos[destino]))
                
                mensaje = {
                    'tipo': 'lsp_flood',
                    'sender': self.nombre,
                    'lsp': lsp.to_dict()
                }
                
                sock.send(json.dumps(mensaje).encode('utf-8'))
                
                # Esperar ACK
                respuesta = sock.recv(1024).decode('utf-8')
                if respuesta:
                    ack = json.loads(respuesta)
                    if ack.get('tipo') == 'ack_lsp':
                        self.lsps_enviados += 1
                        
        except Exception as e:
            print(f"❌ Error enviando LSP a {destino}: {e}")
            
    def calcular_tabla_enrutamiento(self):
        """Calcula tabla de enrutamiento usando Dijkstra sobre LSDB"""
        with self.lock:
            print(f"🧮 Recalculando tabla de enrutamiento...")
            
            # Construir grafo desde LSDB
            grafo_topologia = grafo()
            
            for source, lsp in self.lsdb.items():
                for neighbor, cost in lsp.neighbors.items():
                    grafo_topologia.agregar_conexion(source, neighbor, cost, bidireccional=False)
                    
            if self.nombre not in grafo_topologia.routers:
                print(f"⚠️  Nodo {self.nombre} no encontrado en topología")
                return
                
            try:
                distances, predecessors = dijkstra(grafo_topologia, self.nombre)
                
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
                        
                cambios = self._detectar_cambios_tabla(nueva_tabla)
                self.routing_table = nueva_tabla
                
                if cambios:
                    print(f"   ✅ Tabla actualizada (versión {self.topology_version})")
                    self.mostrar_tabla_compacta()
                    
            except Exception as e:
                print(f"❌ Error calculando tabla: {e}")
                
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
        """Detecta cambios en la tabla de enrutamiento"""
        if not self.routing_table:
            return bool(nueva_tabla)
            
        destinos_viejos = set(self.routing_table.keys())
        destinos_nuevos = set(nueva_tabla.keys())
        
        if destinos_viejos != destinos_nuevos:
            return True
            
        for dest in destinos_nuevos:
            vieja = self.routing_table.get(dest, {})
            nueva = nueva_tabla[dest]
            
            if (vieja.get('next_hop') != nueva.get('next_hop') or 
                abs(vieja.get('distance', 0) - nueva.get('distance', 0)) > 0.001):
                return True
                
        return False
        
    def enviar_mensaje(self, destino: str, contenido: str = "Mensaje Link State"):
        """Envía un mensaje usando la tabla Link State"""
        if destino not in self.routing_table:
            print(f"❌ No hay ruta hacia {destino}")
            return False
            
        info_ruta = self.routing_table[destino]
        siguiente_nodo = info_ruta['next_hop']
        ruta = info_ruta['path']
        
        print(f"\n📤 ENVIANDO MENSAJE (LINK STATE):")
        print(f"   De: {self.nombre}")
        print(f"   Para: {destino}")
        print(f"   Ruta Link State: {' -> '.join(ruta)}")
        print(f"   Costo: {info_ruta['distance']}")
        print(f"   Primer salto: {siguiente_nodo}")
        
        mensaje = {
            'tipo': 'mensaje_usuario',
            'origen': self.nombre,
            'destino': destino,
            'contenido': contenido,
            'ruta': ruta,
            'saltos_recorridos': [self.nombre]
        }
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.host, self.puertos_nodos[siguiente_nodo]))
                
                sock.send(json.dumps(mensaje).encode('utf-8'))
                
                respuesta = sock.recv(1024).decode('utf-8')
                if respuesta:
                    confirmacion = json.loads(respuesta)
                    print(f"   ✅ Mensaje enviado: {confirmacion.get('estado', 'ok')}")
                    self.mensajes_enviados += 1
                    return True
                    
        except Exception as e:
            print(f"   ❌ Error enviando mensaje: {e}")
            return False
            
    def mostrar_tabla_enrutamiento(self):
        """Muestra la tabla de enrutamiento completa"""
        print(f"\n📋 TABLA DE ENRUTAMIENTO LINK STATE - NODO {self.nombre}")
        print("="*60)
        print(f"Versión topología: {self.topology_version} | LSDB size: {len(self.lsdb)}")
        print(f"{'Destino':<8} {'Next-Hop':<10} {'Distancia':<10} {'Ruta':<20}")
        print("-"*60)
        
        if not self.routing_table:
            print("   (tabla vacía - esperando convergencia)")
        else:
            for dest in sorted(self.routing_table.keys()):
                info = self.routing_table[dest]
                ruta_str = ' -> '.join(info['path'])
                dist_str = str(int(info['distance'])) if info['distance'] != float('inf') else "∞"
                print(f"{dest:<8} {info['next_hop']:<10} {dist_str:<10} {ruta_str}")
        print()
        
    def mostrar_tabla_compacta(self):
        """Muestra versión compacta de la tabla"""
        if self.routing_table:
            rutas = []
            for dest in sorted(self.routing_table.keys()):
                info = self.routing_table[dest]
                rutas.append(f"{dest}:{info['next_hop']}({int(info['distance'])})")
            print(f"   📊 Rutas: {', '.join(rutas)}")
            
    def mostrar_lsdb(self):
        """Muestra la base de datos Link State"""
        print(f"\n🗄️  BASE DE DATOS LINK STATE (LSDB) - NODO {self.nombre}")
        print("="*50)
        print(f"{'Nodo':<6} {'Seq':<5} {'Edad':<6} {'Vecinos'}")
        print("-"*50)
        
        for source in sorted(self.lsdb.keys()):
            lsp = self.lsdb[source]
            edad = int(time.time() - lsp.timestamp)
            vecinos_str = ", ".join(f"{v}:{c}" for v, c in sorted(lsp.neighbors.items()))
            print(f"{source:<6} {lsp.sequence_num:<5} {edad:<6}s {vecinos_str}")
        print()
        
    def mostrar_estadisticas(self):
        """Muestra estadísticas del nodo"""
        print(f"\n📊 ESTADÍSTICAS - NODO {self.nombre}")
        print("="*40)
        print(f"LSPs enviados: {self.lsps_enviados}")
        print(f"LSPs recibidos: {self.lsps_recibidos}")
        print(f"Mensajes enviados: {self.mensajes_enviados}")  
        print(f"Mensajes recibidos: {self.mensajes_recibidos}")
        print(f"Vecinos directos: {len(self.vecinos)}")
        print(f"LSDB size: {len(self.lsdb)}")
        print(f"Versión topología: {self.topology_version}")
        print()
        
    def obtener_estado(self):
        """Obtiene el estado completo del nodo"""
        return {
            'nombre': self.nombre,
            'vecinos': self.vecinos,
            'routing_table': self.routing_table,
            'lsdb_size': len(self.lsdb),
            'topology_version': self.topology_version,
            'estadisticas': {
                'lsps_enviados': self.lsps_enviados,
                'lsps_recibidos': self.lsps_recibidos,
                'mensajes_enviados': self.mensajes_enviados,
                'mensajes_recibidos': self.mensajes_recibidos
            }
        }
        
    def menu_interactivo(self):
        """Menú interactivo para el nodo Link State"""
        while self.activo:
            print(f"\n🔧 MENÚ NODO LINK STATE {self.nombre}")
            print("1. Ver tabla de enrutamiento")
            print("2. Ver base de datos Link State (LSDB)")
            print("3. Enviar mensaje")
            print("4. Ver estadísticas")
            print("5. Regenerar y propagar LSP")
            print("6. Salir")
            
            try:
                opcion = input("Opción: ").strip()
                
                if opcion == '1':
                    self.mostrar_tabla_enrutamiento()
                    
                elif opcion == '2':
                    self.mostrar_lsdb()
                    
                elif opcion == '3':
                    if not self.routing_table:
                        print("❌ No hay rutas disponibles. Espera la convergencia.")
                        continue
                        
                    print(f"Destinos disponibles: {', '.join(sorted(self.routing_table.keys()))}")
                    destino = input("Destino: ").upper().strip()
                    
                    if destino in self.routing_table:
                        contenido = input("Mensaje (opcional): ").strip()
                        if not contenido:
                            contenido = f"Mensaje Link State desde {self.nombre}"
                        self.enviar_mensaje(destino, contenido)
                    else:
                        print("❌ Destino no válido o sin ruta")
                        
                elif opcion == '4':
                    self.mostrar_estadisticas()
                    
                elif opcion == '5':
                    print("🔄 Regenerando LSP...")
                    lsp = self.generar_lsp()
                    self.propagar_lsp(lsp)
                    self.calcular_tabla_enrutamiento()
                    
                elif opcion == '6':
                    print(f"🔴 Cerrando nodo Link State {self.nombre}")
                    self.detener()
                    break
                    
                else:
                    print("❌ Opción no válida")
                    
            except KeyboardInterrupt:
                print(f"\n🔴 Nodo {self.nombre} detenido")
                self.detener()
                break
                
    def detener(self):
        """Detiene el nodo"""
        self.activo = False
        if self.servidor_socket:
            self.servidor_socket.close()

def main():
    if len(sys.argv) != 2:
        print("Uso: python link_state_terminal.py <nombre_nodo>")
        print("Nodos disponibles: A, B, C, D, E, F, G, H, I")
        sys.exit(1)
        
    nombre = sys.argv[1].upper().strip()
    
    puertos = {
        'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
        'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
    }
    
    if nombre not in puertos:
        print(f"❌ Nodo '{nombre}' no válido")
        print("Nodos disponibles:", ", ".join(puertos.keys()))
        sys.exit(1)
        
    puerto = puertos[nombre]
    nodo = LinkStateTerminal(nombre, puerto)
    
    # Iniciar servidor en hilo separado
    servidor_thread = threading.Thread(target=nodo.iniciar_servidor, daemon=True)
    servidor_thread.start()
    
    # Esperar a que el servidor se inicie
    time.sleep(1)
    
    # Generar y propagar LSP inicial
    print("🚀 Iniciando protocolo Link State...")
    lsp_inicial = nodo.generar_lsp()
    nodo.propagar_lsp(lsp_inicial)
    nodo.calcular_tabla_enrutamiento()
    
    # Mostrar tabla inicial
    time.sleep(2)  # Dar tiempo para recibir otros LSPs
    nodo.mostrar_tabla_enrutamiento()
    
    # Iniciar menú interactivo
    try:
        nodo.menu_interactivo()
    except KeyboardInterrupt:
        print(f"\n🔴 Nodo {nombre} detenido")
        nodo.detener()

if __name__ == "__main__":
    main()
