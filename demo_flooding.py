#!/usr/bin/env python3
"""
Demo específico del algoritmo de Flooding para cumplir con requerimientos del laboratorio
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flooding_algorithm import FloodingNode, demo_flooding_algorithm

async def demo_flooding_interactivo():
    """Demo interactivo del algoritmo de Flooding"""
    print("🌊 === ALGORITMO DE FLOODING - DEMO INTERACTIVO ===\n")
    
    print("El algoritmo de Flooding:")
    print("• Solo conoce sus vecinos directos")
    print("• Envía mensajes a TODOS los vecinos")
    print("• Cada nodo reenvía el mensaje a todos SUS vecinos")
    print("• Usa TTL y cache para evitar loops infinitos")
    print("• Garantiza que el mensaje llegue si existe una ruta\n")
    
    while True:
        print("Opciones disponibles:")
        print("1. Demo automático (topología lineal)")
        print("2. Demo automático (topología en anillo)")
        print("3. Demo automático (topología en estrella)")
        print("4. Explicación del algoritmo")
        print("5. Comparar con otros algoritmos")
        print("0. Salir")
        
        choice = input("\n👉 Selecciona una opción: ").strip()
        
        if choice == "1":
            await demo_linear_flooding()
        elif choice == "2":
            await demo_ring_flooding()
        elif choice == "3":
            await demo_star_flooding()
        elif choice == "4":
            explain_flooding_algorithm()
        elif choice == "5":
            await compare_with_other_algorithms()
        elif choice == "0":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")
        
        input("\n⏎ Presiona Enter para continuar...")

async def demo_linear_flooding():
    """Demo con topología lineal: A - B - C - D - E"""
    print("\n🌊 === DEMO FLOODING: TOPOLOGÍA LINEAL ===")
    print("Topología: A - B - C - D - E\n")
    
    from routing_node import NeighborInfo
    import time
    
    # Crear nodos
    nodes = {}
    for i, node_id in enumerate(["A", "B", "C", "D", "E"], 1):
        nodes[node_id] = FloodingNode(node_id, 65100 + i)
    
    # Configurar topología lineal
    connections = [
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")
    ]
    
    for n1, n2 in connections:
        nodes[n1].neighbors[n2] = NeighborInfo(n2, 1, time.time())
        nodes[n2].neighbors[n1] = NeighborInfo(n1, 1, time.time())
    
    try:
        # Iniciar nodos
        print("🚀 Iniciando nodos...")
        for node in nodes.values():
            await node.start()
        
        await asyncio.sleep(2)
        
        # Enviar mensaje de extremo a extremo
        print("📤 Enviando mensaje de A hacia E...")
        await nodes["A"].send_user_message("E", "¡Hola E! Mensaje desde A usando flooding")
        
        await asyncio.sleep(5)
        
        print("\n📊 Análisis del flooding:")
        print("• A envía a B")
        print("• B reenvía a A (ya visto) y C")
        print("• C reenvía a B (ya visto) y D")
        print("• D reenvía a C (ya visto) y E")
        print("• E recibe el mensaje ✅")
        
        print("\n📊 ESTADÍSTICAS:")
        for node_id, node in nodes.items():
            status = node.get_status()
            print(f"   {node_id}: {status['packets_forwarded']} reenviados, {status['packets_received']} recibidos")
        
    finally:
        for node in nodes.values():
            await node.stop()

async def demo_ring_flooding():
    """Demo con topología en anillo: A - B - C - D - A"""
    print("\n🌊 === DEMO FLOODING: TOPOLOGÍA EN ANILLO ===")
    print("Topología: A - B - C - D - A (anillo)\n")
    
    from routing_node import NeighborInfo
    import time
    
    # Crear nodos
    nodes = {}
    for i, node_id in enumerate(["A", "B", "C", "D"], 1):
        nodes[node_id] = FloodingNode(node_id, 65200 + i)
    
    # Configurar anillo
    connections = [
        ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")
    ]
    
    for n1, n2 in connections:
        nodes[n1].neighbors[n2] = NeighborInfo(n2, 1, time.time())
        nodes[n2].neighbors[n1] = NeighborInfo(n1, 1, time.time())
    
    try:
        print("🚀 Iniciando nodos...")
        for node in nodes.values():
            await node.start()
        
        await asyncio.sleep(2)
        
        print("📤 Enviando mensaje de A hacia C...")
        await nodes["A"].send_user_message("C", "Mensaje de A para C en anillo")
        
        await asyncio.sleep(5)
        
        print("\n📊 Análisis del flooding en anillo:")
        print("• A envía a B y D (sus dos vecinos)")
        print("• B reenvía a C, D reenvía a C")
        print("• C recibe de ambos lados ✅")
        print("• Flooding garantiza entrega por ambas rutas")
        
        print("\n📊 ESTADÍSTICAS:")
        for node_id, node in nodes.items():
            status = node.get_status()
            print(f"   {node_id}: {status['packets_forwarded']} reenviados, {status['packets_received']} recibidos")
        
    finally:
        for node in nodes.values():
            await node.stop()

async def demo_star_flooding():
    """Demo con topología en estrella: B, C, D conectados a A"""
    print("\n🌊 === DEMO FLOODING: TOPOLOGÍA EN ESTRELLA ===")
    print("Topología: B-A-C, D-A (A es el centro)\n")
    
    from routing_node import NeighborInfo
    import time
    
    # Crear nodos
    nodes = {}
    for i, node_id in enumerate(["A", "B", "C", "D"], 1):
        nodes[node_id] = FloodingNode(node_id, 65300 + i)
    
    # Configurar estrella (A en el centro)
    connections = [
        ("A", "B"), ("A", "C"), ("A", "D")
    ]
    
    for n1, n2 in connections:
        nodes[n1].neighbors[n2] = NeighborInfo(n2, 1, time.time())
        nodes[n2].neighbors[n1] = NeighborInfo(n1, 1, time.time())
    
    try:
        print("🚀 Iniciando nodos...")
        for node in nodes.values():
            await node.start()
        
        await asyncio.sleep(2)
        
        print("📤 Enviando mensaje de B hacia D (a través del centro A)...")
        await nodes["B"].send_user_message("D", "De B para D vía centro A")
        
        await asyncio.sleep(5)
        
        print("\n📊 Análisis del flooding en estrella:")
        print("• B envía a A (su único vecino)")
        print("• A reenvía a C y D (sus otros vecinos)")
        print("• D recibe el mensaje ✅")
        print("• C también lo recibe pero lo ignora (no es el destino)")
        
        print("\n📊 ESTADÍSTICAS:")
        for node_id, node in nodes.items():
            status = node.get_status()
            print(f"   {node_id}: {status['packets_forwarded']} reenviados, {status['packets_received']} recibidos")
        
    finally:
        for node in nodes.values():
            await node.stop()

def explain_flooding_algorithm():
    """Explica cómo funciona el algoritmo de flooding"""
    print("\n📚 === EXPLICACIÓN DEL ALGORITMO DE FLOODING ===\n")
    
    print("🌊 PRINCIPIO BÁSICO:")
    print("   Flooding envía el mensaje a TODOS los vecinos conocidos")
    print("   Cada nodo que recibe el mensaje lo reenvía a TODOS sus vecinos")
    print("   Continúa hasta que todos los nodos alcanzables han visto el mensaje\n")
    
    print("🔧 IMPLEMENTACIÓN:")
    print("   1. Solo requiere conocimiento de vecinos directos")
    print("   2. Cada mensaje tiene un ID único")
    print("   3. Los nodos mantienen cache de mensajes ya vistos")
    print("   4. TTL (Time To Live) previene loops infinitos")
    print("   5. No se reenvía al nodo que envió el mensaje\n")
    
    print("✅ VENTAJAS:")
    print("   • Simplicidad extrema")
    print("   • Garantiza entrega si existe ruta")
    print("   • No requiere mantener tablas de routing")
    print("   • Funciona incluso con topología desconocida")
    print("   • Tolerante a fallas de nodos individuales\n")
    
    print("❌ DESVENTAJAS:")
    print("   • Genera mucho tráfico de red")
    print("   • No es eficiente para redes grandes")
    print("   • Todos los nodos procesan todos los mensajes")
    print("   • Desperdicia ancho de banda")
    print("   • No proporciona la ruta más corta necesariamente\n")
    
    print("🎯 CASOS DE USO:")
    print("   • Redes pequeñas o con topología simple")
    print("   • Sistemas donde la entrega es más importante que la eficiencia")
    print("   • Protocolos de descubrimiento de red")
    print("   • Sistemas de emergencia")
    print("   • Como base para algoritmos más complejos (LSR)")

async def compare_with_other_algorithms():
    """Compara flooding con otros algoritmos"""
    print("\n⚖️ === COMPARACIÓN DE ALGORITMOS ===\n")
    
    print("🌊 FLOODING vs 🎯 DIJKSTRA:")
    print("   Flooding: Solo vecinos directos | Dijkstra: Topología completa")
    print("   Flooding: Envía a todos        | Dijkstra: Ruta más corta")
    print("   Flooding: Simple               | Dijkstra: Requiere cálculo")
    print("   Flooding: Mucho tráfico        | Dijkstra: Tráfico mínimo\n")
    
    print("🌊 FLOODING vs 🎯 DIJKSTRA:")
    print("   Flooding: Solo vecinos directos | Dijkstra: Topología completa")
    print("   Flooding: Envía a todos        | Dijkstra: Ruta más corta")
    print("   Flooding: Simple               | Dijkstra: Requiere cálculo")
    print("   Flooding: Mucho tráfico        | Dijkstra: Tráfico mínimo\n")
    
    print("🌊 FLOODING vs 🌐 LINK STATE:")
    print("   Flooding: Parte de LSR         | LSR: Usa flooding para LSPs")
    print("   Flooding: Datos de usuario     | LSR: Información de topología")
    print("   Flooding: Directo              | LSR: Flooding + Dijkstra")
    print("   Flooding: Siempre flooding     | LSR: Flooding solo para actualizaciones\n")
    
    print("📈 CUÁNDO USAR CADA UNO:")
    print("   🌊 Flooding: Redes muy pequeñas, sistemas simples")
    print("   🎯 Dijkstra: Cuando tienes topología completa")
    print("   🌐 LSR: Redes grandes, cambios frecuentes")

if __name__ == "__main__":
    try:
        asyncio.run(demo_flooding_interactivo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
