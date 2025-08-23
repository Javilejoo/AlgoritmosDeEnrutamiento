"""
Pruebas comparativas entre Link State Routing y cálculo estático con Dijkstra
"""

import time
import json
from typing import Dict, List
from link_state import LinkStateNode, simulacion_link_state
from dijkstra import construir_tablas_para_todos, imprimir_tabla
from grafo import grafo

def crear_grafo_ejemplo():
    """Crea el grafo de ejemplo usado en el proyecto"""
    g = grafo()
    edges = [
        ("A","B",7), ("A","I",1), ("A","C",7), ("B","F",2), ("I","D",6),
        ("C","D",5), ("D","F",1), ("D","E",1), ("F","G",3), ("F","H",4), ("G","E",4),
    ]
    for a, b, w in edges:
        g.agregar_conexion(a, b, w)
    return g

def comparar_enrutamiento_estatico_vs_dinamico():
    """Compara el enrutamiento estático (Dijkstra) vs dinámico (Link State)"""
    
    print("="*80)
    print("COMPARACIÓN: ENRUTAMIENTO ESTÁTICO vs LINK STATE DINÁMICO")
    print("="*80)
    
    # 1. Calcular tablas estáticas con Dijkstra
    print("\n📊 PARTE 1: CÁLCULO ESTÁTICO CON DIJKSTRA")
    print("-" * 50)
    
    g = crear_grafo_ejemplo()
    print("Topología de red:")
    print(g)
    
    tablas_estaticas = construir_tablas_para_todos(g, incluir_ruta=True)
    
    print("\nTablas de enrutamiento estáticas calculadas:")
    for nodo in ['A', 'D', 'H']:
        imprimir_tabla(nodo, tablas_estaticas[nodo])
    
    # 2. Simular Link State
    print("\n🌐 PARTE 2: LINK STATE DINÁMICO")
    print("-" * 50)
    
    # Crear topología para Link State
    topologia_ls = {
        "A": {"B": 7, "I": 1, "C": 7},
        "B": {"A": 7, "F": 2},
        "C": {"A": 7, "D": 5},
        "D": {"I": 6, "C": 5, "F": 1, "E": 1},
        "E": {"D": 1, "G": 4},
        "F": {"B": 2, "D": 1, "G": 3, "H": 4},
        "G": {"F": 3, "E": 4},
        "H": {"F": 4},
        "I": {"A": 1, "D": 6}
    }
    
    # Crear nodos Link State
    nodos_ls = {}
    for name, neighbors in topologia_ls.items():
        nodos_ls[name] = LinkStateNode(name, neighbors)
    
    # Simular intercambio inicial de LSPs
    all_lsps = []
    for node in nodos_ls.values():
        all_lsps.append(node.lsdb.lsp_db[node.name])
    
    for node in nodos_ls.values():
        for lsp in all_lsps:
            if lsp.source != node.name:
                node.receive_lsp(lsp)
    
    print("\nTablas Link State después de convergencia inicial:")
    for nodo in ['A', 'D', 'H']:
        nodos_ls[nodo].print_routing_table()
    
    # 3. Comparar resultados
    print("\n🔍 PARTE 3: COMPARACIÓN DE RESULTADOS")
    print("-" * 50)
    
    diferencias_encontradas = False
    
    for nodo_origen in ['A', 'D', 'H']:
        print(f"\n--- Comparando rutas desde {nodo_origen} ---")
        
        # Obtener rutas estáticas
        rutas_estaticas = {}
        for destino, next_hop, costo, ruta in tablas_estaticas[nodo_origen]:
            if destino != nodo_origen and costo != float('inf'):
                rutas_estaticas[destino] = {
                    'next_hop': next_hop,
                    'costo': costo,
                    'ruta': ruta
                }
        
        # Obtener rutas Link State
        rutas_ls = nodos_ls[nodo_origen].routing_table
        
        # Comparar cada destino
        for destino in sorted(set(rutas_estaticas.keys()) | set(rutas_ls.keys())):
            if destino == nodo_origen:
                continue
                
            ruta_estatica = rutas_estaticas.get(destino)
            ruta_ls = rutas_ls.get(destino)
            
            if ruta_estatica and ruta_ls:
                # Ambos tienen ruta
                if (ruta_estatica['next_hop'] == ruta_ls['next_hop'] and 
                    abs(ruta_estatica['costo'] - ruta_ls['distance']) < 0.001):
                    print(f"  ✅ {destino}: Coinciden (next_hop={ruta_ls['next_hop']}, costo={ruta_ls['distance']})")
                else:
                    print(f"  ❌ {destino}: DIFERENCIA!")
                    print(f"     Estático: next_hop={ruta_estatica['next_hop']}, costo={ruta_estatica['costo']}")
                    print(f"     Link State: next_hop={ruta_ls['next_hop']}, costo={ruta_ls['distance']}")
                    diferencias_encontradas = True
            elif ruta_estatica:
                print(f"  ⚠️  {destino}: Solo en estático")
                diferencias_encontradas = True
            elif ruta_ls:
                print(f"  ⚠️  {destino}: Solo en Link State")
                diferencias_encontradas = True
    
    if not diferencias_encontradas:
        print("\n✅ RESULTADO: Las tablas coinciden perfectamente!")
        print("   Tanto Dijkstra estático como Link State producen los mismos resultados.")
    else:
        print("\n❌ RESULTADO: Se encontraron diferencias entre los métodos.")
    
    return nodos_ls

