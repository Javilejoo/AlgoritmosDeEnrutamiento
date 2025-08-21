# dijkstra.py
from typing import Dict, Optional, List, Tuple
import heapq
import os, json


# Importa tu clase grafo
from grafo import grafo

def dijkstra(G: grafo, source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Calcula distancias mínimas desde 'source' y el predecesor de cada nodo.
    Devuelve (dist, prev):
      - dist[nodo] = costo mínimo desde source a nodo
      - prev[nodo] = predecesor en el camino más corto (None si no hay)
    """
    # Inicialización
    dist: Dict[str, float] = {r: float("inf") for r in G.routers}
    prev: Dict[str, Optional[str]] = {r: None for r in G.routers}
    dist[source] = 0.0

    # Priority queue: (distancia acumulada, nodo)
    pq: List[Tuple[float, str]] = [(0.0, source)]
    visited: set[str] = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        # Si el elemento extraído está desactualizado, sáltalo
        if d > dist[u]:
            continue

        # Relajar aristas u -> v
        for v, w in G.conexiones.get(u, {}).items():
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(pq, (alt, v))

    return dist, prev


def first_hop(source: str, dest: str, prev: Dict[str, Optional[str]]) -> Optional[str]:
    """
    Dado el diccionario 'prev' (predecesores), obtiene el primer salto (next-hop)
    desde 'source' hacia 'dest'. Devuelve None si no hay ruta o si dest==source.
    """
    if source == dest:
        return None
    # Reconstruye camino dest -> source usando prev
    path: List[str] = []
    cur = dest
    while cur is not None:
        path.append(cur)
        if cur == source:
            break
        cur = prev[cur]
    if not path or path[-1] != source:
        return None  # no hay camino
    path.reverse()  # ahora: source ... dest
    return path[1] if len(path) >= 2 else None


def forwarding_table(G: grafo, source: str) -> List[Tuple[str, Optional[str], float]]:
    """
    Construye la tabla de enrutamiento (destino, next-hop, costo_total) para 'source'.
    """
    dist, prev = dijkstra(G, source)
    filas: List[Tuple[str, Optional[str], float]] = []
    for dest in sorted(G.routers):
        nh = first_hop(source, dest, prev)
        filas.append((dest, nh, dist[dest]))
    return filas

def reconstruir_ruta(source: str, dest: str, prev: Dict[str, Optional[str]]) -> Optional[List[str]]:
    if source == dest:
        return [source]
    path = []
    cur = dest
    while cur is not None:
        path.append(cur)
        if cur == source:
            break
        cur = prev[cur]
    if not path or path[-1] != source:
        return None
    path.reverse()
    return path

def construir_tablas_para_todos(G: grafo, incluir_ruta: bool = False) -> Dict[str, List[Tuple[str, Optional[str], float, Optional[List[str]]]]]:
    """
    Devuelve un dict: tablas[router] = lista de filas
    Cada fila: (destino, next_hop, costo_total, ruta_opcional)
    """
    tablas: Dict[str, List[Tuple[str, Optional[str], float, Optional[List[str]]]]] = {}
    for origen in sorted(G.routers):
        dist, prev = dijkstra(G, origen)
        filas = []
        for dest in sorted(G.routers):
            nh = first_hop(origen, dest, prev)
            ruta = reconstruir_ruta(origen, dest, prev) if incluir_ruta else None
            filas.append((dest, nh, dist[dest], ruta))
        tablas[origen] = filas
    return tablas

def imprimir_tabla(origen: str, filas: List[Tuple[str, Optional[str], float, Optional[List[str]]]]) -> None:
    print(f"\nTabla de enrutamiento para {origen}")
    print("Destino | next-hop | costo | ruta")
    print("-------------------------------------------")
    for dest, nh, cost, ruta in filas:
        costo_str = "∞" if cost == float("inf") else (f"{int(cost)}" if float(cost).is_integer() else f"{cost:.3f}")
        nh_str = nh if nh is not None else "-"
        ruta_str = "->".join(ruta) if ruta else "-"
        print(f"{dest:7} {nh_str:9} {costo_str:6}  {ruta_str}")


def guardar_tablas_json(tablas: Dict[str, List[Tuple[str, Optional[str], float, Optional[List[str]]]]],
                        carpeta: str = "tablas_json") -> None:
    """
    Guarda cada tabla en un archivo JSON: tabla_A.json, tabla_B.json, ...
    """
    os.makedirs(carpeta, exist_ok=True)
    for origen, filas in tablas.items():
        data = []
        for dest, nh, cost, ruta in filas:
            data.append({
                "destino": dest,
                "next_hop": nh if nh is not None else "",
                "costo": cost if cost != float("inf") else None,
                "ruta": ruta if ruta else []
            })
        ruta_archivo = os.path.join(carpeta, f"tabla_{origen}.json")
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    
    g = grafo()

    edges = [
        ("A","B",7),
        ("A","I",1),
        ("A","C",7),
        ("B","F",2),
        ("I","D",6),
        ("C","D",5),
        ("D","F",1),
        ("D","E",1),
        ("F","G",3),
        ("F","H",4),
        ("G","E",4),
    ]

    for a,b,w in edges:
        g.agregar_conexion(a,b,w)

    print(g)  # para ver la estructura

        # 1) Calcula todas las tablas (incluyendo ruta completa)
    tablas = construir_tablas_para_todos(g, incluir_ruta=True)

    # 2) Accede a cada una como tablas['A'], tablas['B'], ...
    tabla_A = tablas['A']
    tabla_B = tablas['B']
    tabla_C = tablas['C']
    tabla_D = tablas['D']
    tabla_E = tablas['E']
    tabla_F = tablas['F']
    tabla_G = tablas['G']
    tabla_H = tablas['H']
    tabla_I = tablas['I']


    # 3) Imprime una o varias
    imprimir_tabla('A', tabla_A)
    imprimir_tabla('B', tabla_B)
    imprimir_tabla('C', tabla_C)
    imprimir_tabla('D', tabla_D)
    imprimir_tabla('E', tabla_E)
    imprimir_tabla('F', tabla_F)
    imprimir_tabla('G', tabla_G)
    imprimir_tabla('H', tabla_H)
    imprimir_tabla('I', tabla_I)

    # 4) (opcional) Guarda cada tabla en JSON
    # si ya existen los archivos no guardar, si no existen guardarlos
    if not os.path.exists("tablas_json"):
       guardar_tablas_json(tablas, carpeta="tablas_json")
       print("\nJSON generados en carpeta 'tablas_json/'.")
