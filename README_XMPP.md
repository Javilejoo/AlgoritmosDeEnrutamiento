# Algoritmos de Enrutamiento - Versión Expandida

Este proyecto implementa múltiples algoritmos de enrutamiento con soporte completo para XMPP y protocolos de red estándar.

## 🆕 Nuevas Características (Laboratorio XMPP)

### 🌐 Protocolo de Comunicación Estándar
- **Formato JSON unificado** para interoperabilidad entre grupos
- **Tipos de mensaje**: DATA, HELLO, ECHO, INFO, LSP, DV
- **Headers personalizables** y TTL automático
- **Validación completa** de mensajes

### 🔗 Soporte XMPP Completo
- **Cliente XMPP asíncrono** con slixmpp
- **Modo offline** para desarrollo local
- **Gestión de conexiones** y manejo de errores
- **Interoperabilidad** con otros grupos

### 🤖 Algoritmos Implementados
- **Distance Vector Routing (DVR)** distribuido
- **Link State Routing (LSR)** con flooding
- **Dijkstra centralizado** (base existente)
- **Flooding** para descubrimiento y propagación

### 🎯 Procesos Separados
Cada nodo implementa:
- **Proceso de Forwarding**: Manejo de paquetes entrantes/salientes
- **Proceso de Routing**: Cálculo y actualización de tablas
- **Proceso de Discovery**: Descubrimiento de vecinos

## 📁 Estructura Expandida del Proyecto

### Archivos Nuevos:
```
protocolo.py              # Definición del protocolo JSON estándar
xmpp_client.py            # Cliente XMPP para comunicación real
routing_node.py           # Nodo base con forwarding/routing separados
routing_algorithms.py     # Implementaciones DVR y LSR específicas
config_manager.py         # Gestión de configuraciones y topologías
test_coordinator.py       # Coordinador para pruebas automáticas
main_xmpp.py             # Interfaz unificada nueva
```

### Archivos de Configuración:
```
topology.json            # Topología de red (nodos y conexiones)
nodes.json              # Configuración de nodos (JIDs, passwords)
scenario_*.json         # Escenarios de prueba predefinidos
```

## 🚀 Inicio Rápido - Nueva Interfaz

### Opción 1: Interfaz Unificada (Recomendado)
```bash
python main_xmpp.py
```

### Opción 2: Componentes Individuales
```bash
# Crear configuraciones
python config_manager.py

# Probar protocolo
python protocolo.py

# Demo de algoritmos
python routing_algorithms.py
```

## 🌐 Configuración XMPP

### Para Producción (XMPP Real):
1. **Instalar dependencias**:
   ```bash
   pip install slixmpp
   ```

2. **Configurar servidor XMPP** (ejabberd, openfire, etc.)

3. **Crear cuentas de usuario**:
   - `node_a@servidor.com`
   - `node_b@servidor.com`
   - etc.

4. **Editar configuración**:
   ```json
   {
     "node_id": "A",
     "jid": "node_a@servidor.com",
     "password": "password_real",
     "resource": "routing"
   }
   ```

5. **Cambiar a modo XMPP**:
   ```python
   coordinator = TestCoordinator(use_xmpp=True)
   ```

### Para Desarrollo (Modo Offline):
```python
# Ya configurado por defecto
coordinator = TestCoordinator(use_xmpp=False)
```

## 🎯 Protocolo de Mensajes

### Estructura Estándar:
```json
{
  "proto": "dijkstra|flooding|lsr|dvr",
  "type": "message|echo|info|hello|data|lsp|dv",
  "from": "node_a@server.com/resource",
  "to": "node_b@server.com/resource",
  "ttl": 5,
  "headers": [{"forwarded_by": "node_c"}, {"timestamp": 1234567890}],
  "payload": "contenido específico del mensaje"
}
```

### Tipos de Mensaje:
- **DATA**: Mensajes de usuario
- **HELLO**: Descubrimiento de vecinos
- **ECHO**: Ping/Pong para latencia
- **LSP**: Link State Packets
- **DV**: Distance Vectors
- **INFO**: Información general

## 🧪 Pruebas y Validación

### Suite de Pruebas Completa:
```bash
python main_xmpp.py
# Seleccionar opción 9: Prueba completa de conectividad
```

### Pruebas Específicas:
- **Conectividad**: Verificar entrega de mensajes
- **Flooding**: Probar propagación de información
- **Rendimiento**: Medir throughput y latencia
- **Fallas**: Simular caídas de nodos
- **Convergencia**: Verificar estabilización de algoritmos

### Algoritmos Comparables:
```bash
# DVR vs LSR vs Dijkstra
python main_xmpp.py
# Opción 11: Comparar algoritmos
```

## 📊 Escenarios de Prueba

### Topologías Predefinidas:
- **Lineal**: A-B-C-D-E
- **Anillo**: Conexión circular
- **Estrella**: Un nodo central conectado a todos
- **Malla**: Todos conectados con todos
- **Custom**: Tu topología personalizada

