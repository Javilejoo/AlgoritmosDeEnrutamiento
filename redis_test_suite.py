"""
Sistema de testing automático para algoritmos de enrutamiento con Redis
Prueba Flooding y Link State Routing en diferentes topologías
"""

import asyncio
import json
import time
from typing import Dict, List
from redis_protocol import RedisProtocolNode

class RoutingTestSuite:
    """Suite de pruebas para algoritmos de enrutamiento"""
    
    def __init__(self, seccion: str = "sec20"):
        self.seccion = seccion
        self.nodes: Dict[str, RedisProtocolNode] = {}
        self.scenarios = self._load_scenarios()
        self.test_results = []
    
    def _load_scenarios(self) -> Dict:
        """Cargar escenarios de testing"""
        try:
            with open('redis_scenarios.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Archivo redis_scenarios.json no encontrado")
            return self._default_scenarios()
    
    def _default_scenarios(self) -> Dict:
        """Escenarios por defecto"""
        return {
            "topologias": {
                "simple": {
                    "descripcion": "Red simple A-B-C",
                    "nodos": {
                        "A": {"vecinos": {"B": 5}},
                        "B": {"vecinos": {"A": 5, "C": 3}},
                        "C": {"vecinos": {"B": 3}}
                    }
                }
            }
        }
    
    async def setup_topology(self, topologia_name: str) -> bool:
        """Configurar topología de prueba"""
        if topologia_name not in self.scenarios["topologias"]:
            print(f"❌ Topología {topologia_name} no encontrada")
            return False
        
        topologia = self.scenarios["topologias"][topologia_name]
        print(f"\n🌐 Configurando topología: {topologia['descripcion']}")
        
        # Crear nodos
        self.nodes = {}
        for node_id, config in topologia["nodos"].items():
            node = RedisProtocolNode(node_id, self.seccion, topologia_name)
            node.set_neighbours(config["vecinos"])
            self.nodes[node_id] = node
            print(f"  📍 Nodo {node_id}: {config['vecinos']}")
        
        # Conectar todos los nodos
        connected = 0
        for node_id, node in self.nodes.items():
            if await node.connect():
                connected += 1
            else:
                print(f"❌ Error conectando nodo {node_id}")
        
        if connected == len(self.nodes):
            print(f"✅ {connected} nodos conectados exitosamente")
            return True
        else:
            print(f"⚠️ Solo {connected}/{len(self.nodes)} nodos conectados")
            return False
    
    async def test_flooding_algorithm(self, topologia_name: str) -> Dict:
        """Probar algoritmo de Flooding"""
        print(f"\n🌊 PRUEBA: FLOODING en {topologia_name}")
        
        if not await self.setup_topology(topologia_name):
            return {"error": "No se pudo configurar topología"}
        
        # Configurar todos los nodos para flooding
        for node in self.nodes.values():
            node.set_algorithm("flooding")
        
        test_start = time.time()
        
        # Fase 1: Enviar mensajes INIT
        print("📤 Fase 1: Enviando mensajes INIT...")
        init_tasks = []
        for node in self.nodes.values():
            init_tasks.append(node.send_init_message())
        await asyncio.gather(*init_tasks)
        
        await asyncio.sleep(1)  # Esperar propagación
        
        # Fase 2: Enviar mensajes de prueba
        print("📤 Fase 2: Enviando mensajes de prueba...")
        
        # Cada nodo envía un mensaje a otro nodo
        message_tasks = []
        node_list = list(self.nodes.keys())
        
        for i, sender_id in enumerate(node_list):
            target_id = node_list[(i + 1) % len(node_list)]  # Siguiente nodo
            sender = self.nodes[sender_id]
            message = f"Flooding test from {sender_id} to {target_id}"
            message_tasks.append(sender.send_message(target_id, message))
        
        await asyncio.gather(*message_tasks)
        await asyncio.sleep(2)  # Esperar propagación
        
        # Fase 3: Finalizar
        print("📤 Fase 3: Enviando mensajes DONE...")
        done_tasks = []
        for node in self.nodes.values():
            done_tasks.append(node.send_done_message())
        await asyncio.gather(*done_tasks)
        
        test_duration = time.time() - test_start
        
        # Desconectar nodos
        await self._cleanup_nodes()
        
        result = {
            "algoritmo": "flooding",
            "topologia": topologia_name,
            "nodos": len(self.nodes),
            "duracion": test_duration,
            "exito": True,
            "detalles": "Flooding test completed successfully"
        }
        
        print(f"✅ Prueba Flooding completada en {test_duration:.2f}s")
        return result
    
    async def test_link_state_algorithm(self, topologia_name: str) -> Dict:
        """Probar algoritmo de Link State Routing"""
        print(f"\n🗺️ PRUEBA: LINK STATE ROUTING en {topologia_name}")
        
        if not await self.setup_topology(topologia_name):
            return {"error": "No se pudo configurar topología"}
        
        # Configurar todos los nodos para LSR
        for node in self.nodes.values():
            node.set_algorithm("link_state")
        
        test_start = time.time()
        
        # Fase 1: Intercambio de información de estado
        print("📤 Fase 1: Intercambiando información de estado...")
        init_tasks = []
        for node in self.nodes.values():
            init_tasks.append(node.send_init_message())
        await asyncio.gather(*init_tasks)
        
        await asyncio.sleep(2)  # Tiempo para cálculo de tablas
        
        # Fase 2: Enviar mensajes usando LSR
        print("📤 Fase 2: Enviando mensajes con LSR...")
        
        message_tasks = []
        node_list = list(self.nodes.keys())
        
        # Enviar mensajes entre todos los pares
        for sender_id in node_list:
            for target_id in node_list:
                if sender_id != target_id:
                    sender = self.nodes[sender_id]
                    message = f"LSR test from {sender_id} to {target_id}"
                    message_tasks.append(sender.send_message(target_id, message))
        
        await asyncio.gather(*message_tasks)
        await asyncio.sleep(3)  # Esperar entrega
        
        # Fase 3: Finalizar
        print("📤 Fase 3: Finalizando...")
        done_tasks = []
        for node in self.nodes.values():
            done_tasks.append(node.send_done_message())
        await asyncio.gather(*done_tasks)
        
        test_duration = time.time() - test_start
        
        # Mostrar tablas de enrutamiento
        print("\n📊 TABLAS DE ENRUTAMIENTO:")
        for node_id, node in self.nodes.items():
            if node.routing_table:
                print(f"  {node_id}: {node.routing_table}")
            else:
                print(f"  {node_id}: [tabla vacía]")
        
        # Desconectar nodos
        await self._cleanup_nodes()
        
        result = {
            "algoritmo": "link_state",
            "topologia": topologia_name,
            "nodos": len(self.nodes),
            "duracion": test_duration,
            "exito": True,
            "detalles": "Link State Routing test completed successfully"
        }
        
        print(f"✅ Prueba LSR completada en {test_duration:.2f}s")
        return result
    
    async def _cleanup_nodes(self):
        """Desconectar todos los nodos"""
        cleanup_tasks = []
        for node in self.nodes.values():
            cleanup_tasks.append(node.disconnect())
        await asyncio.gather(*cleanup_tasks)
        self.nodes = {}
    
    async def run_comprehensive_test(self):
        """Ejecutar suite completa de pruebas"""
        print("\n" + "="*60)
        print("  🧪 SUITE COMPLETA DE PRUEBAS - ALGORITMOS DE ENRUTAMIENTO")
        print("="*60)
        
        topologias = list(self.scenarios["topologias"].keys())
        algoritmos = ["flooding", "link_state"]
        
        total_tests = len(topologias) * len(algoritmos)
        test_count = 0
        
        for topologia in topologias:
            print(f"\n📍 TOPOLOGÍA: {topologia}")
            
            # Probar Flooding
            test_count += 1
            print(f"\n[{test_count}/{total_tests}] Testing Flooding...")
            result = await self.test_flooding_algorithm(topologia)
            self.test_results.append(result)
            
            await asyncio.sleep(1)  # Pausa entre pruebas
            
            # Probar Link State
            test_count += 1
            print(f"\n[{test_count}/{total_tests}] Testing Link State...")
            result = await self.test_link_state_algorithm(topologia)
            self.test_results.append(result)
            
            await asyncio.sleep(1)  # Pausa entre pruebas
        
        # Mostrar resumen
        self._print_test_summary()
    
    def _print_test_summary(self):
        """Mostrar resumen de pruebas"""
        print("\n" + "="*60)
        print("  📊 RESUMEN DE PRUEBAS")
        print("="*60)
        
        successful = 0
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result.get("exito", False) else "❌"
            algo = result.get("algoritmo", "N/A")
            topo = result.get("topologia", "N/A")
            duration = result.get("duracion", 0)
            
            print(f"{status} {algo.upper():12} | {topo:12} | {duration:.2f}s")
            
            if result.get("exito", False):
                successful += 1
        
        print("-"*60)
        print(f"📈 RESULTADOS: {successful}/{total} pruebas exitosas")
        
        if successful == total:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        else:
            print(f"⚠️ {total - successful} pruebas fallaron")

# Funciones de interfaz
async def interactive_menu():
    """Menú interactivo para testing"""
    suite = RoutingTestSuite()
    
    while True:
        print("\n" + "="*50)
        print("  🧪 TESTING DE ALGORITMOS")
        print("="*50)
        print("1. Probar Flooding en topología específica")
        print("2. Probar Link State en topología específica")
        print("3. Ejecutar suite completa de pruebas")
        print("4. Listar topologías disponibles")
        print("0. Salir")
        print("-"*50)
        
        choice = input("👉 Seleccione opción: ").strip()
        
        if choice == "0":
            print("👋 ¡Hasta luego!")
            break
        elif choice == "1":
            topo = input("Topología: ").strip()
            await suite.test_flooding_algorithm(topo)
        elif choice == "2":
            topo = input("Topología: ").strip()
            await suite.test_link_state_algorithm(topo)
        elif choice == "3":
            await suite.run_comprehensive_test()
        elif choice == "4":
            print("\n📍 TOPOLOGÍAS DISPONIBLES:")
            for name, info in suite.scenarios["topologias"].items():
                print(f"  • {name}: {info['descripcion']}")
        else:
            print("❌ Opción no válida")

async def main():
    """Función principal"""
    print("🚀 Iniciando sistema de testing...")
    
    # Verificar dependencias
    try:
        import redis.asyncio
        print("✅ Redis disponible")
    except ImportError:
        print("❌ Redis no instalado. Use: pip install redis[hiredis]")
        return
    
    await interactive_menu()

if __name__ == "__main__":
    asyncio.run(main())
