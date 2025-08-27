"""
Definición del protocolo de comunicación para algoritmos de enrutamiento
Basado en JSON con estructura estándar para interoperabilidad
"""

import json
import time
from typing import Dict, List, Optional, Any
from enum import Enum

class ProtocolType(Enum):
    """Tipos de protocolo soportados"""
    DIJKSTRA = "dijkstra"
    FLOODING = "flooding"
    LSR = "lsr"  # Link State Routing
    DVR = "dvr"  # Distance Vector Routing

class MessageType(Enum):
    """Tipos de mensaje soportados"""
    MESSAGE = "message"     # Mensaje de usuario
    ECHO = "echo"          # Echo/Ping
    INFO = "info"          # Información de tablas/ruteo
    HELLO = "hello"        # Descubrimiento de nodos
    TABLE = "table"        # Información de tablas
    DATA = "data"          # Datos de usuario
    LSP = "lsp"           # Link State Packet
    DV = "dv"             # Distance Vector
    ACK = "ack"           # Confirmación

class NetworkMessage:
    """Clase para manejar mensajes de red según el protocolo definido"""
    
    def __init__(self, proto: str, msg_type: str, from_addr: str, to_addr: str, 
                 payload: Any, ttl: int = 5, headers: Optional[List[Dict]] = None):
        self.proto = proto
        self.type = msg_type
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.ttl = ttl
        self.headers = headers or []
        self.payload = payload
        self.timestamp = time.time()
        
    def to_json(self) -> str:
        """Convierte el mensaje a JSON"""
        message_dict = {
            "proto": self.proto,
            "type": self.type,
            "from": self.from_addr,
            "to": self.to_addr,
            "ttl": self.ttl,
            "headers": self.headers,
            "payload": self.payload,
            "timestamp": self.timestamp
        }
        return json.dumps(message_dict, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """Crea un mensaje desde JSON"""
        data = json.loads(json_str)
        msg = cls(
            proto=data["proto"],
            msg_type=data["type"],
            from_addr=data["from"],
            to_addr=data["to"],
            payload=data["payload"],
            ttl=data.get("ttl", 5),
            headers=data.get("headers", [])
        )
        msg.timestamp = data.get("timestamp", time.time())
        return msg
    
    def decrement_ttl(self) -> bool:
        """Decrementa TTL y retorna True si aún es válido"""
        self.ttl -= 1
        return self.ttl > 0
    
    def add_header(self, key: str, value: Any):
        """Agrega un header al mensaje"""
        self.headers.append({key: value})

class MessageFactory:
    """Factory para crear diferentes tipos de mensajes"""
    
    @staticmethod
    def create_hello_message(from_addr: str, to_addr: str, node_info: Dict) -> NetworkMessage:
        """Crea un mensaje HELLO para descubrimiento de nodos"""
        return NetworkMessage(
            proto=ProtocolType.LSR.value,
            msg_type=MessageType.HELLO.value,
            from_addr=from_addr,
            to_addr=to_addr,
            payload=node_info,
            ttl=1  # HELLO solo para vecinos directos
        )
    
    @staticmethod
    def create_ping_message(from_addr: str, to_addr: str, ping_id: str) -> NetworkMessage:
        """Crea un mensaje PING para medir latencia"""
        return NetworkMessage(
            proto=ProtocolType.LSR.value,
            msg_type=MessageType.ECHO.value,
            from_addr=from_addr,
            to_addr=to_addr,
            payload={"ping_id": ping_id, "timestamp": time.time()},
            ttl=10
        )
    
    @staticmethod
    def create_lsp_message(from_addr: str, lsp_data: Dict) -> NetworkMessage:
        """Crea un mensaje LSP para Link State Routing"""
        return NetworkMessage(
            proto=ProtocolType.LSR.value,
            msg_type=MessageType.LSP.value,
            from_addr=from_addr,
            to_addr="broadcast",  # LSP se envía a todos
            payload=lsp_data,
            ttl=10
        )
    
    @staticmethod
    def create_dv_message(from_addr: str, to_addr: str, distance_vector: Dict) -> NetworkMessage:
        """Crea un mensaje Distance Vector"""
        return NetworkMessage(
            proto=ProtocolType.DVR.value,
            msg_type=MessageType.DV.value,
            from_addr=from_addr,
            to_addr=to_addr,
            payload={"distance_vector": distance_vector},
            ttl=2  # Solo para vecinos
        )
    
    @staticmethod
    def create_data_message(from_addr: str, to_addr: str, user_message: str, 
                          proto: str = ProtocolType.LSR.value) -> NetworkMessage:
        """Crea un mensaje de datos de usuario"""
        return NetworkMessage(
            proto=proto,
            msg_type=MessageType.DATA.value,
            from_addr=from_addr,
            to_addr=to_addr,
            payload={"message": user_message},
            ttl=15
        )
    
    @staticmethod
    def create_table_info_message(from_addr: str, to_addr: str, table_info: Dict) -> NetworkMessage:
        """Crea un mensaje con información de tablas"""
        return NetworkMessage(
            proto=ProtocolType.LSR.value,
            msg_type=MessageType.TABLE.value,
            from_addr=from_addr,
            to_addr=to_addr,
            payload=table_info,
            ttl=5
        )

class ProtocolValidator:
    """Validador para mensajes del protocolo"""
    
    @staticmethod
    def validate_message(message: NetworkMessage) -> bool:
        """Valida que el mensaje cumple con el protocolo"""
        try:
            # Validar campos requeridos
            if not all([message.proto, message.type, message.from_addr, 
                       message.to_addr, message.payload is not None]):
                return False
            
            # Validar tipos válidos
            valid_protos = [p.value for p in ProtocolType]
            valid_types = [t.value for t in MessageType]
            
            if message.proto not in valid_protos:
                return False
            
            if message.type not in valid_types:
                return False
            
            # Validar TTL
            if message.ttl < 0 or message.ttl > 255:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_json_message(json_str: str) -> bool:
        """Valida un mensaje JSON"""
        try:
            message = NetworkMessage.from_json(json_str)
            return ProtocolValidator.validate_message(message)
        except Exception:
            return False

# Ejemplo de uso y testing
if __name__ == "__main__":
    print("=== PROTOCOLO DE COMUNICACIÓN ===")
    
    # Crear diferentes tipos de mensajes
    hello_msg = MessageFactory.create_hello_message(
        "node_A@server.com/resource", 
        "node_B@server.com/resource",
        {"node_id": "A", "neighbors": ["B", "C"]}
    )
    
    ping_msg = MessageFactory.create_ping_message(
        "node_A@server.com/resource",
        "node_B@server.com/resource", 
        "ping_123"
    )
    
    data_msg = MessageFactory.create_data_message(
        "node_A@server.com/resource",
        "node_D@server.com/resource",
        "Hola, este es un mensaje de prueba!"
    )
    
    # Mostrar mensajes
    print("\n1. Mensaje HELLO:")
    print(hello_msg.to_json())
    
    print("\n2. Mensaje PING:")
    print(ping_msg.to_json())
    
    print("\n3. Mensaje DATA:")
    print(data_msg.to_json())
    
    # Validar mensajes
    print(f"\nValidación HELLO: {ProtocolValidator.validate_message(hello_msg)}")
    print(f"Validación PING: {ProtocolValidator.validate_message(ping_msg)}")
    print(f"Validación DATA: {ProtocolValidator.validate_message(data_msg)}")
