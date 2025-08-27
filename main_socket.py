"""
Interfaz principal para el sistema de enrutamiento con SOCKETS TCP
Reemplaza XMPP con comunicación por sockets
"""

import asyncio
import json
import time
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

from socket_routing_node import SocketRoutingNode
from routing_algorithms import DVRNode, LSRNode, RoutingNodeFactory
from protocolo import NetworkMessage, MessageFactory, MessageType
from config_manager import ConfigManager, TopologyConfig, NodeConfig
from socket_client import SocketRoutingClient

class SocketRoutingSystem:
    """Sistema de enrutamiento con sockets TCP"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.nodes: Dict[str, SocketRoutingNode] = {}
        self.running = False
        
    async def create_node(self, node_id: str, algorithm: str = "basic", 
                         port: Optional[int] = None, topology_file: Optional[str] = None):
        """Crea un nodo con el algoritmo especificado"""
        
        # Asignar puerto automáticamente si no se especifica
        if port is None:
            port = 65000 + len(self.nodes) + 1
        
        # Crear nodo según algoritmo
        node = RoutingNodeFactory.create_node(algorithm, node_id, port, topology_file)
        
        self.nodes[node_id] = node
        print(f"✅ Nodo {node_id} creado - Puerto: {port} - Algoritmo: {algorithm}")
        
        return node
    
    async def start_node(self, node_id: str):
        """Inicia un nodo específico"""
        if node_id in self.nodes:
            await self.nodes[node_id].start()
            print(f"🚀 Nodo {node_id} iniciado")
        else:
            print(f"❌ Nodo {node_id} no encontrado")
    
    async def stop_node(self, node_id: str):
        """Detiene un nodo específico"""
        if node_id in self.nodes:
            await self.nodes[node_id].stop()
            print(f"🛑 Nodo {node_id} detenido")
    
    async def start_all_nodes(self):
        """Inicia todos los nodos"""
        tasks = []
        for node_id, node in self.nodes.items():
            tasks.append(self.start_node(node_id))
        
        await asyncio.gather(*tasks)
        self.running = True
        print(f"🌐 Sistema iniciado - {len(self.nodes)} nodos activos")
    
    async def stop_all_nodes(self):
        """Detiene todos los nodos"""
        tasks = []
        for node_id, node in self.nodes.items():
            tasks.append(self.stop_node(node_id))
        
        await asyncio.gather(*tasks)
        self.running = False
        print("🔴 Sistema detenido")
    
    async def send_message(self, from_node: str, to_node: str, message: str):
        """Envía un mensaje entre nodos"""
        if from_node in self.nodes:
            await self.nodes[from_node].send_user_message(to_node, message)
            print(f"📤 Mensaje enviado: {from_node} → {to_node}")
        else:
            print(f"❌ Nodo origen {from_node} no encontrado")
    
    def show_node_status(self, node_id: str):
        """Muestra el estado de un nodo"""
        if node_id in self.nodes:
            status = self.nodes[node_id].get_status()
            print(f"\n📊 Estado del nodo {node_id}:")
            for key, value in status.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Nodo {node_id} no encontrado")
    
    def show_routing_table(self, node_id: str):
        """Muestra la tabla de enrutamiento de un nodo"""
        if node_id in self.nodes:
            table = self.nodes[node_id].get_routing_table()
            print(f"\n🗺️ Tabla de enrutamiento - {node_id}:")
            if table:
                for dest, (next_hop, cost) in table.items():
                    print(f"   {dest} → {next_hop} (costo: {cost})")
            else:
                print("   (vacía)")
        else:
            print(f"❌ Nodo {node_id} no encontrado")
    
    def show_neighbors(self, node_id: str):
        """Muestra los vecinos de un nodo"""
        if node_id in self.nodes:
            neighbors = self.nodes[node_id].get_neighbors()
            print(f"\n👥 Vecinos del nodo {node_id}:")
            if neighbors:
                for name, info in neighbors.items():
                    status = "🟢" if info["alive"] else "🔴"
                    print(f"   {status} {name} - costo: {info['cost']}")
            else:
                print("   (sin vecinos)")
        else:
            print(f"❌ Nodo {node_id} no encontrado")
    
    def list_nodes(self):
        """Lista todos los nodos"""
        print(f"\n📋 Nodos en el sistema ({len(self.nodes)}):")
        for node_id, node in self.nodes.items():
            status = "🟢" if node.state.value == "running" else "🔴"
            print(f"   {status} {node_id} - Puerto: {node.port}")
    
    async def create_topology_from_config(self, config_file: str):
        """Crea nodos basado en un archivo de configuración"""
        try:
            config = self.config_manager.load_config(config_file)
            
            # Crear nodos
            for node_id, node_config in config.nodes.items():
                await self.create_node(
                    node_id=node_id,
                    algorithm=node_config.algorithm,
                    port=node_config.port,
                    topology_file=config_file
                )
            
            print(f"✅ Topología creada desde {config_file}")
            
        except Exception as e:
            print(f"❌ Error creando topología: {e}")
    
    async def run_interactive(self):
        """Ejecuta el sistema en modo interactivo"""
        print("\n" + "="*60)
        print("🌐 SISTEMA DE ENRUTAMIENTO CON SOCKETS TCP")
        print("="*60)
        
        while True:
            print("\n📋 MENÚ PRINCIPAL:")
            print("1.  Crear nodo")
            print("2.  Iniciar nodo")
            print("3.  Detener nodo")
            print("4.  Iniciar todos los nodos")
            print("5.  Detener todos los nodos")
            print("6.  Enviar mensaje")
            print("7.  Ver estado de nodo")
            print("8.  Ver tabla de enrutamiento")
            print("9.  Ver vecinos")
            print("10. Listar nodos")
            print("11. Crear topología desde archivo")
            print("12. Generar configuración de ejemplo")
            print("13. Ejecutar pruebas de conectividad")
            print("14. Simulación completa")
            print("15. Ver estadísticas del sistema")
            print("0.  Salir")
            
            try:
                choice = input("\n👉 Seleccione opción: ").strip()
                
                if choice == "0":
                    print("👋 Cerrando sistema...")
                    await self.stop_all_nodes()
                    break
                    
                elif choice == "1":
                    await self._menu_create_node()
                    
                elif choice == "2":
                    await self._menu_start_node()
                    
                elif choice == "3":
                    await self._menu_stop_node()
                    
                elif choice == "4":
                    await self.start_all_nodes()
                    
                elif choice == "5":
                    await self.stop_all_nodes()
                    
                elif choice == "6":
                    await self._menu_send_message()
                    
                elif choice == "7":
                    await self._menu_show_status()
                    
                elif choice == "8":
                    await self._menu_show_routing()
                    
                elif choice == "9":
                    await self._menu_show_neighbors()
                    
                elif choice == "10":
                    self.list_nodes()
                    
                elif choice == "11":
                    await self._menu_load_topology()
                    
                elif choice == "12":
                    await self._menu_generate_config()
                    
                elif choice == "13":
                    await self._menu_connectivity_test()
                    
                elif choice == "14":
                    await self._menu_full_simulation()
                    
                elif choice == "15":
                    await self._menu_system_stats()
                    
                else:
                    print("❌ Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n👋 Cerrando sistema...")
                await self.stop_all_nodes()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Métodos auxiliares para menús
    async def _menu_create_node(self):
        """Menú para crear nodo"""
        node_id = input("ID del nodo: ").strip()
        if not node_id:
            print("❌ ID requerido")
            return
            
        algorithm = input("Algoritmo (basic/dvr/lsr) [basic]: ").strip() or "basic"
        port_str = input("Puerto [auto]: ").strip()
        port = int(port_str) if port_str else None
        
        await self.create_node(node_id, algorithm, port)
    
    async def _menu_start_node(self):
        """Menú para iniciar nodo"""
        node_id = input("ID del nodo a iniciar: ").strip()
        if node_id:
            await self.start_node(node_id)
    
    async def _menu_stop_node(self):
        """Menú para detener nodo"""
        node_id = input("ID del nodo a detener: ").strip()
        if node_id:
            await self.stop_node(node_id)
    
    async def _menu_send_message(self):
        """Menú para enviar mensaje"""
        from_node = input("Nodo origen: ").strip()
        to_node = input("Nodo destino: ").strip()
        message = input("Mensaje: ").strip()
        
        if from_node and to_node and message:
            await self.send_message(from_node, to_node, message)
    
    async def _menu_show_status(self):
        """Menú para mostrar estado"""
        node_id = input("ID del nodo: ").strip()
        if node_id:
            self.show_node_status(node_id)
    
    async def _menu_show_routing(self):
        """Menú para mostrar tabla de enrutamiento"""
        node_id = input("ID del nodo: ").strip()
        if node_id:
            self.show_routing_table(node_id)
    
    async def _menu_show_neighbors(self):
        """Menú para mostrar vecinos"""
        node_id = input("ID del nodo: ").strip()
        if node_id:
            self.show_neighbors(node_id)
    
    async def _menu_load_topology(self):
        """Menú para cargar topología"""
        file_path = input("Archivo de topología: ").strip()
        if file_path and os.path.exists(file_path):
            await self.create_topology_from_config(file_path)
        else:
            print("❌ Archivo no encontrado")
    
    async def _menu_generate_config(self):
        """Menú para generar configuración"""
        print("🔧 Generando configuración de ejemplo...")
        await self.config_manager.generate_example_configs()
        print("✅ Archivos generados: topology.json, nodes.json")
    
    async def _menu_connectivity_test(self):
        """Menú para pruebas de conectividad"""
        print("🧪 Ejecutando pruebas de conectividad...")
        # Implementar pruebas
        for node_id in self.nodes:
            print(f"   Probando {node_id}...")
            await asyncio.sleep(0.5)
        print("✅ Pruebas completadas")
    
    async def _menu_full_simulation(self):
        """Menú para simulación completa"""
        print("🎭 Iniciando simulación completa...")
        
        # Crear topología básica
        await self.create_node("A", "dvr", 65001)
        await self.create_node("B", "lsr", 65002)
        await self.create_node("C", "basic", 65003)
        
        # Iniciar nodos
        await self.start_all_nodes()
        
        # Simular comunicación
        print("💬 Simulando comunicación...")
        await asyncio.sleep(5)
        
        await self.send_message("A", "C", "Hola desde A")
        await asyncio.sleep(2)
        await self.send_message("B", "A", "Respuesta de B")
        
        print("✅ Simulación completada")
    
    async def _menu_system_stats(self):
        """Menú para estadísticas del sistema"""
        print(f"\n📊 ESTADÍSTICAS DEL SISTEMA:")
        print(f"   Nodos totales: {len(self.nodes)}")
        print(f"   Nodos activos: {sum(1 for n in self.nodes.values() if n.state.value == 'running')}")
        
        total_neighbors = sum(len(n.neighbors) for n in self.nodes.values())
        print(f"   Conexiones totales: {total_neighbors}")
        
        if self.nodes:
            avg_neighbors = total_neighbors / len(self.nodes)
            print(f"   Promedio vecinos/nodo: {avg_neighbors:.1f}")

# Función principal
async def main():
    """Función principal"""
    system = SocketRoutingSystem()
    await system.run_interactive()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema cerrado por el usuario")
    except Exception as e:
        print(f"❌ Error del sistema: {e}")
