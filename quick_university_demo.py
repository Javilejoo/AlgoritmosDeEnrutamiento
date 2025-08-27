"""
Inicio rápido para el protocolo universitario
Configuración automática para pruebas inmediatas
"""

import asyncio
from university_network_manager import UniversityNetworkManager

async def quick_demo():
    """Demo rápido del protocolo universitario"""
    print("🎓 === DEMO RÁPIDO PROTOCOLO UNIVERSITARIO ===\n")
    
    # Crear gestor
    manager = UniversityNetworkManager()
    
    # Crear red básica automáticamente
    print("🏗️ Creando red de ejemplo...")
    manager.add_node("A", 65801, "flooding")
    manager.add_node("B", 65802, "lsr")
    manager.add_node("C", 65803, "flooding")
    manager.add_node("D", 65804, "lsr")
    
    # Topología: A-B-C-D en línea con conexión A-C
    manager.add_connection("A", "B", 5)
    manager.add_connection("B", "C", 3)
    manager.add_connection("C", "D", 7)
    manager.add_connection("A", "C", 10)  # Ruta alternativa
    
    print("✅ Red creada con 4 nodos (A=flooding, B=lsr, C=flooding, D=lsr)")
    print("   Topología: A-B-C-D con conexión directa A-C\n")
    
    try:
        # 1. Iniciar red
        print("🚀 1. Iniciando todos los nodos...")
        await manager.start_network()
        await asyncio.sleep(2)
        
        # 2. Protocolo INIT
        print("📢 2. Enviando mensajes INIT...")
        await manager.initialize_network()
        await asyncio.sleep(3)
        
        # 3. Calcular rutas
        print("🔄 3. Calculando rutas...")
        await manager.calculate_all_routes()
        await manager.wait_for_convergence(10)
        await asyncio.sleep(2)
        
        # 4. Mostrar estado después de INIT y cálculos
        print("\n📊 ESTADO DESPUÉS DE INIT Y CÁLCULOS:")
        manager.print_network_status()
        
        # 5. Enviar mensajes de prueba
        print("\n📤 4. Enviando mensajes de prueba...")
        
        # Mensaje específico A -> D
        await manager.nodes["A"].send_user_message("D", "Hola desde A flooding hacia D lsr")
        await asyncio.sleep(1)
        
        # Mensaje específico D -> A
        await manager.nodes["D"].send_user_message("A", "Respuesta desde D lsr hacia A flooding")
        await asyncio.sleep(1)
        
        # Mensaje B -> C
        await manager.nodes["B"].send_user_message("C", "Mensaje LSR a Flooding")
        await asyncio.sleep(2)
        
        # 6. Estado final
        print("\n📈 ESTADO FINAL:")
        manager.print_network_status()
        
        # 7. Guardar configuración
        manager.save_network_config("demo_university_config.json")
        
        print("\n✅ Demo completado exitosamente!")
        print("💾 Configuración guardada en 'demo_university_config.json'")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        
    finally:
        print("\n🛑 Cerrando demo...")
        await manager.stop_network()

async def quick_flooding_test():
    """Prueba específica de flooding"""
    print("🌊 === PRUEBA ESPECÍFICA DE FLOODING ===\n")
    
    manager = UniversityNetworkManager()
    
    # Red solo con nodos flooding
    manager.add_node("F1", 65901, "flooding")
    manager.add_node("F2", 65902, "flooding")
    manager.add_node("F3", 65903, "flooding")
    manager.add_node("F4", 65904, "flooding")
    
    # Topología en anillo
    manager.add_connection("F1", "F2", 1)
    manager.add_connection("F2", "F3", 1)
    manager.add_connection("F3", "F4", 1)
    manager.add_connection("F4", "F1", 1)
    
    try:
        await manager.start_network()
        await manager.initialize_network()
        await asyncio.sleep(2)
        
        # Enviar mensaje que debe hacer flooding completo
        print("🌊 Enviando mensaje para flooding completo...")
        await manager.nodes["F1"].send_user_message("F3", "Mensaje con flooding por toda la red")
        
        await asyncio.sleep(3)
        manager.print_network_status()
        
    finally:
        await manager.stop_network()

async def quick_lsr_test():
    """Prueba específica de LSR"""
    print("📍 === PRUEBA ESPECÍFICA DE LSR ===\n")
    
    manager = UniversityNetworkManager()
    
    # Red solo con nodos LSR
    manager.add_node("L1", 66001, "lsr")
    manager.add_node("L2", 66002, "lsr")
    manager.add_node("L3", 66003, "lsr")
    manager.add_node("L4", 66004, "lsr")
    
    # Topología con diferentes costos
    manager.add_connection("L1", "L2", 10)  # Costo alto
    manager.add_connection("L2", "L3", 1)   # Costo bajo
    manager.add_connection("L3", "L4", 1)   # Costo bajo
    manager.add_connection("L1", "L4", 2)   # Ruta directa más eficiente
    
    try:
        await manager.start_network()
        await manager.initialize_network()
        await asyncio.sleep(3)
        
        await manager.calculate_all_routes()
        await manager.wait_for_convergence()
        await asyncio.sleep(2)
        
        # Mensaje que debe usar la ruta más eficiente L1->L4
        print("📍 Enviando mensaje que debe usar ruta óptima...")
        await manager.nodes["L1"].send_user_message("L4", "Mensaje LSR por ruta óptima")
        
        await asyncio.sleep(3)
        manager.print_network_status()
        
    finally:
        await manager.stop_network()

async def main():
    """Menú de demos rápidos"""
    print("🎓 DEMOS RÁPIDOS PROTOCOLO UNIVERSITARIO")
    print("="*50)
    print("1. Demo completo (flooding + LSR)")
    print("2. Prueba específica de flooding")
    print("3. Prueba específica de LSR")
    print("4. Interfaz completa")
    
    choice = input("\nSeleccione opción (1-4): ").strip()
    
    if choice == "1":
        await quick_demo()
    elif choice == "2":
        await quick_flooding_test()
    elif choice == "3":
        await quick_lsr_test()
    elif choice == "4":
        print("🚀 Iniciando interfaz completa...")
        from main_university import main as university_main
        await university_main()
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    asyncio.run(main())
