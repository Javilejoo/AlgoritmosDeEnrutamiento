"""
Demo simple del protocolo de red distribuida
Muestra los mensajes init, message, done funcionando
"""

import asyncio
import time
from network_protocol import NetworkMessageFactory, NetworkProtocolValidator

async def simple_protocol_demo():
    """Demo simple del protocolo"""
    print("🌐 === DEMO PROTOCOLO DE RED DISTRIBUIDA ===\n")
    
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
    nodos = ["A", "B", "C"]
    for nodo in nodos:
        neighbors = {n: 5 for n in nodos if n != nodo}
        init = NetworkMessageFactory.create_init_message(nodo, neighbors)
        print(f"  {nodo} envía INIT a sus vecinos")
        await asyncio.sleep(0.5)
    
    print("\nFASE 2: Nodos calculan rutas")
    for nodo in nodos:
        print(f"  {nodo} calculando rutas...")
        await asyncio.sleep(0.3)
    
    print("\nFASE 3: Nodos envían DONE")
    for nodo in nodos:
        done = NetworkMessageFactory.create_done_message(nodo)
        print(f"  {nodo} envía DONE - cálculos terminados")
        await asyncio.sleep(0.3)
    
    print("\nFASE 4: Intercambio de mensajes")
    mensajes_demo = [
        ("A", "C", "Hola desde A"),
        ("C", "A", "Respuesta desde C"),
        ("B", "C", "Mensaje de B para C")
    ]
    
    for origen, destino, contenido in mensajes_demo:
        message = NetworkMessageFactory.create_message(origen, destino, contenido)
        print(f"  {origen} → {destino}: {contenido}")
        await asyncio.sleep(0.5)
    
    print("\n✅ Demo completado exitosamente!")
    print("\n📋 RESUMEN:")
    print("  ✓ Protocolo INIT - Nodos se presentan")
    print("  ✓ Cálculo de rutas")  
    print("  ✓ Protocolo DONE - Convergencia")
    print("  ✓ Intercambio de mensajes")
    
def show_protocol_specification():
    """Muestra la especificación del protocolo"""
    print("\n📋 ESPECIFICACIÓN DEL PROTOCOLO:")
    print("="*50)
    
    print("\n1. MENSAJE INIT:")
    print("   Propósito: Nodo se presenta ante sus vecinos")
    print("   Formato:")
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
    print("   Formato:")
    print("   {")
    print('     "type": "message",')
    print('     "origin": "<nodo_origen>",')
    print('     "destination": "<nodo_destino>",')
    print('     "ttl": <tiempo_vida>,')
    print('     "content": "<contenido>"')
    print("   }")
    
    print("\n3. MENSAJE DONE:")
    print("   Propósito: Indicar que terminó cálculos")
    print("   Formato:")
    print("   {")
    print('     "type": "done",')
    print('     "whoAmI": "<nodo_id>"')
    print("   }")

async def main():
    """Función principal"""
    print("🌐 SISTEMA DE ENRUTAMIENTO DISTRIBUIDO")
    print("Protocolo específico para algoritmos Flooding y LSR")
    print("="*60)
    
    while True:
        print("\n📋 OPCIONES:")
        print("1. Demo del protocolo")
        print("2. Ver especificación del protocolo")
        print("3. Sistema completo")
        print("0. Salir")
        
        choice = input("\nSeleccione opción: ").strip()
        
        if choice == "1":
            await simple_protocol_demo()
        elif choice == "2":
            show_protocol_specification()
        elif choice == "3":
            print("🚀 Iniciando sistema completo...")
            from main_routing_system import main as routing_main
            await routing_main()
            break
        elif choice == "0":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    asyncio.run(main())
