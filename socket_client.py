"""
Cliente de comunicación usando sockets TCP (sin XMPP)
Mantiene el protocolo JSON estándar pero usa sockets simples
"""

import socket
import json
import time
import threading
import asyncio
from typing import Dict, List, Optional, Callable, Any
import logging

from protocolo import NetworkMessage, MessageFactory, ProtocolValidator

class SocketRoutingClient:
    """Cliente de enrutamiento usando sockets TCP simples"""
    
    def __init__(self, node_name: str, port: int):
        self.node_name = node_name
        self.port = port
        self.host = '127.0.0.1'
        self.jid = f"node_{node_name}@localhost:{port}"  # Simular JID
        self.connected = False
        
        # Callbacks para diferentes tipos de mensajes
        self.message_handlers: Dict[str, Callable] = {}
        
        # Información del nodo
        self.neighbors = {}  # {neighbor_address: cost}
        self.routing_table = {}
        
        # Socket servidor
        self.server_socket = None
        self.client_connections = {}  # {address: socket}
        
        # Estadísticas
        self.messages_sent = 0
        self.messages_received = 0
        
        # Puertos de otros nodos
        self.node_ports = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"SocketClient-{node_name}")
    
    async def connect(self) -> bool:
        """Inicia el servidor de sockets"""
        try:
            # Iniciar servidor
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            # Iniciar thread para aceptar conexiones
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
            self.connected = True
            self.logger.info(f"✅ Servidor socket iniciado en puerto {self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servidor: {e}")
            return False
    
    def _accept_connections(self):
        """Acepta conexiones entrantes"""
        while self.connected:
            try:
                client_socket, address = self.server_socket.accept()
                # Manejar cliente en thread separado
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, address), 
                    daemon=True
                ).start()
            except Exception as e:
                if self.connected:  # Solo mostrar si no estamos cerrando
                    self.logger.error(f"Error aceptando conexión: {e}")
                break
    
    def _handle_client(self, client_socket, address):
        """Maneja un cliente conectado"""
        try:
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                # Procesar mensaje JSON
                asyncio.run(self._process_message(data, address))
                
        except Exception as e:
            self.logger.error(f"Error manejando cliente {address}: {e}")
        finally:
            client_socket.close()
    
    async def disconnect(self):
        """Desconecta el servidor"""
        self.connected = False
        if self.server_socket:
            self.server_socket.close()
        
        # Cerrar conexiones de clientes
        for conn in self.client_connections.values():
            try:
                conn.close()
            except:
                pass
        
        self.logger.info("🔌 Servidor socket desconectado")
    
    def register_handler(self, message_type: str, handler: Callable):
        """Registra un handler para un tipo de mensaje específico"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"📝 Handler registrado para {message_type}")
    
    async def send_message(self, message: NetworkMessage) -> bool:
        """Envía un mensaje via socket TCP"""
        try:
            # Validar mensaje
            if not ProtocolValidator.validate_message(message):
                self.logger.error("❌ Mensaje inválido")
                return False
            
            json_message = message.to_json()
            
            if message.to_addr == "broadcast":
                # Enviar a todos los vecinos
                success_count = 0
                for neighbor_node, _ in self.neighbors.items():
                    if await self._send_to_node(neighbor_node, json_message):
                        success_count += 1
                
                self.messages_sent += success_count
                self.logger.info(f"📤 Broadcast enviado a {success_count} vecinos")
                return success_count > 0
            else:
                # Extraer nodo destino
                dest_node = self._extract_node_from_address(message.to_addr)
                success = await self._send_to_node(dest_node, json_message)
                if success:
                    self.messages_sent += 1
                    self.logger.info(f"📤 Mensaje {message.type} enviado a {dest_node}")
                return success
                
        except Exception as e:
            self.logger.error(f"❌ Error enviando mensaje: {e}")
            return False
    
    async def _send_to_node(self, node_name: str, message_content: str) -> bool:
        """Envía mensaje a un nodo específico via socket"""
        try:
            if node_name not in self.node_ports:
                self.logger.error(f"Nodo {node_name} no conocido")
                return False
            
            target_port = self.node_ports[node_name]
            
            # Crear conexión temporal
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # Timeout de 5 segundos
            
            try:
                sock.connect((self.host, target_port))
                sock.send(message_content.encode('utf-8'))
                sock.close()
                return True
            except Exception as e:
                self.logger.warning(f"No se pudo conectar a {node_name}:{target_port} - {e}")
                sock.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando a {node_name}: {e}")
            return False
    
    async def _process_message(self, message_content: str, from_address):
        """Procesa un mensaje entrante"""
        try:
            # Parsear mensaje JSON
            message = NetworkMessage.from_json(message_content)
            
            # Validar mensaje
            if not ProtocolValidator.validate_message(message):
                self.logger.warning(f"⚠️ Mensaje inválido de {from_address}")
                return
            
            self.messages_received += 1
            self.logger.info(f"📥 Mensaje {message.type} recibido de {message.from_addr}")
            
            # Verificar TTL
            if not message.decrement_ttl():
                self.logger.warning(f"⏰ TTL expirado para mensaje de {message.from_addr}")
                return
            
            # Llamar handler específico si existe
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](message, message.from_addr)
            else:
                # Handler por defecto
                await self._default_message_handler(message, message.from_addr)
                
        except Exception as e:
            self.logger.error(f"❌ Error procesando mensaje de {from_address}: {e}")
    
    async def _default_message_handler(self, message: NetworkMessage, from_addr: str):
        """Handler por defecto para mensajes"""
        self.logger.info(f"📨 Mensaje no manejado: {message.type} de {from_addr}")
        print(f"   Payload: {message.payload}")
    
    def _extract_node_from_address(self, address: str) -> str:
        """Extrae el nombre del nodo de una dirección"""
        # Ejemplo: node_A@localhost:65001 -> A
        if "node_" in address:
            return address.split("node_")[1].split("@")[0]
        return address.split("@")[0]
    
    # Métodos de conveniencia para enviar diferentes tipos de mensajes
    async def send_hello(self, to_node: str, node_info: Dict):
        """Envía mensaje HELLO"""
        to_addr = f"node_{to_node}@localhost:{self.node_ports.get(to_node, 65000)}"
        message = MessageFactory.create_hello_message(self.jid, to_addr, node_info)
        return await self.send_message(message)
    
    async def send_ping(self, to_node: str, ping_id: str):
        """Envía mensaje PING"""
        to_addr = f"node_{to_node}@localhost:{self.node_ports.get(to_node, 65000)}"
        message = MessageFactory.create_ping_message(self.jid, to_addr, ping_id)
        return await self.send_message(message)
    
    async def send_data(self, to_node: str, user_message: str, proto: str = "lsr"):
        """Envía mensaje de datos"""
        to_addr = f"node_{to_node}@localhost:{self.node_ports.get(to_node, 65000)}"
        message = MessageFactory.create_data_message(self.jid, to_addr, user_message, proto)
        return await self.send_message(message)
    
    async def send_lsp(self, lsp_data: Dict):
        """Envía LSP (broadcast)"""
        message = MessageFactory.create_lsp_message(self.jid, lsp_data)
        return await self.send_message(message)
    
    async def send_distance_vector(self, to_node: str, distance_vector: Dict):
        """Envía Distance Vector"""
        to_addr = f"node_{to_node}@localhost:{self.node_ports.get(to_node, 65000)}"
        message = MessageFactory.create_dv_message(self.jid, to_addr, distance_vector)
        return await self.send_message(message)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del cliente"""
        return {
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "neighbors": len(self.neighbors),
            "node_name": self.node_name,
            "port": self.port
        }

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== CLIENTE SOCKET PARA ENRUTAMIENTO ===")
        
        # Crear dos clientes para demo
        client_a = SocketRoutingClient("A", 65001)
        client_b = SocketRoutingClient("B", 65002)
        
        # Configurar vecinos
        client_a.neighbors["B"] = 1
        client_b.neighbors["A"] = 1
        
        # Registrar handlers
        async def handle_hello_a(message, from_addr):
            print(f"🤝 A recibió HELLO de {from_addr}: {message.payload}")
        
        async def handle_hello_b(message, from_addr):
            print(f"🤝 B recibió HELLO de {from_addr}: {message.payload}")
        
        client_a.register_handler("hello", handle_hello_a)
        client_b.register_handler("hello", handle_hello_b)
        
        # Conectar
        await client_a.connect()
        await client_b.connect()
        
        print("✅ Clientes conectados")
        
        # Esperar un poco para que los servidores estén listos
        await asyncio.sleep(2)
        
        # Intercambiar mensajes HELLO
        print("\n📤 A enviando HELLO a B...")
        await client_a.send_hello("B", {"node_id": "A", "neighbors": ["B"]})
        
        await asyncio.sleep(1)
        
        print("📤 B enviando HELLO a A...")
        await client_b.send_hello("A", {"node_id": "B", "neighbors": ["A"]})
        
        await asyncio.sleep(2)
        
        # Mostrar estadísticas
        print(f"\nEstadísticas A: {client_a.get_stats()}")
        print(f"Estadísticas B: {client_b.get_stats()}")
        
        # Desconectar
        await client_a.disconnect()
        await client_b.disconnect()
        
        print("✅ Demo completada")
    
    asyncio.run(main())
