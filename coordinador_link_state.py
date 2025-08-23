"""
Coordinador para la red distribuida Link State
Facilita el inicio, monitoreo y control de múltiples nodos
"""

import subprocess
import time
import socket
import json
import threading
import os
import signal
from typing import Dict, List, Optional

class LinkStateCoordinator:
    """Coordinador para gestionar múltiples nodos Link State"""
    
    def __init__(self):
        self.procesos = {}  # {nombre: subprocess.Popen}
        self.puertos_nodos = {
            'A': 65001, 'B': 65002, 'C': 65003, 'D': 65004, 'E': 65005,
            'F': 65006, 'G': 65007, 'H': 65008, 'I': 65009
        }
        self.host = '127.0.0.1'
        self.activo = True
        
    def iniciar_nodo(self, nombre: str) -> bool:
        """Inicia un nodo específico"""
        if nombre in self.procesos and self.procesos[nombre].poll() is None:
            print(f"❌ Nodo {nombre} ya está ejecutándose")
            return False
            
        puerto = self.puertos_nodos[nombre]
        
        try:
            # Iniciar proceso del nodo
            cmd = ['python', 'link_state_socket.py', nombre, str(puerto)]
            proceso = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.procesos[nombre] = proceso
            print(f"✅ Nodo {nombre} iniciado en puerto {puerto} (PID: {proceso.pid})")
            
            # Monitorear salida en hilo separado
            threading.Thread(
                target=self.monitorear_nodo,
                args=(nombre, proceso),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando nodo {nombre}: {e}")
            return False
            
    def monitorear_nodo(self, nombre: str, proceso: subprocess.Popen):
        """Monitorea la salida de un nodo"""
        try:
            while proceso.poll() is None and self.activo:
                line = proceso.stdout.readline()
                if line:
                    print(f"[{nombre}] {line.strip()}")
                    
            # El proceso terminó
            if proceso.returncode is not None:
                if proceso.returncode == 0:
                    print(f"🔴 Nodo {nombre} terminó normalmente")
                else:
                    print(f"💥 Nodo {nombre} terminó con error (código: {proceso.returncode})")
                    
                # Leer errores si los hay
                errors = proceso.stderr.read()
                if errors:
                    print(f"[{nombre}] STDERR: {errors}")
                    
        except Exception as e:
            print(f"Error monitoreando nodo {nombre}: {e}")
            
    def detener_nodo(self, nombre: str) -> bool:
        """Detiene un nodo específico"""
        if nombre not in self.procesos:
            print(f"❌ Nodo {nombre} no está iniciado")
            return False
            
        proceso = self.procesos[nombre]
        
        if proceso.poll() is not None:
            print(f"❌ Nodo {nombre} ya está detenido")
            return False
            
        try:
            # Intentar terminar gracefully
            proceso.terminate()
            
            # Esperar hasta 5 segundos
            try:
                proceso.wait(timeout=5)
                print(f"✅ Nodo {nombre} detenido")
            except subprocess.TimeoutExpired:
                # Si no termina, forzar
                proceso.kill()
                proceso.wait()
                print(f"🔨 Nodo {nombre} terminado forzadamente")
                
            del self.procesos[nombre]
            return True
            
        except Exception as e:
            print(f"❌ Error deteniendo nodo {nombre}: {e}")
            return False
            
    def iniciar_red_completa(self, nodos: List[str] = None):
        """Inicia todos los nodos o una lista específica"""
        if nodos is None:
            nodos = list(self.puertos_nodos.keys())
            
        print(f"🚀 Iniciando red Link State con nodos: {nodos}")
        
        exitos = 0
        for nombre in nodos:
            if self.iniciar_nodo(nombre):
                exitos += 1
                time.sleep(0.5)  # Pausa pequeña entre inicios
                
        print(f"✅ Red iniciada: {exitos}/{len(nodos)} nodos activos")
        
        # Esperar convergencia
        if exitos > 0:
            print("⏳ Esperando convergencia inicial (10 segundos)...")
            time.sleep(10)
            print("✅ Convergencia completada")
            
    def detener_red_completa(self):
        """Detiene todos los nodos"""
        nodos_activos = list(self.procesos.keys())
        
        if not nodos_activos:
            print("ℹ️ No hay nodos activos")
            return
            
        print(f"🛑 Deteniendo nodos: {nodos_activos}")
        
        for nombre in nodos_activos:
            self.detener_nodo(nombre)
            
        print("✅ Todos los nodos detenidos")
        
    def obtener_estado_nodo(self, nombre: str) -> Optional[Dict]:
        """Obtiene el estado de un nodo via socket"""
        if nombre not in self.puertos_nodos:
            return None
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3.0)
                sock.connect((self.host, self.puertos_nodos[nombre]))
                
                mensaje = {'tipo': 'get_status'}
                sock.send(json.dumps(mensaje).encode('utf-8'))
                
                respuesta = sock.recv(4096).decode('utf-8')
                if respuesta:
                    datos = json.loads(respuesta)
                    return datos.get('estado')
                    
        except Exception as e:
            print(f"❌ Error obteniendo estado de {nombre}: {e}")
            
        return None
        
    def listar_nodos_activos(self):
        """Lista los nodos actualmente activos"""
        activos = []
        
        for nombre, proceso in self.procesos.items():
            if proceso.poll() is None:
                activos.append(nombre)
                
        return activos
        
    def mostrar_estado_red(self):
        """Muestra el estado completo de la red"""
        print("\n" + "="*60)
        print("ESTADO DE LA RED LINK STATE")
        print("="*60)
        
        activos = self.listar_nodos_activos()
        
        if not activos:
            print("❌ No hay nodos activos")
            return
            
        print(f"Nodos activos: {', '.join(sorted(activos))}")
        print()
        
        for nombre in sorted(activos):
            estado = self.obtener_estado_nodo(nombre)
            if estado:
                print(f"--- Nodo {nombre} ---")
                print(f"  Vecinos: {estado.get('vecinos', {})}")
                print(f"  LSP seq: {estado.get('sequence_num', 0)}")
                print(f"  LSDB size: {estado.get('lsdb_size', 0)}")
                print(f"  Rutas activas: {len(estado.get('routing_table', {}))}")
                
                stats = estado.get('estadisticas', {})
                print(f"  LSPs enviados: {stats.get('lsps_enviados', 0)}")
                print(f"  LSPs recibidos: {stats.get('lsps_recibidos', 0)}")
                print()
            else:
                print(f"--- Nodo {nombre} ---")
                print("  ❌ No se pudo obtener estado")
                print()
                
    def simular_falla_enlace(self, nodo: str, vecino: str):
        """Simula la falla de un enlace (requiere implementación en los nodos)"""
        print(f"🔥 Simulando falla del enlace {nodo}-{vecino}")
        print("⚠️  Esta funcionalidad requiere comandos adicionales en los nodos")
        
    def menu_interactivo(self):
        """Menú interactivo para gestionar la red"""
        while self.activo:
            print("\n" + "="*50)
            print("COORDINADOR LINK STATE - MENÚ PRINCIPAL")
            print("="*50)
            print("1. Iniciar nodo específico")
            print("2. Detener nodo específico")
            print("3. Iniciar red completa")
            print("4. Detener red completa")
            print("5. Mostrar nodos activos")
            print("6. Mostrar estado de la red")
            print("7. Obtener estado de nodo específico")
            print("8. Iniciar demo con subconjunto")
            print("0. Salir")
            print("-" * 50)
            
            try:
                opcion = input("Selecciona una opción (0-8): ").strip()
                
                if opcion == "0":
                    print("👋 Saliendo...")
                    self.detener_red_completa()
                    self.activo = False
                    break
                    
                elif opcion == "1":
                    nombre = input("Nombre del nodo (A-I): ").strip().upper()
                    if nombre in self.puertos_nodos:
                        self.iniciar_nodo(nombre)
                    else:
                        print(f"❌ Nodo inválido. Disponibles: {list(self.puertos_nodos.keys())}")
                        
                elif opcion == "2":
                    nombre = input("Nombre del nodo (A-I): ").strip().upper()
                    self.detener_nodo(nombre)
                    
                elif opcion == "3":
                    self.iniciar_red_completa()
                    
                elif opcion == "4":
                    self.detener_red_completa()
                    
                elif opcion == "5":
                    activos = self.listar_nodos_activos()
                    if activos:
                        print(f"📡 Nodos activos: {', '.join(sorted(activos))}")
                    else:
                        print("❌ No hay nodos activos")
                        
                elif opcion == "6":
                    self.mostrar_estado_red()
                    
                elif opcion == "7":
                    nombre = input("Nombre del nodo (A-I): ").strip().upper()
                    estado = self.obtener_estado_nodo(nombre)
                    if estado:
                        print(f"\n--- Estado detallado de {nombre} ---")
                        print(json.dumps(estado, indent=2))
                    else:
                        print(f"❌ No se pudo obtener estado de {nombre}")
                        
                elif opcion == "8":
                    print("\nDemos disponibles:")
                    print("1. Demo básico (A, B, F)")
                    print("2. Demo topología estrella (A, B, C, D)")
                    print("3. Demo ruta larga (A, B, F, H)")
                    
                    demo = input("Selecciona demo (1-3): ").strip()
                    
                    if demo == "1":
                        self.iniciar_red_completa(['A', 'B', 'F'])
                    elif demo == "2":
                        self.iniciar_red_completa(['A', 'B', 'C', 'D'])
                    elif demo == "3":
                        self.iniciar_red_completa(['A', 'B', 'F', 'H'])
                    else:
                        print("❌ Demo inválido")
                        
                else:
                    print("❌ Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n👋 Interrumpido por usuario")
                self.detener_red_completa()
                self.activo = False
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
            # Pausa para leer
            if self.activo:
                input("\nPresiona Enter para continuar...")
                
def main():
    print("🌐 COORDINADOR LINK STATE")
    print("=" * 40)
    print("Este coordinador te permite gestionar una red")
    print("distribuida de nodos Link State.")
    
    coordinador = LinkStateCoordinator()
    
    try:
        coordinador.menu_interactivo()
    except KeyboardInterrupt:
        print("\n🛑 Terminando coordinador...")
        coordinador.detener_red_completa()
    
if __name__ == "__main__":
    main()
