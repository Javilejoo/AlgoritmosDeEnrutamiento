from collections import defaultdict
from typing import Dict, Set

class grafo:
    def __init__(self):
        # Conjunto de routers y mapa de adyacencia: r -> { vecino -> costo }
        self.routers: Set[str] = set()
        self.conexiones: Dict[str, Dict[str, int]] = defaultdict(dict)

    def agregar_router(self, r: str) -> None:
        self.routers.add(r)
        # defaultdict ya crea el dict interno cuando haga falta

    def agregar_conexion(self, router1: str, router2: str, peso: int, bidireccional: bool = True) -> None:
        """Agrega una arista router1 -> router2 con 'peso'.
           Por defecto es bidireccional (como en el dibujo)."""
        self.agregar_router(router1)
        self.agregar_router(router2)
        self.conexiones[router1][router2] = int(peso)
        if bidireccional:
            self.conexiones[router2][router1] = int(peso)

    def __repr__(self):
        # impresión bonita del grafo
        lines = []
        for r in sorted(self.routers):
            vecinos = ", ".join(f"{v}:{w}" for v, w in sorted(self.conexiones[r].items()))
            lines.append(f"{r} -> {{ {vecinos} }}")
        return "\n".join(lines)

g = grafo()

edges = [
    ("A","B",7),
    ("A","I",3),
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
