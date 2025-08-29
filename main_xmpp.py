"""
Interfaz principal unificada para el proyecto de algoritmos de enrutamiento
Incluye soporte para XMPP y todos los algoritmos implementados
"""

import asyncio
import sys
import os
from typing import List, Optional

# Importar módulos del proyecto
from config_manager import ConfigManager
from test_coordinator import TestCoordinator, TestScenarios
from routing_algorithms import RoutingNodeFactory
from protocolo import MessageFactory

class UnifiedInterface:
    """Interfaz principal unificada del proyecto"""
    
    def __init__(self):
        self.current_coordinator = None
        
    def show_main_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*70)
        print("  ALGORITMOS DE ENRUTAMIENTO - LABORATORIO REDES")
        print("         Implementaciones: Dijkstra, Flooding, LSR, XMPP")
        print("="*70)
        print()
        print("🔧 CONFIGURACIÓN Y SETUP:")
        print("  1. Crear archivos de configuración")
        print("  2. Generar escenarios de prueba")
        print()
        print("🎯 ALGORITMOS CLÁSICOS (Local):")
        print("  3. Dijkstra centralizado")
        print("  4. Flooding puro (demo interactivo)")
        print("  5. Sistema distribuido con terminales")
        print("  6. Link State clásico (simulación)")
        print()
        print("🌐 ALGORITMOS CON XMPP:")
        print("  7. Prueba Flooding con XMPP")
        print("  8. Prueba LSR con XMPP")
        print("  9. Prueba completa de conectividad")
        print(" 10. Simulación de fallas y recuperación")
        print()
        print("📊 TESTING Y EVALUACIÓN:")
        print(" 11. Comparar algoritmos")
        print(" 12. Análisis de rendimiento")
        print(" 13. Generar reportes")
        print()
        print("🚀 DEMOS Y TUTORIALES:")
        print(" 14. Demo interactivo básico")
        print(" 15. Tutorial XMPP paso a paso")
        print(" 16. Simulación completa de red")
        print()
        print(" 0. Salir")
        print("-"*70)
    
    async def handle_choice(self, choice: str):
        """Maneja la selección del usuario"""
        try:
            if choice == '1':
                await self.create_config_files()
            elif choice == '2':
                await self.generate_test_scenarios()
            elif choice == '3':
                await self.run_centralized_dijkstra()
            elif choice == '4':
                await self.run_flooding_demo()
            elif choice == '5':
                await self.run_distributed_terminals()
            elif choice == '6':
                await self.run_classic_link_state()
            elif choice == '7':
                await self.test_flooding_xmpp()
            elif choice == '8':
                await self.test_lsr_xmpp()
            elif choice == '9':
                await self.test_full_connectivity()
            elif choice == '10':
                await self.test_failure_recovery()
            elif choice == '11':
                await self.compare_algorithms()
            elif choice == '12':
                await self.performance_analysis()
            elif choice == '13':
                await self.generate_reports()
            elif choice == '14':
                await self.interactive_demo()
            elif choice == '15':
                await self.xmpp_tutorial()
            elif choice == '16':
                await self.full_network_simulation()
            elif choice == '0':
                print("👋 ¡Hasta luego!")
                return False
            else:
                print("❌ Opción no válida")
                
        except Exception as e:
            print(f"❌ Error ejecutando opción: {e}")
            import traceback
            traceback.print_exc()
        
        return True
    
    # Implementación de cada opción
    
    async def create_config_files(self):
        """Opción 1: Crear archivos de configuración"""
        print("\n🔧 CREANDO ARCHIVOS DE CONFIGURACIÓN")
        print("-" * 40)
        
        ConfigManager.create_config_files()
        
        print("\n✅ Archivos creados:")
        print("   📁 topology.json - Topología de red")
        print("   📁 nodes.json - Configuración de nodos")
        print("\n💡 Puedes editar estos archivos para personalizar la red")
    
    async def generate_test_scenarios(self):
        """Opción 2: Generar escenarios de prueba"""
        print("\n🎬 GENERANDO ESCENARIOS DE PRUEBA")
        print("-" * 40)
        
        from config_manager import ScenarioGenerator
        
        scenarios = {
            "linear_5": ScenarioGenerator.linear_topology(5),
            "ring_6": ScenarioGenerator.ring_topology(6),
            "star_7": ScenarioGenerator.star_topology(7),
            "mesh_4": ScenarioGenerator.mesh_topology(4)
        }
        
        for name, scenario in scenarios.items():
            ConfigManager.save_topology(scenario, f"scenario_{name}.json")
            print(f"   📁 scenario_{name}.json - {len(scenario.nodes)} nodos")
        
        print("\n✅ Escenarios generados para diferentes topologías")
    
    async def run_centralized_dijkstra(self):
        """Opción 3: Dijkstra centralizado"""
        print("\n🎯 EJECUTANDO DIJKSTRA CENTRALIZADO")
        print("-" * 40)
        
        import subprocess
        subprocess.run([sys.executable, "dijkstra.py"])
    
    async def run_distributed_terminals(self):
        """Opción 4: Sistema distribuido con terminales"""
        print("\n🖥️ SISTEMA DISTRIBUIDO CON TERMINALES")
        print("-" * 40)
        
        import subprocess
        subprocess.run([sys.executable, "abrir_nodos.py"])
    
    async def run_classic_link_state(self):
        """Opción 5: Link State clásico"""
        print("\n🌐 LINK STATE CLÁSICO")
        print("-" * 40)
        
        import subprocess
        subprocess.run([sys.executable, "demo_link_state.py"])
    
    async def run_flooding_demo(self):
        """Opción 4: Demo de flooding puro"""
        print("\n🌊 DEMO DE FLOODING PURO")
        print("-" * 40)
        
        import subprocess
        subprocess.run([sys.executable, "demo_flooding.py"])
    
    async def test_flooding_xmpp(self):
        """Opción 7: Prueba Flooding con XMPP"""
        print("\n� PRUEBA FLOODING CON XMPP")
        print("-" * 40)
        
        if not os.path.exists("topology.json"):
            print("⚠️ Creando archivos de configuración primero...")
            ConfigManager.create_config_files()
        
        # Usar modo offline para demo
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        # Crear nodos Flooding
        test_nodes = ["A", "B", "C", "D"]
        await coordinator.create_nodes(test_nodes)
        
        # Cambiar algoritmo a Flooding
        for node_id, node in coordinator.nodes.items():
            # Reemplazar con nodo Flooding
            new_node = RoutingNodeFactory.create_node(
                "flooding", node_id, node.jid, node.password, use_xmpp=False
            )
            new_node.neighbors = node.neighbors
            new_node.topology = node.topology
            coordinator.nodes[node_id] = new_node
        
        await coordinator.start_network()
        
        print("⏳ Probando Flooding (30 segundos)...")
        await asyncio.sleep(30)
        
        results = await coordinator.run_flooding_test()
        
        avg_coverage = sum(t['coverage'] for t in results['flooding_tests']) / len(results['flooding_tests'])
        print(f"\n📊 RESULTADOS FLOODING:")
        print(f"   Cobertura promedio: {avg_coverage:.1f}%")
        
        await coordinator.stop_network()
        self.current_coordinator = coordinator
    
    async def test_lsr_xmpp(self):
        """Opción 8: Prueba LSR con XMPP"""
        print("\n🌐 PRUEBA LSR CON XMPP")
        print("-" * 40)
        
        if not os.path.exists("topology.json"):
            ConfigManager.create_config_files()
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        test_nodes = ["A", "B", "C", "D"]
        await coordinator.create_nodes(test_nodes)
        
        # Cambiar algoritmo a LSR
        for node_id, node in coordinator.nodes.items():
            new_node = RoutingNodeFactory.create_node(
                "lsr", node_id, node.jid, node.password, use_xmpp=False
            )
            new_node.neighbors = node.neighbors
            new_node.topology = node.topology
            coordinator.nodes[node_id] = new_node
        
        await coordinator.start_network()
        
        print("⏳ Probando LSR (30 segundos)...")
        await asyncio.sleep(30)
        
        results = await coordinator.run_connectivity_test()
        
        success_rate = (results['successful_deliveries'] / results['total_tests']) * 100
        print(f"\n📊 RESULTADOS LSR:")
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        print(f"   Entregas: {results['successful_deliveries']}/{results['total_tests']}")
        
        await coordinator.stop_network()
        self.current_coordinator = coordinator
    
    async def test_full_connectivity(self):
        """Opción 9: Prueba completa de conectividad"""
        print("\n🔍 PRUEBA COMPLETA DE CONECTIVIDAD")
        print("-" * 40)
        
        if not os.path.exists("topology.json"):
            ConfigManager.create_config_files()
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        # Usar todos los nodos
        await coordinator.create_nodes()
        await coordinator.start_network()
        
        print("🧪 Ejecutando pruebas completas...")
        results = await TestScenarios.comprehensive_test(coordinator)
        
        print("\n📊 RESULTADOS COMPLETOS:")
        for result in results:
            test_type = result.get('type', 'unknown')
            print(f"\n   {test_type.upper()}:")
            
            if 'successful_deliveries' in result:
                success_rate = (result['successful_deliveries'] / result['total_tests']) * 100
                print(f"     Tasa de éxito: {success_rate:.1f}%")
                
            if 'flooding_tests' in result:
                avg_coverage = sum(t['coverage'] for t in result['flooding_tests']) / len(result['flooding_tests'])
                print(f"     Cobertura promedio: {avg_coverage:.1f}%")
                
            if 'messages_sent' in result:
                print(f"     Mensajes enviados: {result['messages_sent']}")
        
        # Guardar resultados
        coordinator.save_results(results, "connectivity_test_results.json")
        
        await coordinator.stop_network()
        self.current_coordinator = coordinator
    
    async def test_failure_recovery(self):
        """Opción 10: Simulación de fallas y recuperación"""
        print("\n💥 SIMULACIÓN DE FALLAS Y RECUPERACIÓN")
        print("-" * 40)
        
        if not os.path.exists("topology.json"):
            ConfigManager.create_config_files()
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        test_nodes = ["A", "B", "C", "D", "F"]  # Nodos con buena conectividad
        await coordinator.create_nodes(test_nodes)
        await coordinator.start_network()
        
        print("🧪 Ejecutando pruebas de fallas...")
        results = await TestScenarios.failure_recovery_test(coordinator)
        
        print("\n📊 RESULTADOS DE RECUPERACIÓN:")
        for result in results:
            test_type = result.get('type', 'unknown')
            if 'successful_deliveries' in result:
                success_rate = (result['successful_deliveries'] / result['total_tests']) * 100
                print(f"   {test_type}: {success_rate:.1f}% éxito")
        
        await coordinator.stop_network()
        self.current_coordinator = coordinator
    
    async def compare_algorithms(self):
        """Opción 11: Comparar algoritmos"""
        print("\n⚖️ COMPARACIÓN DE ALGORITMOS")
        print("-" * 40)
        
        algorithms = ["dijkstra", "flooding", "lsr"]
        results = {}
        
        for algo in algorithms:
            print(f"\n🧪 Probando {algo.upper()}...")
            
            coordinator = TestCoordinator(use_xmpp=False)
            coordinator.load_configuration("topology.json", "nodes.json")
            
            test_nodes = ["A", "B", "C", "D"]
            await coordinator.create_nodes(test_nodes)
            
            # Configurar algoritmo
            if algo != "dijkstra":
                for node_id, node in coordinator.nodes.items():
                    new_node = RoutingNodeFactory.create_node(
                        algo, node_id, node.jid, node.password, use_xmpp=False
                    )
                    new_node.neighbors = node.neighbors
                    new_node.topology = node.topology
                    coordinator.nodes[node_id] = new_node
            
            await coordinator.start_network()
            await asyncio.sleep(20)  # Tiempo para convergencia
            
            if algo == "flooding":
                test_result = await coordinator.run_flooding_test()
                avg_coverage = sum(t['coverage'] for t in test_result['flooding_tests']) / len(test_result['flooding_tests'])
                results[algo] = {"coverage": avg_coverage, "type": "flooding"}
            else:
                test_result = await coordinator.run_connectivity_test()
                results[algo] = test_result
            
            await coordinator.stop_network()
        
        print("\n📊 COMPARACIÓN FINAL:")
        print("-" * 40)
        for algo, result in results.items():
            if result.get("type") == "flooding":
                print(f"   {algo.upper()}: {result['coverage']:.1f}% cobertura")
            else:
                success_rate = (result['successful_deliveries'] / result['total_tests']) * 100
                print(f"   {algo.upper()}: {success_rate:.1f}% éxito")
    
    async def performance_analysis(self):
        """Opción 12: Análisis de rendimiento"""
        print("\n⚡ ANÁLISIS DE RENDIMIENTO")
        print("-" * 40)
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        await coordinator.create_nodes(["A", "B", "C", "D", "F"])
        await coordinator.start_network()
        
        print("⏳ Ejecutando prueba de rendimiento (60 segundos)...")
        results = await coordinator.run_performance_test(60)
        
        print(f"\n📊 RESULTADOS DE RENDIMIENTO:")
        print(f"   Mensajes enviados: {results['messages_sent']}")
        print(f"   Duración: {results['duration']} segundos")
        print(f"   Tasa: {results['messages_sent']/results['duration']:.2f} msg/seg")
        
        print("\n   Por nodo:")
        for node_id, stats in results['node_stats'].items():
            print(f"     {node_id}: {stats['packets_forwarded']} reenviados, {stats['packets_received']} recibidos")
        
        await coordinator.stop_network()
    
    async def generate_reports(self):
        """Opción 13: Generar reportes"""
        print("\n📋 GENERANDO REPORTES")
        print("-" * 40)
        
        if self.current_coordinator:
            print("📝 Generando reporte del último test...")
            # Usar resultados del último coordinator
            report = self.current_coordinator.generate_test_report([])
            
            with open("test_report.txt", "w") as f:
                f.write(report)
            
            print("✅ Reporte guardado en test_report.txt")
        else:
            print("⚠️ No hay datos de pruebas recientes")
            print("💡 Ejecuta alguna prueba primero (opciones 7-10)")
    
    async def interactive_demo(self):
        """Opción 14: Demo interactivo básico"""
        print("\n🎮 DEMO INTERACTIVO BÁSICO")
        print("-" * 40)
        
        print("¿Qué te gustaría ver?")
        print("1. Envío de mensaje simple")
        print("2. Convergencia de algoritmo")
        print("3. Efecto de falla de nodo")
        
        choice = input("Opción (1-3): ").strip()
        
        if choice == "1":
            await self._demo_simple_message()
        elif choice == "2":
            await self._demo_convergence()
        elif choice == "3":
            await self._demo_node_failure()
        else:
            print("❌ Opción no válida")
    
    async def _demo_simple_message(self):
        """Demo de envío de mensaje simple"""
        print("\n📨 DEMO: Envío de mensaje simple")
        
        # Crear 2 nodos simples
        from routing_node import NeighborInfo
        import time
        
        node_a = RoutingNodeFactory.create_node("lsr", "A", "a@demo", "pass", use_xmpp=False)
        node_b = RoutingNodeFactory.create_node("lsr", "B", "b@demo", "pass", use_xmpp=False)
        
        # Conectarlos como vecinos
        node_a.neighbors["b@demo"] = NeighborInfo("b@demo", 1, time.time())
        node_b.neighbors["a@demo"] = NeighborInfo("a@demo", 1, time.time())
        
        await node_a.start()
        await node_b.start()
        
        print("✅ Nodos A y B iniciados")
        print("📤 A enviando mensaje a B...")
        
        await node_a.send_user_message("B", "¡Hola desde A!")
        
        await asyncio.sleep(3)
        
        print(f"📊 Estado final:")
        print(f"   A: {node_a.packets_forwarded} enviados")
        print(f"   B: {node_b.packets_received} recibidos")
        
        await node_a.stop()
        await node_b.stop()
    
    async def _demo_convergence(self):
        """Demo de convergencia de algoritmo"""
        print("\n🔄 DEMO: Convergencia LSR")
        
        # Crear pequeña red LSR
        nodes = {}
        for node_id in ["A", "B", "C"]:
            nodes[node_id] = RoutingNodeFactory.create_node(
                "lsr", node_id, f"{node_id}@demo", "pass", use_xmpp=False
            )
        
        # Topología lineal A-B-C
        from routing_node import NeighborInfo
        import time
        
        nodes["A"].neighbors["B@demo"] = NeighborInfo("B@demo", 1, time.time())
        nodes["B"].neighbors["A@demo"] = NeighborInfo("A@demo", 1, time.time())
        nodes["B"].neighbors["C@demo"] = NeighborInfo("C@demo", 2, time.time())
        nodes["C"].neighbors["B@demo"] = NeighborInfo("B@demo", 2, time.time())
        
        print("🚀 Iniciando red A-B-C...")
        for node in nodes.values():
            await node.start()
        
        print("⏳ Observando convergencia (20 segundos)...")
        
        for i in range(4):
            await asyncio.sleep(5)
            updates = sum(node.routing_updates for node in nodes.values())
            print(f"   t={5*(i+1)}s: {updates} actualizaciones totales")
        
        print("✅ Convergencia observada")
        
        for node in nodes.values():
            await node.stop()
    
    async def _demo_node_failure(self):
        """Demo de falla de nodo"""
        print("\n💥 DEMO: Falla y recuperación de nodo")
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        await coordinator.create_nodes(["A", "B", "C", "D"])
        await coordinator.start_network()
        
        print("✅ Red iniciada")
        print("📊 Probando conectividad inicial...")
        
        initial = await coordinator.run_connectivity_test()
        initial_success = (initial['successful_deliveries'] / initial['total_tests']) * 100
        
        print(f"   Éxito inicial: {initial_success:.1f}%")
        print("💥 Simulando falla del nodo B...")
        
        await coordinator.simulate_node_failure("B", 15)
        
        print("📊 Probando conectividad final...")
        final = await coordinator.run_connectivity_test()
        final_success = (final['successful_deliveries'] / final['total_tests']) * 100
        
        print(f"   Éxito final: {final_success:.1f}%")
        print("🔄 Red recuperada")
        
        await coordinator.stop_network()
    
    async def xmpp_tutorial(self):
        """Opción 15: Tutorial XMPP paso a paso"""
        print("\n📚 TUTORIAL XMPP PASO A PASO")
        print("-" * 40)
        
        print("Este tutorial te guía para usar XMPP real:")
        print()
        print("1️⃣ INSTALAR DEPENDENCIAS:")
        print("   pip install slixmpp")
        print()
        print("2️⃣ CONFIGURAR SERVIDOR XMPP:")
        print("   - Instalar ejabberd o usar servidor existente")
        print("   - Crear cuentas: node_a@servidor.com, node_b@servidor.com, etc.")
        print()
        print("3️⃣ MODIFICAR CONFIGURACIÓN:")
        print("   - Editar nodes.json con JIDs reales")
        print("   - Configurar contraseñas")
        print()
        print("4️⃣ EJECUTAR CON XMPP:")
        print("   - Cambiar use_xmpp=True en test_coordinator.py")
        print("   - Ejecutar pruebas (opciones 7-10)")
        print()
        print("💡 Para desarrollo local, usa use_xmpp=False (modo actual)")
    
    async def full_network_simulation(self):
        """Opción 16: Simulación completa de red"""
        print("\n🌐 SIMULACIÓN COMPLETA DE RED")
        print("-" * 40)
        
        print("🏗️ Configurando simulación completa...")
        
        if not os.path.exists("topology.json"):
            ConfigManager.create_config_files()
        
        coordinator = TestCoordinator(use_xmpp=False)
        coordinator.load_configuration("topology.json", "nodes.json")
        
        # Usar toda la topología
        await coordinator.create_nodes()
        await coordinator.start_network()
        
        print(f"✅ Red completa iniciada: {len(coordinator.nodes)} nodos")
        
        # Ejecutar suite completa de pruebas
        print("\n🧪 Ejecutando suite completa...")
        
        all_results = []
        
        # 1. Conectividad básica
        print("   📡 Prueba de conectividad...")
        connectivity = await coordinator.run_connectivity_test()
        connectivity["type"] = "connectivity"
        all_results.append(connectivity)
        
        # 2. Flooding
        print("   🌊 Prueba de flooding...")
        flooding = await coordinator.run_flooding_test()
        flooding["type"] = "flooding"
        all_results.append(flooding)
        
        # 3. Rendimiento
        print("   ⚡ Prueba de rendimiento...")
        performance = await coordinator.run_performance_test(45)
        performance["type"] = "performance"
        all_results.append(performance)
        
        # 4. Recuperación ante fallas
        print("   💥 Prueba de fallas...")
        failure_tests = await TestScenarios.failure_recovery_test(coordinator)
        all_results.extend(failure_tests)
        
        # Generar reporte completo
        print("\n📋 Generando reporte completo...")
        report = coordinator.generate_test_report(all_results)
        
        with open("simulation_complete_report.txt", "w") as f:
            f.write(report)
        
        coordinator.save_results(all_results, "simulation_complete_results.json")
        
        print("\n📊 RESUMEN DE SIMULACIÓN COMPLETA:")
        for result in all_results:
            test_type = result.get('type', 'unknown')
            if 'successful_deliveries' in result:
                success_rate = (result['successful_deliveries'] / result['total_tests']) * 100
                print(f"   {test_type}: {success_rate:.1f}% éxito")
        
        print("\n✅ Simulación completa finalizada")
        print("📁 Archivos generados:")
        print("   - simulation_complete_report.txt")
        print("   - simulation_complete_results.json")
        
        await coordinator.stop_network()
        self.current_coordinator = coordinator

    async def run(self):
        """Ejecuta la interfaz principal"""
        print("🚀 Iniciando interfaz unificada...")
        
        # Verificar archivos básicos
        if not os.path.exists("topology.json"):
            print("⚠️ Archivos de configuración no encontrados")
            print("🔧 Creándolos automáticamente...")
            ConfigManager.create_config_files()
        
        while True:
            self.show_main_menu()
            choice = input("👉 Selecciona una opción: ").strip()
            
            if not await self.handle_choice(choice):
                break
            
            input("\n⏎ Presiona Enter para continuar...")

# Punto de entrada principal
if __name__ == "__main__":
    async def main():
        interface = UnifiedInterface()
        await interface.run()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
