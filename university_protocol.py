"""
Protocolo específico para compartir nodos en la Universidad
Implementa los tipos de mensaje: init, message, done
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class UniversityMessage:
    """Mensaje según protocolo universitario"""
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
    def from_json(cls, json_str: str) -> 'UniversityMessage':
        """Crea mensaje desde JSON"""
        data = json.loads(json_str)
        msg_type = data.pop("type")
        return cls(type=msg_type, data=data)

class UniversityMessageFactory:
    """Factory para crear mensajes del protocolo universitario"""
    
    @staticmethod
    def create_init_message(node_id: str, neighbours: Dict[str, int]) -> UniversityMessage:
        """Crea mensaje INIT cuando el nodo se presenta ante sus vecinos"""
        return UniversityMessage(
            type="init",
            data={
                "whoAmI": node_id,
                "neighbours": neighbours
            }
        )
    
    @staticmethod
    def create_message(origin: str, destination: str, content: str, ttl: int = 5) -> UniversityMessage:
        """Crea mensaje MESSAGE para enviar contenido entre nodos"""
        return UniversityMessage(
            type="message",
            data={
                "origin": origin,
                "destination": destination,
                "ttl": ttl,
                "content": content
            }
        )
    
    @staticmethod
    def create_done_message(node_id: str) -> UniversityMessage:
        """Crea mensaje DONE cuando terminó de calcular sus tablas"""
        return UniversityMessage(
            type="done",
            data={
                "whoAmI": node_id
            }
        )

class UniversityProtocolValidator:
    """Validador para mensajes del protocolo universitario"""
    
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
    def validate_university_message(message: UniversityMessage) -> bool:
        """Valida cualquier mensaje del protocolo universitario"""
        if message.type == "init":
            return UniversityProtocolValidator.validate_init_message(message.data)
        elif message.type == "message":
            return UniversityProtocolValidator.validate_message(message.data)
        elif message.type == "done":
            return UniversityProtocolValidator.validate_done_message(message.data)
        else:
            return False

# Ejemplo de uso
if __name__ == "__main__":
    print("=== PROTOCOLO UNIVERSITARIO ===\n")
    
    # Ejemplo INIT
    init_msg = UniversityMessageFactory.create_init_message(
        "nodo1",
        {"nodo2": 5, "nodo3": 10}
    )
    print("MENSAJE INIT:")
    print(init_msg.to_json())
    print()
    
    # Ejemplo MESSAGE
    message_msg = UniversityMessageFactory.create_message(
        "nodo1",
        "nodo2", 
        "asdflkjalsdkfjalksjdf",
        5
    )
    print("MENSAJE MESSAGE:")
    print(message_msg.to_json())
    print()
    
    # Ejemplo DONE
    done_msg = UniversityMessageFactory.create_done_message("nodo1")
    print("MENSAJE DONE:")
    print(done_msg.to_json())
    print()
    
    # Validación
    print("Validaciones:")
    print(f"INIT válido: {UniversityProtocolValidator.validate_university_message(init_msg)}")
    print(f"MESSAGE válido: {UniversityProtocolValidator.validate_university_message(message_msg)}")
    print(f"DONE válido: {UniversityProtocolValidator.validate_university_message(done_msg)}")
