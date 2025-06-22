# Simulación de Tráfico con Pygame

Este proyecto simula el tráfico vehicular utilizando el autómata celular Regla 184. La simulación representa vehículos con '1' y espacios vacíos con '0'. Los vehículos se mueven en diferentes escenarios: carril único, doble carril o cruce de carreteras.

## Estructura del Proyecto

```
Rule-184-ECA
├── src
│   ├── carril.py          # Simulación de carril único (dos carriles en el mismo sentido)
│   ├── doble_carril.py    # Simulación de doble carretera (cada una con dos carriles)
│   └── cruce.py           # Simulación de cruce de carreteras
├── assets
│   ├── carril.png         # Fondo para la simulación de carril único
│   ├── doble_carril.png   # Fondo para la simulación de doble carril
│   ├── cruce.png          # Fondo para la simulación de cruce
│   ├── 1_right.png        # Imagen de vehículo en dirección derecha
│   ├── 1_left.png         # Imagen de vehículo en dirección izquierda
│   ├── 1_up.png           # Imagen de vehículo en dirección arriba
│   ├── 1_down.png         # Imagen de vehículo en dirección abajo
│   ├── 2_right.png        # Variantes de vehículos tipo 2
│   ├── 2_left.png
│   ├── 2_up.png
│   ├── 2_down.png
│   ├── 3_right.png        # Variantes de vehículos tipo 3
│   ├── 3_left.png
│   ├── 3_up.png
│   ├── 3_down.png
│   ├── 4_right.png        # Variantes de vehículos tipo 4
│   ├── 4_left.png
│   ├── 4_up.png
│   └── 4_down.png
├── requirements.txt       # Dependencias requeridas para el proyecto
└── README.md              # Documentación del proyecto
```

## Instalación

1. Clona el repositorio:
   ```
   git clone <repository-url>
   cd Rule-184-ECA
   ```

2. Instala las dependencias requeridas:
   ```
   pip install -r requirements.txt
   ```

## Uso

Puedes ejecutar cualquiera de las tres simulaciones disponibles:

```
python src/carril.py      # Para la simulación de carril único
python src/doble_carril.py # Para la simulación de doble carretera
python src/cruce.py       # Para la simulación de cruce de carreteras
```

### Controles comunes:

- **Espacio**: Pausar/Reanudar la simulación
- **T**: Cambiar a modo Toroide (frontera cíclica)
- **N**: Cambiar a modo Nulo (fronteras abiertas)
- **R**: Reiniciar la simulación
- **↑/↓**: Aumentar/Disminuir la velocidad de la simulación

## Implementación de la Regla 184

La Regla 184 es un autómata celular unidimensional que modela el flujo de tráfico. En esta implementación:
- Los vehículos se representan como '1' en el arreglo
- Los espacios vacíos se representan como '0'
- Un vehículo avanza si hay espacio delante de él
- Un vehículo se detiene si hay otro vehículo adelante

## Características adicionales

- **Cambios de carril**: Los vehículos pueden cambiar de carril para evitar obstáculos.
- **Averías de vehículos**: Los vehículos pueden descomponerse temporalmente y bloquear el tráfico.
- **Modos de frontera**: 
  - Toroide: Los vehículos que salen por un extremo aparecen por el opuesto.
  - Nulo: Los vehículos pueden entrar y salir por los límites del escenario.
- **Velocidad ajustable**: La velocidad de la simulación puede modificarse durante la ejecución.
- **Visualización mejorada**: Efectos visuales para una mejor representación del tráfico.

## Simulador de Cruce

La simulación del cruce de carreteras implementa:
- Cuatro carreteras (dos horizontales y dos verticales)
- Cada carretera tiene dos carriles (uno en cada sentido)
- Aplicación de la Regla 184 para el movimiento de vehículos
- Gestión de tráfico en el área de intersección

## Assets

El proyecto utiliza las siguientes imágenes para la visualización:
- Fondos de carreteras (`carril.png`, `doble_carril.png`, `cruce.png`)
- Imágenes de vehículos en cuatro direcciones (arriba, abajo, izquierda, derecha)
- Cuatro tipos diferentes de vehículos para aumentar la variedad visual