import socket
import json

HOST = '127.0.0.1'
PORT = 65432

def main():
    origen = input('Nodo origen: ')
    destino = input('Nodo destino: ')
    mensaje = {'origen': origen, 'destino': destino}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(json.dumps(mensaje).encode())
        data = s.recv(1024)
        respuesta = json.loads(data.decode())
        if 'error' in respuesta:
            print('Error:', respuesta['error'])
        else:
            print(f"Costo: {respuesta['costo']}")
            print(f"Ruta: {' -> '.join(respuesta['ruta'])}")

if __name__ == '__main__':
    main()
