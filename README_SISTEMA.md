# 🌐 Sistema de Algoritmos de Enrutamiento con Dijkstra

Este proyecto implementa el algoritmo de Dijkstra para calcular rutas óptimas en una red, usando múltiples enfoques incluyendo comunicación por sockets.

## 🚀 Inicio Rápido

### Opción 1: Ejecutar todo desde el menú principal
```bash
python main.py
```
Selecciona la **opción 5** para la experiencia completa con terminales separadas.

### Opción 2: Abrir nodos directamente
```bash
python abrir_nodos.py
```

### Opción 3: Nodo individual (manual)
```bash
python nodo_terminal.py A
```

## 📋 Estructura del Proyecto

### Archivos Principales
- **`main.py`** - Menú principal con todas las opciones
- **`dijkstra.py`** - Implementación centralizada del algoritmo
- **`grafo.py`** - Clase para manejar el grafo de la red
- **`nodo_terminal.py`** - Nodo individual interactivo
- **`abrir_nodos.py`** - Gestor para abrir múltiples terminales

### Sistema Cliente-Servidor Simple
- **`servidor.py`** - Servidor para consultas punto a punto
- **`cliente.py`** - Cliente para hacer consultas específicas

### Sistema Distribuido Automático
- **`coordinador.py`** - Coordina la red distribuida
- **`red_distribuida.py`** - Gestor del sistema distribuido
- **`nodo.py`** - Implementación de nodo para sistema automático

## 🎯 Uso Recomendado: Nodos en Terminales Separadas

### 1. Ejecutar el gestor:
```bash
python abrir_nodos.py
```

### 2. Seleccionar "Abrir todas las terminales"
Esto abrirá 9 terminales, una para cada nodo (A, B, C, D, E, F, G, H, I)

### 3. En cualquier terminal de nodo:
- **Opción 1**: Ver tabla de enrutamiento
- **Opción 2**: Enviar paquete a otro nodo
- **Opción 3**: Cerrar nodo

### 4. Ejemplo de flujo:
1. En terminal del Nodo A: seleccionar opción 2
2. Escribir destino: `D`
3. Escribir mensaje: `Hola desde A`
4. En la terminal del Nodo D verás:

```
📦 PAQUETE RECIBIDO!
   De: A
   Para: D
   Mensaje: Hola desde A
   Ruta usada: A -> I -> D
   Costo total: 7
   ✅ ENTREGADO EXITOSAMENTE
```

## 🗺️ Topología de la Red

```
        B -------- F -------- H
       /|          |\        
      7 |          | \3      
     /  |2         |1 \      
    A   |          |   G ---- E
    |\  |          |  /4    /
    |7\ |          | /     /4
    | \ |          |/     /
    |1 \|          D ----/
    |   C ---------/  1
    |   |  5       
    |   |          
    I---/          
      6            
```

### Nodos: A, B, C, D, E, F, G, H, I
### Puertos TCP: 
- A: 65001, B: 65002, C: 65003, D: 65004, E: 65005
- F: 65006, G: 65007, H: 65008, I: 65009

## 📊 Ejemplos de Rutas Calculadas

### Desde Nodo A:
- **A → B**: Ruta: A → B, Costo: 7
- **A → D**: Ruta: A → I → D, Costo: 7
- **A → E**: Ruta: A → I → D → E, Costo: 8
- **A → F**: Ruta: A → I → D → F, Costo: 8

## 🔧 Modos de Operación

### 1. **Centralizado** (`dijkstra.py`)
Calcula todas las tablas de una vez y las guarda en JSON

### 2. **Cliente-Servidor** (`servidor.py` + `cliente.py`)
Consultas individuales de ruta entre dos nodos

### 3. **Distribuido Automático** (`coordinador.py`)
Simula una red donde todos los nodos calculan automáticamente

### 4. **Nodos Interactivos** (`nodo_terminal.py`) ⭐
Cada nodo en su terminal, envío manual de paquetes con confirmación

## 📁 Archivos Generados

- **`tablas_json/`** - Tablas del algoritmo centralizado
- **`tablas_distribuidas/`** - Tablas del sistema distribuido

## ⚙️ Requisitos

- Python 3.7+
- Módulos estándar: socket, json, threading, heapq, subprocess

## 🎮 Comandos Útiles

### Abrir un nodo específico:
```bash
python nodo_terminal.py A
```

### Ver solo la implementación centralizada:
```bash
python dijkstra.py
```

### Comparar implementaciones:
```bash
python red_distribuida.py
```
Selecciona opción 5 para comparar centralizado vs distribuido.

---

## 💡 Características Destacadas

- ✅ **Visualización en tiempo real** del envío de paquetes
- ✅ **Confirmación de entrega** con ruta y costo
- ✅ **Múltiples terminales** para mejor comprensión
- ✅ **Cálculo automático** de rutas óptimas
- ✅ **Interfaz intuitiva** para cada nodo
- ✅ **Comparación** entre implementaciones
