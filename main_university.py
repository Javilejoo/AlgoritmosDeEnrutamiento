"""
Interfaz principal para el protocolo universitario
Menú unificado para manejar nodos con protocolo específico
"""

import asyncio
import json
import os
from university_network_manager import UniversityNetworkManager
from university_node import UniversityNode

class UniversityInterface:
    """Interfaz principal para el protocolo universitario"""
    
    def __init__(self):
        self.manager = UniversityNetworkManager()
        self.running = True
    
    def show_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*60)
        print("🎓 PROTOCOLO UNIVERSITARIO - ALGORITMOS DE ENRUTAMIENTO")
        print("="*60)
        print("1.  Crear nueva red")
        print("2.  Cargar red desde archivo")
        print("3.  Agregar nodo a red actual")
        print("4.  Agregar conexión entre nodos")
        print("5.  Iniciar red completa")
        print("6.  Enviar mensajes INIT")
        print("7.  Calcular rutas (todos los nodos)")
        print("8.  Enviar mensajes de prueba")
        print("9.  Mostrar estado de la red")
        print("10. Ejecutar protocolo completo")
        print("11. Demo flooding vs LSR")
        print("12. Simular falla de nodo")
        print("13. Guardar configuración")
        print("14. Crear red predefinida")
        print("15. Monitor en tiempo real")
        print("0.  Salir")
        print("-"*60)
    
    async def run(self):
        """Ejecuta la interfaz principal"""
        print("🎓 Bienvenido al sistema de protocolo universitario")
        
        while self.running:
            self.show_menu()
            choice = input("Seleccione una opción: ").strip()
            
            try:
                await self.handle_choice(choice)
            except KeyboardInterrupt:
                print("\n🛑 Detenido por usuario")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def handle_choice(self, choice: str):
        """Maneja la opción seleccionada"""
        if choice == "1":
            await self.create_new_network()
        elif choice == "2":
            await self.load_network()
        elif choice == "3":
            await self.add_node()
        elif choice == "4":
            await self.add_connection()
        elif choice == "5":
            await self.start_network()
        elif choice == "6":
            await self.send_init_messages()
        elif choice == "7":
            await self.calculate_routes()
        elif choice == "8":
            await self.send_test_messages()
        elif choice == "9":
            self.show_network_status()
        elif choice == "10":
            await self.run_complete_protocol()
        elif choice == "11":
            await self.demo_algorithms()
        elif choice == "12":
            await self.simulate_node_failure()
        elif choice == "13":
            self.save_configuration()
        elif choice == "14":
            await self.create_predefined_network()
        elif choice == "15":
            await self.real_time_monitor()
        elif choice == "0":
            await self.exit_program()
        else:
            print("❌ Opción inválida")
    
    async def create_new_network(self):
        """Crea una nueva red"""
        print("\n🆕 Creando nueva red...")
        self.manager = UniversityNetworkManager()
        print("✅ Nueva red creada")
    
    async def load_network(self):
        """Carga red desde archivo"""
        filename = input("Archivo de configuración: ").strip()
        
        if os.path.exists(filename):
            try:
                self.manager = UniversityNetworkManager.load_network_config(filename)
                print("✅ Red cargada exitosamente")
            except Exception as e:
                print(f"❌ Error cargando red: {e}")
        else:
            print("❌ Archivo no encontrado")
    
    async def add_node(self):
        """Agrega un nodo a la red"""
        print("\n➕ Agregando nodo...")
        
        node_id = input("ID del nodo: ").strip().upper()
        
        try:
            port = int(input("Puerto (ejemplo: 65000): "))
            algorithm = input("Algoritmo (flooding/lsr): ").strip().lower()
            
            if algorithm not in ["flooding", "lsr"]:
                print("❌ Algoritmo debe ser 'flooding' o 'lsr'")
                return
            
            self.manager.add_node(node_id, port, algorithm)
            print(f"✅ Nodo {node_id} agregado")
            
        except ValueError:
            print("❌ Puerto debe ser un número")
    
    async def add_connection(self):
        """Agrega conexión entre nodos"""
        print("\n🔗 Agregando conexión...")
        
        if len(self.manager.nodes) < 2:
            print("❌ Se necesitan al menos 2 nodos")
            return
        
        print("Nodos disponibles:", list(self.manager.nodes.keys()))
        
        node1 = input("Primer nodo: ").strip().upper()
        node2 = input("Segundo nodo: ").strip().upper()
        
        if node1 not in self.manager.nodes or node2 not in self.manager.nodes:
            print("❌ Uno o ambos nodos no existen")
            return
        
        try:
            cost = int(input("Costo de la conexión: "))
            self.manager.add_connection(node1, node2, cost)
            print(f"✅ Conexión {node1} <-> {node2} agregada")
        except ValueError:
            print("❌ Costo debe ser un número")
    
    async def start_network(self):
        """Inicia la red completa"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n🚀 Iniciando red...")
        await self.manager.start_network()
        print("✅ Red iniciada")
    
    async def send_init_messages(self):
        """Envía mensajes INIT"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n📢 Enviando mensajes INIT...")
        await self.manager.initialize_network()
        print("✅ Mensajes INIT enviados")
    
    async def calculate_routes(self):
        """Calcula rutas en todos los nodos"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n🔄 Calculando rutas...")
        await self.manager.calculate_all_routes()
        await self.manager.wait_for_convergence()
        print("✅ Rutas calculadas")
    
    async def send_test_messages(self):
        """Envía mensajes de prueba"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n📤 Enviando mensajes de prueba...")
        await self.manager.send_test_messages()
        print("✅ Mensajes enviados")
    
    def show_network_status(self):
        """Muestra estado de la red"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        self.manager.print_network_status()
    
    async def run_complete_protocol(self):
        """Ejecuta el protocolo completo"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n🎯 Ejecutando protocolo completo...")
        
        await self.manager.start_network()
        await asyncio.sleep(2)
        
        await self.manager.initialize_network()
        await asyncio.sleep(3)
        
        await self.manager.calculate_all_routes()
        await self.manager.wait_for_convergence()
        await asyncio.sleep(2)
        
        await self.manager.send_test_messages()
        await asyncio.sleep(5)
        
        self.manager.print_network_status()
        print("✅ Protocolo completo ejecutado")
    
    async def demo_algorithms(self):
        """Demo comparando flooding vs LSR"""
        print("\n🆚 Demo: Flooding vs LSR")
        
        # Crear red temporal
        temp_manager = UniversityNetworkManager()
        
        # Red con nodos flooding y LSR
        temp_manager.add_node("F1", 65601, "flooding")
        temp_manager.add_node("F2", 65602, "flooding")  
        temp_manager.add_node("L1", 65603, "lsr")
        temp_manager.add_node("L2", 65604, "lsr")
        
        temp_manager.add_connection("F1", "F2", 5)
        temp_manager.add_connection("F2", "L1", 3)
        temp_manager.add_connection("L1", "L2", 7)
        temp_manager.add_connection("L2", "F1", 4)
        
        try:
            await temp_manager.start_network()
            await temp_manager.initialize_network()
            await asyncio.sleep(3)
            
            await temp_manager.calculate_all_routes()
            await temp_manager.wait_for_convergence()
            await asyncio.sleep(2)
            
            # Enviar mensaje específico
            await temp_manager.nodes["F1"].send_user_message(
                "L2", "Mensaje desde Flooding hacia LSR"
            )
            
            await asyncio.sleep(3)
            temp_manager.print_network_status()
            
        finally:
            await temp_manager.stop_network()
    
    async def simulate_node_failure(self):
        """Simula falla de un nodo"""
        if len(self.manager.nodes) < 2:
            print("❌ Se necesitan al menos 2 nodos")
            return
        
        print("\nNodos disponibles:", list(self.manager.nodes.keys()))
        node_id = input("Nodo a fallar: ").strip().upper()
        
        if node_id not in self.manager.nodes:
            print("❌ Nodo no existe")
            return
        
        print(f"💥 Simulando falla del nodo {node_id}...")
        
        # Detener el nodo
        await self.manager.nodes[node_id].stop()
        
        # Remover de conexiones de otros nodos
        for other_node in self.manager.nodes.values():
            if node_id in other_node.neighbours:
                del other_node.neighbours[node_id]
            if node_id in other_node.neighbor_connections:
                del other_node.neighbor_connections[node_id]
        
        print(f"❌ Nodo {node_id} falló")
        await asyncio.sleep(2)
        
        # Recalcular rutas
        await self.calculate_routes()
    
    def save_configuration(self):
        """Guarda configuración actual"""
        if not self.manager.nodes:
            print("❌ No hay nodos para guardar")
            return
        
        filename = input("Nombre del archivo: ").strip()
        if not filename.endswith(".json"):
            filename += ".json"
        
        self.manager.save_network_config(filename)
    
    async def create_predefined_network(self):
        """Crea una red predefinida"""
        print("\n🏗️ Redes predefinidas:")
        print("1. Red lineal (A-B-C-D)")
        print("2. Red en anillo (A-B-C-D-A)")
        print("3. Red en estrella (B al centro)")
        print("4. Red completa (todos conectados)")
        
        choice = input("Seleccione red: ").strip()
        
        # Crear nueva red
        self.manager = UniversityNetworkManager()
        
        if choice == "1":
            # Red lineal
            self.manager.add_node("A", 65701, "flooding")
            self.manager.add_node("B", 65702, "lsr")
            self.manager.add_node("C", 65703, "flooding")
            self.manager.add_node("D", 65704, "lsr")
            
            self.manager.add_connection("A", "B", 5)
            self.manager.add_connection("B", "C", 3)
            self.manager.add_connection("C", "D", 7)
            
        elif choice == "2":
            # Red en anillo
            self.manager.add_node("A", 65711, "flooding")
            self.manager.add_node("B", 65712, "lsr")
            self.manager.add_node("C", 65713, "flooding")
            self.manager.add_node("D", 65714, "lsr")
            
            self.manager.add_connection("A", "B", 5)
            self.manager.add_connection("B", "C", 3)
            self.manager.add_connection("C", "D", 7)
            self.manager.add_connection("D", "A", 4)
            
        elif choice == "3":
            # Red en estrella
            self.manager.add_node("A", 65721, "flooding")
            self.manager.add_node("B", 65722, "lsr")  # Centro
            self.manager.add_node("C", 65723, "flooding")
            self.manager.add_node("D", 65724, "lsr")
            
            self.manager.add_connection("B", "A", 5)
            self.manager.add_connection("B", "C", 3)
            self.manager.add_connection("B", "D", 7)
            
        elif choice == "4":
            # Red completa
            self.manager.add_node("A", 65731, "flooding")
            self.manager.add_node("B", 65732, "lsr")
            self.manager.add_node("C", 65733, "flooding")
            
            self.manager.add_connection("A", "B", 5)
            self.manager.add_connection("B", "C", 3)
            self.manager.add_connection("A", "C", 8)
        
        else:
            print("❌ Opción inválida")
            return
        
        print("✅ Red predefinida creada")
    
    async def real_time_monitor(self):
        """Monitor en tiempo real"""
        if not self.manager.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n📡 Monitor en tiempo real (Ctrl+C para detener)")
        print("Actualizando cada 3 segundos...")
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("📡 MONITOR EN TIEMPO REAL")
                print("="*50)
                
                for node_id, node in self.manager.nodes.items():
                    print(f"\n🔷 NODO {node_id} ({node.algorithm})")
                    print(f"   Mensajes enviados: {node.messages_sent}")
                    print(f"   Mensajes recibidos: {node.messages_received}")
                    print(f"   Estado: {'✅ Terminado' if node.calculation_done else '🔄 Calculando'}")
                
                await asyncio.sleep(3)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido")
    
    async def exit_program(self):
        """Sale del programa"""
        print("\n🛑 Cerrando programa...")
        
        if self.manager.nodes:
            await self.manager.stop_network()
        
        self.running = False
        print("👋 ¡Hasta luego!")

# Punto de entrada principal
async def main():
    """Función principal"""
    interface = UniversityInterface()
    await interface.run()

if __name__ == "__main__":
    print("🎓 INICIANDO SISTEMA UNIVERSITARIO...")
    asyncio.run(main())
