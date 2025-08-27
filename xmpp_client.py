"""
Cliente XMPP para algoritmos de enrutamiento
Maneja la conexión y comunicación via XMPP según el protocolo definido
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Callable, Any
import logging

# Para XMPP usaremos slixmpp (instalable con: pip install slixmpp)
try:
    import slixmpp
    from slixmpp.exceptions import XMPPError
    XMPP_AVAILABLE = True
except ImportError:
    XMPP_AVAILABLE = False
    print("⚠️ slixmpp no está instalado. Usar: pip install slixmpp")

from protocolo import NetworkMessage, MessageFactory, ProtocolValidator

class XMPPRoutingClient:
    """Cliente XMPP para algoritmos de enrutamiento"""
    
    def __init__(self, jid: str, password: str, node_name: str):
        self.jid = jid
        self.password = password
        self.node_name = node_name
        self.connected = False
        
        # Callbacks para diferentes tipos de mensajes
        self.message_handlers: Dict[str, Callable] = {}
        
        # Cola de mensajes entrantes
        self.incoming_messages = asyncio.Queue()
        
        # Información del nodo
        self.neighbors = {}  # {neighbor_jid: cost}
        self.routing_table = {}
        
        # Estadísticas
        self.messages_sent = 0
        self.messages_received = 0
        
        if XMPP_AVAILABLE:
            self.xmpp_client = XMPPClient(self.jid, self.password, self)
        else:
            self.xmpp_client = None
            print("⚠️ Modo OFFLINE: XMPP no disponible")
    
    async def connect(self) -> bool:
        """Conecta al servidor XMPP"""
        if not XMPP_AVAILABLE:
            print("❌ No se puede conectar: XMPP no disponible")
            return False
        
        try:
            await self.xmpp_client.connect()
            self.connected = True
            print(f"✅ Conectado como {self.jid}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    async def disconnect(self):
        """Desconecta del servidor XMPP"""
        if self.xmpp_client:
            await self.xmpp_client.disconnect()
        self.connected = False
        print("🔌 Desconectado de XMPP")
    
    def register_handler(self, message_type: str, handler: Callable):
        """Registra un handler para un tipo de mensaje específico"""
        self.message_handlers[message_type] = handler
        print(f"📝 Handler registrado para {message_type}")
    
    async def send_message(self, message: NetworkMessage) -> bool:
        """Envía un mensaje via XMPP"""
        try:
            if not self.connected:
                print("❌ No conectado a XMPP")
                return False
            
            # Validar mensaje
            if not ProtocolValidator.validate_message(message):
                print("❌ Mensaje inválido")
                return False
            
            # Enviar via XMPP
            json_message = message.to_json()
            
            if message.to_addr == "broadcast":
                # Enviar a todos los vecinos
                for neighbor in self.neighbors:
                    await self._send_to_jid(neighbor, json_message)
            else:
                await self._send_to_jid(message.to_addr, json_message)
            
            self.messages_sent += 1
            print(f"📤 Mensaje {message.type} enviado a {message.to_addr}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    async def _send_to_jid(self, to_jid: str, message_content: str):
        """Envía mensaje a un JID específico"""
        if self.xmpp_client:
            await self.xmpp_client.send_message(to_jid, message_content)
    
    async def process_incoming_message(self, from_jid: str, message_content: str):
        """Procesa un mensaje entrante"""
        try:
            # Parsear mensaje JSON
            message = NetworkMessage.from_json(message_content)
            
            # Validar mensaje
            if not ProtocolValidator.validate_message(message):
                print(f"⚠️ Mensaje inválido de {from_jid}")
                return
            
            self.messages_received += 1
            print(f"📥 Mensaje {message.type} recibido de {from_jid}")
            
            # Verificar TTL
            if not message.decrement_ttl():
                print(f"⏰ TTL expirado para mensaje de {from_jid}")
                return
            
            # Llamar handler específico si existe
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](message, from_jid)
            else:
                # Handler por defecto
                await self._default_message_handler(message, from_jid)
                
        except Exception as e:
            print(f"❌ Error procesando mensaje de {from_jid}: {e}")
    
    async def _default_message_handler(self, message: NetworkMessage, from_jid: str):
        """Handler por defecto para mensajes"""
        print(f"📨 Mensaje no manejado: {message.type} de {from_jid}")
        print(f"   Payload: {message.payload}")
    
    # Métodos de conveniencia para enviar diferentes tipos de mensajes
    async def send_hello(self, to_jid: str, node_info: Dict):
        """Envía mensaje HELLO"""
        message = MessageFactory.create_hello_message(self.jid, to_jid, node_info)
        return await self.send_message(message)
    
    async def send_ping(self, to_jid: str, ping_id: str):
        """Envía mensaje PING"""
        message = MessageFactory.create_ping_message(self.jid, to_jid, ping_id)
        return await self.send_message(message)
    
    async def send_data(self, to_jid: str, user_message: str, proto: str = "lsr"):
        """Envía mensaje de datos"""
        message = MessageFactory.create_data_message(self.jid, to_jid, user_message, proto)
        return await self.send_message(message)
    
    async def send_lsp(self, lsp_data: Dict):
        """Envía LSP (broadcast)"""
        message = MessageFactory.create_lsp_message(self.jid, lsp_data)
        return await self.send_message(message)
    
    async def send_distance_vector(self, to_jid: str, distance_vector: Dict):
        """Envía Distance Vector"""
        message = MessageFactory.create_dv_message(self.jid, to_jid, distance_vector)
        return await self.send_message(message)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del cliente"""
        return {
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "neighbors": len(self.neighbors),
            "jid": self.jid,
            "node_name": self.node_name
        }

