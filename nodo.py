import socket
import json
import threading
import time
from typing import Dict, List, Optional, Set
from dijkstra import dijkstra
from grafo import grafo

class Nodo:
    def __init__(self, nombre: str, puerto: int, grafo_completo: grafo):
        self.nombre = nombre
        self.puerto = puerto
        self.host = '127.0.0.1'
        self.grafo = grafo_completo
        
        # Información de enrutamiento
        self.tabla_distancias = {}
        self.tabla_rutas = {}
        self.vecinos = list(grafo_completo.conexiones.get(nombre, {}).keys())
        
        # Sockets
        self.servidor_socket = None
        self.activo = True
        
        # Puertos de otros nodos (se configurará externamente)
        self.puertos_nodos = {}
        
    def iniciar_servidor(self):
        """Inicia el servidor del nodo para recibir mensajes"""
        self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servidor_socket.bind((self.host, self.puerto))
        self.servidor_socket.listen(5)
        print(f"Nodo {self.nombre} escuchando en puerto {self.puerto}")
        
        while self.activo:
            try:
                cliente, direccion = self.servidor_socket.accept()
                threading.Thread(target=self.manejar_cliente, args=(cliente,)).start()
            except:
                break
                
    def manejar_cliente(self, cliente):
        """Maneja mensajes entrantes de otros nodos"""
        try:
            data = cliente.recv(1024).decode()
            mensaje = json.loads(data)
            
            if mensaje['tipo'] == 'solicitud_distancias':
                # Otro nodo solicita nuestras distancias
                respuesta = {
                    'tipo': 'respuesta_distancias',
                    'nodo': self.nombre,
                    'distancias': self.tabla_distancias
                }
                cliente.send(json.dumps(respuesta).encode())
                
            elif mensaje['tipo'] == 'actualizar_distancias':
                # Recibir actualizaciones de distancias de otros nodos
                self.procesar_actualizacion(mensaje)
                
        except Exception as e:
            print(f"Error en nodo {self.nombre}: {e}")
        finally:
            cliente.close()
            
    def calcular_tabla_local(self):
        """Calcula las distancias usando Dijkstra desde este nodo"""
        distancias, predecesores = dijkstra(self.grafo, self.nombre)
        self.tabla_distancias = {dest: dist for dest, dist in distancias.items() 
                               if dist != float('inf')}
        
        # Construir rutas
        self.tabla_rutas = {}
        for destino in self.tabla_distancias:
            ruta = self.reconstruir_ruta(destino, predecesores)
            if ruta:
                self.tabla_rutas[destino] = ruta
        
        print(f"\n--- Tabla calculada para nodo {self.nombre} ---")
        for destino, distancia in self.tabla_distancias.items():
            ruta = " -> ".join(self.tabla_rutas.get(destino, []))
            print(f"  {destino}: distancia={distancia}, ruta={ruta}")
        
    def reconstruir_ruta(self, destino: str, predecesores: Dict[str, Optional[str]]) -> List[str]:
        """Reconstruye la ruta desde el nodo actual hasta el destino"""
        if self.nombre == destino:
            return [self.nombre]
        
        ruta = []
        actual = destino
        while actual is not None:
            ruta.append(actual)
            if actual == self.nombre:
                break
            actual = predecesores.get(actual)
            
        if not ruta or ruta[-1] != self.nombre:
            return []
        
        ruta.reverse()
        return ruta
        
    def solicitar_distancias_vecinos(self):
        """Solicita las tablas de distancias a los nodos vecinos"""
        distancias_vecinos = {}
        
        for vecino in self.vecinos:
            if vecino in self.puertos_nodos:
                try:
                    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    cliente.connect((self.host, self.puertos_nodos[vecino]))
                    
                    solicitud = {'tipo': 'solicitud_distancias', 'nodo': self.nombre}
                    cliente.send(json.dumps(solicitud).encode())
                    
                    respuesta = cliente.recv(1024).decode()
                    datos = json.loads(respuesta)
                    
                    if datos['tipo'] == 'respuesta_distancias':
                        distancias_vecinos[vecino] = datos['distancias']
                        
                    cliente.close()
                except Exception as e:
                    print(f"Error conectando con {vecino}: {e}")
                    
        return distancias_vecinos
        
    def procesar_actualizacion(self, mensaje):
        """Procesa actualizaciones de distancias recibidas"""
        print(f"Nodo {self.nombre} recibió actualización de {mensaje['nodo']}")
        
    def obtener_estado(self):
        """Devuelve el estado actual del nodo"""
        return {
            'nodo': self.nombre,
            'tabla_distancias': self.tabla_distancias,
            'tabla_rutas': self.tabla_rutas,
            'vecinos': self.vecinos
        }
        
    def detener(self):
        """Detiene el nodo"""
        self.activo = False
        if self.servidor_socket:
            self.servidor_socket.close()

def ejecutar_nodo(nombre: str, puerto: int, grafo_red: grafo, puertos_nodos: Dict[str, int]):
    """Función para ejecutar un nodo en un proceso separado"""
    nodo = Nodo(nombre, puerto, grafo_red)
    nodo.puertos_nodos = puertos_nodos
    
    # Iniciar servidor en hilo separado
    servidor_thread = threading.Thread(target=nodo.iniciar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # Esperar un poco para que todos los nodos estén listos
    time.sleep(2)
    
    # Calcular tabla local
    nodo.calcular_tabla_local()
    
    # Mantener el nodo activo
    try:
        while nodo.activo:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\nDeteniendo nodo {nombre}")
        nodo.detener()

if __name__ == "__main__":
    # Este código se ejecutará si se llama directamente al archivo
    import sys
    if len(sys.argv) < 3:
        print("Uso: python nodo.py <nombre> <puerto>")
        sys.exit(1)
        
    nombre = sys.argv[1]
    puerto = int(sys.argv[2])
    
    # Crear el grafo (misma estructura que en dijkstra.py)
    g = grafo()
    edges = [
        ("A","B",7), ("A","I",1), ("A","C",7), ("B","F",2), ("I","D",6),
        ("C","D",5), ("D","F",1), ("D","E",1), ("F","G",3), ("F","H",4), ("G","E",4),
    ]
    for a, b, w in edges:
        g.agregar_conexion(a, b, w)
    
    # Puertos por defecto para cada nodo
    puertos_default = {
        'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
        'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
    }
    
    ejecutar_nodo(nombre, puerto, g, puertos_default)
