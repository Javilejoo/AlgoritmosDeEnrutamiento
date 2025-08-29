#!/usr/bin/env python3

import asyncio
from redis_protocol import RedisProtocolNode

async def test_node_creation():
    print("🔍 PRUEBA DE CONVERSIÓN DE MAYÚSCULAS")
    
    # Crear nodo con minúsculas
    node_id = "nodo10"
    print(f"Input original: '{node_id}'")
    
    # Crear el nodo
    node = RedisProtocolNode(node_id, "sec20", "topologia2")
    
    print(f"node_id almacenado: '{node.node_id}'")
    print(f"channel_name: '{node.channel_name}'")
    
    # Configurar vecinos
    neighbours = {"nodo2": 1, "nodo6": 2}
    print(f"Vecinos a configurar: {neighbours}")
    
    node.configure_neighbours(neighbours)
    print(f"Vecinos configurados: {node.neighbours}")
    
    # Probar envío de canal
    for neighbor in node.neighbours.keys():
        channel = f"channel:{node.seccion}.{node.topologia}.{neighbor}"
        print(f"Canal para {neighbor}: '{channel}'")

if __name__ == "__main__":
    asyncio.run(test_node_creation())
