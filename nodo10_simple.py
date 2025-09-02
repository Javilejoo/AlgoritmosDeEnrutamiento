#!/usr/bin/env python3
"""
Cliente LSR simplificado - Nodo10 automático
Menú simple para comunicación con otros nodos
"""

import asyncio
import redis.asyncio as redis
import json
import uuid
from datetime import datetime

REDIS_HOST = "lab3.redesuvg.cloud"
REDIS_PORT = 6379
REDIS_PASSWORD = "UVGRedis2025"

class Nodo10Client:
    def __init__(self):
        self.node_id = "sec20.topologia2.nodo10"
        self.redis_client = None
        self.pubsub = None
        self.algorithm = "flooding"  # Algoritmo por defecto
        self.test_mode = False  # Modo de prueba
        self.test_node_id = "sec20.topologia1.nodo1.prueba1"  # Canal de prueba
        
    async def connect(self):
        """Conectar automáticamente"""
        try:
            self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            
            if self.test_mode:
                # Modo prueba: solo escuchar canal de prueba
                await self.pubsub.subscribe(self.test_node_id)
                print(f"✅ Nodo conectado en MODO PRUEBA")
                print(f"👂 Escuchando en: {self.test_node_id}")
            else:
                # Modo normal: escuchar múltiples canales
                channels_to_listen = [
                    self.node_id,  # Propio canal para mensajes directos
                    "sec20.topologia2.nodo5",
                    "sec20.topologia2.nodo6", 
                    "sec20.topologia2.nodo7",
                    "sec20.topologia2.nodo8",
                    "sec20.topologia2.nodo9"
                ]
                
                for channel in channels_to_listen:
                    await self.pubsub.subscribe(channel)
                
                print(f"✅ Nodo conectado en MODO NORMAL")
                print(f"👂 Escuchando en: {self.node_id} + otros nodos")
            
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    async def send_hello(self, target_nodes=None):
        """Enviar HELLO a nodos específicos o todos"""
        if target_nodes is None:
            target_nodes = ["nodo5", "nodo6", "nodo7", "nodo8", "nodo9"]
        
        msg = {
            "proto": "lsr",
            "type": "hello",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": 5,
            "headers": [],
            "payload": ""
        }
        
        print(f"📤 Enviando HELLO...")
        for target in target_nodes:
            channel = f"sec20.topologia2.{target}"
            await self.redis_client.publish(channel, json.dumps(msg))
            print(f"   👋 HELLO → {target}")
            
            # Mostrar el formato completo del mensaje HELLO enviado
            message_format = {
                'type': 'message',
                'pattern': None,
                'channel': channel.encode(),
                'data': json.dumps(msg).encode()
            }
            print(f"   📋 Formato: {message_format}")
    
    async def send_message(self, target_node, content):
        """Enviar mensaje según el algoritmo seleccionado"""
        
        # Determinar el ID del remitente según el modo
        from_node = self.test_node_id if self.test_mode else self.node_id
        
        # AMBOS algoritmos usan protocolo LSR, pero difieren en el envío
        msg = {
            "proto": "lsr",
            "type": "message", 
            "from": from_node,
            "to": f"sec20.topologia2.{target_node}" if not self.test_mode else self.test_node_id,
            "ttl": 5,
            "headers": [],
            "payload": content,
            "algorithm": self.algorithm
        }
        
        if self.algorithm == "flooding":
            # FLOODING: Enviar a TODOS los vecinos/canales
            if self.test_mode:
                # En modo prueba, enviar múltiples veces al mismo canal de prueba para simular flooding
                print(f"📤 FLOODING (PRUEBA): Enviando mensaje para {target_node} al canal de prueba:")
                channel = self.test_node_id
                await self.redis_client.publish(channel, json.dumps(msg))
                print(f"   🌊 Flooding (Prueba) → {self.test_node_id}")
                
                # Mostrar el formato completo del mensaje enviado
                message_format = {
                    'type': 'message',
                    'pattern': None,
                    'channel': channel.encode(),
                    'data': json.dumps(msg).encode()
                }
                print(f"   📋 Formato: {message_format}")
            else:
                # Modo normal: enviar a todos los vecinos
                all_neighbors = ["nodo5", "nodo6", "nodo7", "nodo8", "nodo9"]
                
                print(f"📤 FLOODING: Enviando mensaje para {target_node} a TODOS los vecinos:")
                for neighbor in all_neighbors:
                    channel = f"sec20.topologia2.{neighbor}"
                    await self.redis_client.publish(channel, json.dumps(msg))
                    print(f"   🌊 Flooding → {neighbor}")
                    
                    # Mostrar el formato completo del mensaje enviado
                    message_format = {
                        'type': 'message',
                        'pattern': None,
                        'channel': channel.encode(),
                        'data': json.dumps(msg).encode()
                    }
                    print(f"   📋 Formato: {message_format}")
            
        else:
            # LINK STATE: Enviar solo al destino específico
            if self.test_mode:
                # En modo prueba, enviar al canal de prueba
                channel = self.test_node_id
                await self.redis_client.publish(channel, json.dumps(msg))
                print(f"📤 LSR (PRUEBA): Mensaje enviado al canal de prueba: {content}")
                
                # Mostrar el formato completo del mensaje enviado
                message_format = {
                    'type': 'message',
                    'pattern': None,
                    'channel': channel.encode(),
                    'data': json.dumps(msg).encode()
                }
                print(f"   📋 Formato: {message_format}")
            else:
                # Modo normal: enviar solo al destino
                channel = f"sec20.topologia2.{target_node}"
                await self.redis_client.publish(channel, json.dumps(msg))
                print(f"📤 LSR: Mensaje enviado directamente a {target_node}: {content}")
                
                # Mostrar el formato completo del mensaje enviado
                message_format = {
                    'type': 'message',
                    'pattern': None,
                    'channel': channel.encode(),
                    'data': json.dumps(msg).encode()
                }
                print(f"   📋 Formato: {message_format}")
    
    def set_algorithm(self, algorithm):
        """Cambiar algoritmo de enrutamiento"""
        self.algorithm = algorithm
        print(f"🎯 Algoritmo cambiado a: {algorithm}")
    
    def toggle_test_mode(self):
        """Alternar entre modo normal y modo prueba"""
        self.test_mode = not self.test_mode
        mode_name = "PRUEBA" if self.test_mode else "NORMAL"
        print(f"🔄 Modo cambiado a: {mode_name}")
        if self.test_mode:
            print(f"📡 Canal de prueba: {self.test_node_id}")
        else:
            print(f"📡 Canal normal: {self.node_id}")
        print("⚠️  Necesita reconectar para aplicar cambios")
    
    async def listen_messages(self):
        """Modo escucha directo (bloquea hasta Ctrl+C)"""
        if not self.pubsub:
            print("❌ No hay conexión pubsub")
            return
        
        print(f"👂 MODO ESCUCHA ACTIVADO")
        print(f"� Escuchando en: {self.node_id}")
        print("Time     | From     | Type    | Content")
        print("-" * 45)
        print("Presiona Ctrl+C para volver al menú")
        
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
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Manejar mensajes LSR (AMBOS algoritmos usan LSR ahora)
            if parsed.get("proto") == "lsr":
                msg_type = parsed.get("type")
                from_node = parsed.get("from", "Unknown")
                payload = parsed.get("payload", "")
                algorithm = parsed.get("algorithm", "unknown")
                
                # Solo mostrar mensajes de otros nodos
                if from_node != self.node_id:
                    from_short = from_node.split(".")[-1] if "." in from_node else from_node
                    
                    if msg_type == "hello":
                        print(f"{timestamp} | {from_short:8} | HELLO   | Saludo recibido")
                        
                    elif msg_type == "message":
                        to_node = parsed.get("to", "")
                        
                        if to_node == self.node_id:
                            # Mensaje dirigido a nosotros
                            algo_label = "FLOOD" if algorithm == "flooding" else "LSR"
                            print(f"{timestamp} | {from_short:8} | {algo_label:7} | {str(payload)[:20]}")
                            print(f"🎉 MENSAJE {algo_label} PARA TI: {payload}")
                        else:
                            # Mensaje en tránsito
                            algo_label = "FLD-TRA" if algorithm == "flooding" else "LSR-TRA"
                            to_short = parsed.get('to', 'N/A').split('.')[-1] if '.' in parsed.get('to', '') else parsed.get('to', 'N/A')
                            print(f"{timestamp} | {from_short:8} | {algo_label:7} | Para {to_short}")
                        
                    elif msg_type == "info":
                        print(f"{timestamp} | {from_short:8} | INFO    | Tabla de rutas")
                        
        except json.JSONDecodeError:
            pass  # Ignorar mensajes no JSON
        except Exception as e:
            pass  # Ignorar errores
    
    async def disconnect(self):
        """Desconectar"""
        self.running = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
        print("🔌 Desconectado")

