# Constants used throughout the project

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 300

# Colors
ROAD_COLOR = (50, 50, 50)  # Dark gray for road background
CAR_COLOR1 = (0, 150, 255)  # Blue for cars in lane 1
CAR_COLOR2 = (255, 100, 0)  # Orange for cars in lane 2

# Simulation parameters
CAR_SIZE = 65  # Tamaño fijo de los autos en píxeles
CELL_SIZE = CAR_SIZE  # Hacemos que cada celda tenga exactamente el mismo tamaño que un auto
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE  # Número de celdas que caben en el ancho de la pantalla
GRID_HEIGHT = 100  # Simulation steps
DENSITY = 0.3  # Initial density of cars
LANE_CHANGE_PROBABILITY = 0.002  # 0.2% probability of lane change