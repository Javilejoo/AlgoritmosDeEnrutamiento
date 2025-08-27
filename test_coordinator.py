"""
Coordinador para pruebas con XMPP
Facilita el testing y demostración de los algoritmos de enrutamiento
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Any
import logging

from routing_node import RoutingNode
from config_manager import ConfigManager, TopologyConfig, NodeConfig
from protocolo import MessageFactory

class TestCoordinator:
    """Coordinador para pruebas de algoritmos de enrutamiento"""
    
    def __init__(self, use_xmpp: bool = False):
        self.use_xmpp = use_xmpp
        self.nodes: Dict[str, RoutingNode] = {}
        self.topology: Optional[TopologyConfig] = None
        self.node_configs: List[NodeConfig] = []
        
        # Estado de la prueba
        self.test_running = False
        self.test_results = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("TestCoordinator")
    
    def load_configuration(self, topology_file: str, nodes_file: str):
        """Carga configuración desde archivos"""
        try:
            self.topology = ConfigManager.load_topology(topology_file)
            self.node_configs = ConfigManager.load_nodes(nodes_file)
            
            self.logger.info(f"✅ Configuración cargada:")
            self.logger.info(f"   - {len(self.topology.nodes)} nodos")
            self.logger.info(f"   - {sum(len(conns) for conns in self.topology.connections.values())} conexiones")
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            raise
    
    async def create_nodes(self, node_subset: Optional[List[str]] = None):
        """Crea los nodos de la red"""
        nodes_to_create = node_subset or self.topology.nodes
        
        self.logger.info(f"🏗️ Creando {len(nodes_to_create)} nodos...")
        
        for node_config in self.node_configs:
            if node_config.node_id in nodes_to_create:
                # Crear nodo
                node = RoutingNode(
                    node_id=node_config.node_id,
                    jid=f"{node_config.jid}/{node_config.resource}",
                    password=node_config.password,
                    topology_file=None,  # Se configurará manualmente
                    use_xmpp=self.use_xmpp
                )
                
                # Configurar vecinos desde topología
                neighbors = self.topology.get_neighbors(node_config.node_id)
                for neighbor_id, cost in neighbors.items():
                    neighbor_config = next(
                        (nc for nc in self.node_configs if nc.node_id == neighbor_id), 
                        None
                    )
                    if neighbor_config:
                        neighbor_jid = f"{neighbor_config.jid}/{neighbor_config.resource}"
                        from routing_node import NeighborInfo
                        node.neighbors[neighbor_jid] = NeighborInfo(
                            jid=neighbor_jid,
                            cost=float(cost),
                            last_hello=0
                        )
                
                # Configurar topología completa
                from routing_node import TopologyEntry
                node.topology = TopologyEntry(
                    nodes=self.topology.nodes,
                    connections=self.topology.connections
                )
                
                self.nodes[node_config.node_id] = node
                self.logger.info(f"   ✅ Nodo {node_config.node_id} creado")
        
        self.logger.info(f"🎯 {len(self.nodes)} nodos listos")
    
    async def start_network(self):
        """Inicia todos los nodos de la red"""
        self.logger.info("🚀 Iniciando red...")
        
        # Iniciar nodos secuencialmente para evitar conflictos
        for node_id, node in self.nodes.items():
            await node.start()
            await asyncio.sleep(1)  # Pausa entre inicios
        
        # Esperar estabilización
        self.logger.info("⏳ Esperando estabilización de la red...")
        await asyncio.sleep(10)
        
        self.test_running = True
        self.logger.info("✅ Red iniciada y estabilizada")
    
    async def stop_network(self):
        """Detiene todos los nodos"""
        self.logger.info("🛑 Deteniendo red...")
        
        for node_id, node in self.nodes.items():
            await node.stop()
        
        self.test_running = False
        self.logger.info("🔴 Red detenida")
    
    async def run_connectivity_test(self) -> Dict[str, Any]:
        """Ejecuta prueba de conectividad entre todos los nodos"""
        self.logger.info("🔍 Iniciando prueba de conectividad...")
        
        results = {
            "timestamp": time.time(),
            "total_tests": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "delivery_details": []
        }
        
        # Probar envío de mensajes entre todos los pares de nodos
        for from_node_id in self.nodes:
            for to_node_id in self.nodes:
                if from_node_id != to_node_id:
                    success = await self._test_message_delivery(from_node_id, to_node_id)
                    results["total_tests"] += 1
                    
                    if success:
                        results["successful_deliveries"] += 1
                    else:
                        results["failed_deliveries"] += 1
                    
                    results["delivery_details"].append({
                        "from": from_node_id,
                        "to": to_node_id,
                        "success": success
                    })
                    
                    # Pausa entre envíos
                    await asyncio.sleep(0.5)
        
        success_rate = (results["successful_deliveries"] / results["total_tests"]) * 100
        self.logger.info(f"📊 Prueba completada: {success_rate:.1f}% éxito")
        
        return results
    
    async def _test_message_delivery(self, from_node: str, to_node: str) -> bool:
        """Prueba el envío de un mensaje entre dos nodos"""
        try:
            message = f"Test message from {from_node} to {to_node} at {time.time()}"
            
            # Obtener estado inicial del nodo destino
            initial_received = self.nodes[to_node].packets_received
            
            # Enviar mensaje
            await self.nodes[from_node].send_user_message(to_node, message)
            
            # Esperar entrega
            await asyncio.sleep(2)
            
            # Verificar si se recibió
            final_received = self.nodes[to_node].packets_received
            delivered = final_received > initial_received
            
            if delivered:
                self.logger.info(f"✅ {from_node} -> {to_node}: Entregado")
            else:
                self.logger.warning(f"❌ {from_node} -> {to_node}: Falló")
            
            return delivered
            
        except Exception as e:
            self.logger.error(f"❌ Error en prueba {from_node} -> {to_node}: {e}")
            return False
    
    async def run_flooding_test(self) -> Dict[str, Any]:
        """Ejecuta prueba del algoritmo de flooding"""
        self.logger.info("🌊 Iniciando prueba de flooding...")
        
        results = {
            "timestamp": time.time(),
            "flooding_tests": []
        }
        
        # Probar flooding desde cada nodo
        for source_node in self.nodes:
            # Resetear contadores
            for node in self.nodes.values():
                node.packets_received = 0
            
            # Enviar mensaje de flooding
            flood_message = f"FLOOD from {source_node} at {time.time()}"
            
            # Simular flooding (enviar a todos los vecinos)
            for neighbor_jid in self.nodes[source_node].neighbors:
                await self.nodes[source_node].xmpp_client.send_data(
                    neighbor_jid, 
                    flood_message
                )
            
            # Esperar propagación
            await asyncio.sleep(3)
            
            # Recopilar resultados
            nodes_reached = sum(1 for node in self.nodes.values() if node.packets_received > 0)
            
            results["flooding_tests"].append({
                "source": source_node,
                "nodes_reached": nodes_reached,
                "total_nodes": len(self.nodes),
                "coverage": (nodes_reached / len(self.nodes)) * 100
            })
            
            self.logger.info(f"🌊 Flooding desde {source_node}: {nodes_reached}/{len(self.nodes)} nodos alcanzados")
        
        return results
    
    async def run_performance_test(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Ejecuta prueba de rendimiento durante un tiempo determinado"""
        self.logger.info(f"⚡ Iniciando prueba de rendimiento ({duration_seconds}s)...")
        
        start_time = time.time()
        results = {
            "timestamp": start_time,
            "duration": duration_seconds,
            "messages_sent": 0,
            "node_stats": {}
        }
        
        # Enviar mensajes continuamente
        while time.time() - start_time < duration_seconds:
            # Seleccionar par de nodos aleatorio
            import random
            nodes_list = list(self.nodes.keys())
            from_node = random.choice(nodes_list)
            to_node = random.choice([n for n in nodes_list if n != from_node])
            
            # Enviar mensaje
            message = f"Performance test {results['messages_sent']}"
            await self.nodes[from_node].send_user_message(to_node, message)
            results["messages_sent"] += 1
            
            # Pausa corta
            await asyncio.sleep(0.1)
        
        # Recopilar estadísticas finales
        for node_id, node in self.nodes.items():
            results["node_stats"][node_id] = node.get_status()
        
        self.logger.info(f"⚡ Prueba completada: {results['messages_sent']} mensajes enviados")
        return results
    
    async def simulate_node_failure(self, node_id: str, failure_duration: int = 30):
        """Simula la falla de un nodo"""
        if node_id not in self.nodes:
            self.logger.error(f"❌ Nodo {node_id} no existe")
            return
        
        self.logger.info(f"💥 Simulando falla del nodo {node_id} por {failure_duration}s...")
        
        # "Fallar" el nodo (detenerlo)
        await self.nodes[node_id].stop()
        
        # Esperar tiempo de falla
        await asyncio.sleep(failure_duration)
        
        # Reiniciar nodo
        await self.nodes[node_id].start()
        
        self.logger.info(f"🔄 Nodo {node_id} recuperado")
    
    def generate_test_report(self, test_results: List[Dict]) -> str:
        """Genera reporte de pruebas"""
        report = "="*60 + "\n"
        report += "REPORTE DE PRUEBAS DE ENRUTAMIENTO\n"
        report += "="*60 + "\n\n"
        
        for i, result in enumerate(test_results):
            report += f"PRUEBA {i+1}: {result.get('type', 'Unknown')}\n"
            report += f"Timestamp: {time.ctime(result.get('timestamp', 0))}\n"
            
            if 'successful_deliveries' in result:
                success_rate = (result['successful_deliveries'] / result['total_tests']) * 100
                report += f"Tasa de éxito: {success_rate:.1f}%\n"
                report += f"Entregas exitosas: {result['successful_deliveries']}/{result['total_tests']}\n"
            
            report += "\n" + "-"*40 + "\n\n"
        
        # Estadísticas de nodos
        report += "ESTADÍSTICAS FINALES DE NODOS\n"
        report += "-"*40 + "\n"
        
        for node_id, node in self.nodes.items():
            stats = node.get_status()
            report += f"Nodo {node_id}:\n"
            report += f"  Paquetes reenviados: {stats['packets_forwarded']}\n"
            report += f"  Paquetes recibidos: {stats['packets_received']}\n"
            report += f"  Actualizaciones de routing: {stats['routing_updates']}\n"
            report += f"  Vecinos activos: {stats['neighbors']}\n\n"
        
        return report
    
    def save_results(self, results: List[Dict], filename: str):
        """Guarda resultados en archivo JSON"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        self.logger.info(f"📁 Resultados guardados en {filename}")

# Scripts de prueba predefinidos
class TestScenarios:
    """Escenarios de prueba predefinidos"""
    
    @staticmethod
    async def basic_connectivity_test(coordinator: TestCoordinator):
        """Prueba básica de conectividad"""
        results = []
        
        # Prueba de conectividad
        connectivity_result = await coordinator.run_connectivity_test()
        connectivity_result["type"] = "connectivity"
        results.append(connectivity_result)
        
        return results
    
    @staticmethod
    async def comprehensive_test(coordinator: TestCoordinator):
        """Prueba completa de todos los algoritmos"""
        results = []
        
        # 1. Conectividad
        connectivity_result = await coordinator.run_connectivity_test()
        connectivity_result["type"] = "connectivity"
        results.append(connectivity_result)
        
        # 2. Flooding
        flooding_result = await coordinator.run_flooding_test()
        flooding_result["type"] = "flooding"
        results.append(flooding_result)
        
        # 3. Rendimiento
        performance_result = await coordinator.run_performance_test(30)
        performance_result["type"] = "performance"
        results.append(performance_result)
        
        return results
    
    @staticmethod
    async def failure_recovery_test(coordinator: TestCoordinator):
        """Prueba de recuperación ante fallas"""
        results = []
        
        # Prueba inicial
        initial_result = await coordinator.run_connectivity_test()
        initial_result["type"] = "pre_failure"
        results.append(initial_result)
        
        # Simular falla de nodo central
        central_nodes = ["A", "D", "F"]  # Nodos con más conexiones
        for node_id in central_nodes:
            if node_id in coordinator.nodes:
                await coordinator.simulate_node_failure(node_id, 20)
                
                # Probar conectividad después de recuperación
                recovery_result = await coordinator.run_connectivity_test()
                recovery_result["type"] = f"post_failure_{node_id}"
                results.append(recovery_result)
                break
        
        return results

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== COORDINADOR DE PRUEBAS XMPP ===")
        
        # Crear archivos de configuración si no existen
        ConfigManager.create_config_files()
        
        # Crear coordinador (modo offline para demo)
        coordinator = TestCoordinator(use_xmpp=False)
        
        # Cargar configuración
        coordinator.load_configuration("topology.json", "nodes.json")
        
        # Crear subset de nodos para demo
        test_nodes = ["A", "B", "D", "F"]  # Solo algunos nodos para demo rápida
        await coordinator.create_nodes(test_nodes)
        
        # Iniciar red
        await coordinator.start_network()
        
        # Ejecutar pruebas
        print("\n🧪 Ejecutando pruebas...")
        results = await TestScenarios.basic_connectivity_test(coordinator)
        
        # Generar reporte
        report = coordinator.generate_test_report(results)
        print("\n" + report)
        
        # Guardar resultados
        coordinator.save_results(results, "test_results.json")
        
        # Detener red
        await coordinator.stop_network()
        
        print("✅ Pruebas completadas")
    
    asyncio.run(main())