def print_menu():
    """Mostrar menú simplificado"""
    print("\n" + "="*50)
    print("  🌐 NODO10 - COMUNICACIÓN LSR")
    print("="*50)
    print()
    print("📡 COMUNICACIÓN:")
    print("  1. Enviar HELLO a todos")
    print("  2. Enviar HELLO a nodo específico")
    print("  3. Enviar mensaje a nodo específico")
    print("  4. Modo escucha (Ctrl+C para salir)")
    print("  5. Seleccionar algoritmo")
    print("  6. Cambiar modo (Normal/Prueba)")
    print("  7. Reconectar")
    print()
    print("🎯 NODOS DISPONIBLES:")
    print("  nodo5, nodo6, nodo7, nodo8, nodo9")
    print()
    print("  0. Salir")
    print("-"*50)

async def main():
    """Función principal"""
    print("🚀 INICIANDO NODO10...")
    
    client = Nodo10Client()
    
    # Conectar automáticamente
    if not await client.connect():
        print("❌ No se pudo conectar. Saliendo...")
        return
    
    # Conexión exitosa
    mode_name = "PRUEBA" if client.test_mode else "NORMAL"
    print(f"🎯 Algoritmo actual: {client.algorithm}")
    print(f"🔧 Modo actual: {mode_name}")
    if client.test_mode:
        print(f"📡 Canal de prueba: {client.test_node_id}")
    
    try:
        while True:
            print_menu()
            choice = input("👉 Seleccione opción: ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
                
            elif choice == "1":
                # Enviar HELLO a todos
                await client.send_hello()
                
            elif choice == "2":
                # Enviar HELLO a nodo específico
                print("\n👋 ENVIAR HELLO ESPECÍFICO")
                print("Nodos disponibles: nodo5, nodo6, nodo7, nodo8, nodo9")
                
                target = input("¿A qué nodo? (ej: nodo5): ").strip()
                if not target:
                    print("❌ Debe especificar un nodo")
                    continue
                
                # Agregar 'nodo' si solo pusieron el número
                if target.isdigit():
                    target = f"nodo{target}"
                    
                await client.send_hello([target])
                
            elif choice == "3":
                # Enviar mensaje a nodo específico
                print(f"\n💌 ENVIAR MENSAJE (Algoritmo: {client.algorithm})")
                print("Nodos disponibles: nodo5, nodo6, nodo7, nodo8, nodo9")
                
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
                
            elif choice == "4":
                # Modo escucha directo
                await client.listen_messages()
                    
            elif choice == "5":
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
                    
            elif choice == "6":
                # Cambiar modo
                client.toggle_test_mode()
                
            elif choice == "7":
                # Reconectar
                print("🔄 Reconectando...")
                await client.disconnect()
                if await client.connect():
                    print("✅ Reconexión exitosa")
                else:
                    print("❌ Error en reconexión")
                    
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
