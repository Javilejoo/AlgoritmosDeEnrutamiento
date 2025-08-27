"""
Protocolo de red distribuida para algoritmos de enrutamiento
Implementa los tipos de mensaje: init, message, done
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class NetworkMessage:
    """Mensaje según protocolo de red distribuida"""
    type: str  # "init", "message", "done"
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """Convierte a JSON"""
        message_dict = {"type": self.type, **self.data}
        return json.dumps(message_dict, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """Crea mensaje desde JSON"""
        data = json.loads(json_str)
        msg_type = data.pop("type")
        return cls(type=msg_type, data=data)

class NetworkMessageFactory:
    """Factory para crear mensajes del protocolo de red distribuida"""
    
    @staticmethod
    def create_init_message(node_id: str, neighbours: Dict[str, int]) -> NetworkMessage:
        """Crea mensaje INIT cuando el nodo se presenta ante sus vecinos"""
        return NetworkMessage(
            type="init",
            data={
                "whoAmI": node_id,
                "neighbours": neighbours
            }
        )
    
    @staticmethod
    def create_message(origin: str, destination: str, content: str, ttl: int = 5) -> NetworkMessage:
        """Crea mensaje MESSAGE para enviar contenido entre nodos"""
        return NetworkMessage(
            type="message",
            data={
                "origin": origin,
                "destination": destination,
                "ttl": ttl,
                "content": content
            }
        )
    
    @staticmethod
    def create_done_message(node_id: str) -> NetworkMessage:
        """Crea mensaje DONE cuando terminó de calcular sus tablas"""
        return NetworkMessage(
            type="done",
            data={
                "whoAmI": node_id
            }
        )

class NetworkProtocolValidator:
    """Validador para mensajes del protocolo de red distribuida"""
    
    @staticmethod
    def validate_init_message(data: Dict) -> bool:
        """Valida mensaje INIT"""
        required_fields = ["whoAmI", "neighbours"]
        if not all(field in data for field in required_fields):
            return False
        
        if not isinstance(data["neighbours"], dict):
            return False
        
        # Verificar que los costos sean números
        for neighbor, cost in data["neighbours"].items():
            if not isinstance(cost, (int, float)) or cost < 0:
                return False
        
        return True
    
    @staticmethod
    def validate_message(data: Dict) -> bool:
        """Valida mensaje MESSAGE"""
        required_fields = ["origin", "destination", "ttl", "content"]
        if not all(field in data for field in required_fields):
            return False
        
        if not isinstance(data["ttl"], int) or data["ttl"] < 0:
            return False
        
        return True
    
    @staticmethod
    def validate_done_message(data: Dict) -> bool:
        """Valida mensaje DONE"""
        return "whoAmI" in data
    
    @staticmethod
    def validate_network_message(message: NetworkMessage) -> bool:
        """Valida cualquier mensaje del protocolo de red distribuida"""
        if message.type == "init":
            return NetworkProtocolValidator.validate_init_message(message.data)
        elif message.type == "message":
            return NetworkProtocolValidator.validate_message(message.data)
        elif message.type == "done":
            return NetworkProtocolValidator.validate_done_message(message.data)
        else:
            return False

# Ejemplo de uso
if __name__ == "__main__":
    print("=== PROTOCOLO DE RED DISTRIBUIDA ===\n")
    
    # Ejemplo INIT
    init_msg = NetworkMessageFactory.create_init_message(
        "nodo1",
        {"nodo2": 5, "nodo3": 10}
    )
    print("MENSAJE INIT:")
    print(init_msg.to_json())
    print()
    
    # Ejemplo MESSAGE
    message_msg = NetworkMessageFactory.create_message(
        "nodo1",
        "nodo2", 
        "asdflkjalsdkfjalksjdf",
        5
    )
    print("MENSAJE MESSAGE:")
    print(message_msg.to_json())
    print()
    
    # Ejemplo DONE
    done_msg = NetworkMessageFactory.create_done_message("nodo1")
    print("MENSAJE DONE:")
    print(done_msg.to_json())
    print()
    
    # Validación
    print("Validaciones:")
    print(f"INIT válido: {NetworkProtocolValidator.validate_network_message(init_msg)}")
    print(f"MESSAGE válido: {NetworkProtocolValidator.validate_network_message(message_msg)}")
    print(f"DONE válido: {NetworkProtocolValidator.validate_network_message(done_msg)}")
