# Algoritmo de Link State Routing

Este proyecto implementa el algoritmo de **Link State Routing** basándose en Dijkstra para calcular las rutas óptimas en una red distribuida.

## Archivos implementados

### 1. `link_state.py` - Implementación principal
- **LSP (Link State Packet)**: Paquetes que contienen información de vecindad
- **LinkStateDB**: Base de datos de estados de enlace
- **LinkStateNode**: Nodo que implementa el protocolo Link State
- **Simulación completa**: Demuestra convergencia, fallas y recuperación

### 2. `test_link_state.py` - Pruebas comparativas
- Compara Link State vs cálculo estático con Dijkstra
- Prueba escenarios dinámicos (fallas, mejoras, particiones)
- Análisis de convergencia y características del algoritmo

### 3. `demo_link_state.py` - Demo interactivo
- Menú interactivo para experimentar con Link State
- Permite modificar enlaces en tiempo real
- Escenarios predefinidos para probar diferentes situaciones

## Cómo ejecutar

### Simulación completa
```bash
python link_state.py
```

### Pruebas comparativas
```bash
python test_link_state.py
```

### Demo interactivo
```bash
python demo_link_state.py
```

## Características implementadas

### ✅ Protocolo Link State completo
- **LSPs (Link State Packets)** con número de secuencia y edad
- **Flooding** de LSPs a todos los nodos
- **LSDB (Link State Database)** para mantener topología completa
- **Detección de cambios** y regeneración de LSPs

### ✅ Integración con Dijkstra
- Usa tu implementación existente de Dijkstra
- Recálculo automático de rutas cuando cambia la topología
- Tablas de enrutamiento con next-hop y rutas completas

### ✅ Manejo de eventos dinámicos
- **Falla de enlaces**: Detección y propagación automática
- **Recuperación de enlaces**: Con nuevos costos
- **Partición de red**: Manejo de nodos desconectados
- **Nuevos enlaces**: Incorporación dinámica

## Topología de prueba

La implementación usa la misma topología que tu proyecto:

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

## Ejemplo de uso básico

```python
from link_state import LinkStateNode

# Crear nodo con vecinos
nodo_A = LinkStateNode("A", {"B": 7, "I": 1, "C": 7})

# Simular cambio en la red
nodo_A.update_neighbor("B", 5)  # Cambiar costo A-B de 7 a 5

# Ver tabla de enrutamiento
nodo_A.print_routing_table()
```

## Diferencias con Distance Vector

| Aspecto | Link State | Distance Vector |
|---------|------------|-----------------|
| **Información** | Topología completa | Solo distancias |
| **Convergencia** | Rápida | Lenta (count-to-infinity) |
| **Loops** | No hay | Posibles |
| **Escalabilidad** | Mejor | Limitada |
| **Memoria** | Mayor (LSDB) | Menor |
| **Tráfico control** | Flooding de LSPs | Intercambio de vectores |

## Ventajas implementadas

1. **Vista completa de topología**: Cada nodo conoce toda la red
2. **Cálculo independiente**: Cada nodo calcula sus propias rutas
3. **Convergencia rápida**: Cambios se propagan inmediatamente
4. **Sin loops**: Dijkstra garantiza rutas óptimas sin loops
5. **Detección automática**: De fallas y recuperaciones
6. **Escalabilidad**: Funciona bien en redes grandes

## Casos de prueba incluidos

### 1. Convergencia inicial
- Intercambio de LSPs entre todos los nodos
- Construcción de LSDB completa
- Cálculo inicial de tablas de enrutamiento

### 2. Falla de enlace (F-H)
- Detección de falla
- Generación de nuevos LSPs
- Propagación del cambio
- Recálculo de rutas afectadas

### 3. Mejora de enlace (A-C: 7→2)
- Detección de mejora
- Actualización de costos
- Recálculo para encontrar rutas mejores

### 4. Partición de red
- Desconexión de nodo I
- Manejo de nodos inalcanzables
- Cleanup de rutas obsoletas

### 5. Recuperación con nueva topología
- Reconexión con costos diferentes
- Redescubrimiento de rutas
- Actualización de tablas

## Comparación con tu Dijkstra estático

El algoritmo implementado produce **exactamente los mismos resultados** que tu implementación de Dijkstra estático, pero añade:

- **Dinamismo**: Se adapta automáticamente a cambios
- **Distribución**: Cada nodo mantiene su propia vista
- **Robustez**: Maneja fallas y recuperaciones
- **Realismo**: Simula un protocolo de enrutamiento real

¡Ejecuta los demos para experimentar con diferentes escenarios y ver Link State en acción! 🚀
