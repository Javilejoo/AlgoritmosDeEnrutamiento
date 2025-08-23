"""
Cliente para interactuar con nodos Link State
Permite enviar comandos y monitorear el estado de la red
"""

import socket
import json
import time
import threading
from typing import Dict, List, Optional

class LinkStateClient:
    """Cliente para interactuar con nodos Link State"""
    
    def __init__(self):
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        self.host = '127.0.0.1'
        
    def enviar_comando(self, nodo: str, comando: dict) -> Optional[dict]:
        """Envía un comando a un nodo específico"""
        if nodo not in self.puertos_nodos:
            print(f"❌ Nodo {nodo} no existe")
            return None
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.host, self.puertos_nodos[nodo]))
                
                # Enviar comando
                mensaje = json.dumps(comando).encode('utf-8')
                sock.send(mensaje)
                
                # Recibir respuesta
                respuesta = sock.recv(4096).decode('utf-8')
                if respuesta:
                    return json.loads(respuesta)
                    
        except ConnectionRefusedError:
            print(f"❌ No se puede conectar al nodo {nodo} (puerto {self.puertos_nodos[nodo]})")
        except socket.timeout:
            print(f"⏱️ Timeout conectando al nodo {nodo}")
        except Exception as e:
            print(f"❌ Error comunicándose con {nodo}: {e}")
            
        return None
        
    def verificar_conectividad(self, nodo: str) -> bool:
        """Verifica si un nodo está accesible"""
        comando = {'tipo': 'hello'}
        respuesta = self.enviar_comando(nodo, comando)
        
        if respuesta and respuesta.get('tipo') == 'hello_response':
            print(f"✅ Nodo {nodo} responde correctamente")
            return True
        else:
            print(f"❌ Nodo {nodo} no responde")
            return False
            
    def obtener_estado_nodo(self, nodo: str) -> Optional[dict]:
        """Obtiene el estado completo de un nodo"""
        comando = {'tipo': 'get_status'}
        respuesta = self.enviar_comando(nodo, comando)
        
        if respuesta and respuesta.get('tipo') == 'status_response':
            return respuesta.get('estado')
        else:
            print(f"❌ No se pudo obtener estado de {nodo}")
            return None
            
    def mostrar_tabla_enrutamiento(self, nodo: str):
        """Muestra la tabla de enrutamiento de un nodo"""
        estado = self.obtener_estado_nodo(nodo)
        if not estado:
            return
            
        tabla = estado.get('routing_table', {})
        
        print(f"\n--- Tabla de Enrutamiento de {nodo} ---")
        print("Destino | Next-Hop | Distancia | Estado")
        print("-" * 45)
        
        if not tabla:
            print("  (tabla vacía)")
        else:
            for dest in sorted(tabla.keys()):
                info = tabla[dest]
                next_hop = info.get('next_hop', 'N/A')
                distance = info.get('distance', float('inf'))
                distance_str = str(int(distance)) if distance != float('inf') else "∞"
                
                print(f"{dest:7} | {next_hop:8} | {distance_str:9} | Activa")
                
        print("-" * 45)
        
    def mostrar_lsdb(self, nodo: str):
        """Muestra la base de datos Link State de un nodo"""
        estado = self.obtener_estado_nodo(nodo)
        if not estado:
            return
            
        print(f"\n--- LSDB de {nodo} ---")
        print(f"Versión de topología: {estado.get('topology_version', 0)}")
        print(f"Tamaño LSDB: {estado.get('lsdb_size', 0)} entradas")
        
        # Mostrar estadísticas
        stats = estado.get('estadisticas', {})
        print(f"LSPs enviados: {stats.get('lsps_enviados', 0)}")
        print(f"LSPs recibidos: {stats.get('lsps_recibidos', 0)}")
        print(f"Tablas calculadas: {stats.get('tablas_calculadas', 0)}")
        
    def comparar_tablas_enrutamiento(self, nodos: List[str]):
        """Compara las tablas de enrutamiento de múltiples nodos"""
        print(f"\n🔍 COMPARACIÓN DE TABLAS DE ENRUTAMIENTO")
        print("=" * 60)
        
        estados = {}
        for nodo in nodos:
            estado = self.obtener_estado_nodo(nodo)
            if estado:
                estados[nodo] = estado.get('routing_table', {})
            else:
                print(f"❌ No se pudo obtener estado de {nodo}")
                
        if len(estados) < 2:
            print("❌ Se necesitan al menos 2 nodos para comparar")
            return
            
        # Obtener todos los destinos posibles
        todos_destinos = set()
        for tabla in estados.values():
            todos_destinos.update(tabla.keys())
            
        # Comparar ruta por ruta
        for destino in sorted(todos_destinos):
            print(f"\n--- Rutas hacia {destino} ---")
            
            rutas_encontradas = {}
            for nodo, tabla in estados.items():
                if destino in tabla and destino != nodo:
                    info = tabla[destino]
                    path = info.get('path', [])
                    distance = info.get('distance', float('inf'))
                    ruta_str = " -> ".join(path) if path else "N/A"
                    rutas_encontradas[nodo] = (ruta_str, distance)
                else:
                    rutas_encontradas[nodo] = ("SIN RUTA", float('inf'))
                    
            # Mostrar rutas
            for nodo, (ruta, distancia) in rutas_encontradas.items():
                dist_str = str(int(distancia)) if distancia != float('inf') else "∞"
                print(f"  {nodo}: {ruta} (costo: {dist_str})")
                
            # Verificar consistencia
            distancias = [d for _, d in rutas_encontradas.values() if d != float('inf')]
            if distancias and len(set(distancias)) > 1:
                print("  ⚠️  INCONSISTENCIA: Diferentes costos para el mismo destino")
                
    def verificar_conectividad_red(self, nodos: List[str] = None):
        """Verifica la conectividad de todos los nodos"""
        if nodos is None:
            nodos = list(self.puertos_nodos.keys())
            
        print(f"\n🔗 VERIFICACIÓN DE CONECTIVIDAD")
        print("=" * 40)
        
        activos = []
        inactivos = []
        
        for nodo in nodos:
            if self.verificar_conectividad(nodo):
                activos.append(nodo)
            else:
                inactivos.append(nodo)
                
        print(f"\n📊 Resumen:")
        print(f"✅ Nodos activos: {activos} ({len(activos)}/{len(nodos)})")
        if inactivos:
            print(f"❌ Nodos inactivos: {inactivos}")
            
        return activos, inactivos
        
    def monitorear_convergencia(self, nodos: List[str], duracion: int = 30):
        """Monitorea el proceso de convergencia de la red"""
        print(f"\n📡 MONITOREANDO CONVERGENCIA ({duracion} segundos)")
        print("=" * 50)
        
        inicio = time.time()
        iteracion = 0
        
        while time.time() - inicio < duracion:
            iteracion += 1
            print(f"\n--- Iteración {iteracion} (t={int(time.time() - inicio)}s) ---")
            
            # Obtener estadísticas de cada nodo
            for nodo in nodos:
                estado = self.obtener_estado_nodo(nodo)
                if estado:
                    stats = estado.get('estadisticas', {})
                    rutas = len(estado.get('routing_table', {}))
                    lsdb_size = estado.get('lsdb_size', 0)
                    version = estado.get('topology_version', 0)
                    
                    print(f"  {nodo}: {rutas} rutas, LSDB={lsdb_size}, v={version}")
                else:
                    print(f"  {nodo}: ❌ No responde")
                    
            time.sleep(5)  # Esperar 5 segundos entre iteraciones
            
        print(f"\n✅ Monitoreo completado")
        
    def ejecutar_demo_basico(self):
        """Ejecuta un demo básico de Link State"""
        print("\n🚀 DEMO BÁSICO LINK STATE")
        print("=" * 40)
        
        # 1. Verificar nodos activos
        activos, _ = self.verificar_conectividad_red(['A', 'B', 'F', 'D'])
        
        if len(activos) < 3:
            print("❌ Se necesitan al menos 3 nodos activos para el demo")
            return
            
        print(f"✅ Usando nodos: {activos}")
        
        # 2. Mostrar estado inicial
        print(f"\n📋 ESTADO INICIAL")
        print("-" * 30)
        for nodo in activos[:3]:  # Mostrar solo los primeros 3
            self.mostrar_tabla_enrutamiento(nodo)
            
        # 3. Comparar tablas
        self.comparar_tablas_enrutamiento(activos)
        
        # 4. Mostrar estadísticas LSDB
        print(f"\n📊 ESTADÍSTICAS LSDB")
        print("-" * 30)
        for nodo in activos:
            self.mostrar_lsdb(nodo)
            
    def menu_interactivo(self):
        """Menú interactivo para el cliente"""
        while True:
            print("\n" + "="*50)
            print("CLIENTE LINK STATE - MENÚ PRINCIPAL")
            print("="*50)
            print("1. Verificar conectividad de un nodo")
            print("2. Mostrar tabla de enrutamiento")
            print("3. Mostrar LSDB de un nodo")
            print("4. Comparar tablas de enrutamiento")
            print("5. Verificar conectividad de la red")
            print("6. Monitorear convergencia")
            print("7. Ejecutar demo básico")
            print("8. Obtener estado completo de nodo")
            print("0. Salir")
            print("-" * 50)
            
            try:
                opcion = input("Selecciona una opción (0-8): ").strip()
                
                if opcion == "0":
                    print("👋 ¡Hasta luego!")
                    break
                    
                elif opcion == "1":
                    nodo = input("Nombre del nodo (A-I): ").strip().upper()
                    self.verificar_conectividad(nodo)
                    
                elif opcion == "2":
                    nodo = input("Nombre del nodo (A-I): ").strip().upper()
                    self.mostrar_tabla_enrutamiento(nodo)
                    
                elif opcion == "3":
                    nodo = input("Nombre del nodo (A-I): ").strip().upper()
                    self.mostrar_lsdb(nodo)
                    
                elif opcion == "4":
                    nodos_str = input("Nodos separados por comas (ej: A,B,F): ").strip().upper()
                    nodos = [n.strip() for n in nodos_str.split(',') if n.strip()]
                    if len(nodos) >= 2:
                        self.comparar_tablas_enrutamiento(nodos)
                    else:
                        print("❌ Se necesitan al menos 2 nodos")
                        
                elif opcion == "5":
                    self.verificar_conectividad_red()
                    
                elif opcion == "6":
                    nodos_str = input("Nodos a monitorear (separados por comas): ").strip().upper()
                    if nodos_str:
                        nodos = [n.strip() for n in nodos_str.split(',') if n.strip()]
                        duracion = int(input("Duración en segundos (default 30): ").strip() or "30")
                        self.monitorear_convergencia(nodos, duracion)
                    else:
                        print("❌ Especifica al menos un nodo")
                        
                elif opcion == "7":
                    self.ejecutar_demo_basico()
                    
                elif opcion == "8":
                    nodo = input("Nombre del nodo (A-I): ").strip().upper()
                    estado = self.obtener_estado_nodo(nodo)
                    if estado:
                        print(f"\n--- Estado completo de {nodo} ---")
                        print(json.dumps(estado, indent=2, ensure_ascii=False))
                    else:
                        print(f"❌ No se pudo obtener estado de {nodo}")
                        
                else:
                    print("❌ Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n👋 Interrumpido por usuario")
                break
            except ValueError as e:
                print(f"❌ Valor inválido: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
            # Pausa para leer
            input("\nPresiona Enter para continuar...")

def main():
    print("📱 CLIENTE LINK STATE")
    print("=" * 30)
    print("Cliente para interactuar con nodos Link State")
    print("Asegúrate de tener nodos ejecutándose antes de usar este cliente.")
    
    cliente = LinkStateClient()
    cliente.menu_interactivo()

if __name__ == "__main__":
    main()
