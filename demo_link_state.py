"""
Demo interactivo del algoritmo Link State
Permite probar diferentes escenarios de forma sencilla
"""

from link_state import LinkStateNode
from dijkstra import construir_tablas_para_todos, imprimir_tabla
from grafo import grafo
import time

class LinkStateDemo:
    """Demo interactivo para experimentar con Link State"""
    
    def __init__(self):
        self.nodos = {}
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
        
    def inicializar_red(self):
        """Inicializa la red Link State"""
        print("🌐 Inicializando red Link State...")
        print("Topología:")
        for nodo, vecinos in self.topologia_inicial.items():
            print(f"  {nodo}: {vecinos}")
        
        # Crear nodos
        self.nodos = {}
        for name, neighbors in self.topologia_inicial.items():
            self.nodos[name] = LinkStateNode(name, neighbors)
        
        # Simular convergencia inicial
        print("\n📡 Intercambiando LSPs para convergencia inicial...")
        all_lsps = []
        for node in self.nodos.values():
            all_lsps.append(node.lsdb.lsp_db[node.name])
        
        for node in self.nodos.values():
            for lsp in all_lsps:
                if lsp.source != node.name:
                    node.receive_lsp(lsp)
        
        print("✅ Red inicializada y convergida!")
        
    def mostrar_tabla_nodo(self, nodo_name: str):
        """Muestra la tabla de enrutamiento de un nodo específico"""
        if nodo_name in self.nodos:
            self.nodos[nodo_name].print_routing_table()
        else:
            print(f"❌ Nodo {nodo_name} no existe")
    
    def mostrar_ruta(self, origen: str, destino: str):
        """Muestra la ruta específica entre dos nodos"""
        if origen not in self.nodos:
            print(f"❌ Nodo origen {origen} no existe")
            return
        
        if destino in self.nodos[origen].routing_table:
            info = self.nodos[origen].routing_table[destino]
            path = " -> ".join(info['path'])
            print(f"📍 Ruta {origen} -> {destino}:")
            print(f"   Camino: {path}")
            print(f"   Costo total: {info['distance']}")
            print(f"   Siguiente salto: {info['next_hop']}")
        else:
            print(f"❌ No hay ruta de {origen} a {destino}")
    
    def cambiar_enlace(self, nodo1: str, nodo2: str, nuevo_costo: int):
        """Cambia el costo de un enlace entre dos nodos"""
        if nodo1 not in self.nodos or nodo2 not in self.nodos:
            print(f"❌ Uno de los nodos no existe")
            return
        
        print(f"🔧 Cambiando enlace {nodo1}-{nodo2} a costo {nuevo_costo}")
        
        # Actualizar en ambos nodos
        if nuevo_costo > 0:
            self.nodos[nodo1].update_neighbor(nodo2, nuevo_costo)
            self.nodos[nodo2].update_neighbor(nodo1, nuevo_costo)
        else:
            self.nodos[nodo1].remove_neighbor(nodo2)
            self.nodos[nodo2].remove_neighbor(nodo1)
        
        # Propagar cambios
        self._propagar_cambios([nodo1, nodo2])
        print("✅ Cambio aplicado y propagado")
    
    def eliminar_enlace(self, nodo1: str, nodo2: str):
        """Elimina un enlace entre dos nodos"""
        print(f"🚫 Eliminando enlace {nodo1}-{nodo2}")
        self.cambiar_enlace(nodo1, nodo2, 0)
    
    def agregar_enlace(self, nodo1: str, nodo2: str, costo: int):
        """Agrega un nuevo enlace entre dos nodos"""
        print(f"➕ Agregando enlace {nodo1}-{nodo2} con costo {costo}")
        self.cambiar_enlace(nodo1, nodo2, costo)
    
    def _propagar_cambios(self, nodos_modificados: list):
        """Propaga los cambios a todos los nodos de la red"""
        new_lsps = []
        for nodo_name in nodos_modificados:
            new_lsps.append(self.nodos[nodo_name].lsdb.lsp_db[nodo_name])
        
        for node in self.nodos.values():
            if node.name not in nodos_modificados:
                for lsp in new_lsps:
                    node.receive_lsp(lsp)
    
    def comparar_con_dijkstra_estatico(self):
        """Compara las rutas Link State con cálculo estático de Dijkstra"""
        print("🔍 Comparando con cálculo estático de Dijkstra...")
        
        # Crear grafo para Dijkstra estático
        g = grafo()
        for nodo_name, nodo in self.nodos.items():
            for vecino, costo in nodo.neighbors.items():
                g.agregar_conexion(nodo_name, vecino, costo, bidireccional=False)
        
        # Calcular tablas estáticas
        tablas_estaticas = construir_tablas_para_todos(g, incluir_ruta=True)
        
        print("\n=== COMPARACIÓN NODO A ===")
        print("\n--- Link State ---")
        self.nodos['A'].print_routing_table()
        
        print("\n--- Dijkstra Estático ---")
        imprimir_tabla('A', tablas_estaticas['A'])
    
    def mostrar_estado_completo(self):
        """Muestra el estado completo de la red"""
        print("\n" + "="*60)
        print("ESTADO COMPLETO DE LA RED")
        print("="*60)
        
        # Mostrar topología actual
        print("\n📊 Topología actual:")
        for nodo_name in sorted(self.nodos.keys()):
            vecinos = self.nodos[nodo_name].neighbors
            if vecinos:
                vecinos_str = ", ".join(f"{v}:{c}" for v, c in sorted(vecinos.items()))
                print(f"  {nodo_name}: {vecinos_str}")
            else:
                print(f"  {nodo_name}: (sin vecinos)")
        
        # Mostrar algunas tablas representativas
        print(f"\n📋 Tablas de enrutamiento:")
        for nodo in ['A', 'D', 'F']:
            print(f"\n--- Nodo {nodo} ---")
            self.mostrar_tabla_nodo(nodo)
    
    def menu_interactivo(self):
        """Menú interactivo para experimentar con Link State"""
        
        while True:
            print("\n" + "="*60)
            print("DEMO INTERACTIVO - ALGORITMO LINK STATE")
            print("="*60)
            print("1. Inicializar/Reiniciar red")
            print("2. Mostrar tabla de un nodo")
            print("3. Mostrar ruta específica")
            print("4. Cambiar costo de enlace")
            print("5. Eliminar enlace")
            print("6. Agregar enlace")
            print("7. Comparar con Dijkstra estático")
            print("8. Mostrar estado completo de la red")
            print("9. Escenarios predefinidos")
            print("0. Salir")
            print("-" * 60)
            
            try:
                opcion = input("Selecciona una opción (0-9): ").strip()
                
                if opcion == "0":
                    print("👋 ¡Hasta luego!")
                    break
                    
                elif opcion == "1":
                    self.inicializar_red()
                    
                elif opcion == "2":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    nodo = input("Ingresa el nodo (A-I): ").strip().upper()
                    self.mostrar_tabla_nodo(nodo)
                    
                elif opcion == "3":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    origen = input("Nodo origen (A-I): ").strip().upper()
                    destino = input("Nodo destino (A-I): ").strip().upper()
                    self.mostrar_ruta(origen, destino)
                    
                elif opcion == "4":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    nodo1 = input("Primer nodo del enlace: ").strip().upper()
                    nodo2 = input("Segundo nodo del enlace: ").strip().upper()
                    try:
                        costo = int(input("Nuevo costo: "))
                        self.cambiar_enlace(nodo1, nodo2, costo)
                    except ValueError:
                        print("❌ El costo debe ser un número entero")
                        
                elif opcion == "5":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    nodo1 = input("Primer nodo del enlace: ").strip().upper()
                    nodo2 = input("Segundo nodo del enlace: ").strip().upper()
                    self.eliminar_enlace(nodo1, nodo2)
                    
                elif opcion == "6":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    nodo1 = input("Primer nodo del enlace: ").strip().upper()
                    nodo2 = input("Segundo nodo del enlace: ").strip().upper()
                    try:
                        costo = int(input("Costo del enlace: "))
                        self.agregar_enlace(nodo1, nodo2, costo)
                    except ValueError:
                        print("❌ El costo debe ser un número entero")
                        
                elif opcion == "7":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    self.comparar_con_dijkstra_estatico()
                    
                elif opcion == "8":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    self.mostrar_estado_completo()
                    
                elif opcion == "9":
                    if not self.nodos:
                        print("❌ Primero inicializa la red (opción 1)")
                        continue
                    self.ejecutar_escenarios_predefinidos()
                    
                else:
                    print("❌ Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
            # Pausa para que el usuario pueda leer
            input("\nPresiona Enter para continuar...")
    
    def ejecutar_escenarios_predefinidos(self):
        """Ejecuta escenarios predefinidos interesantes"""
        
        print("\n🎬 ESCENARIOS PREDEFINIDOS")
        print("="*40)
        print("1. Falla del enlace F-H")
        print("2. Mejora del enlace A-C")
        print("3. Partición de red (desconectar I)")
        print("4. Nuevo enlace E-H")
        
        try:
            escenario = input("Selecciona escenario (1-4): ").strip()
            
            if escenario == "1":
                print("\n🔥 Simulando falla del enlace F-H")
                print("Estado antes:")
                self.mostrar_ruta("A", "H")
                self.eliminar_enlace("F", "H")
                print("Estado después:")
                self.mostrar_ruta("A", "H")
                
            elif escenario == "2":
                print("\n⚡ Mejorando enlace A-C (7 -> 2)")
                print("Estado antes:")
                self.mostrar_ruta("A", "E")
                self.cambiar_enlace("A", "C", 2)
                print("Estado después:")
                self.mostrar_ruta("A", "E")
                
            elif escenario == "3":
                print("\n🚫 Desconectando nodo I")
                print("Estado antes:")
                self.mostrar_ruta("A", "I")
                self.eliminar_enlace("I", "A")
                self.eliminar_enlace("I", "D")
                print("Estado después:")
                self.mostrar_ruta("A", "I")
                
            elif escenario == "4":
                print("\n➕ Agregando enlace directo E-H con costo 3")
                print("Estado antes:")
                self.mostrar_ruta("E", "H")
                self.agregar_enlace("E", "H", 3)
                print("Estado después:")
                self.mostrar_ruta("E", "H")
                
            else:
                print("❌ Escenario no válido")
                
        except Exception as e:
            print(f"❌ Error en escenario: {e}")

def main():
    """Función principal"""
    demo = LinkStateDemo()
    
    print("🚀 BIENVENIDO AL DEMO DE LINK STATE")
    print("="*50)
    print("Este demo te permite experimentar con el algoritmo")
    print("de enrutamiento Link State de forma interactiva.")
    print("¡Prueba diferentes cambios en la red y observa")
    print("cómo se actualiza el enrutamiento automáticamente!")
    
    demo.menu_interactivo()

if __name__ == "__main__":
    main()
