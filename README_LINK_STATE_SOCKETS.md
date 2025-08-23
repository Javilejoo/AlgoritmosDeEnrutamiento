# Link State con Sockets - Guía de Uso

## 📋 Descripción

Implementación distribuida del algoritmo **Link State Routing** usando sockets TCP. Cada nodo es un proceso independiente que se comunica con otros nodos para intercambiar información de topología y calcular rutas óptimas usando Dijkstra.

## 🚀 Inicio Rápido

### Opción 1: Script automático (Windows)
```cmd
inicio_rapido.bat
```

### Opción 2: Coordinador interactivo
```cmd
python coordinador_link_state.py
```

### Opción 3: Nodos individuales
```cmd
python link_state_socket.py A 65001
python link_state_socket.py B 65002
python link_state_socket.py F 65006
```

## 📁 Archivos del Sistema

### 🔧 Archivos principales
- **`link_state_socket.py`** - Nodo Link State distribuido
- **`coordinador_link_state.py`** - Gestor de múltiples nodos
- **`cliente_link_state.py`** - Cliente para monitorear y controlar

### 🎯 Archivos de utilidad
- **`inicio_rapido.bat`** - Script de inicio automático
- **`README_LINK_STATE_SOCKETS.md`** - Esta documentación

## 🌐 Topología de Red

```
     A ----7---- B
     |  \        |
     7   1       2
     |    \      |
     C     I     F ----4---- H
     |     |     |  \      /
     5     6     1   3    /
     |     |     |    \  /
     D ----1---- F ---- G
     |           |
     1           4
     |           |
     E ----4---- G
```

## 🔧 Configuración de Puertos

| Nodo | Puerto |
|------|--------|
| A    | 65001  |
| B    | 65002  |
| C    | 65003  |
| D    | 65004  |
| E    | 65005  |
| F    | 65006  |
| G    | 65007  |
| H    | 65008  |
| I    | 65009  |

## 🎮 Uso del Sistema

### 1. Iniciar nodos

**Nodo individual:**
```cmd
python link_state_socket.py <NODO> <PUERTO>

# Ejemplos:
python link_state_socket.py A 65001
python link_state_socket.py B 65002
```

**Con coordinador:**
```cmd
python coordinador_link_state.py
# Seleccionar opción 3: "Iniciar red completa"
```

### 2. Monitorear la red

**Cliente interactivo:**
```cmd
python cliente_link_state.py
```

Opciones disponibles:
- ✅ Verificar conectividad de nodos
- 📋 Ver tablas de enrutamiento
- 🗄️ Examinar bases de datos Link State (LSDB)
- 🔍 Comparar rutas entre nodos
- 📡 Monitorear convergencia

### 3. Gestión con coordinador

```cmd
python coordinador_link_state.py
```

Funcionalidades:
- 🚀 Inicio/parada de nodos individuales o completos
- 📊 Estado de la red en tiempo real
- 🔧 Demos predefinidos
- 📈 Monitoreo de procesos

## 💡 Ejemplos de Uso

### Demo básico (3 nodos)
```cmd
# Terminal 1: Iniciar nodos
python coordinador_link_state.py
# Seleccionar: 8 -> 1 (Demo básico A,B,F)

# Terminal 2: Monitorear
python cliente_link_state.py
# Seleccionar: 7 (Ejecutar demo básico)
```

### Verificar convergencia
```cmd
python cliente_link_state.py
# Seleccionar: 6 (Monitorear convergencia)
# Ingresar nodos: A,B,F,D
# Duración: 30 segundos
```

### Comparar tablas de enrutamiento
```cmd
python cliente_link_state.py
# Seleccionar: 4 (Comparar tablas)
# Ingresar nodos: A,B,F
```

## 🔍 Características Implementadas

### ✅ Protocolo Link State completo
- **LSPs (Link State Packets)** con número de secuencia
- **Flooding** confiable con confirmaciones (ACK)
- **LSDB (Link State Database)** distribuida
- **Detección de duplicados** con cache de LSPs

### ✅ Comunicación por sockets
- **TCP confiable** para intercambio de LSPs
- **Threading** para manejo concurrente de conexiones
- **Timeouts** y manejo robusto de errores
- **JSON** para serialización de mensajes

### ✅ Integración con Dijkstra
- Usa tu implementación existente de `dijkstra.py`
- Recálculo automático cuando cambia la topología
- Tablas de enrutamiento con next-hop y rutas completas

### ✅ Herramientas de gestión
- **Coordinador** para gestión centralizada
- **Cliente** para monitoreo y análisis
- **Scripts** de inicio automático

## 📊 Tipos de Mensajes

### 1. LSP Flood
```json
{
  "tipo": "lsp_flood",
  "sender": "A",
  "lsp": {
    "source": "A",
    "sequence_num": 5,
    "age": 0,
    "neighbors": {"B": 7, "I": 1, "C": 7},
    "timestamp": 1692720000.0
  }
}
```

### 2. Hello (Verificar conectividad)
```json
{
  "tipo": "hello"
}
```

### 3. Get Status (Obtener estado)
```json
{
  "tipo": "get_status"
}
```

## 🐛 Solución de Problemas

### Nodo no responde
```cmd
# Verificar si el proceso está ejecutándose
netstat -an | findstr 65001

# Reiniciar nodo
python link_state_socket.py A 65001
```

### Error de puerto en uso
```cmd
# Matar procesos Python
taskkill /f /im python.exe

# O usar puertos diferentes
python link_state_socket.py A 65011
```

### LSPs no se propagan
- Verificar que los nodos vecinos estén activos
- Revisar logs de conectividad en cada nodo
- Usar el cliente para verificar estados

## 📈 Monitoreo y Estadísticas

### Estado de nodo (ejemplo)
```json
{
  "nombre": "A",
  "vecinos": {"B": 7, "I": 1, "C": 7},
  "sequence_num": 3,
  "topology_version": 12,
  "lsdb_size": 4,
  "estadisticas": {
    "lsps_enviados": 8,
    "lsps_recibidos": 15,
    "tablas_calculadas": 4
  }
}
```

### Tabla de enrutamiento (ejemplo)
```
--- Tabla de Enrutamiento de A ---
Destino | Next-Hop | Distancia | Ruta
-----------------------------------------
B       | B        | 7         | A -> B
D       | I        | 7         | A -> I -> D
F       | B        | 9         | A -> B -> F
```

## 🔄 Flujo del Algoritmo

1. **Inicialización**
   - Nodo inicia servidor TCP
   - Genera LSP inicial con vecinos
   - Calcula tabla local con Dijkstra

2. **Intercambio inicial**
   - Propaga LSP a vecinos directos
   - Recibe LSPs de otros nodos
   - Actualiza LSDB y recalcula rutas

3. **Convergencia**
   - Flooding de LSPs por toda la red
   - Cada nodo construye vista completa
   - Tablas de enrutamiento convergen

4. **Operación estable**
   - Monitoreo de cambios de topología
   - Regeneración de LSPs ante cambios
   - Propagación automática de actualizaciones

## 🎯 Ventajas de esta implementación

- **🌐 Distribuida real**: Cada nodo es un proceso independiente
- **🔄 Dinámica**: Responde automáticamente a cambios
- **🔍 Observable**: Herramientas completas de monitoreo
- **🎮 Interactiva**: Menús y demos para experimentar
- **🔧 Modular**: Coordinador, cliente y nodos separados
- **📊 Instrumentada**: Estadísticas detalladas de operación

¡Experimenta con diferentes topologías y observa cómo Link State mantiene la consistencia de enrutamiento en toda la red distribuida! 🚀