def probar_escenarios_dinamicos():
    """Prueba escenarios dinámicos que solo Link State puede manejar"""
    
    print("\n" + "="*80)
    print("PRUEBAS DE ESCENARIOS DINÁMICOS")
    print("="*80)
    
    # Crear red Link State
    topologia = {
        "A": {"B": 7, "I": 1, "C": 7},
        "B": {"A": 7, "F": 2},
        "C": {"A": 7, "D": 5},
        "D": {"I": 6, "C": 5, "F": 1, "E": 1},
        "E": {"D": 1, "G": 4},
        "F": {"B": 2, "D": 1, "G": 3, "H": 4},
        "G": {"F": 3, "E": 4},
        "H": {"F": 4},
        "I": {"A": 1, "D": 6}
    }
    
    nodos = {}
    for name, neighbors in topologia.items():
        nodos[name] = LinkStateNode(name, neighbors)
    
    # Convergencia inicial
    all_lsps = []
    for node in nodos.values():
        all_lsps.append(node.lsdb.lsp_db[node.name])
    
    for node in nodos.values():
        for lsp in all_lsps:
            if lsp.source != node.name:
                node.receive_lsp(lsp)
    
    print("\n🔧 ESCENARIO 1: Mejora de enlace")
    print("-" * 40)
    
    # Guardar ruta original A -> H
    ruta_original = nodos['A'].routing_table.get('H')
    if ruta_original:
        print(f"Ruta original A->H: {' -> '.join(ruta_original['path'])} (costo: {ruta_original['distance']})")
    
    # Mejorar enlace A-C (de 7 a 2)
    print("\nMejorando enlace A-C: costo 7 -> 2")
    nodos['A'].update_neighbor('C', 2)
    nodos['C'].update_neighbor('A', 2)
    
    # Propagar cambios
    new_lsps = [nodos['A'].lsdb.lsp_db['A'], nodos['C'].lsdb.lsp_db['C']]
    for node in nodos.values():
        if node.name not in ['A', 'C']:
            for lsp in new_lsps:
                node.receive_lsp(lsp)
    
    # Ver nueva ruta A -> H
    ruta_nueva = nodos['A'].routing_table.get('H')
    if ruta_nueva:
        print(f"Nueva ruta A->H: {' -> '.join(ruta_nueva['path'])} (costo: {ruta_nueva['distance']})")
        
        if ruta_original and ruta_nueva['distance'] < ruta_original['distance']:
            print("✅ Link State encontró automáticamente una ruta mejor!")
        elif ruta_original and abs(ruta_nueva['distance'] - ruta_original['distance']) < 0.001:
            print("ℹ️  El costo total se mantiene igual")
        else:
            print("⚠️  Cambio en enrutamiento detectado")
    
    print("\n🚫 ESCENARIO 2: Partición de red")
    print("-" * 40)
    
    # Desconectar nodo I de la red (eliminar enlaces I-A e I-D)
    print("Desconectando nodo I de la red...")
    nodos['I'].remove_neighbor('A')
    nodos['I'].remove_neighbor('D')
    nodos['A'].remove_neighbor('I')
    nodos['D'].remove_neighbor('I')
    
    # Propagar cambios
    partition_lsps = [
        nodos['I'].lsdb.lsp_db['I'],
        nodos['A'].lsdb.lsp_db['A'],
        nodos['D'].lsdb.lsp_db['D']
    ]
    
    for node in nodos.values():
        if node.name not in ['I', 'A', 'D']:
            for lsp in partition_lsps:
                node.receive_lsp(lsp)
    
    # Verificar conectividad
    print("\nVerificando conectividad después de partición:")
    for nodo_origen in ['A', 'B', 'F']:
        if 'I' in nodos[nodo_origen].routing_table:
            ruta_i = nodos[nodo_origen].routing_table['I']
            print(f"  {nodo_origen} -> I: {' -> '.join(ruta_i['path'])} (costo: {ruta_i['distance']})")
        else:
            print(f"  {nodo_origen} -> I: ❌ SIN CONECTIVIDAD")
    
    print("\n🔄 ESCENARIO 3: Reconexión con nueva topología")
    print("-" * 40)
    
    # Reconectar I pero solo con D y con costo diferente
    print("Reconectando I solo con D (costo 3 en lugar de 6)...")
    nodos['I'].update_neighbor('D', 3)
    nodos['D'].update_neighbor('I', 3)
    
    # Propagar reconexión
    reconnect_lsps = [nodos['I'].lsdb.lsp_db['I'], nodos['D'].lsdb.lsp_db['D']]
    for node in nodos.values():
        if node.name not in ['I', 'D']:
            for lsp in reconnect_lsps:
                node.receive_lsp(lsp)
    
    print("\nConectividad después de reconexión:")
    for nodo_origen in ['A', 'B', 'F']:
        if 'I' in nodos[nodo_origen].routing_table:
            ruta_i = nodos[nodo_origen].routing_table['I']
            print(f"  {nodo_origen} -> I: {' -> '.join(ruta_i['path'])} (costo: {ruta_i['distance']})")
        else:
            print(f"  {nodo_origen} -> I: ❌ SIN CONECTIVIDAD")
    
    return nodos

