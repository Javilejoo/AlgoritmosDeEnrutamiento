"""
Demo directo del protocolo de red distribuida
Se ejecuta automáticamente sin menús
"""

import asyncio
import time
from network_protocol import NetworkMessageFactory, NetworkProtocolValidator

async def ejecutar_demo_completo():
    """Ejecuta el demo completo automáticamente"""
    print("🌐 === DEMO PROTOCOLO DE RED DISTRIBUIDA ===")
    print("Ejecutándose automáticamente...\n")
    
    # 1. Demostrar creación de mensajes
    print("📝 1. CREACIÓN DE MENSAJES:")
    print("-" * 40)
    
    # Mensaje INIT
    init_msg = NetworkMessageFactory.create_init_message("A", {"B": 5, "C": 10})
    print("MENSAJE INIT:")
    print(init_msg.to_json())
    print()
    
    # Mensaje MESSAGE  
    msg = NetworkMessageFactory.create_message("A", "C", "Hola desde A para C", 5)
    print("MENSAJE MESSAGE:")
    print(msg.to_json())
    print()
    
    # Mensaje DONE
    done_msg = NetworkMessageFactory.create_done_message("A")
    print("MENSAJE DONE:")
    print(done_msg.to_json())
    print()
    
    # 2. Validar mensajes
    print("✅ 2. VALIDACIÓN DE MENSAJES:")
    print("-" * 40)
    print(f"INIT válido: {NetworkProtocolValidator.validate_network_message(init_msg)}")
    print(f"MESSAGE válido: {NetworkProtocolValidator.validate_network_message(msg)}")
    print(f"DONE válido: {NetworkProtocolValidator.validate_network_message(done_msg)}")
    print()
    
    # 3. Simular flujo de protocolo
    print("🔄 3. SIMULACIÓN DE FLUJO DE PROTOCOLO:")
    print("-" * 40)
    
    # Fase INIT
    print("FASE 1: Nodos se presentan (INIT)")
    nodos = ["A", "B", "C", "D"]
    for nodo in nodos:
        neighbors = {}
        if nodo == "A":
            neighbors = {"B": 1}
        elif nodo == "B":
            neighbors = {"A": 1, "C": 1}
        elif nodo == "C":
            neighbors = {"B": 1, "D": 1}
        elif nodo == "D":
            neighbors = {"C": 1}
            
        init = NetworkMessageFactory.create_init_message(nodo, neighbors)
        print(f"  {nodo} envía INIT a vecinos: {list(neighbors.keys())}")
        await asyncio.sleep(0.5)
    
    print("\nFASE 2: Nodos calculan rutas usando algoritmo LSR")
    print("  A: Calculando rutas a B(1), C(2), D(3)")
    await asyncio.sleep(0.5)
    print("  B: Calculando rutas a A(1), C(1), D(2)")
    await asyncio.sleep(0.5)
    print("  C: Calculando rutas a A(2), B(1), D(1)")
    await asyncio.sleep(0.5)
    print("  D: Calculando rutas a A(3), B(2), C(1)")
    await asyncio.sleep(0.5)
    
    print("\nFASE 3: Nodos envían DONE")
    for nodo in nodos:
        done = NetworkMessageFactory.create_done_message(nodo)
        print(f"  {nodo} envía DONE - cálculos terminados")
        await asyncio.sleep(0.3)
    
    print("\nFASE 4: Intercambio de mensajes en red A-B-C-D")
    mensajes_demo = [
        ("A", "D", "Mensaje de extremo a extremo"),
        ("D", "A", "Respuesta de vuelta"),
        ("B", "C", "Mensaje entre vecinos"),
        ("A", "C", "Mensaje con 2 saltos")
    ]
    
    for origen, destino, contenido in mensajes_demo:
        message = NetworkMessageFactory.create_message(origen, destino, contenido)
        print(f"  📨 {origen} → {destino}: {contenido}")
        await asyncio.sleep(0.5)
    
    print("\n✅ Demo completado exitosamente!")
    print("\n📋 RESUMEN DEL PROTOCOLO:")
    print("  ✓ INIT - Nodos se presentan con sus vecinos")
    print("  ✓ LSR - Cálculo de rutas más cortas")  
    print("  ✓ DONE - Convergencia del algoritmo")
    print("  ✓ MESSAGE - Intercambio de datos")
    
    print("\n📋 ESPECIFICACIÓN TÉCNICA:")
    print("="*50)
    
    print("\n1. MENSAJE INIT:")
    print("   Propósito: Nodo anuncia su presencia y vecinos")
    print("   Formato JSON:")
    print("   {")
    print('     "type": "init",')
    print('     "whoAmI": "<nodo_id>",')
    print('     "neighbours": {')
    print('       "<vecino1>": <costo>,')
    print('       "<vecino2>": <costo>')
    print("     }")
    print("   }")
    
    print("\n2. MENSAJE MESSAGE:")
    print("   Propósito: Enviar datos entre nodos")
    print("   Formato JSON:")
    print("   {")
    print('     "type": "message",')
    print('     "origin": "<nodo_origen>",')
    print('     "destination": "<nodo_destino>",')
    print('     "ttl": <tiempo_vida>,')
    print('     "content": "<datos>"')
    print("   }")
    
    print("\n3. MENSAJE DONE:")
    print("   Propósito: Indicar convergencia")
    print("   Formato JSON:")
    print("   {")
    print('     "type": "done",')
    print('     "whoAmI": "<nodo_id>"')
    print("   }")
    
    print("\n🎯 ALGORITMOS SOPORTADOS:")
    print("  • Flooding - Inundación de mensajes")
    print("  • LSR (Link State Routing) - Estado de enlaces")
    print("  • Enrutamiento distribuido con convergencia")

if __name__ == "__main__":
    print("🚀 Iniciando demo automático...")
    asyncio.run(ejecutar_demo_completo())
    print("\n🏁 Demo finalizado. Presiona Enter para continuar...")
    input()
