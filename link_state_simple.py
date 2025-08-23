"""
Nodo terminal SIMPLE para Link State - Funciona igual que nodo_terminal.py
Pero usa protocolo Link State real para calcular rutas dinámicamente
"""

import socket
import json
import threading
import time
import sys
from typing import Dict, List, Optional
from dijkstra import dijkstra, first_hop
from grafo import grafo

class NodoLinkStateSimple:
    """Nodo Link State simple - igual que NodoRouter pero con Link State real"""
    
    def __init__(self, nombre: str, puerto: int):
        self.nombre = nombre
        self.puerto = puerto
        self.host = '127.0.0.1'
        
        # Topología Link State (los vecinos que este nodo conoce directamente)
        topologia_inicial = {
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
        
        # Mis vecinos directos
        self.vecinos_directos = topologia_inicial.get(nombre, {})
        
        # Estado Link State
        self.lsdb = {}  # Base de datos Link State: {nodo: {vecinos}}
        self.sequence_num = 0
        self.routing_table = {}
        
        # Socket y estado
        self.servidor_socket = None
        self.activo = True
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        
        # Inicializar con mi propia información
        self.lsdb[self.nombre] = self.vecinos_directos.copy()
        self.calcular_rutas()
        
    def iniciar_servidor(self):
        """Inicia el servidor para recibir LSPs y paquetes"""
        self.servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.servidor_socket.bind((self.host, self.puerto))
            self.servidor_socket.listen(5)
            print(f"\n🟢 NODO LINK STATE {self.nombre} ACTIVO en puerto {self.puerto}")
            
            while self.activo:
                try:
                    cliente, direccion = self.servidor_socket.accept()
                    threading.Thread(target=self.manejar_cliente, args=(cliente,), daemon=True).start()
                except:
                    if self.activo:
                        break
                        
        except Exception as e:
            print(f"❌ Error iniciando nodo {self.nombre}: {e}")
            
    def manejar_cliente(self, cliente):
        """Maneja mensajes entrantes - igual que nodo_terminal.py pero con Link State"""
        try:
            cliente.settimeout(8)
            data = cliente.recv(1024).decode()
            
            if not data:
                return
                
            mensaje = json.loads(data)
            
            if mensaje['tipo'] == 'lsp_update':
                # Recibir actualización Link State
                nodo_origen = mensaje['nodo']
                vecinos_info = mensaje['vecinos']
                
                print(f"📡 Link State recibido de {nodo_origen}: {vecinos_info}")
                
                # Actualizar LSDB
                self.lsdb[nodo_origen] = vecinos_info
                
                # Recalcular rutas
                self.calcular_rutas()
                
                # Confirmar
                respuesta = {'tipo': 'ack_lsp'}
                cliente.send(json.dumps(respuesta).encode())
                
            elif mensaje['tipo'] == 'ping_nodo':
                # Ping igual que en nodo_terminal.py
                esperado = mensaje.get('esperando', 'desconocido')
                desde = mensaje.get('desde', 'desconocido')
                
                print(f"   🏓 Ping recibido de {desde}, esperan nodo: {esperado}")
                print(f"   🆔 Enviando identificación: {self.nombre}")
                
                respuesta_ping = {
                    'tipo': 'pong_nodo',
                    'nodo': self.nombre,
                    'puerto': self.puerto,
                    'timestamp': time.time()
                }
                
                cliente.send(json.dumps(respuesta_ping).encode())
                
                # Esperar el paquete real
                cliente.settimeout(8)
                data_paquete = cliente.recv(1024).decode()
                
                if data_paquete:
                    try:
                        paquete_real = json.loads(data_paquete)
                        if paquete_real.get('tipo') == 'envio_paquete':
                            self.procesar_paquete_real(paquete_real, cliente)
                    except Exception as e:
                        print(f"   ❌ Error procesando paquete real: {e}")
                        
            elif mensaje['tipo'] == 'envio_paquete':
                # Paquete directo
                self.procesar_paquete_real(mensaje, cliente)
                
        except Exception as e:
            print(f"❌ Error manejando cliente: {e}")
        finally:
            try:
                cliente.close()
            except:
                pass
                
    def procesar_paquete_real(self, paquete: dict, cliente):
        """Procesa paquetes - igual que nodo_terminal.py"""
        try:
            origen_original = paquete['origen']
            destino_final = paquete['destino']
            mensaje = paquete['mensaje']
            ruta_completa = paquete['ruta']
            costo_total = paquete['costo']
            saltos_recorridos = paquete.get('saltos_recorridos', [])
            
            # Agregar este nodo a los saltos recorridos
            saltos_recorridos.append(self.nombre)
            
            # Verificar si somos el destino final
            if self.nombre == destino_final:
                print(f"\n📦 PAQUETE FINAL RECIBIDO! (LINK STATE)")
                print(f"   De: {origen_original}")
                print(f"   Para: {destino_final}")
                print(f"   Mensaje: {mensaje}")
                print(f"   Ruta Link State: {' -> '.join(ruta_completa)}")
                print(f"   Saltos realizados: {' -> '.join(saltos_recorridos)}")
                print(f"   Costo total: {costo_total}")
                print(f"   ✅ ENTREGADO EXITOSAMENTE AL DESTINO FINAL\n")
                
                respuesta = {'estado': 'entregado', 'nodo_receptor': self.nombre}
                cliente.send(json.dumps(respuesta).encode())
                
            else:
                # Reenviar usando siguiente salto Link State
                print(f"\n🔄 PAQUETE EN TRÁNSITO! (LINK STATE)")
                print(f"   De: {origen_original} → Para: {destino_final}")
                print(f"   Pasando por: {self.nombre}")
                print(f"   Ruta original: {' -> '.join(ruta_completa)}")
                print(f"   Saltos hasta ahora: {' -> '.join(saltos_recorridos)}")
                
                # Encontrar el siguiente salto usando nuestra tabla Link State
                siguiente_nodo = None
                
                try:
                    indice_actual = ruta_completa.index(self.nombre)
                    if indice_actual + 1 < len(ruta_completa):
                        siguiente_nodo = ruta_completa[indice_actual + 1]
                    else:
                        print(f"   ❌ Error: No hay siguiente nodo en la ruta")
                        respuesta = {'estado': 'error', 'mensaje': 'Fin de ruta inesperado'}
                        cliente.send(json.dumps(respuesta).encode())
                        return
                except ValueError:
                    print(f"   ❌ Error: Nodo {self.nombre} no encontrado en la ruta")
                    respuesta = {'estado': 'error', 'mensaje': 'Nodo no en ruta'}
                    cliente.send(json.dumps(respuesta).encode())
                    return
                
                print(f"   🚀 Reenviando a: {siguiente_nodo}")
                
                # Actualizar paquete
                paquete['saltos_recorridos'] = saltos_recorridos
                
                # Reenviar
                self.reenviar_paquete(siguiente_nodo, paquete)
                
                respuesta = {'estado': 'reenviado', 'nodo_intermedio': self.nombre}
                cliente.send(json.dumps(respuesta).encode())
                
        except Exception as e:
            print(f"❌ Error procesando paquete real: {e}")
            respuesta = {'estado': 'error', 'mensaje': str(e)}
            cliente.send(json.dumps(respuesta).encode())
            
    def reenviar_paquete(self, siguiente_nodo: str, paquete: dict):
        """Reenvía paquete - igual que nodo_terminal.py"""
        try:
            print(f"   🔗 Intentando conectar con {siguiente_nodo}...")
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            puerto_siguiente = self.puertos_nodos[siguiente_nodo]
            
            cliente.settimeout(5)
            cliente.connect((self.host, puerto_siguiente))
            
            # Ping primero
            mensaje_ping = {
                'tipo': 'ping_nodo',
                'esperando': siguiente_nodo,
                'desde': self.nombre
            }
            
            cliente.send(json.dumps(mensaje_ping).encode())
            respuesta_ping = cliente.recv(1024).decode()
            
            if respuesta_ping:
                ping_data = json.loads(respuesta_ping)
                nodo_real = ping_data.get('nodo', 'desconocido')
                
                if nodo_real == siguiente_nodo:
                    print(f"   ✅ Identificación correcta: {nodo_real}")
                    
                    # Enviar paquete real
                    cliente.send(json.dumps(paquete).encode())
                    
                    # Esperar confirmación
                    respuesta = cliente.recv(1024).decode()
                    if respuesta:
                        confirmacion = json.loads(respuesta)
                        print(f"   📨 Confirmación recibida: {confirmacion}")
                        
                        if confirmacion['estado'] == 'reenviado':
                            print(f"   ✅ Paquete reenviado exitosamente a {siguiente_nodo}")
                        elif confirmacion['estado'] == 'entregado':
                            print(f"   ✅ Paquete entregado al destino final por {siguiente_nodo}")
                else:
                    print(f"   ❌ Nodo incorrecto: esperado {siguiente_nodo}, respondió {nodo_real}")
                    
            cliente.close()
            
        except Exception as e:
            print(f"   ❌ Error reenviando a {siguiente_nodo}: {e}")
            
    def calcular_rutas(self):
        """Calcula rutas usando Dijkstra sobre la LSDB actual"""
        try:
            # Construir grafo desde LSDB
            g = grafo()
            
            for nodo, vecinos in self.lsdb.items():
                for vecino, costo in vecinos.items():
                    g.agregar_conexion(nodo, vecino, costo)
                    
            # Calcular rutas desde este nodo
            if self.nombre in g.routers:
                distancias, predecesores = dijkstra(g, self.nombre)
                
                # Construir tabla
                self.routing_table = {}
                for destino in g.routers:
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
                        
                        self.routing_table[destino] = {
                            'distancia': distancias[destino],
                            'ruta': ruta
                        }
                        
                print(f"🧮 Tabla Link State actualizada: {len(self.routing_table)} destinos")
            else:
                print(f"⚠️  Nodo {self.nombre} no encontrado en topología Link State")
                
        except Exception as e:
            print(f"❌ Error calculando rutas Link State: {e}")
            
    def propagar_link_state(self):
        """Propaga información Link State a vecinos directos"""
        mensaje_lsp = {
            'tipo': 'lsp_update',
            'nodo': self.nombre,
            'vecinos': self.vecinos_directos
        }
        
        for vecino in self.vecinos_directos.keys():
            if vecino in self.puertos_nodos:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(3)
                        sock.connect((self.host, self.puertos_nodos[vecino]))
                        sock.send(json.dumps(mensaje_lsp).encode())
                        
                        # Esperar confirmación
                        respuesta = sock.recv(1024).decode()
                        if respuesta:
                            ack = json.loads(respuesta)
                            if ack.get('tipo') == 'ack_lsp':
                                print(f"✅ Link State enviado a {vecino}")
                except Exception as e:
                    print(f"❌ Error enviando Link State a {vecino}: {e}")
                    
    def enviar_paquete(self, destino: str, mensaje: str = "Paquete Link State"):
        """Envía paquete usando rutas Link State"""
        if destino not in self.routing_table:
            print(f"❌ No hay ruta Link State hacia {destino}")
            return False
            
        info_ruta = self.routing_table[destino]
        ruta = info_ruta['ruta']
        costo = info_ruta['distancia']
        
        print(f"\n📤 ENVIANDO PAQUETE (LINK STATE):")
        print(f"   De: {self.nombre}")
        print(f"   Para: {destino}")
        print(f"   Ruta Link State calculada: {' -> '.join(ruta)}")
        print(f"   Costo: {costo}")
        
        if len(ruta) < 2:
            print(f"   ❌ Error: Ruta Link State inválida")
            return False
            
        primer_salto = ruta[1]
        print(f"   🚀 Enviando primero a: {primer_salto}")
        
        # Preparar paquete
        paquete = {
            'tipo': 'envio_paquete',
            'origen': self.nombre,
            'destino': destino,
            'mensaje': mensaje,
            'ruta': ruta,
            'costo': costo,
            'saltos_recorridos': [self.nombre]
        }
        
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            puerto_primer_salto = self.puertos_nodos[primer_salto]
            cliente.settimeout(3)
            cliente.connect((self.host, puerto_primer_salto))
            
            # Ping primero
            mensaje_ping = {
                'tipo': 'ping_nodo',
                'esperando': primer_salto,
                'desde': self.nombre
            }
            
            cliente.send(json.dumps(mensaje_ping).encode())
            respuesta_ping = cliente.recv(1024).decode()
            
            if respuesta_ping:
                ping_data = json.loads(respuesta_ping)
                nodo_real = ping_data.get('nodo', 'desconocido')
                
                if nodo_real == primer_salto:
                    # Enviar paquete real
                    cliente.send(json.dumps(paquete).encode())
                    
                    # Esperar confirmación
                    respuesta = cliente.recv(1024).decode()
                    if respuesta:
                        confirmacion = json.loads(respuesta)
                        print(f"   ✅ Paquete Link State enviado: {confirmacion.get('estado', 'ok')}")
                        print(f"   🎯 El paquete seguirá la ruta Link State: {' -> '.join(ruta)}")
                        
                        cliente.close()
                        return True
                        
            cliente.close()
            return False
            
        except Exception as e:
            print(f"   ❌ Error enviando paquete Link State: {e}")
            return False
            
    def mostrar_tabla_enrutamiento(self):
        """Muestra tabla de enrutamiento Link State"""
        print(f"\n📋 TABLA DE ENRUTAMIENTO LINK STATE - NODO {self.nombre}")
        print("="*60)
        print(f"LSDB conoce {len(self.lsdb)} nodos: {list(self.lsdb.keys())}")
        print(f"{'Destino':<8} {'Ruta Link State':<25} {'Costo':<6}")
        print("-"*60)
        
        for destino in sorted(self.routing_table.keys()):
            info = self.routing_table[destino]
            ruta = ' -> '.join(info['ruta'])
            costo = info['distancia']
            print(f"{destino:<8} {ruta:<25} {costo:<6}")
        print()
        
    def mostrar_lsdb(self):
        """Muestra base de datos Link State"""
        print(f"\n🗄️  BASE DE DATOS LINK STATE - NODO {self.nombre}")
        print("="*50)
        
        for nodo in sorted(self.lsdb.keys()):
            vecinos = self.lsdb[nodo]
            vecinos_str = ", ".join(f"{v}:{c}" for v, c in sorted(vecinos.items()))
            print(f"{nodo}: {vecinos_str}")
        print()
        
    def menu_interactivo(self):
        """Menú interactivo - igual que nodo_terminal.py"""
        while self.activo:
            print(f"\n🔧 MENÚ LINK STATE {self.nombre}")
            print("1. Ver tabla de enrutamiento Link State")
            print("2. Ver base de datos Link State (LSDB)")
            print("3. Enviar paquete")
            print("4. Propagar Link State")
            print("5. Salir")
            
            opcion = input("Opción: ").strip()
            
            if opcion == '1':
                self.mostrar_tabla_enrutamiento()
                
            elif opcion == '2':
                self.mostrar_lsdb()
                
            elif opcion == '3':
                print("\nDestinos disponibles:", ", ".join(sorted([n for n in self.routing_table.keys()])))
                destino = input("Destino: ").upper().strip()
                
                if destino in self.routing_table:
                    mensaje = input("Mensaje (opcional): ").strip()
                    if not mensaje:
                        mensaje = f"Paquete Link State desde {self.nombre}"
                    self.enviar_paquete(destino, mensaje)
                else:
                    print("❌ Destino no válido o sin ruta Link State")
                    
            elif opcion == '4':
                print("🔄 Propagando Link State a vecinos...")
                self.propagar_link_state()
                
            elif opcion == '5':
                print(f"🔴 Cerrando nodo Link State {self.nombre}")
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
    if len(sys.argv) != 2:
        print("Uso: python link_state_simple.py <nombre_nodo>")
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
    nodo = NodoLinkStateSimple(nombre, puerto)
    
    # Iniciar servidor
    servidor_thread = threading.Thread(target=nodo.iniciar_servidor, daemon=True)
    servidor_thread.start()
    
    time.sleep(1)
    
    # Propagar Link State inicial
    print("🚀 Propagando Link State inicial...")
    nodo.propagar_link_state()
    
    time.sleep(2)  # Dar tiempo para recibir otros Link States
    
    # Mostrar tabla inicial
    nodo.mostrar_tabla_enrutamiento()
    
    # Iniciar menú
    try:
        nodo.menu_interactivo()
    except KeyboardInterrupt:
        print(f"\n🔴 Nodo {nombre} detenido")
        nodo.detener()

if __name__ == "__main__":
    main()