class XMPPClient:
    """Wrapper para slixmpp client"""
    
    def __init__(self, jid: str, password: str, routing_client):
        if not XMPP_AVAILABLE:
            return
            
        self.routing_client = routing_client
        
        class RoutingBot(slixmpp.ClientXMPP):
            def __init__(self, jid, password, parent):
                super().__init__(jid, password)
                self.parent = parent
                self.add_event_handler("session_start", self.session_start)
                self.add_event_handler("message", self.message)
            
            async def session_start(self, event):
                self.send_presence()
                await self.get_roster()
                print(f"✅ Sesión XMPP iniciada para {self.boundjid}")
            
            async def message(self, msg):
                if msg['type'] in ('chat', 'normal'):
                    await self.parent.routing_client.process_incoming_message(
                        str(msg['from']), 
                        str(msg['body'])
                    )
        
        self.bot = RoutingBot(jid, password, self)
    
    async def connect(self):
        """Conecta al servidor XMPP"""
        if self.bot:
            await self.bot.connect()
    
    async def disconnect(self):
        """Desconecta del servidor XMPP"""
        if self.bot:
            await self.bot.disconnect()
    
    async def send_message(self, to_jid: str, message: str):
        """Envía mensaje via XMPP"""
        if self.bot:
            self.bot.send_message(mto=to_jid, mbody=message, mtype='chat')

# Función de utilidad para testing sin XMPP
class OfflineXMPPClient:
    """Cliente simulado para testing offline"""
    
    def __init__(self, jid: str, password: str, node_name: str):
        self.client = XMPPRoutingClient(jid, password, node_name)
        self.client.connected = True  # Simular conexión
        print(f"🔧 Cliente OFFLINE creado: {jid}")
    
    async def simulate_message_exchange(self, other_client, message_type: str = "hello"):
        """Simula intercambio de mensajes entre clientes"""
        if message_type == "hello":
            message = MessageFactory.create_hello_message(
                self.client.jid,
                other_client.client.jid,
                {"node_id": self.client.node_name}
            )
        elif message_type == "ping":
            message = MessageFactory.create_ping_message(
                self.client.jid,
                other_client.client.jid,
                f"ping_{int(time.time())}"
            )
        else:
            message = MessageFactory.create_data_message(
                self.client.jid,
                other_client.client.jid,
                "Mensaje de prueba offline"
            )
        
        # Simular envío
        print(f"📤 {self.client.jid} -> {other_client.client.jid}: {message.type}")
        
        # Simular recepción
        await other_client.client.process_incoming_message(
            self.client.jid, 
            message.to_json()
        )

# Ejemplo de uso
if __name__ == "__main__":
    async def main():
        print("=== CLIENTE XMPP PARA ENRUTAMIENTO ===")
        
        if XMPP_AVAILABLE:
            # Cliente XMPP real (requiere servidor XMPP)
            client = XMPPRoutingClient(
                "node_a@localhost",
                "password123", 
                "A"
            )
            
            # Registrar handlers
            async def handle_hello(message, from_jid):
                print(f"🤝 HELLO recibido de {from_jid}: {message.payload}")
            
            client.register_handler("hello", handle_hello)
            
            # Conectar (comentado para demo)
            # await client.connect()
            print("✅ Cliente XMPP configurado")
            
        else:
            # Demo offline
            client_a = OfflineXMPPClient("node_a@server.com", "pass", "A")
            client_b = OfflineXMPPClient("node_b@server.com", "pass", "B")
            
            # Simular intercambio
            await client_a.simulate_message_exchange(client_b, "hello")
            await client_b.simulate_message_exchange(client_a, "ping")
            
            print(f"\nEstadísticas A: {client_a.client.get_stats()}")
            print(f"Estadísticas B: {client_b.client.get_stats()}")
    
    asyncio.run(main())
