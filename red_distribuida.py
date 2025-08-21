import subprocess
import sys
import time
import os
from typing import List

class GestorRedDistribuida:
    def __init__(self):
        self.procesos_nodos = []
        self.nodos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        self.puertos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        
    def mostrar_menu(self):
        """Muestra el menú de opciones"""
        print("\n" + "="*50)
        print("   SISTEMA DISTRIBUIDO DE ENRUTAMIENTO")
        print("        Algoritmo Dijkstra con Sockets")
        print("="*50)
        print("1. Ejecutar simulación automática (Coordinador)")
        print("2. Iniciar nodos individuales manualmente")
        print("3. Iniciar un nodo específico")
        print("4. Ver estado de la red")
        print("5. Comparar con implementación centralizada")
        print("6. Salir")
        print("-"*50)
        
    def ejecutar_simulacion_automatica(self):
        """Ejecuta la simulación completa usando el coordinador"""
        print("Iniciando simulación automática...")
        try:
            subprocess.run([sys.executable, "coordinador.py"])
        except KeyboardInterrupt:
            print("\nSimulación detenida por el usuario")
        except Exception as e:
            print(f"Error ejecutando simulación: {e}")
            
    def iniciar_nodos_manuales(self):
        """Inicia todos los nodos como procesos separados"""
        print("Iniciando nodos individuales...")
        
        try:
            for nodo in self.nodos:
                puerto = self.puertos[nodo]
                print(f"Iniciando nodo {nodo} en puerto {puerto}")
                
                # Crear proceso para cada nodo
                proceso = subprocess.Popen([
                    sys.executable, "nodo.py", nodo, str(puerto)
                ])
                self.procesos_nodos.append(proceso)
                time.sleep(0.5)  # Esperar entre inicios
                
            print(f"\nTodos los {len(self.nodos)} nodos iniciados")
            print("Presiona Ctrl+C para detener todos los nodos")
            
            # Esperar hasta que el usuario termine
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.detener_todos_los_nodos()
            
    def iniciar_nodo_especifico(self):
        """Permite iniciar un nodo específico"""
        print("Nodos disponibles:", ", ".join(self.nodos))
        nodo = input("Ingresa el nombre del nodo a iniciar: ").upper().strip()
        
        if nodo not in self.nodos:
            print(f"Nodo '{nodo}' no válido")
            return
            
        puerto = self.puertos[nodo]
        print(f"Iniciando nodo {nodo} en puerto {puerto}")
        
        try:
            subprocess.run([sys.executable, "nodo.py", nodo, str(puerto)])
        except KeyboardInterrupt:
            print(f"\nNodo {nodo} detenido")
            
    def ver_estado_red(self):
        """Muestra información sobre la red"""
        print("\n--- INFORMACIÓN DE LA RED ---")
        print(f"Nodos en la red: {', '.join(self.nodos)}")
        print("Asignación de puertos:")
        for nodo, puerto in self.puertos.items():
            print(f"  {nodo}: puerto {puerto}")
            
        # Verificar si existen tablas generadas
        if os.path.exists("tablas_json"):
            print(f"\nTablas centralizadas encontradas en 'tablas_json/'")
            
        if os.path.exists("tablas_distribuidas"):
            print(f"Tablas distribuidas encontradas en 'tablas_distribuidas/'")
            
    def comparar_implementaciones(self):
        """Compara las implementaciones centralizada y distribuida"""
        print("\n--- COMPARACIÓN DE IMPLEMENTACIONES ---")
        
        # Ejecutar implementación centralizada
        print("1. Ejecutando implementación centralizada (dijkstra.py)...")
        try:
            subprocess.run([sys.executable, "dijkstra.py"])
            print("   ✓ Implementación centralizada completada")
        except Exception as e:
            print(f"   ✗ Error en implementación centralizada: {e}")
            
        # Ejecutar implementación distribuida
        print("\n2. Ejecutando implementación distribuida...")
        try:
            subprocess.run([sys.executable, "coordinador.py"])
            print("   ✓ Implementación distribuida completada")
        except Exception as e:
            print(f"   ✗ Error en implementación distribuida: {e}")
            
        print("\n3. Comparación de resultados:")
        print("   - Revisa las carpetas 'tablas_json/' y 'tablas_distribuidas/'")
        print("   - Ambas deberían generar las mismas rutas y costos")
        
    def detener_todos_los_nodos(self):
        """Detiene todos los procesos de nodos"""
        print("\nDeteniendo todos los nodos...")
        for proceso in self.procesos_nodos:
            try:
                proceso.terminate()
                proceso.wait(timeout=5)
            except:
                proceso.kill()
        self.procesos_nodos = []
        print("Todos los nodos detenidos")
        
    def ejecutar(self):
        """Bucle principal del programa"""
        while True:
            self.mostrar_menu()
            opcion = input("Selecciona una opción (1-6): ").strip()
            
            if opcion == '1':
                self.ejecutar_simulacion_automatica()
            elif opcion == '2':
                self.iniciar_nodos_manuales()
            elif opcion == '3':
                self.iniciar_nodo_especifico()
            elif opcion == '4':
                self.ver_estado_red()
            elif opcion == '5':
                self.comparar_implementaciones()
            elif opcion == '6':
                self.detener_todos_los_nodos()
                print("¡Hasta luego!")
                break
            else:
                print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    gestor = GestorRedDistribuida()
    try:
        gestor.ejecutar()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido")
        gestor.detener_todos_los_nodos()