def analisis_convergencia():
    """Analiza el proceso de convergencia de Link State"""
    
    print("\n" + "="*80)
    print("ANÁLISIS DE CONVERGENCIA")
    print("="*80)
    
    print("\n📈 Ventajas del algoritmo Link State:")
    print("="*50)
    print("✓ Cada nodo tiene vista completa de la topología")
    print("✓ Cálculo independiente de rutas óptimas (Dijkstra)")
    print("✓ Convergencia rápida ante cambios")
    print("✓ No hay loops de enrutamiento")
    print("✓ Escalabilidad para redes grandes")
    
    print("\n📉 Desventajas y consideraciones:")
    print("="*50)
    print("⚠ Mayor uso de memoria (LSDB completa)")
    print("⚠ Mayor tráfico de control (flooding de LSPs)")
    print("⚠ Necesidad de números de secuencia y control de edad")
    print("⚠ Procesamiento más intensivo (múltiples Dijkstra)")
    
    print("\n🔄 Comparación con Distance Vector:")
    print("="*50)
    print("Link State vs Distance Vector:")
    print("• Información: Topología completa vs Solo distancias")
    print("• Convergencia: Rápida vs Lenta (count-to-infinity)")
    print("• Loops: No vs Posibles")
    print("• Escalabilidad: Mejor vs Limitada")
    print("• Complejidad: Mayor vs Menor")

def main():
    """Función principal que ejecuta todas las pruebas"""
    
    print("🚀 INICIANDO PRUEBAS COMPLETAS DEL ALGORITMO LINK STATE")
    print("="*80)
    
    # 1. Comparación estático vs dinámico
    nodos_comparacion = comparar_enrutamiento_estatico_vs_dinamico()
    
    # 2. Escenarios dinámicos
    nodos_dinamicos = probar_escenarios_dinamicos()
    
    # 3. Análisis de convergencia
    analisis_convergencia()
    
    # 4. Ejecutar simulación completa
    print("\n" + "="*80)
    print("EJECUTANDO SIMULACIÓN COMPLETA")
    print("="*80)
    
    nodos_simulacion = simulacion_link_state()
    
    print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
    print("="*80)
    print("Link State implementado exitosamente con las siguientes características:")
    print("• ✅ Intercambio de LSPs (Link State Packets)")
    print("• ✅ Base de datos de estados de enlace (LSDB)")
    print("• ✅ Cálculo de rutas con Dijkstra")
    print("• ✅ Detección de cambios de topología")
    print("• ✅ Convergencia automática")
    print("• ✅ Manejo de particiones y reconexiones")
    
    return nodos_simulacion

if __name__ == "__main__":
    nodos_finales = main()
