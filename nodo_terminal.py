import socket
import json
import threading
import time
from typing import Dict, List, Optional
from dijkstra import dijkstra
from grafo import grafo

class NodoRouter:
    def __init__(self, nombre: str, puerto: int):
        self.nombre = nombre
        self.puerto = puerto
        self.host = '127.0.0.1'
        self.grafo = self.crear_grafo()
        
        # Tabla de enrutamiento local
        self.tabla_distancias = {}
        self.tabla_rutas = {}
        self.calcular_tabla_enrutamiento()
        
        # Socket servidor
        self.servidor_socket = None
        self.activo = True
        
        # Puertos de otros nodos
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        
    def crear_grafo(self):
        """Crea el grafo de la red"""
        g = grafo()
        edges = [
            ("A","B",7), ("A","I",1), ("A","C",7), ("B","F",2), ("I","D",6),
            ("C","D",5), ("D","F",1), ("D","E",1), ("F","G",3), ("F","H",4), ("G","E",4),
        ]
        for a, b, w in edges:
            g.agregar_conexion(a, b, w)
        return g
        
    def calcular_tabla_enrutamiento(self):
        """Calcula la tabla de enrutamiento usando Dijkstra"""
        distancias, predecesores = dijkstra(self.grafo, self.nombre)
        
        for destino in self.grafo.routers:
            if destino != self.nombre and distancias[destino] != float('inf'):
                # Reconstruir ruta
                ruta = []
                actual = destino
                while actual is not None:
                    ruta.append(actual)
                    if actual == self.nombre:
                        break
                    actual = predecesores.get(actual)
                ruta.reverse()
                
                self.tabla_distancias[destino] = distancias[destino]
                self.tabla_rutas[destino] = ruta
                
    def iniciar_servidor(self):
        """Inicia el servidor para recibir paquetes"""
        self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.servidor_socket.bind((self.host, self.puerto))
            self.servidor_socket.listen(5)
            print(f"\n🟢 NODO {self.nombre} ACTIVO en puerto {self.puerto}")
            print(f"Esperando paquetes...")
            
            while self.activo:
                try:
                    cliente, direccion = self.servidor_socket.accept()
                    threading.Thread(target=self.procesar_paquete, args=(cliente,)).start()
                except:
                    break
                    
        except Exception as e:
            print(f"❌ Error iniciando nodo {self.nombre}: {e}")
            
    def procesar_paquete(self, cliente):
        """Procesa un paquete recibido"""
        try:
            data = cliente.recv(1024).decode()
            paquete = json.loads(data)
            
            if paquete['tipo'] == 'envio_paquete':
                origen_original = paquete['origen']
                destino_final = paquete['destino']
                mensaje = paquete['mensaje']
                ruta_completa = paquete['ruta']
                costo_total = paquete['costo']
                saltos_recorridos = paquete.get('saltos_recorridos', [])
                
                # Agregar este nodo a los saltos recorridos
                saltos_recorridos.append(self.nombre)
                
                # Verificar si este nodo es el destino final
                if self.nombre == destino_final:
                    print(f"\n📦 PAQUETE FINAL RECIBIDO!")
                    print(f"   De: {origen_original}")
                    print(f"   Para: {destino_final}")
                    print(f"   Mensaje: {mensaje}")
                    print(f"   Ruta planificada: {' -> '.join(ruta_completa)}")
                    print(f"   Saltos realizados: {' -> '.join(saltos_recorridos)}")
                    print(f"   Costo total: {costo_total}")
                    print(f"   ✅ ENTREGADO EXITOSAMENTE AL DESTINO FINAL\n")
                    
                    respuesta = {'estado': 'entregado', 'nodo_receptor': self.nombre}
                    cliente.send(json.dumps(respuesta).encode())
                    
                else:
                    # Este es un nodo intermedio, reenviar el paquete
                    print(f"\n🔄 PAQUETE EN TRÁNSITO!")
                    print(f"   De: {origen_original} → Para: {destino_final}")
                    print(f"   Pasando por: {self.nombre}")
                    print(f"   Ruta: {' -> '.join(ruta_completa)}")
                    print(f"   Saltos hasta ahora: {' -> '.join(saltos_recorridos)}")
                    
                    # Encontrar el siguiente salto en la ruta
                    try:
                        indice_actual = ruta_completa.index(self.nombre)
                        if indice_actual + 1 < len(ruta_completa):
                            siguiente_nodo = ruta_completa[indice_actual + 1]
                            print(f"   🚀 Reenviando a: {siguiente_nodo}\n")
                            
                            # Actualizar el paquete con los saltos recorridos
                            paquete['saltos_recorridos'] = saltos_recorridos
                            
                            # Reenviar al siguiente nodo
                            self.reenviar_paquete(siguiente_nodo, paquete)
                            
                            respuesta = {'estado': 'reenviado', 'nodo_intermedio': self.nombre}
                            cliente.send(json.dumps(respuesta).encode())
                        else:
                            print(f"   ❌ Error: No hay siguiente nodo en la ruta")
                            respuesta = {'estado': 'error', 'mensaje': 'Fin de ruta inesperado'}
                            cliente.send(json.dumps(respuesta).encode())
                            
                    except ValueError:
                        print(f"   ❌ Error: Nodo {self.nombre} no encontrado en la ruta")
                        respuesta = {'estado': 'error', 'mensaje': 'Nodo no en ruta'}
                        cliente.send(json.dumps(respuesta).encode())
                
        except Exception as e:
            print(f"❌ Error procesando paquete: {e}")
        finally:
            cliente.close()
            
    def reenviar_paquete(self, siguiente_nodo: str, paquete: dict):
        """Reenvía un paquete al siguiente nodo en la ruta"""
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            puerto_siguiente = self.puertos_nodos[siguiente_nodo]
            cliente.connect((self.host, puerto_siguiente))
            
            # Enviar paquete
            cliente.send(json.dumps(paquete).encode())
            
            # Esperar confirmación
            respuesta = cliente.recv(1024).decode()
            confirmacion = json.loads(respuesta)
            
            if confirmacion['estado'] == 'reenviado':
                print(f"   ✅ Paquete reenviado exitosamente a {siguiente_nodo}")
            elif confirmacion['estado'] == 'entregado':
                print(f"   ✅ Paquete entregado al destino final por {siguiente_nodo}")
                
            cliente.close()
            
        except Exception as e:
            print(f"   ❌ Error reenviando a {siguiente_nodo}: {e}")
            
    def enviar_paquete(self, destino: str, mensaje: str = "Paquete de prueba"):
        """Envía un paquete a otro nodo siguiendo la ruta calculada"""
        if destino not in self.tabla_rutas:
            print(f"❌ No hay ruta hacia {destino}")
            return False
            
        ruta = self.tabla_rutas[destino]
        costo = self.tabla_distancias[destino]
        
        print(f"\n📤 ENVIANDO PAQUETE:")
        print(f"   De: {self.nombre}")
        print(f"   Para: {destino}")
        print(f"   Ruta planificada: {' -> '.join(ruta)}")
        print(f"   Costo: {costo}")
        
        # El primer salto es el segundo nodo en la ruta (índice 1)
        if len(ruta) < 2:
            print(f"   ❌ Error: Ruta inválida")
            return False
            
        primer_salto = ruta[1]  # El siguiente nodo después del origen
        
        print(f"   🚀 Enviando primero a: {primer_salto}")
        
        # Preparar paquete
        paquete = {
            'tipo': 'envio_paquete',
            'origen': self.nombre,
            'destino': destino,
            'mensaje': mensaje,
            'ruta': ruta,
            'costo': costo,
            'saltos_recorridos': [self.nombre]  # Iniciar con el nodo origen
        }
        
        try:
            # Conectar con el primer nodo en la ruta
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            puerto_primer_salto = self.puertos_nodos[primer_salto]
            cliente.connect((self.host, puerto_primer_salto))
            
            # Enviar paquete
            cliente.send(json.dumps(paquete).encode())
            
            # Esperar confirmación
            respuesta = cliente.recv(1024).decode()
            confirmacion = json.loads(respuesta)
            
            print(f"   ✅ Paquete enviado a {primer_salto}")
            print(f"   📋 Estado: {confirmacion.get('estado', 'desconocido')}")
            print(f"   🎯 El paquete seguirá la ruta: {' -> '.join(ruta)}")
            
            cliente.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Error enviando a {primer_salto}: {e}")
            return False
            
    def mostrar_tabla_enrutamiento(self):
        """Muestra la tabla de enrutamiento del nodo"""
        print(f"\n📋 TABLA DE ENRUTAMIENTO - NODO {self.nombre}")
        print("="*50)
        print(f"{'Destino':<8} {'Ruta':<20} {'Costo':<6}")
        print("-"*50)
        
        for destino in sorted(self.tabla_rutas.keys()):
            ruta = ' -> '.join(self.tabla_rutas[destino])
            costo = self.tabla_distancias[destino]
            print(f"{destino:<8} {ruta:<20} {costo:<6}")
        print()
        
    def menu_interactivo(self):
        """Menú interactivo para el nodo"""
        while self.activo:
            print(f"\n🔧 MENÚ NODO {self.nombre}")
            print("1. Ver tabla de enrutamiento")
            print("2. Enviar paquete")
            print("3. Salir")
            
            opcion = input("Opción: ").strip()
            
            if opcion == '1':
                self.mostrar_tabla_enrutamiento()
                
            elif opcion == '2':
                print("\nNodos disponibles:", ", ".join(sorted([n for n in self.grafo.routers if n != self.nombre])))
                destino = input("Destino: ").upper().strip()
                
                if destino in self.grafo.routers and destino != self.nombre:
                    mensaje = input("Mensaje (opcional): ").strip()
                    if not mensaje:
                        mensaje = f"Paquete enviado desde {self.nombre}"
                    self.enviar_paquete(destino, mensaje)
                else:
                    print("❌ Nodo destino no válido")
                    
            elif opcion == '3':
                print(f"🔴 Cerrando nodo {self.nombre}")
                self.detener()
                break
                
            else:
                print("❌ Opción no válida")
                
    def detener(self):
        """Detiene el nodo"""
        self.activo = False
        if self.servidor_socket:
            self.servidor_socket.close()

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python nodo_terminal.py <nombre_nodo>")
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
    nodo = NodoRouter(nombre, puerto)
    
    # Iniciar servidor en hilo separado
    servidor_thread = threading.Thread(target=nodo.iniciar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    
    # Esperar un momento para que el servidor se inicie
    time.sleep(1)
    
    # Mostrar tabla inicial
    nodo.mostrar_tabla_enrutamiento()
    
    # Iniciar menú interactivo
    try:
        nodo.menu_interactivo()
    except KeyboardInterrupt:
        print(f"\n🔴 Nodo {nombre} detenido")
        nodo.detener()

if __name__ == "__main__":
    main()
