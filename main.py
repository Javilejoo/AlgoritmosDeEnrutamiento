import subprocess
import sys

print("=" * 60)
print("        ALGORITMOS DE ENRUTAMIENTO - DIJKSTRA")
print("=" * 60)
print("Selecciona el modo de ejecución:")
print("1. Servidor simple (consultas punto a punto)")
print("2. Cliente simple (consultas punto a punto)")
print("3. Dijkstra centralizado (generar todas las tablas)")
print("4. Sistema distribuido automático (coordinador)")
print("5. 🎯 NODOS EN TERMINALES SEPARADAS (Recomendado)")
print("6. Salir")
print("-" * 60)

opcion = input("Opción (1-6): ").strip()

if opcion == '1':
    print("Iniciando servidor simple...")
    subprocess.run([sys.executable, "servidor.py"])
elif opcion == '2':
    print("Iniciando cliente simple...")
    subprocess.run([sys.executable, "cliente.py"])
elif opcion == '3':
    print("Ejecutando Dijkstra centralizado...")
    subprocess.run([sys.executable, "dijkstra.py"])
elif opcion == '4':
    print("Iniciando sistema distribuido automático...")
    subprocess.run([sys.executable, "red_distribuida.py"])
elif opcion == '5':
    print("🎯 Iniciando gestor de nodos en terminales...")
    subprocess.run([sys.executable, "abrir_nodos.py"])
elif opcion == '6':
    print("¡Hasta luego!")
else:
    print("Opción no válida.")
