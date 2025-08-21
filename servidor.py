import socket
import json
from dijkstra import dijkstra
from grafo import grafo

# Configuración del servidor
HOST = '127.0.0.1'
PORT = 65432

def cargar_grafo():
    # Crear el grafo con las mismas conexiones que en dijkstra.py
    g = grafo()
    edges = [
        ("A","B",7), ("A","I",1), ("A","C",7), ("B","F",2), ("I","D",6),
        ("C","D",5), ("D","F",1), ("D","E",1), ("F","G",3), ("F","H",4), ("G","E",4),
    ]
    for a, b, w in edges:
        g.agregar_conexion(a, b, w)
    return g

def main():
    grafo = cargar_grafo()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'Servidor escuchando en {HOST}:{PORT}')
        while True:
            conn, addr = s.accept()
            with conn:
                print('Conectado por', addr)
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    mensaje = json.loads(data.decode())
                    origen = mensaje['origen']
                    destino = mensaje['destino']
                    
                    # Calcular ruta usando dijkstra
                    distancias, predecesores = dijkstra(grafo, origen)
                    
                    if destino not in distancias or distancias[destino] == float('inf'):
                        respuesta = {'error': f'No hay ruta desde {origen} hasta {destino}'}
                    else:
                        costo = distancias[destino]
                        
                        # Reconstruir ruta
                        ruta = []
                        actual = destino
                        while actual is not None:
                            ruta.append(actual)
                            if actual == origen:
                                break
                            actual = predecesores.get(actual)
                        ruta.reverse()
                        
                        respuesta = {'costo': costo, 'ruta': ruta}
                        
                except Exception as e:
                    respuesta = {'error': str(e)}
                conn.sendall(json.dumps(respuesta).encode())

if __name__ == '__main__':
    main()
