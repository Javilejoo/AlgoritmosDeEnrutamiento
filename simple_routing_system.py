"""
Sistema de Enrutamiento Distribuido Profesional
Versión simplificada con corrección de puertos
"""

import asyncio
import json
import socket
from network_protocol import NetworkMessageFactory, NetworkProtocolValidator

class SimpleDistributedNode:
    """Nodo distribuido simplificado"""
    
    def __init__(self, node_id, port=None):
        self.node_id = node_id
        self.port = port or self._get_available_port()
        self.neighbors = {}
        self.routing_table = {}
        self.running = False
        self.server = None
        
    def _get_available_port(self):
        """Obtiene un puerto disponible automáticamente"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            return s.getsockname()[1]
    
    async def start(self):
        """Inicia el nodo"""
        self.running = True
        try:
            self.server = await asyncio.start_server(
                self.handle_connection, 
                'localhost', 
                self.port
            )
            print(f"✅ Nodo {self.node_id} iniciado en puerto {self.port}")
            return True
        except Exception as e:
            print(f"❌ Error iniciando nodo {self.node_id}: {e}")
            return False
    
    async def handle_connection(self, reader, writer):
        """Maneja conexiones entrantes"""
        try:
            data = await reader.read(1024)
            if data:
                message_str = data.decode()
                print(f"📨 {self.node_id} recibió: {message_str}")
                
                # Procesar mensaje
                try:
                    message_data = json.loads(message_str)
                    await self.process_message(message_data)
                except json.JSONDecodeError:
                    print(f"❌ Mensaje inválido en {self.node_id}")
                
        except Exception as e:
            print(f"❌ Error en conexión de {self.node_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def process_message(self, message_data):
        """Procesa mensajes recibidos"""
        msg_type = message_data.get('type', '')
        
        if msg_type == 'init':
            await self.handle_init_message(message_data)
        elif msg_type == 'message':
            await self.handle_data_message(message_data)
        elif msg_type == 'done':
            await self.handle_done_message(message_data)
    
    async def handle_init_message(self, message_data):
        """Maneja mensajes INIT"""
        who = message_data.get('whoAmI', '')
        neighbors = message_data.get('neighbours', {})
        print(f"🔗 {self.node_id}: {who} se presenta con vecinos {list(neighbors.keys())}")
    
    async def handle_data_message(self, message_data):
        """Maneja mensajes de datos"""
        origin = message_data.get('origin', '')
        destination = message_data.get('destination', '')
        content = message_data.get('content', '')
        print(f"📬 {self.node_id}: Mensaje {origin}→{destination}: {content}")
    
    async def handle_done_message(self, message_data):
        """Maneja mensajes DONE"""
        who = message_data.get('whoAmI', '')
        print(f"✅ {self.node_id}: {who} terminó sus cálculos")
    
    async def send_message_to(self, target_port, message):
        """Envía mensaje a otro nodo"""
        try:
            reader, writer = await asyncio.open_connection('localhost', target_port)
            writer.write(message.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"❌ Error enviando mensaje desde {self.node_id}: {e}")
    
    async def stop(self):
        """Detiene el nodo"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