### Generar Escenarios:
```python
from config_manager import ScenarioGenerator

# Topología lineal de 5 nodos
linear = ScenarioGenerator.linear_topology(5)

# Topología en anillo de 6 nodos  
ring = ScenarioGenerator.ring_topology(6)

# Topología en estrella con 7 nodos
star = ScenarioGenerator.star_topology(7)
```

## 🔍 Monitoreo y Debugging

### Logs Detallados:
Cada nodo genera logs con:
- Mensajes enviados/recibidos
- Actualizaciones de routing
- Errores de conexión
- Estados de convergencia

### Estadísticas en Tiempo Real:
```python
node_stats = node.get_status()
# {
#   "packets_forwarded": 25,
#   "packets_received": 18,
#   "routing_updates": 3,
#   "neighbors": 2
# }
```

### Reportes Automáticos:
- Tasas de éxito de entrega
- Tiempos de convergencia
- Análisis de rutas
- Detección de loops

## 💡 Características Avanzadas

### 🔄 Tolerancia a Fallas:
- Detección automática de nodos caídos
- Recálculo de rutas dinámico
- Recuperación automática
- Simulación de fallas controladas

### ⚡ Optimizaciones:
- Cache de mensajes para evitar loops
- TTL automático para prevenir flooding infinito
- Compresión de headers opcionales
- Batch processing para mejor rendimiento

### 🛡️ Validación:
- Verificación de formato de mensajes
- Validación de topología
- Detección de configuraciones inválidas
- Prevención de ataques simples

## 🎮 Modo Interactivo

### Demo en Vivo:
```bash
python main_xmpp.py
# Opción 14: Demo interactivo básico
```

Incluye:
- Envío de mensajes paso a paso
- Visualización de convergencia
- Simulación de fallas interactiva
- Tutorial XMPP guiado

## 🤝 Interoperabilidad

### Estándar Entre Grupos:
- **Protocolo JSON unificado** definido
- **Tipos de mensaje estándar** 
- **Validación cruzada** de implementaciones
- **Testing conjunto** posible

### Formato de Intercambio:
```python
# Mensaje estándar que cualquier grupo puede procesar
message = MessageFactory.create_data_message(
    from_addr="grupo1_node_a@server.com",
    to_addr="grupo2_node_b@server.com", 
    user_message="Hola desde Grupo 1!",
    proto="lsr"
)
```

## 📚 Documentación de APIs

### NetworkMessage:
```python
# Crear mensaje
msg = NetworkMessage(proto, type, from_addr, to_addr, payload)

# Serializar
json_str = msg.to_json()

# Deserializar  
msg = NetworkMessage.from_json(json_str)
```

### RoutingNode:
```python
# Crear nodo
node = RoutingNode(node_id, jid, password)

# Iniciar procesos
await node.start()

# Enviar mensaje de usuario
await node.send_user_message(dest_node, "Hola!")

# Obtener estado
status = node.get_status()
```

### TestCoordinator:
```python
# Configurar pruebas
coordinator = TestCoordinator(use_xmpp=False)
coordinator.load_configuration("topology.json", "nodes.json")

# Ejecutar pruebas
results = await coordinator.run_connectivity_test()
```

## 🎯 Casos de Uso

### 1. Desarrollo de Algoritmo:
```bash
# Crear nuevo algoritmo
python routing_algorithms.py
# Implementar en clase que hereda de RoutingNode
```

### 2. Testing Intergrupal:
```bash
# Configurar XMPP común
# Ejecutar nodos de diferentes grupos
# Verificar interoperabilidad
```

### 3. Análisis Académico:
```bash
# Comparar algoritmos
# Generar métricas
# Crear reportes automáticos
```

### 4. Simulación de Red Real:
```bash
# Cargar topología real
# Simular condiciones de red
# Analizar comportamiento
```

## ⚠️ Consideraciones Importantes

### Rendimiento:
- Modo offline más rápido para desarrollo
- XMPP real más lento pero realista
- Configurar timeouts apropiados

### Seguridad:
- Validar todos los mensajes entrantes
- Implementar rate limiting si necesario
- Usar contraseñas seguras en producción

### Escalabilidad:
- Testeado hasta 9 nodos
- Optimizar para redes más grandes
- Considerar particionado si necesario

## 🚀 Roadmap Futuro

### Próximas Características:
- [ ] Algoritmo OSPF completo
- [ ] Soporte para IPv6
- [ ] Interfaz web para monitoreo
- [ ] Métricas de QoS
- [ ] Simulación de latencia variable

### Optimizaciones Planeadas:
- [ ] Paralelización de cálculos
- [ ] Compresión de mensajes
- [ ] Cache distribuido
- [ ] Load balancing automático

---

## 🙋 Soporte

Para preguntas o problemas:
1. Revisar logs detallados
2. Verificar configuración de topología
3. Probar en modo offline primero
4. Consultar ejemplos en `main_xmpp.py`

**¡El proyecto ahora está listo para el laboratorio de XMPP y pruebas intergrupales!** 🎉
