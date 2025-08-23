"""
Abridor automático de nodos Link State Simple
Abre varios nodos para que puedas probarlos fácilmente
"""

import subprocess
import time
import sys

def abrir_nodos_link_state():
    """Abre varios nodos Link State Simple para pruebas"""
    
    print("🚀 ABRIENDO NODOS LINK STATE SIMPLE")
    print("=" * 50)
    
    # Lista de nodos para abrir
    nodos = ['A', 'D', 'I', 'F']  # Los mismos que pediste
    
    procesos = []
    
    for nodo in nodos:
        try:
            print(f"📡 Iniciando nodo Link State {nodo}...")
            
            # Abrir cada nodo en una nueva ventana de comando
            comando = [
                'cmd', '/c', 'start', 'cmd', '/k',
                f'python link_state_simple.py {nodo}'
            ]
            
            proceso = subprocess.Popen(comando, shell=True)
            procesos.append(proceso)
            
            time.sleep(1.5)  # Pausa entre nodos para evitar conflictos
            
        except Exception as e:
            print(f"❌ Error iniciando nodo {nodo}: {e}")
    
    print(f"\n✅ {len(nodos)} nodos Link State iniciados!")
    print("\nNodos activos:")
    for nodo in nodos:
        puerto = {'A': 65001, 'D': 65004, 'I': 65009, 'F': 65006}[nodo]
        print(f"  - Nodo {nodo}: puerto {puerto}")
    
    print("\n📋 INSTRUCCIONES DE USO:")
    print("1. Espera 5-10 segundos para que los nodos se conecten")
    print("2. En cualquier nodo, usa opción '4' para propagar Link State")
    print("3. En cualquier nodo, usa opción '1' para ver rutas calculadas")
    print("4. En cualquier nodo, usa opción '3' para enviar paquetes")
    print("5. ¡Los paquetes usarán rutas calculadas dinámicamente con Link State!")
    
    print("\n🧪 EJEMPLO DE PRUEBA:")
    print("- En nodo A: envía paquete a F")
    print("- En nodo D: envía paquete a I")
    print("- En nodo I: envía paquete a A")
    print("- En nodo F: envía paquete a D")
    
    print("\n❌ Para cerrar: usa opción '5' en cada nodo")
    print("🔧 Cada nodo calculará rutas usando Link State dinámicamente!")
    
    return procesos

if __name__ == "__main__":
    print("🔗 SIMULADOR DE RED LINK STATE SIMPLE")
    print("Igual que nodo_terminal.py pero con Link State REAL")
    print()
    
    input("Presiona Enter para abrir los nodos Link State...")
    
    procesos = abrir_nodos_link_state()
    
    print("\n⏱️  Presiona Enter cuando hayas terminado de probar...")
    input()
    
    print("🔴 Cerrando simulación...")