class SimpleNetworkManager:
    """Gestor de red simplificado"""
    
    def __init__(self):
        self.nodes = {}
        self.topology = {}
    
    async def create_linear_network(self):
        """Crea red lineal A-B-C-D"""
        print("🏗️ Creando red lineal A-B-C-D...")
        
        # Crear nodos
        nodes_config = ['A', 'B', 'C', 'D']
        for node_id in nodes_config:
            node = SimpleDistributedNode(node_id)
            success = await node.start()
            if success:
                self.nodes[node_id] = node
                print(f"  ✅ Nodo {node_id} creado en puerto {node.port}")
            else:
                print(f"  ❌ Falló crear nodo {node_id}")
                return False
        
        # Configurar topología lineal
        self.topology = {
            'A': {'B': 1},
            'B': {'A': 1, 'C': 1},
            'C': {'B': 1, 'D': 1},
            'D': {'C': 1}
        }
        
        print("✅ Red lineal creada exitosamente")
        return True
    
    async def run_protocol_demo(self):
        """Ejecuta demo del protocolo"""
        if not self.nodes:
            print("❌ No hay nodos en la red")
            return
        
        print("\n🚀 Ejecutando protocolo distribuido...")
        
        # Fase 1: INIT
        print("\n📋 FASE 1: Mensajes INIT")
        for node_id, neighbors in self.topology.items():
            if node_id in self.nodes:
                init_msg = NetworkMessageFactory.create_init_message(node_id, neighbors)
                print(f"  {node_id} envía INIT: {list(neighbors.keys())}")
                
                # Enviar a vecinos
                for neighbor_id in neighbors:
                    if neighbor_id in self.nodes:
                        target_port = self.nodes[neighbor_id].port
                        await self.nodes[node_id].send_message_to(target_port, init_msg.to_json())
                
                await asyncio.sleep(0.5)
        
        # Fase 2: Procesamiento
        print("\n⚙️ FASE 2: Cálculo de rutas")
        await asyncio.sleep(2)
        
        # Fase 3: DONE
        print("\n📋 FASE 3: Mensajes DONE")
        for node_id in self.nodes:
            done_msg = NetworkMessageFactory.create_done_message(node_id)
            print(f"  {node_id} envía DONE")
            await asyncio.sleep(0.3)
        
        # Fase 4: Mensajes de prueba
        print("\n📬 FASE 4: Mensajes de prueba")
        test_messages = [
            ("A", "D", "Hola desde extremo A"),
            ("D", "A", "Respuesta desde extremo D"),
            ("B", "C", "Mensaje entre vecinos")
        ]
        
        for origin, destination, content in test_messages:
            if origin in self.nodes and destination in self.nodes:
                msg = NetworkMessageFactory.create_message(origin, destination, content)
                print(f"  📨 {origin} → {destination}: {content}")
                
                # Enviar al destino (simplificado)
                target_port = self.nodes[destination].port
                await self.nodes[origin].send_message_to(target_port, msg.to_json())
                await asyncio.sleep(0.5)
        
        print("\n✅ Demo del protocolo completado!")
    
    async def stop_all_nodes(self):
        """Detiene todos los nodos"""
        print("\n🛑 Deteniendo todos los nodos...")
        for node in self.nodes.values():
            await node.stop()
        self.nodes.clear()
        print("✅ Todos los nodos detenidos")

async def main():
    """Función principal"""
    print("🌐 SISTEMA DE ENRUTAMIENTO DISTRIBUIDO")
    print("Protocolo Profesional para Redes Distribuidas")
    print("="*50)
    
    manager = SimpleNetworkManager()
    
    try:
        while True:
            print("\n📋 OPCIONES:")
            print("1. Crear red lineal A-B-C-D")
            print("2. Ejecutar protocolo completo")
            print("3. Ver estado de la red")
            print("4. Detener todos los nodos")
            print("0. Salir")
            
            choice = input("\nSeleccione opción: ").strip()
            
            if choice == "1":
                await manager.create_linear_network()
                
            elif choice == "2":
                await manager.run_protocol_demo()
                
            elif choice == "3":
                print("\n📊 ESTADO DE LA RED:")
                if manager.nodes:
                    for node_id, node in manager.nodes.items():
                        print(f"  {node_id}: Puerto {node.port}, Estado: {'🟢 Activo' if node.running else '🔴 Inactivo'}")
                else:
                    print("  No hay nodos activos")
                    
            elif choice == "4":
                await manager.stop_all_nodes()
                
            elif choice == "0":
                await manager.stop_all_nodes()
                print("👋 ¡Sistema cerrado correctamente!")
                break
                
            else:
                print("❌ Opción inválida")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupción detectada...")
        await manager.stop_all_nodes()
        print("👋 ¡Sistema cerrado!")

if __name__ == "__main__":
    asyncio.run(main())
