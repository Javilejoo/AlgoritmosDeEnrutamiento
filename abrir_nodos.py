import subprocess
import sys
import os
import time

class GestorTerminales:
    def __init__(self):
        self.nodos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        
    def mostrar_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*60)
        print("  🌐 SISTEMA DE NODOS DISTRIBUIDO - DIJKSTRA")
        print("      Cada nodo en su propia terminal")
        print("="*60)
        print("1. Abrir todas las terminales (9 nodos)")
        print("2. Abrir terminal para un nodo específico")
        print("3. Ver instrucciones de uso manual")
        print("4. Salir")
        print("-"*60)
        
    def abrir_terminal_nodo(self, nodo: str):
        """Abre una terminal para un nodo específico"""
        try:
            # Para Windows
            if os.name == 'nt':
                comando = f'start cmd /k "python nodo_terminal.py {nodo}"'
                subprocess.Popen(comando, shell=True)
            # Para Linux/Mac
            else:
                comando = f'gnome-terminal -- python3 nodo_terminal.py {nodo}'
                subprocess.Popen(comando, shell=True)
                
            print(f"✅ Terminal abierta para nodo {nodo}")
            
        except Exception as e:
            print(f"❌ Error abriendo terminal para {nodo}: {e}")
            
    def abrir_todas_las_terminales(self):
        """Abre una terminal para cada nodo"""
        print("\n🚀 Abriendo terminales para todos los nodos...")
        print("Espera 2 segundos entre cada terminal...")
        
        for i, nodo in enumerate(self.nodos):
            print(f"Abriendo terminal {i+1}/9 para nodo {nodo}")
            self.abrir_terminal_nodo(nodo)
            time.sleep(2)  # Esperar entre terminales
            
        print("\n✅ Todas las terminales abiertas!")
        print("\n📝 INSTRUCCIONES:")
        print("- Cada terminal representa un nodo de la red")
        print("- Usa opción '2' en cualquier nodo para enviar paquetes")
        print("- El nodo receptor mostrará el mensaje de confirmación")
        print("- Usa opción '1' para ver la tabla de enrutamiento")
        
    def abrir_nodo_especifico(self):
        """Permite al usuario elegir un nodo específico"""
        print(f"\nNodos disponibles: {', '.join(self.nodos)}")
        nodo = input("¿Qué nodo quieres abrir? ").upper().strip()
        
        if nodo in self.nodos:
            self.abrir_terminal_nodo(nodo)
        else:
            print(f"❌ Nodo '{nodo}' no válido")
            
    def mostrar_instrucciones(self):
        """Muestra instrucciones de uso manual"""
        print("\n" + "="*60)
        print("📖 INSTRUCCIONES DE USO MANUAL")
        print("="*60)
        print("\n1️⃣ ABRIR NODO MANUALMENTE:")
        print("   python nodo_terminal.py <NODO>")
        print("   Ejemplo: python nodo_terminal.py A")
        print("\n2️⃣ NODOS DISPONIBLES:")
        print(f"   {', '.join(self.nodos)}")
        print("\n3️⃣ UNA VEZ EN EL NODO:")
        print("   • Opción 1: Ver tabla de enrutamiento")
        print("   • Opción 2: Enviar paquete a otro nodo")
        print("   • Opción 3: Cerrar nodo")
        print("\n4️⃣ EJEMPLO DE FLUJO:")
        print("   Terminal 1: python nodo_terminal.py A")
        print("   Terminal 2: python nodo_terminal.py D")
        print("   En terminal A: elegir opción 2, destino D")
        print("   En terminal D: verás 'PAQUETE RECIBIDO' con la ruta")
        print("\n5️⃣ PUERTOS USADOS:")
        puertos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        for nodo, puerto in puertos.items():
            print(f"   Nodo {nodo}: puerto {puerto}")
        print("="*60)
        
    def ejecutar(self):
        """Bucle principal"""
        while True:
            self.mostrar_menu()
            opcion = input("Selecciona una opción (1-4): ").strip()
            
            if opcion == '1':
                self.abrir_todas_las_terminales()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == '2':
                self.abrir_nodo_especifico()
                
            elif opcion == '3':
                self.mostrar_instrucciones()
                input("\nPresiona Enter para continuar...")
                
            elif opcion == '4':
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida")

if __name__ == "__main__":
    gestor = GestorTerminales()
    try:
        gestor.ejecutar()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido")
