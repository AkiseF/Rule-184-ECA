# Simulación de Tráfico con Pygame

Este proyecto simula el tráfico vehicular utilizando el autómata celular Regla 184. La simulación representa vehículos con '1' y espacios vacíos con '0'. Los vehículos se mueven en diferentes escenarios: carril único, doble carril o cruce con semáforo.

## Estructura del Proyecto

```
Rule-184-ECA
├── src
│   ├── main.py            # Menú principal para seleccionar el tipo de simulación
│   ├── carril.py          # Simulación de carril único (dos carriles en sentidos opuestos)
│   ├── doble_carril.py    # Simulación de doble carril (dos carriles en cada sentido)
│   ├── cruce.py           # Simulación de cruce con semáforo
│   ├── simulation.py      # Implementación del autómata celular y visualización
│   └── utils
│       └── constants.py   # Constantes utilizadas en el proyecto
├── assets
│   ├── carril.png         # Fondo para la simulación de carril único
│   ├── doble_carril.png   # Fondo para la simulación de doble carril
│   ├── cruce.png          # Fondo para la simulación de cruce
│   ├── 1_right.png        # Imagen de vehículo en dirección derecha
│   ├── 1_left.png         # Imagen de vehículo en dirección izquierda
│   ├── 1_up.png           # Imagen de vehículo en dirección arriba
│   ├── 1_down.png         # Imagen de vehículo en dirección abajo
│   └── ... (otras imágenes de vehículos)
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

Para ejecutar la simulación, usa el siguiente comando:
```
python src/main.py
```

Esto abrirá un menú donde podrás seleccionar entre tres tipos de simulación:
- **Carril Único**: Dos carriles con tráfico en sentidos opuestos
- **Doble Carril**: Cuatro carriles (dos en cada sentido)
- **Cruce**: Intersección con semáforo

## Implementación de la Regla 184

La Regla 184 es un autómata celular unidimensional que modela el flujo de tráfico. En esta implementación:
- Los vehículos se representan como '1' en el arreglo
- Los espacios vacíos se representan como '0'
- Un vehículo avanza si hay espacio delante de él
- Un vehículo se detiene si hay otro vehículo adelante

## Assets

Asegúrate de incluir todas las imágenes necesarias en el directorio `assets` para que la simulación se muestre correctamente:
- Fondos de carreteras (`carril.png`, `doble_carril.png`, `cruce.png`)
- Imágenes de vehículos en diferentes direcciones