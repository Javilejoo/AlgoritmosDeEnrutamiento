import threading
import time
import json
from typing import Dict, List
from grafo import grafo
from nodo import Nodo

class CoordinadorRed:
    def __init__(self):
        self.grafo_red = self.crear_grafo()
        self.nodos = {}
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        self.hilos_nodos = []
        
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
    
    def iniciar_todos_los_nodos(self):
        """Inicia todos los nodos de la red"""
        print("=== INICIANDO RED DISTRIBUIDA ===")
        print(f"Grafo de la red:\n{self.grafo_red}\n")
        
        # Crear e iniciar cada nodo
        for nombre_nodo in sorted(self.grafo_red.routers):
            puerto = self.puertos_nodos[nombre_nodo]
            nodo = Nodo(nombre_nodo, puerto, self.grafo_red)
            nodo.puertos_nodos = self.puertos_nodos
            self.nodos[nombre_nodo] = nodo
            
            # Iniciar servidor del nodo en hilo separado
            hilo = threading.Thread(target=self.ejecutar_nodo, args=(nodo,))
            hilo.daemon = True
            hilo.start()
            self.hilos_nodos.append(hilo)
            
        print(f"Iniciados {len(self.nodos)} nodos")
        
        # Esperar que todos los servidores estén listos
        time.sleep(3)
        
    def ejecutar_nodo(self, nodo: Nodo):
        """Ejecuta un nodo individual"""
        # Iniciar servidor
        servidor_thread = threading.Thread(target=nodo.iniciar_servidor)
        servidor_thread.daemon = True
        servidor_thread.start()
        
        # Esperar que todos los servidores estén listos
        time.sleep(2)
        
        # Calcular tabla local
        nodo.calcular_tabla_local()
        
    def simular_intercambio_rutas(self):
        """Simula el intercambio de información de rutas entre nodos vecinos"""
        print("\n=== SIMULANDO INTERCAMBIO DE RUTAS ===")
        
        for nombre_nodo, nodo in self.nodos.items():
            print(f"\n--- Nodo {nombre_nodo} solicitando info de vecinos ---")
            distancias_vecinos = nodo.solicitar_distancias_vecinos()
            
            for vecino, distancias in distancias_vecinos.items():
                print(f"  Recibido de {vecino}: {len(distancias)} destinos")
                
    def mostrar_estado_completo(self):
        """Muestra el estado de todos los nodos"""
        print("\n=== ESTADO FINAL DE LA RED ===")
        
        for nombre_nodo in sorted(self.nodos.keys()):
            nodo = self.nodos[nombre_nodo]
            estado = nodo.obtener_estado()
            
            print(f"\n--- Nodo {nombre_nodo} ---")
            print(f"Vecinos: {', '.join(estado['vecinos'])}")
            print("Tabla de rutas:")
            
            for destino, distancia in estado['tabla_distancias'].items():
                ruta = " -> ".join(estado['tabla_rutas'].get(destino, []))
                print(f"  {destino}: costo={distancia}, ruta={ruta}")
                
    def guardar_tablas_distribuidas(self, carpeta: str = "tablas_distribuidas"):
        """Guarda las tablas calculadas por el sistema distribuido"""
        import os
        os.makedirs(carpeta, exist_ok=True)
        
        for nombre_nodo, nodo in self.nodos.items():
            estado = nodo.obtener_estado()
            
            # Convertir a formato similar al original
            data = []
            for destino, distancia in estado['tabla_distancias'].items():
                ruta = estado['tabla_rutas'].get(destino, [])
                next_hop = ruta[1] if len(ruta) > 1 else None
                
                data.append({
                    "destino": destino,
                    "next_hop": next_hop if next_hop else "",
                    "costo": distancia,
                    "ruta": ruta
                })
            
            archivo = os.path.join(carpeta, f"tabla_{nombre_nodo}_distribuida.json")
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        print(f"\nTablas distribuidas guardadas en '{carpeta}/'")
        
    def detener_red(self):
        """Detiene todos los nodos de la red"""
        print("\n=== DETENIENDO RED ===")
        for nodo in self.nodos.values():
            nodo.detener()
            
    def ejecutar_simulacion_completa(self):
        """Ejecuta la simulación completa del algoritmo distribuido"""
        try:
            # 1. Iniciar todos los nodos
            self.iniciar_todos_los_nodos()
            
            # 2. Esperar que todos calculen sus tablas
            time.sleep(2)
            
            # 3. Simular intercambio de información
            self.simular_intercambio_rutas()
            
            # 4. Mostrar estado final
            self.mostrar_estado_completo()
            
            # 5. Guardar tablas
            self.guardar_tablas_distribuidas()
            
            # 6. Mantener activa la red
            print("\n=== RED ACTIVA - Presiona Ctrl+C para detener ===")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.detener_red()
            print("Red detenida correctamente")

if __name__ == "__main__":
    coordinador = CoordinadorRed()
    coordinador.ejecutar_simulacion_completa()
