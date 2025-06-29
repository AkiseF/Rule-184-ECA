import pygame
import numpy as np
import random
import os
import math
import sys

# Inicializar pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 800, 800  # Dimensiones del canvas
CELL_SIZE = 20  # Tamaño de celda (20px como se especifica)
NUM_CELLS = 50  # Número de celdas por carril
MAX_CARS_PER_ROAD = 30  # Límite de coches iniciales por carretera

# Posiciones Y para los carriles horizontales (carreteras 1 y 2)
UPPER_LANE_1_Y = 372  # Carril superior de primera carretera (Este a Oeste)
LOWER_LANE_1_Y = 388  # Carril inferior de primera carretera (Este a Oeste)
UPPER_LANE_2_Y = 412  # Carril superior de segunda carretera (Oeste a Este)
LOWER_LANE_2_Y = 428  # Carril inferior de segunda carretera (Oeste a Este)

# Posiciones X para los carriles verticales (carreteras 3 y 4)
LEFT_LANE_3_X = 372   # Carril izquierdo de tercera carretera (Norte a Sur)
RIGHT_LANE_3_X = 388  # Carril derecho de tercera carretera (Norte a Sur)
LEFT_LANE_4_X = 412   # Carril izquierdo de cuarta carretera (Sur a Norte)
RIGHT_LANE_4_X = 428  # Carril derecho de cuarta carretera (Sur a Norte)

# Centro del cruce
CROSS_X = WIDTH // 2
CROSS_Y = HEIGHT // 2

# Probabilidades
CAR_BREAKDOWN_PROB = 0.05      # Probabilidad de avería (5%)
CAR_CHANGE_LANE_PROB = 0.1     # Probabilidad de cambiar de carril (20%)
CAR_TURN_PROB = 0.4            # Probabilidad de dar vuelta en el cruce (20%)
REPAIR_ATTEMPTS = 20           # Tiempo para intentar reparar (iteraciones)
REPAIR_PROB = 0.7              # Probabilidad de reparación (70%)
FRONTIER_SURVIVAL_PROB = 0.2   # Probabilidad de supervivencia en frontera nula (20%)

