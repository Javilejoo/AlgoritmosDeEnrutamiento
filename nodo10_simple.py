#!/usr/bin/env python3
"""
Cliente LSR simplificado - Nodo configurable
Menú simple para comunicación con otros nodos
Permite seleccionar qué nodo ser y enviar mensajes a cualquier nodo
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from datetime import datetime
import heapq

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

# Topología de la red - definir vecinos y costos para cada nodo
NETWORK_TOPOLOGY = {
    1: {2: 1, 3: 2, 5: 3},  # nodo1 conectado a nodo2, nodo3, nodo5
    2: {1: 1, 3: 1, 4: 2},  # nodo2 conectado a nodo1, nodo3, nodo4
    3: {1: 2, 2: 1, 4: 1, 5: 2},  # nodo3 conectado a nodo1, nodo2, nodo4, nodo5
    4: {2: 2, 3: 1, 6: 3},  # nodo4 conectado a nodo2, nodo3, nodo6
    5: {1: 3, 3: 2, 6: 1, 7: 2},  # nodo5 conectado a nodo1, nodo3, nodo6, nodo7
    6: {4: 3, 5: 1, 7: 1, 8: 2},  # nodo6 conectado a nodo4, nodo5, nodo7, nodo8
    7: {5: 2, 6: 1, 8: 1, 9: 2},  # nodo7 conectado a nodo5, nodo6, nodo8, nodo9
    8: {6: 2, 7: 1, 9: 1, 10: 2},  # nodo8 conectado a nodo6, nodo7, nodo9, nodo10
    9: {7: 2, 8: 1, 10: 1},  # nodo9 conectado a nodo7, nodo8, nodo10
    10: {8: 2, 9: 1}  # nodo10 conectado a nodo8, nodo9
}

class NodelClient:
    def __init__(self, node_number=10):
        self.node_id = f"sec20.topologia2.nodo{node_number}"
        self.node_number = node_number
        self.redis_client = None
        self.pubsub = None
        self.algorithm = "flooding"  # Algoritmo por defecto
        self.received_messages = set()  # Para evitar duplicados
        self.topology = NETWORK_TOPOLOGY  # Topología completa de la red
        self.max_received_messages = 100  # Límite de mensajes en memoria
        
    async def connect(self):
        """Conectar automáticamente"""
        try:
            self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(self.node_id)
            
            print(f"✅ Nodo{self.node_number} conectado automáticamente")
            print(f"👂 Escuchando en: {self.node_id}")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    def dijkstra(self, start, end):
        """Calcular la ruta más corta usando algoritmo de Dijkstra"""
        distances = {node: float('infinity') for node in self.topology}
        distances[start] = 0
        previous = {}
        unvisited = [(0, start)]
        
        while unvisited:
            current_distance, current = heapq.heappop(unvisited)
            
            if current == end:
                # Reconstruir la ruta
                path = []
                while current is not None:
                    path.append(current)
                    current = previous.get(current)
                return list(reversed(path))
            
            if current_distance > distances[current]:
                continue
                
            for neighbor, weight in self.topology.get(current, {}).items():
                distance = current_distance + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(unvisited, (distance, neighbor))
        
        return []  # No hay ruta
    
    def get_neighbors(self):
        """Obtener lista de vecinos del nodo actual"""
        return list(self.topology.get(self.node_number, {}).keys())
    
    async def flooding_send(self, message_data, exclude_node=None):
        """Implementar flooding: enviar a todos los vecinos excepto el que lo envió"""
        neighbors = self.get_neighbors()
        if exclude_node:
            exclude_num = int(exclude_node.split("nodo")[-1]) if "nodo" in str(exclude_node) else exclude_node
            neighbors = [n for n in neighbors if n != exclude_num]
        
        print(f"🌊 FLOODING: Enviando a vecinos {neighbors}")
        
        for neighbor in neighbors:
            channel = f"sec20.topologia2.nodo{neighbor}"
            await self.redis_client.publish(channel, json.dumps(message_data))
            print(f"   📤 Flooding → nodo{neighbor}")
    
    async def lsr_send(self, message_data, target_node):
        """Implementar LSR: calcular mejor ruta y enviar por ahí"""
        target_num = int(target_node.split("nodo")[-1]) if "nodo" in str(target_node) else target_node
        
        # Calcular la mejor ruta usando Dijkstra
        path = self.dijkstra(self.node_number, target_num)
        
        if len(path) < 2:
            print(f"❌ No hay ruta a nodo{target_num}")
            return
        
        next_hop = path[1]  # El siguiente nodo en la ruta óptima
        print(f"🛤️  LSR: Ruta calculada: {' → '.join([f'nodo{n}' for n in path])}")
        print(f"📤 LSR: Enviando a siguiente salto → nodo{next_hop}")
        
        channel = f"sec20.topologia2.nodo{next_hop}"
        await self.redis_client.publish(channel, json.dumps(message_data))
    
    async def send_message(self, target_node, content):
        """Enviar mensaje usando el algoritmo seleccionado"""
        # Generar ID único para evitar loops en flooding
        message_id = str(uuid.uuid4())[:8]
        
        # Definir el protocolo según el algoritmo
        if self.algorithm == "flooding":
            proto = "flooding"
        elif self.algorithm == "link_state":
            proto = "lsr"
        else:
            proto = "lsr"  # Por defecto
        
        msg = {
            "proto": proto,  # El protocolo cambia según el algoritmo
            "type": "message", 
            "from": self.node_id,
            "to": f"sec20.topologia2.{target_node}",
            "ttl": 5,
            "headers": [],
            "payload": content,
            "message_id": message_id,
            "path": [self.node_number]  # Para tracking de la ruta
        }
        
        # Imprimir el JSON completo que se envía
        print(f"\n📤 ENVIANDO MENSAJE - Algoritmo: {self.algorithm}")
        print(f"JSON completo: {json.dumps(msg, indent=2)}")
        
        if self.algorithm == "flooding":
            print(f"🌊 Usando FLOODING para difundir mensaje")
            await self.flooding_send(msg)
        elif self.algorithm == "link_state":
            print(f"🛤️  Usando LSR para calcular ruta óptima")
            await self.lsr_send(msg, target_node)
        
        print(f"✅ Mensaje enviado: {content}")
    
    def set_algorithm(self, algorithm):
        """Cambiar algoritmo de enrutamiento"""
        self.algorithm = algorithm
        print(f"🎯 Algoritmo cambiado a: {algorithm}")
    
    def show_topology(self):
        """Mostrar topología de la red y rutas desde este nodo"""
        print(f"\n🌐 TOPOLOGÍA DE LA RED")
        print("="*50)
        
        for node, neighbors in self.topology.items():
            neighbors_str = ", ".join([f"nodo{n}(costo:{c})" for n, c in neighbors.items()])
            print(f"nodo{node}: {neighbors_str}")
        
        print(f"\n🛤️  RUTAS DESDE NODO{self.node_number} (usando Dijkstra)")
        print("-"*50)
        
        for target in range(1, 11):
            if target != self.node_number:
                path = self.dijkstra(self.node_number, target)
                if path:
                    path_str = " → ".join([f"nodo{n}" for n in path])
                    print(f"A nodo{target}: {path_str}")
                else:
                    print(f"A nodo{target}: ❌ Sin ruta")
        
        print(f"\n👥 MIS VECINOS DIRECTOS: {self.get_neighbors()}")
    
    def clear_message_cache(self):
        """Limpiar caché de mensajes recibidos"""
        old_count = len(self.received_messages)
        self.received_messages.clear()
        print(f"🧹 Caché limpiada: {old_count} mensajes eliminados")
        print("✅ Ahora se pueden recibir mensajes duplicados nuevamente")
    
    def show_stats(self):
        """Mostrar estadísticas del nodo"""
        print(f"\n📊 ESTADÍSTICAS DE NODO{self.node_number}")
        print("="*40)
        print(f"🎯 Algoritmo actual: {self.algorithm}")
        print(f"📝 Mensajes en caché: {len(self.received_messages)}")
        print(f"👥 Vecinos directos: {self.get_neighbors()}")
        print(f"🌐 Nodos en topología: {list(self.topology.keys())}")
        
        if self.received_messages:
            print(f"🔍 Últimos IDs de mensajes:")
            recent = list(self.received_messages)[-5:]
            for msg_id in recent:
                print(f"   • {msg_id}")
        else:
            print("📭 No hay mensajes en caché")
    
    async def listen_messages(self):
        """Modo escucha directo (bloquea hasta Ctrl+C)"""
        if not self.pubsub:
            print("❌ No hay conexión pubsub")
            return
        
        print(f"👂 MODO ESCUCHA ACTIVADO")
        print(f"🎯 Escuchando en: {self.node_id}")
        print("Time     | From     | Type    | Details")
        print("-" * 50)
        print("Presiona Ctrl+C para volver al menú")
        print("📝 Se mostrará el JSON completo de cada mensaje recibido")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message["data"].decode())
        except KeyboardInterrupt:
            print("\n🛑 Modo escucha detenido - Volviendo al menú")
        except Exception as e:
            print(f"❌ Error en escucha: {e}")
    
    async def _handle_message(self, data):
        """Procesar mensaje recibido"""
        try:
            parsed = json.loads(data)
            
            proto = parsed.get("proto", "")
            
            # FILTRO ESTRICTO: Solo procesar protocolos que reconocemos
            if proto not in ["lsr", "flooding"]:
                # Ignorar silenciosamente protocolos desconocidos
                return
            
            msg_type = parsed.get("type")
            from_node = parsed.get("from", "Unknown")
            to_node = parsed.get("to", "")
            payload = parsed.get("payload", "")
            message_id = parsed.get("message_id", "")
            ttl = parsed.get("ttl", 0)
            path = parsed.get("path", [])
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            from_short = from_node.split(".")[-1] if "." in from_node else from_node
            to_short = to_node.split(".")[-1] if "." in to_node else to_node
            
            # CONTROL SUPER ESTRICTO DE LOOPS Y DUPLICADOS
            
            # 1. NO procesar mensajes que nosotros mismos enviamos (PRIMERO)
            if from_node == self.node_id:
                return
            
            # 2. Para mensajes HELLO: Ignorar completamente si no tienen message_id
            if msg_type == "hello" and not message_id:
                print(f"🚫 HELLO sin ID ignorado de {from_short}")
                return
            
            # 3. Verificar duplicados PARA TODOS los tipos de mensaje
            if message_id and message_id in self.received_messages:
                return
            
            # 4. Verificar si este nodo ya está en el path (evitar loops)
            if self.node_number in path:
                print(f"🔄 Loop detectado - nodo{self.node_number} ya en path: {path}")
                return
            
            # 5. Verificar TTL mínimo
            if ttl <= 0:
                print(f"⏰ TTL inválido o expirado: {ttl}")
                return
            
            # Marcar como recibido
            if message_id:
                self.received_messages.add(message_id)
                # Limpiar mensajes antiguos si hay demasiados
                if len(self.received_messages) > self.max_received_messages:
                    old_messages = list(self.received_messages)
                    self.received_messages = set(old_messages[-50:])
            
            # DIAGNÓSTICO: Mostrar información del mensaje
            print(f"\n📥 MENSAJE VÁLIDO - {timestamp}")
            print(f"De: {from_short} | Para: {to_short} | Tipo: {msg_type} | Proto: {proto}")
            print(f"ID: {message_id[:8]} | TTL: {ttl} | Path: {path}")
            
            if msg_type == "hello":
                print(f"👋 HELLO de {from_short}")
                # NO reenviar mensajes HELLO bajo ninguna circunstancia
                
            elif msg_type == "message":
                # Agregar este nodo al path
                new_path = path + [self.node_number]
                
                if to_node == self.node_id:
                    # Mensaje para este nodo
                    print(f"🎉 MENSAJE PARA TI: {payload}")
                    print(f"📊 De {from_short} usando {proto.upper()}")
                    print(f"🛤️  Ruta: {' → '.join([f'nodo{n}' for n in new_path])}")
                else:
                    # Mensaje en tránsito
                    print(f"🚛 TRÁNSITO: Para {to_short} (TTL: {ttl})")
                    
                    # SOLO reenviar si TTL > 1 y no es un loop
                    if ttl > 1:
                        if proto == "flooding":
                            # Extraer número del nodo que envió
                            from_node_num = None
                            if "nodo" in from_node:
                                try:
                                    from_node_num = int(from_node.split("nodo")[-1])
                                except:
                                    pass
                            
                            # Preparar mensaje para reenvío
                            forward_msg = parsed.copy()
                            forward_msg["ttl"] = ttl - 1
                            forward_msg["path"] = new_path
                            
                            print(f"🌊 FLOODING: TTL={ttl-1}, excluyendo nodo{from_node_num}")
                            await self.flooding_send(forward_msg, from_node_num)
                            
                        elif proto == "lsr":
                            # LSR: calcular ruta óptima
                            try:
                                target_num = int(to_short) if to_short.isdigit() else int(to_short.replace("nodo", ""))
                                route = self.dijkstra(self.node_number, target_num)
                                
                                if len(route) >= 2:
                                    next_hop = route[1]
                                    
                                    # Preparar mensaje para reenvío
                                    forward_msg = parsed.copy()
                                    forward_msg["ttl"] = ttl - 1
                                    forward_msg["path"] = new_path
                                    
                                    print(f"🛤️  LSR: Siguiente salto → nodo{next_hop} (TTL: {ttl-1})")
                                    channel = f"sec20.topologia2.nodo{next_hop}"
                                    await self.redis_client.publish(channel, json.dumps(forward_msg))
                                else:
                                    print(f"❌ Sin ruta LSR a {to_short}")
                            except Exception as e:
                                print(f"❌ Error calculando ruta LSR: {e}")
                    else:
                        print(f"⏰ TTL expirado, no reenviar")
                
            elif msg_type == "info":
                print(f"📊 INFO de {from_short}")
                # NO reenviar mensajes INFO automáticamente
                
        except json.JSONDecodeError:
            # Silenciosamente ignorar mensajes que no son JSON
            pass
        except Exception as e:
            print(f"❌ Error procesando: {e}")
    
    async def disconnect(self):
        """Desconectar"""
        self.running = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
        print("🔌 Desconectado")

def print_menu(client):
    """Mostrar menú simplificado"""
    print("\n" + "="*50)
    print(f"  🌐 NODO{client.node_number} - COMUNICACIÓN LSR")
    print("="*50)
    print()
    print("📡 COMUNICACIÓN:")
    print("  1. Enviar mensaje a nodo específico")
    print("  2. Modo escucha (Ctrl+C para salir)")
    print("  3. Seleccionar algoritmo")
    print("  4. Cambiar identidad de nodo")
    print("  5. Ver topología de red y rutas")
    print("  6. Limpiar caché de mensajes")
    print("  7. Ver estadísticas del nodo")
    print()
    print("🎯 NODOS DISPONIBLES:")
    print("  nodo1, nodo2, nodo3, nodo4, nodo5, nodo6, nodo7, nodo8, nodo9, nodo10 (o el que elijas)")
    print()
    print(f"🌐 ALGORITMO ACTUAL: {client.algorithm.upper()}")
    if client.algorithm == "flooding":
        print("   📋 Flooding: Difusión a todos los vecinos")
    else:
        print("   📋 LSR: Ruta óptima calculada con Dijkstra")
    print()
    print("  0. Salir")
    print("-"*50)

async def main():
    """Función principal"""
    print("🚀 INICIANDO CLIENTE LSR...")
    
    # Seleccionar qué nodo ser
    print("\n🎯 SELECCIÓN DE NODO")
    print("¿Qué nodo quieres ser?")
    node_input = input("Ingresa el número del nodo (1-10): ").strip()
    
    try:
        node_number = int(node_input)
        if node_number < 1 or node_number > 10:
            print("❌ Número de nodo debe estar entre 1 y 10. Usando nodo10 por defecto.")
            node_number = 10
    except ValueError:
        print("❌ Número inválido. Usando nodo10 por defecto.")
        node_number = 10
    
    client = NodelClient(node_number)
    
    # Conectar automáticamente
    if not await client.connect():
        print("❌ No se pudo conectar. Saliendo...")
        return
    
    # Conexión exitosa
    print(f"🎯 Algoritmo actual: {client.algorithm}")
    
    try:
        while True:
            print_menu(client)
            choice = input("👉 Seleccione opción: ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
                
            elif choice == "1":
                # Enviar mensaje a nodo específico
                print("\n💌 ENVIAR MENSAJE")
                print("Nodos disponibles: nodo1, nodo2, nodo3, nodo4, nodo5, nodo6, nodo7, nodo8, nodo9, nodo10")
                
                target = input("¿A qué nodo? (ej: nodo5): ").strip()
                if not target:
                    print("❌ Debe especificar un nodo")
                    continue
                
                # Agregar 'nodo' si solo pusieron el número
                if target.isdigit():
                    target = f"nodo{target}"
                
                message = input("Mensaje: ").strip()
                if not message:
                    print("❌ Debe escribir un mensaje")
                    continue
                
                await client.send_message(target, message)
                
            elif choice == "2":
                # Modo escucha directo
                await client.listen_messages()
                    
            elif choice == "3":
                # Seleccionar algoritmo
                print("\n🎯 SELECCIONAR ALGORITMO")
                print("1. Flooding (inundación)")
                print("2. Link State Routing (LSR)")
                
                algo_choice = input("Seleccione algoritmo (1-2): ").strip()
                
                if algo_choice == "1":
                    client.set_algorithm("flooding")
                elif algo_choice == "2":
                    client.set_algorithm("link_state")
                else:
                    print("❌ Opción inválida")
            
            elif choice == "4":
                # Cambiar identidad de nodo
                print("\n🔄 CAMBIAR IDENTIDAD DE NODO")
                print(f"Actualmente eres: nodo{client.node_number}")
                new_node = input("¿Qué nodo quieres ser ahora? (1-10): ").strip()
                
                try:
                    new_node_number = int(new_node)
                    if 1 <= new_node_number <= 10:
                        # Desconectar del canal actual
                        if client.pubsub:
                            await client.pubsub.unsubscribe(client.node_id)
                        
                        # Cambiar identidad
                        client.node_number = new_node_number
                        client.node_id = f"sec20.topologia2.nodo{new_node_number}"
                        
                        # Suscribirse al nuevo canal
                        await client.pubsub.subscribe(client.node_id)
                        
                        print(f"✅ Ahora eres nodo{new_node_number}")
                        print(f"👂 Escuchando en: {client.node_id}")
                    else:
                        print("❌ Número de nodo debe estar entre 1 y 10")
                except ValueError:
                    print("❌ Número inválido")
            
            elif choice == "5":
                # Ver topología de red y rutas
                client.show_topology()
            
            elif choice == "6":
                # Limpiar caché de mensajes
                client.clear_message_cache()
            
            elif choice == "7":
                # Ver estadísticas
                client.show_stats()
                    
            else:
                print("❌ Opción inválida")
            
            # Pausa pequeña
            await asyncio.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
