"""
Cliente interactivo para probar algoritmos de enrutamiento con Redis
Permite seleccionar entre Flooding y Link State Routing
"""

import asyncio
import json
from redis_protocol import RedisProtocolNode, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

class InteractiveRedisClient:
    """Cliente interactivo para testing de algoritmos"""
    
    def __init__(self):
        self.node = None
        self.running = False
    
    def print_menu(self):
        """Mostrar menú principal"""
        print("\n" + "="*60)
        print("  🌐 ALGORITMOS DE ENRUTAMIENTO - REDIS PROTOCOL")
        print("="*60)
        print()
        print("🔧 CONFIGURACIÓN:")
        print("  1. Crear nodo y configurar vecinos")
        print("  2. Seleccionar algoritmo (Flooding / Link State)")
        print("  3. Conectar a servidor Redis")
        print()
        print("📡 COMUNICACIÓN:")
        print("  4. Enviar mensaje INIT")
        print("  5. Enviar mensaje a otro nodo")
        print("  6. Enviar mensaje DONE")
        print("  7. Recibir mensajes")
        print("  8. Ver estado del nodo")
        print()
        print("  0. Salir")
        print("-"*60)
    
    async def create_node(self):
        """Crear y configurar nodo"""
        print("\n🆔 CREAR NODO")
        
        node_id = input("ID del nodo (ej: nodo10, nodo2): ").strip().lower()
        if not node_id:
            print("❌ ID de nodo requerido")
            return
        
        seccion = input("Sección (ej: sec20) [sec20]: ").strip() or "sec20"
        topologia = input("Topología (ej: topologia1) [topologia1]: ").strip() or "topologia1"
        
        self.node = RedisProtocolNode(node_id, seccion, topologia)
        
        # Configurar vecinos
        print("\n👥 CONFIGURAR VECINOS")
        print("Formato: nodo:costo (ej: nodo6:5, nodo2:3)")
        print("Terminar con línea vacía")
        
        neighbours = {}
        while True:
            vecino_input = input("Vecino: ").strip()
            if not vecino_input:
                break
                
            try:
                nodo, costo = vecino_input.split(":")
                neighbours[nodo.strip().lower()] = int(costo.strip())
            except ValueError:
                print("❌ Formato inválido. Use: nodo:costo")
        
        if neighbours:
            self.node.set_neighbours(neighbours)
        
        print(f"✅ Nodo {node_id} creado exitosamente")
    
    async def select_algorithm(self):
        """Seleccionar algoritmo de enrutamiento"""
        if not self.node:
            print("❌ Primero cree un nodo")
            return
        
        print("\n🎯 SELECCIONAR ALGORITMO")
        print("1. Flooding (inundación)")
        print("2. Link State Routing")
        
        choice = input("Seleccione (1-2): ").strip()
        
        if choice == "1":
            self.node.set_algorithm("flooding")
            print("✅ Algoritmo configurado: Flooding")
        elif choice == "2":
            self.node.set_algorithm("link_state")
            print("✅ Algoritmo configurado: Link State Routing")
        else:
            print("❌ Opción inválida")
    
    async def connect_redis(self):
        """Conectar a Redis"""
        if not self.node:
            print("❌ Primero cree un nodo")
            return
        
        print(f"\n🔌 CONECTANDO A REDIS")
        print(f"Servidor: {REDIS_HOST}:{REDIS_PORT}")
        
        if await self.node.connect():
            print("✅ Conexión exitosa")
        else:
            print("❌ Error en conexión")
    
    async def send_init(self):
        """Enviar mensaje INIT"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n📤 ENVIANDO MENSAJE INIT...")
        await self.node.send_init_message()
        print("✅ Mensaje INIT enviado")
    
    async def send_message(self):
        """Enviar mensaje a otro nodo"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n💌 ENVIAR MENSAJE")
        destination = input("Nodo destino: ").strip().lower()
        if not destination:
            print("❌ Destino requerido")
            return
        
        content = input("Mensaje: ").strip()
        if not content:
            print("❌ Contenido requerido")
            return
        
        print(f"📤 Enviando con algoritmo: {self.node.algorithm}")
        await self.node.send_message(destination, content)
        print("✅ Mensaje enviado")
    
    async def send_done(self):
        """Enviar mensaje DONE"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print("\n📤 ENVIANDO MENSAJE DONE...")
        await self.node.send_done_message()
        print("✅ Mensaje DONE enviado")
    
    async def listen_mode(self):
        """Modo escucha para recibir mensajes"""
        if not self.node or not self.node.redis_client:
            print("❌ Nodo no conectado")
            return
        
        print(f"\n👂 MODO ESCUCHA ACTIVADO")
        print(f"Canal: {self.node.channel_name}")
        print("Presione Ctrl+C para detener")
        
        try:
            await self.node.listen()
        except KeyboardInterrupt:
            print("\n🛑 Modo escucha detenido")
        except Exception as e:
            print(f"❌ Error en modo escucha: {e}")
    
    def show_status(self):
        """Mostrar estado del nodo"""
        if not self.node:
            print("❌ No hay nodo creado")
            return
        
        print("\n📊 ESTADO DEL NODO")
        status = self.node.get_status()
        
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
    
    async def auto_test(self):
        """Prueba automática completa"""
        print("\n🧪 PRUEBA AUTOMÁTICA")
        
        # Crear nodo de prueba
        test_node = RedisProtocolNode("TEST")
        test_node.set_neighbours({"A": 5, "B": 3})
        test_node.set_algorithm("flooding")
        
        if await test_node.connect():
            print("✅ Nodo de prueba conectado")
            
            # Enviar init
            await test_node.send_init_message()
            print("✅ INIT enviado")
            
            # Esperar un poco
            await asyncio.sleep(1)
            
            # Enviar mensaje
            await test_node.send_message("A", "Mensaje de prueba automática")
            print("✅ Mensaje enviado")
            
            # Esperar
            await asyncio.sleep(1)
            
            # Enviar done
            await test_node.send_done_message()
            print("✅ DONE enviado")
            
            await test_node.disconnect()
            print("✅ Prueba automática completada")
        else:
            print("❌ No se pudo conectar nodo de prueba")
    
    async def cleanup(self):
        """Limpiar recursos"""
        if self.node:
            await self.node.disconnect()
    
    async def run(self):
        """Ejecutar cliente interactivo"""
        print("🚀 Iniciando cliente Redis...")
        
        try:
            while True:
                self.print_menu()
                choice = input("👉 Seleccione una opción: ").strip()
                
                if choice == "0":
                    print("👋 ¡Hasta luego!")
                    break
                elif choice == "1":
                    await self.create_node()
                elif choice == "2":
                    await self.select_algorithm()
                elif choice == "3":
                    await self.connect_redis()
                elif choice == "4":
                    await self.send_init()
                elif choice == "5":
                    await self.send_message()
                elif choice == "6":
                    await self.send_done()
                elif choice == "7":
                    await self.listen_mode()
                elif choice == "8":
                    self.show_status()
                elif choice == "9":
                    await self.auto_test()
                else:
                    print("❌ Opción no válida")
                
                # Pausa pequeña
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Programa interrumpido")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await self.cleanup()

async def main():
    """Función principal"""
    client = InteractiveRedisClient()
    await client.run()

if __name__ == "__main__":
    print("Verificando dependencias...")
    try:
        import redis.asyncio
        print("✅ redis.asyncio disponible")
        asyncio.run(main())
    except ImportError:
        print("❌ Redis no instalado. Instalar con: pip install redis")
        print("🔧 Comando: pip install redis[hiredis]")
