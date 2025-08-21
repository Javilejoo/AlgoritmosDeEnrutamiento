# dijkstra.py
from __future__ import annotations
from typing import Dict, Optional, List, Tuple
import heapq

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

    origen = "A"
    tabla = forwarding_table(g, origen)
    print(f"Tabla de enrutamiento para {origen}")
    for dest, nh, cost in tabla:
        costo_str = "∞" if cost == float("inf") else (f"{int(cost)}" if cost.is_integer() else f"{cost:.3f}")
        nh_str = nh if nh is not None else "-"
        print(f"{origen} -> {dest:2} | next-hop: {nh_str:2} | costo: {costo_str}")