# Índices para los cruces
# Ajuste los índices para los cruces basados en las posiciones exactas de los carriles
CROSS_INDEX_HORIZONTAL_START = (WIDTH // 2 - 20) // CELL_SIZE
CROSS_INDEX_HORIZONTAL_END = (WIDTH // 2 + 20) // CELL_SIZE
CROSS_INDEX_VERTICAL_START = (HEIGHT // 2 - 20) // CELL_SIZE
CROSS_INDEX_VERTICAL_END = (HEIGHT // 2 + 20) // CELL_SIZE

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (130, 130, 130)
TRANS_WHITE = (255, 255, 255, 180)  # Blanco traslúcido para los controles
SMOKE_COLOR = (80, 80, 80, 180)      # Color del humo para los coches descompuestos

# Crear la ventana
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.HWSURFACE)
pygame.display.set_caption("Simulador de Tráfico en Cruce - Regla 184")
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.VIDEORESIZE])  # Permitir solo eventos específicos

# Función para cargar y escalar imágenes
def load_image(filename, size=(CELL_SIZE, CELL_SIZE)):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    image_path = os.path.join(parent_dir, "assets", filename)
    image = pygame.image.load(image_path)
    return pygame.transform.scale(image, size)

# Cargar imágenes
cruce_img = load_image("cruce.png", (WIDTH, HEIGHT))
brujula_img = load_image("brujula.png", (100, 100))

# Cargar iconos de los coches
car_images = {
    "1_left": load_image("1_left.png"),
    "1_right": load_image("1_right.png"),
    "1_up": load_image("1_up.png"),
    "1_down": load_image("1_down.png"),
    "2_left": load_image("2_left.png"),
    "2_right": load_image("2_right.png"),
    "2_up": load_image("2_up.png"),
    "2_down": load_image("2_down.png"),
    "3_left": load_image("3_left.png"),
    "3_right": load_image("3_right.png"),
    "3_up": load_image("3_up.png"),
    "3_down": load_image("3_down.png"),
    "4_left": load_image("4_left.png"),
    "4_right": load_image("4_right.png"),
    "4_up": load_image("4_up.png"),
    "4_down": load_image("4_down.png")
}

# Configurar icono de ventana
pygame.display.set_icon(load_image("logo_1.png"))

# Definición de la clase Car para representar cada coche en la simulación
class Car:
    def __init__(self, road, lane, position, direction):
        # Información de posición
        self.road = road        # Número de carretera (1, 2, 3, 4)
        self.origin_road = road # Número de carretera original (para mantener el tipo/perfil)
        self.lane = lane        # Nombre del carril ('upper', 'lower', 'left', 'right')
        self.position = position  # Índice en el arreglo
        self.direction = direction  # Dirección: 'left', 'right', 'up', 'down'
        
        # Estado del coche
        self.broken = False
        self.repair_attempts = 0
        self.repair_countdown = 0
        self.changing_lane = False
        
        # Posición para dibujar en pantalla
        self.x = 0
        self.y = 0
        self.update_drawing_position()
        
        # Animación
        self.animation_frames = 10  # Frames que dura la animación
        self.animation_progress = 0
        self.origin_x = 0
        self.origin_y = 0
        self.target_x = 0
        self.target_y = 0
        
        # Humo para coches descompuestos
        self.smoke_particles = []
        
    def update_drawing_position(self):
        """Actualiza la posición de dibujo del coche según su carril y posición."""
        if self.road == 1:  # Este a Oeste (left)
            if self.lane == 'upper':
                self.x = WIDTH - self.position * CELL_SIZE
                self.y = UPPER_LANE_1_Y
            else:  # lower
                self.x = WIDTH - self.position * CELL_SIZE
                self.y = LOWER_LANE_1_Y
        elif self.road == 2:  # Oeste a Este (right)
            if self.lane == 'upper':
                self.x = self.position * CELL_SIZE
                self.y = UPPER_LANE_2_Y
            else:  # lower
                self.x = self.position * CELL_SIZE
                self.y = LOWER_LANE_2_Y
        elif self.road == 3:  # Norte a Sur (down)
            if self.lane == 'left':
                self.x = LEFT_LANE_3_X
                self.y = self.position * CELL_SIZE
            else:  # right
                self.x = RIGHT_LANE_3_X
                self.y = self.position * CELL_SIZE
        elif self.road == 4:  # Sur a Norte (up)
            if self.lane == 'left':
                self.x = LEFT_LANE_4_X
                self.y = HEIGHT - self.position * CELL_SIZE
            else:  # right
                self.x = RIGHT_LANE_4_X
                self.y = HEIGHT - self.position * CELL_SIZE
    
    def break_down(self):
        """El coche se avería."""
        self.broken = True
        self.repair_attempts = REPAIR_ATTEMPTS
        self.smoke_particles.clear()  # Limpiar partículas anteriores
    
    def repair(self):
        """Intenta reparar el coche."""
        if self.broken and self.repair_attempts <= 0:
            if random.random() < REPAIR_PROB:
                self.broken = False
                self.smoke_particles.clear()
                return True  # Coche reparado
            else:
                return False  # Coche remolcado, debe ser eliminado
        self.repair_attempts -= 1
        return None  # Aún no se puede reparar
    
    def start_lane_change(self, new_lane):
        """Inicia la animación de cambio de carril."""
        self.changing_lane = True
        self.animation_progress = 0
        self.origin_x = self.x
        self.origin_y = self.y
        
        # Guardar el carril original para la animación
        old_lane = self.lane
        self.lane = new_lane
        
        # Calcular posición objetivo después del cambio
        self.update_drawing_position()
        self.target_x = self.x
        self.target_y = self.y
        
        # Restaurar carril original hasta completar la animación
        self.lane = old_lane
    
    def start_turn(self, target_road, target_lane):
        """Inicia un giro en la intersección sin animación."""
        old_road = self.road
        self.road = target_road
        self.lane = target_lane
        
        # Ajustar posición y dirección según el tipo de giro
        if old_road == 1 and self.road == 4:  # De Este a Sur -> Norte
            self.position = NUM_CELLS - (CROSS_INDEX_VERTICAL_END + 1)
            self.direction = 'up'
        elif old_road == 2 and self.road == 3:  # De Oeste a Norte -> Sur
            self.position = CROSS_INDEX_VERTICAL_START + 1
            self.direction = 'down'
        elif old_road == 3 and self.road == 1:  # De Norte a Oeste -> Este
            self.position = NUM_CELLS - (CROSS_INDEX_HORIZONTAL_START + 1)
            self.direction = 'left'
        elif old_road == 4 and self.road == 2:  # De Sur a Este -> Oeste
            self.position = CROSS_INDEX_HORIZONTAL_END + 1
            self.direction = 'right'
        
        # Actualizar la posición de dibujo
        self.update_drawing_position()
        old_road = self.road
        old_lane = self.lane
        old_position = self.position
        old_direction = self.direction
        
        # Actualizar temporalmente para calcular posición objetivo
        self.road = target_road
        self.lane = target_lane
        
        # Ajustar posición según el nuevo carril y la dirección del giro
        if old_road == 1 and target_road == 4:  # Este a Sur (left a up)
            self.position = NUM_CELLS - (CROSS_INDEX_VERTICAL_END + 1)
            self.direction = 'up'
        elif old_road == 2 and target_road == 3:  # Oeste a Norte (right a down)
            self.position = CROSS_INDEX_VERTICAL_START + 1
            self.direction = 'down'
        elif old_road == 3 and target_road == 1:  # Norte a Oeste (down a left)
            self.position = NUM_CELLS - (CROSS_INDEX_HORIZONTAL_START + 1)
            self.direction = 'left'
        elif old_road == 4 and target_road == 2:  # Sur a Este (up a right)
            self.position = CROSS_INDEX_HORIZONTAL_END + 1
            self.direction = 'right'
        
        self.update_drawing_position()
        self.target_x = self.x
        self.target_y = self.y
        
        # Restaurar valores originales hasta completar la animación
        self.road = old_road
        self.lane = old_lane
        self.position = old_position
        self.direction = old_direction
        self.update_drawing_position()

    
    def update_animation(self):
        """Actualiza la animación del coche (solo para cambio de carril)."""
        if self.changing_lane:
            self.animation_progress += 1
            progress_ratio = self.animation_progress / self.animation_frames
            
            if self.animation_progress >= self.animation_frames:
                # Animación completa, actualizar carril
                new_lane = 'upper' if self.lane == 'lower' else 'lower' if self.lane == 'upper' else 'left' if self.lane == 'right' else 'right'
                self.lane = new_lane
                self.update_drawing_position()
                self.changing_lane = False
            else:
                # Animación en progreso, interpolar posición
                self.x = self.origin_x + (self.target_x - self.origin_x) * progress_ratio
                self.y = self.origin_y + (self.target_y - self.origin_y) * progress_ratio
    
        # Actualizar partículas de humo si el coche está averiado
        if self.broken:
            # Agregar nuevas partículas de humo
            if random.random() < 0.3:  # 30% de prob. por frame de agregar una nueva partícula
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-15, -5)
                size = random.randint(2, 6)
                lifetime = random.randint(20, 40)
                self.smoke_particles.append({
                    'x': self.x + offset_x,
                    'y': self.y + offset_y,
                    'size': size,
                    'lifetime': lifetime
                })
            
            # Actualizar partículas existentes
            for particle in self.smoke_particles[:]:
                particle['y'] -= 0.5  # El humo sube
                particle['lifetime'] -= 1
                if particle['lifetime'] <= 0:
                    self.smoke_particles.remove(particle)
    
    def draw(self, surface):
        """Dibuja el coche en la superficie dada."""
        # Para cambio de carril, actualizar la animación
        if self.changing_lane:
            self.update_animation()
        
        # Determinar la imagen correcta según el tipo original y la dirección actual
        img_key = f"{self.origin_road}_{self.direction}"
        if img_key in car_images:
            car_img = car_images[img_key].copy()
        else:
            # Imagen predeterminada si no se encuentra la específica
            car_img = car_images["1_left"].copy()
        
        # Si el coche está averiado, añadir tinte rojo
        if self.broken:
            # Dibujar humo primero (detrás del coche)
            for particle in self.smoke_particles:
                smoke_surface = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
                alpha = min(255, particle['lifetime'] * 6)  # Fade out
                smoke_surface.fill((SMOKE_COLOR[0], SMOKE_COLOR[1], SMOKE_COLOR[2], alpha))
                surface.blit(smoke_surface, (particle['x'], particle['y']))
                
            # Tinte rojo para el coche
            red_overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 100))
            car_img.blit(red_overlay, (0, 0))
        
        # Dibujar el coche
        surface.blit(car_img, (self.x - CELL_SIZE//2, self.y - CELL_SIZE//2))
        
    def get_image_key(self):
        """Obtiene la clave para la imagen del coche según su dirección actual y tipo original."""
        return f"{self.origin_road}_{self.direction}"

# Definición de la clase TrafficSimulator para manejar la simulación
class TrafficSimulator:
    def __init__(self):
        # Inicializar arrays para cada carril
        # Usamos arrays de numpy para representar cada celda (0 = vacío, 1 = ocupado)
        # Carretera 1: Este a Oeste
        self.road1_upper = np.zeros(NUM_CELLS, dtype=int)  # Carril superior
        self.road1_lower = np.zeros(NUM_CELLS, dtype=int)  # Carril inferior
        
        # Carretera 2: Oeste a Este
        self.road2_upper = np.zeros(NUM_CELLS, dtype=int)  # Carril superior
        self.road2_lower = np.zeros(NUM_CELLS, dtype=int)  # Carril inferior
        
        # Carretera 3: Norte a Sur
        self.road3_left = np.zeros(NUM_CELLS, dtype=int)   # Carril izquierdo
        self.road3_right = np.zeros(NUM_CELLS, dtype=int)  # Carril derecho
        
        # Carretera 4: Sur a Norte
        self.road4_left = np.zeros(NUM_CELLS, dtype=int)   # Carril izquierdo
        self.road4_right = np.zeros(NUM_CELLS, dtype=int)  # Carril derecho
        
        # Arreglos para guardar los objetos Car
        self.cars = []
        
        # Contadores y estado del simulador
        self.generation = 0
        self.boundary_mode = "toroid"  # Modo inicial: toroid o null
        self.paused = False
        self.simulation_speed = 40  # FPS, velocidad de actualización (ajustable)
        
        # Para controlar la generación de nuevos coches
        self.spawn_timer = 0
        self.spawn_interval = 30  # Frames entre intentos de spawning
        
        # Inicializar coches iniciales de manera aleatoria
        self.initialize_cars()
        
        # Fuente para el texto en la pantalla
        self.font = pygame.font.SysFont("Arial", 16)
    
    def initialize_cars(self):
        """Inicializa los coches de forma aleatoria al inicio de la simulación."""
        # Limpiamos cualquier coche existente
        self.cars = []
        
        # Reiniciamos todos los carriles
        for lane_array in [self.road1_upper, self.road1_lower, self.road2_upper, self.road2_lower,
                          self.road3_left, self.road3_right, self.road4_left, self.road4_right]:
            lane_array.fill(0)
        
        # Colocamos coches en cada carretera (máximo MAX_CARS_PER_ROAD por carretera)
        # Carretera 1: Este a Oeste
        self._initialize_road(1, 'left', MAX_CARS_PER_ROAD)
        
        # Carretera 2: Oeste a Este
        self._initialize_road(2, 'right', MAX_CARS_PER_ROAD)
        
        # Carretera 3: Norte a Sur
        self._initialize_road(3, 'down', MAX_CARS_PER_ROAD)
        
        # Carretera 4: Sur a Norte
        self._initialize_road(4, 'up', MAX_CARS_PER_ROAD)
    
    def _initialize_road(self, road_num, direction, max_cars):
        """Inicializa coches para una carretera específica."""
        cars_to_create = random.randint(max_cars // 2, max_cars)
        valid_positions = list(range(0, NUM_CELLS))
        # Excluir el área del cruce para la inicialización
        if road_num <= 2:  # Carreteras horizontales
            valid_positions = [p for p in valid_positions if p < CROSS_INDEX_HORIZONTAL_START - 1 or p > CROSS_INDEX_HORIZONTAL_END + 1]
        else:  # Carreteras verticales
            valid_positions = [p for p in valid_positions if p < CROSS_INDEX_VERTICAL_START - 1 or p > CROSS_INDEX_VERTICAL_END + 1]
        
        # Seleccionar posiciones aleatorias para los coches
        car_positions = random.sample(valid_positions, min(cars_to_create, len(valid_positions)))
        
        # Crear coches en las posiciones seleccionadas
        for pos in car_positions:
            if road_num == 1:
                # Distribuir entre los dos carriles
                lane = 'upper' if random.random() < 0.5 else 'lower'
                if lane == 'upper':
                    self.road1_upper[pos] = 1
                else:
                    self.road1_lower[pos] = 1
                self.cars.append(Car(1, lane, pos, direction))
            elif road_num == 2:
                lane = 'upper' if random.random() < 0.5 else 'lower'
                if lane == 'upper':
                    self.road2_upper[pos] = 1
                else:
                    self.road2_lower[pos] = 1
                self.cars.append(Car(2, lane, pos, direction))
            elif road_num == 3:
                lane = 'left' if random.random() < 0.5 else 'right'
                if lane == 'left':
                    self.road3_left[pos] = 1
                else:
                    self.road3_right[pos] = 1
                self.cars.append(Car(3, lane, pos, direction))
            elif road_num == 4:
                lane = 'left' if random.random() < 0.5 else 'right'
                if lane == 'left':
                    self.road4_left[pos] = 1
                else:
                    self.road4_right[pos] = 1
                self.cars.append(Car(4, lane, pos, direction))
    
    def get_lane_array(self, road, lane):
        """Devuelve el array numpy correspondiente a un carril específico."""
        if road == 1:
            return self.road1_upper if lane == 'upper' else self.road1_lower
        elif road == 2:
            return self.road2_upper if lane == 'upper' else self.road2_lower
        elif road == 3:
            return self.road3_left if lane == 'left' else self.road3_right
        elif road == 4:
            return self.road4_left if lane == 'left' else self.road4_right
        return None
    
    def is_in_crossing_area(self, road, position):
        """Verifica si una posición está en el área del cruce."""
        if road <= 2:  # Carreteras horizontales
            return CROSS_INDEX_HORIZONTAL_START <= position <= CROSS_INDEX_HORIZONTAL_END
        else:  # Carreteras verticales
            return CROSS_INDEX_VERTICAL_START <= position <= CROSS_INDEX_VERTICAL_END
    
    def is_turn_position(self, car):
        """Comprueba si un coche está en posición de dar vuelta."""
        if car.road == 1 and car.lane == 'upper':
            # Carretera 1 (Este a Oeste), carril superior puede dar vuelta hacia la carretera 4
            return car.position == NUM_CELLS - (CROSS_INDEX_HORIZONTAL_START + 1)
        elif car.road == 2 and car.lane == 'lower':
            # Carretera 2 (Oeste a Este), carril inferior puede dar vuelta hacia la carretera 3
            return car.position == CROSS_INDEX_HORIZONTAL_END - 1
        elif car.road == 3 and car.lane == 'left':
            # Carretera 3 (Norte a Sur), carril izquierdo puede dar vuelta hacia la carretera 1
            return car.position == CROSS_INDEX_VERTICAL_START - 1
        elif car.road == 4 and car.lane == 'right':
            # Carretera 4 (Sur a Norte), carril derecho puede dar vuelta hacia la carretera 2
            return car.position == NUM_CELLS - (CROSS_INDEX_VERTICAL_END + 1)
        return False
    
    def get_target_turn(self, car):
        """Determina la carretera y carril objetivo para un giro."""
        if car.road == 1 and car.lane == 'upper':
            return (4, 'right')  # De carretera 1 a carretera 4
        elif car.road == 2 and car.lane == 'lower':
            return (3, 'left')   # De carretera 2 a carretera 3
        elif car.road == 3 and car.lane == 'left':
            return (1, 'upper')  # De carretera 3 a carretera 1
        elif car.road == 4 and car.lane == 'right':
            return (2, 'lower')  # De carretera 4 a carretera 2
        return None
    
    def apply_rule_184(self, lane_array):
        """Aplica la regla 184 a un carril."""
        new_lane = np.zeros_like(lane_array)
        
        for i in range(len(lane_array)):
            if self.boundary_mode == "toroid":
                left = lane_array[(i - 1) % len(lane_array)]
                center = lane_array[i]
                right = lane_array[(i + 1) % len(lane_array)]
            else:  # Frontera nula
                left = lane_array[i - 1] if i > 0 else 0
                center = lane_array[i]
                right = lane_array[i + 1] if i < len(lane_array) - 1 else 0
            
            # Tabla de búsqueda para Regla 184
            # 111 -> 0, 110 -> 1, 101 -> 0, 100 -> 1
            # 011 -> 1, 010 -> 0, 001 -> 1, 000 -> 0
            pattern = (left << 2) | (center << 1) | right
            rule_output = {
                0: 0, 1: 1, 2: 0, 3: 1,
                4: 1, 5: 0, 6: 1, 7: 0
            }
            new_lane[i] = rule_output[pattern]
        
        return new_lane
    
    def update(self):
        """Actualiza el estado de la simulación."""
        if self.paused:
            return
        
        # Incrementar generación
        self.generation += 1
        
        # Intentar generar nuevos coches
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_new_cars()
        
        # Hacer una copia de los coches para poder modificar la lista original
        temp_cars = self.cars.copy()
        cars_to_remove = []
        
        # Actualizar cada coche
        for car in temp_cars:
            # Saltarse coches en animación de cambio de carril
            if car.changing_lane:
                continue
            
            # Comprobar si el coche está averiado
            if car.broken:
                result = car.repair()
                if result is False:  # Coche remolcado
                    cars_to_remove.append(car)
                    # Liberar la celda
                    lane_array = self.get_lane_array(car.road, car.lane)
                    lane_array[car.position] = 0
                continue
            
            # Verificar si el coche se avería
            if random.random() < CAR_BREAKDOWN_PROB:
                car.break_down()
                continue
            
            # Comprobar si el coche puede dar vuelta
            if self.is_turn_position(car) and random.random() < CAR_TURN_PROB:
                target_road, target_lane = self.get_target_turn(car)
                
                # Calculamos la posición destino según el tipo de giro
                target_pos = 0
                if car.road == 1 and target_road == 4:  # De Este a Sur -> Norte
                    target_pos = NUM_CELLS - (CROSS_INDEX_VERTICAL_END + 1)
                elif car.road == 2 and target_road == 3:  # De Oeste a Norte -> Sur
                    target_pos = CROSS_INDEX_VERTICAL_START + 1
                elif car.road == 3 and target_road == 1:  # De Norte a Oeste -> Este
                    target_pos = NUM_CELLS - (CROSS_INDEX_HORIZONTAL_START + 1)
                elif car.road == 4 and target_road == 2:  # De Sur a Este -> Oeste
                    target_pos = CROSS_INDEX_HORIZONTAL_END + 1
                
                # Verificar si la celda destino está libre
                target_lane_array = self.get_lane_array(target_road, target_lane)
                if target_lane_array[target_pos] == 0:
                    # Liberar la celda actual
                    lane_array = self.get_lane_array(car.road, car.lane)
                    lane_array[car.position] = 0
                    
                    # Realizar el giro de forma inmediata
                    car.road = target_road
                    car.lane = target_lane
                    car.position = target_pos
                    
                    # Actualizar dirección según el tipo de giro
                    if target_road == 1:
                        car.direction = 'left'
                    elif target_road == 2:
                        car.direction = 'right'
                    elif target_road == 3:
                        car.direction = 'down'
                    elif target_road == 4:
                        car.direction = 'up'
                    
                    # NOTA: Mantenemos origin_road sin cambios para preservar el tipo/perfil del coche
                    
                    car.update_drawing_position()
                    
                    # Ocupar la nueva celda en el carril destino
                    target_lane_array[target_pos] = 1
                    continue
            
            # Comprobar cambio de carril (si no está en la zona de cruce)
            if not self.is_in_crossing_area(car.road, car.position) and random.random() < CAR_CHANGE_LANE_PROB:
                new_lane = None
                
                # Determinar el nuevo carril
                if car.road <= 2:  # Carreteras horizontales
                    new_lane = 'lower' if car.lane == 'upper' else 'upper'
                else:  # Carreteras verticales
                    new_lane = 'right' if car.lane == 'left' else 'left'
                
                # Comprobar si la celda del nuevo carril está libre
                new_lane_array = self.get_lane_array(car.road, new_lane)
                if new_lane_array[car.position] == 0:
                    # Iniciar animación de cambio de carril
                    car.start_lane_change(new_lane)
                    
                    # Actualizar arreglos de carriles
                    lane_array = self.get_lane_array(car.road, car.lane)
                    lane_array[car.position] = 0
                    new_lane_array[car.position] = 1
                    continue
            
            # Avanzar el coche según la dirección
            lane_array = self.get_lane_array(car.road, car.lane)
            next_pos = car.position + 1  # Por defecto avanzar una posición

            # Comprobar si llegó al final del carril
            if next_pos >= NUM_CELLS:
                if self.boundary_mode == "toroid":
                    next_pos = 0  # Aparecer en el inicio
                    # Verificar si la celda inicial está libre antes de mover
                    if lane_array[next_pos] == 0:
                        lane_array[car.position] = 0  # Liberar celda actual
                        lane_array[next_pos] = 1      # Ocupar nueva celda
                        car.position = next_pos
                        car.update_drawing_position()
                    # Si no está libre, no se mueve
                else:  # Frontera nula
                    if random.random() < FRONTIER_SURVIVAL_PROB:
                        # El coche sobrevive y reaparece al inicio
                        if lane_array[0] == 0:  # Solo si la celda inicial está libre
                            lane_array[car.position] = 0  # Liberar celda actual
                            lane_array[0] = 1            # Ocupar celda inicial
                            car.position = 0
                            car.update_drawing_position()
                        # Si no está libre, no se mueve ni desaparece
                    else:
                        # El coche se elimina
                        cars_to_remove.append(car)
                        lane_array[car.position] = 0
                    continue
            
            # Si hay espacio para avanzar, mover el coche
            if lane_array[next_pos] == 0:
                lane_array[car.position] = 0  # Liberar celda actual
                lane_array[next_pos] = 1      # Ocupar nueva celda
                car.position = next_pos
                car.update_drawing_position()
        
        # Eliminar coches marcados para eliminar
        for car in cars_to_remove:
            if car in self.cars:
                self.cars.remove(car)
    
    def spawn_new_cars(self):
        """Intenta crear nuevos coches en los puntos de entrada."""
        # Comprobar si hay espacio en la posición inicial de cada carretera
        
        # Carretera 1: Este a Oeste
        if len([c for c in self.cars if c.road == 1]) < MAX_CARS_PER_ROAD:
            if self.road1_upper[0] == 0 and random.random() < 0.3:  # 30% de prob.
                self.road1_upper[0] = 1
                self.cars.append(Car(1, 'upper', 0, 'left'))
            if self.road1_lower[0] == 0 and random.random() < 0.3:
                self.road1_lower[0] = 1
                self.cars.append(Car(1, 'lower', 0, 'left'))
        
        # Carretera 2: Oeste a Este
        if len([c for c in self.cars if c.road == 2]) < MAX_CARS_PER_ROAD:
            if self.road2_upper[0] == 0 and random.random() < 0.3:
                self.road2_upper[0] = 1
                self.cars.append(Car(2, 'upper', 0, 'right'))
            if self.road2_lower[0] == 0 and random.random() < 0.3:
                self.road2_lower[0] = 1
                self.cars.append(Car(2, 'lower', 0, 'right'))
        
        # Carretera 3: Norte a Sur
        if len([c for c in self.cars if c.road == 3]) < MAX_CARS_PER_ROAD:
            if self.road3_left[0] == 0 and random.random() < 0.3:
                self.road3_left[0] = 1
                self.cars.append(Car(3, 'left', 0, 'down'))
            if self.road3_right[0] == 0 and random.random() < 0.3:
                self.road3_right[0] = 1
                self.cars.append(Car(3, 'right', 0, 'down'))
        
        # Carretera 4: Sur a Norte
        if len([c for c in self.cars if c.road == 4]) < MAX_CARS_PER_ROAD:
            if self.road4_left[0] == 0 and random.random() < 0.3:
                self.road4_left[0] = 1
                self.cars.append(Car(4, 'left', 0, 'up'))
            if self.road4_right[0] == 0 and random.random() < 0.3:
                self.road4_right[0] = 1
                self.cars.append(Car(4, 'right', 0, 'up'))
    
    def draw(self, surface):
        """Dibuja la simulación en la superficie dada."""
        # Dibujar imagen de cruce de fondo
        surface.blit(cruce_img, (0, 0))
        
        # Resaltar el área del cruce para mejor visualización
        cross_size = 40  # Tamaño del área del cruce (ancho y alto)
        cross_cells = cross_size // CELL_SIZE  # Número de celdas que abarca el cruce
        cross_area = pygame.Surface((cross_cells * CELL_SIZE, cross_cells * CELL_SIZE), pygame.SRCALPHA)
        cross_area.fill((255, 255, 0, 50))  # Amarillo transparente
        
        # Centrar en el cruce
        cross_x = CROSS_X - (cross_cells * CELL_SIZE) // 2
        cross_y = CROSS_Y - (cross_cells * CELL_SIZE) // 2
        
        # Dibujar el área del cruce
        surface.blit(cross_area, (cross_x, cross_y))
        
        # Dibujar todos los coches
        for car in self.cars:
            car.draw(surface)
        
        # Dibujar brújula en la esquina superior izquierda
        surface.blit(brujula_img, (10, 10))
        
        # Crear un panel para controles e información en la esquina superior derecha
        panel_width = 180
        panel_height = 180
        controls_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        controls_surface.fill((*BLACK[:3], 120))  # Negro más transparente
        surface.blit(controls_surface, (WIDTH - panel_width - 10, 10))
        
        # Textos informativos
        texts = [
            f"Generación: {self.generation}",
            f"Modo: {'Toroide' if self.boundary_mode == 'toroid' else 'Frontera Nula'}",
            f"Coches Totales: {len(self.cars)}",
            f"Velocidad: {self.simulation_speed} FPS",
            f"Cruce: Área amarilla"
        ]
        
        # Posición inicial para textos en el panel
        x_margin = 15
        y_start = 15
        panel_x = WIDTH - panel_width - 10 + x_margin
        
        # Estadísticas
        for i, text in enumerate(texts):
            text_surf = self.font.render(text, True, WHITE)
            surface.blit(text_surf, (panel_x, y_start + i * 16))
        
        # Controles
        controls_title = self.font.render("Controles:", True, WHITE)
        surface.blit(controls_title, (panel_x, y_start + len(texts) * 16 + 5))
        
        controls = [
            "T - Modo Toroide",
            "N - Frontera Nula",
            "Espacio - Pausa",
            "R - Reiniciar",
            "↑/↓ - Velocidad"
        ]
        
        for i, text in enumerate(controls):
            text_surf = self.font.render(text, True, WHITE)
            surface.blit(text_surf, (panel_x, y_start + len(texts) * 16 + 25 + i * 16))
    
    def handle_event(self, event):
        """Maneja eventos de teclado."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.boundary_mode = "toroid"
            elif event.key == pygame.K_n:
                self.boundary_mode = "null"
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.initialize_cars()
                self.generation = 0
            elif event.key == pygame.K_UP:
                self.simulation_speed = min(120, self.simulation_speed + 10)
            elif event.key == pygame.K_DOWN:
                self.simulation_speed = max(10, self.simulation_speed - 10)
            elif event.key == pygame.K_ESCAPE:
                return False  # Señal para salir del juego
        
        return True  # Continuar el juego

# Función principal del juego
def main():
    # Hacer referencia a la variable global screen
    global screen
    
    # Inicializar simulador
    simulator = TrafficSimulator()
    
    # Reloj para controlar FPS
    clock = pygame.time.Clock()
    
    # Bucle principal
    running = True
    while running:
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Mantener el tamaño fijo cuando el usuario intenta redimensionar
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.HWSURFACE)
            else:
                # Manejar eventos del simulador
                result = simulator.handle_event(event)
                if not result:
                    running = False
        
        # Actualizar simulación
        simulator.update()
        
        # Limpiar pantalla
        screen.fill(BLACK)
        
        # Dibujar simulación
        simulator.draw(screen)
        
        # Actualizar pantalla
        pygame.display.flip()
        
        # Controlar velocidad
        clock.tick(simulator.simulation_speed)
    
    # Salir del juego
    pygame.quit()
    sys.exit()

# Ejecutar el juego si este script es el principal
if __name__ == "__main__":
    main()