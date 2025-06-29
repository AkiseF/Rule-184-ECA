import pygame
import numpy as np
import random
import os
import math

# Inicializar pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 800, 800   # Dimensiones para acomodar el cruce
CELL_SIZE = 20             # Tamaño de celda más pequeño para mejor visualización
NUM_CELLS_HORIZONTAL = 60  # Número de celdas horizontales
NUM_CELLS_VERTICAL = 60    # Número de celdas verticales

# Posiciones Y para los carriles horizontales
UPPER_LANE_1_Y = 361   # Carril superior de primera carretera (derecha a izquierda)
LOWER_LANE_1_Y = 379   # Carril inferior de primera carretera (derecha a izquierda)
UPPER_LANE_2_Y = 400   # Carril superior de segunda carretera (izquierda a derecha)
LOWER_LANE_2_Y = 417   # Carril inferior de segunda carretera (izquierda a derecha)

# Posiciones X para los carriles verticales
LEFT_LANE_3_X = 361    # Carril izquierdo de tercera carretera (arriba a abajo)
RIGHT_LANE_3_X = 379   # Carril derecho de tercera carretera (arriba a abajo)
LEFT_LANE_4_X = 400    # Carril izquierdo de cuarta carretera (abajo a arriba)
RIGHT_LANE_4_X = 417   # Carril derecho de cuarta carretera (abajo a arriba)

# Probabilidades
CAR_BREAKDOWN_PROB = 0.2      # Probabilidad de avería/se descomponga un coche 
CAR_INSERTION_PROB = 0.05     # Probabilidad de densidad
CAR_TURN_PROB = 0.2           # Probabilidad de dar vuelta en el cruce
REPAIR_ATTEMPTS = 20          # Número de iteraciones para reparar un coche
REPAIR_PROB = 0.5             # Probabilidad de reparación de un coche

# Posición del cruce (centro del cruce)
CROSS_X = 400
CROSS_Y = 400
CROSS_SIZE = 90  # Tamaño del área del cruce (tanto ancho como alto)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Crear la ventana
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Tráfico en Cruce - Regla 184")

# Cargar imágenes
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
road_img = pygame.image.load(os.path.join(parent_dir, "./assets/cruce.png"))
road_img = pygame.transform.scale(road_img, (WIDTH, HEIGHT))

# Establecer icono de la ventana
icon = pygame.image.load(os.path.join(parent_dir, "./assets/logo_2.png"))
pygame.display.set_icon(icon)

# Cargar la brújula (rosa de los vientos)
compass_img = pygame.image.load(os.path.join(parent_dir, "./assets/brujula.png"))
compass_img = pygame.transform.scale(compass_img, (100, 100))  # Ajusta tamaño según necesites

# Coches para las cuatro direcciones
car_left_img = pygame.image.load(os.path.join(parent_dir, "./assets/1_left.png"))  # Este a Oeste
car_right_img = pygame.image.load(os.path.join(parent_dir, "./assets/2_right.png"))  # Oeste a Este
car_down_img = pygame.image.load(os.path.join(parent_dir, "./assets/3_down.png"))  # Norte a Sur
car_up_img = pygame.image.load(os.path.join(parent_dir, "./assets/4_up.png"))  # Sur a Norte

# Escalar imágenes de coches
car_left_img = pygame.transform.scale(car_left_img, (CELL_SIZE, CELL_SIZE))
car_right_img = pygame.transform.scale(car_right_img, (CELL_SIZE, CELL_SIZE))
car_down_img = pygame.transform.scale(car_down_img, (CELL_SIZE, CELL_SIZE))
car_up_img = pygame.transform.scale(car_up_img, (CELL_SIZE, CELL_SIZE))

# Versiones para coches descompuestos
broken_car_left_img = car_left_img.copy()
broken_car_right_img = car_right_img.copy()
broken_car_down_img = car_down_img.copy()
broken_car_up_img = car_up_img.copy()

# Aplicar tinte rojo a los autos descompuestos
red_overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
red_overlay.fill((255, 0, 0, 100))
broken_car_left_img.blit(red_overlay, (0, 0))
broken_car_right_img.blit(red_overlay, (0, 0))
broken_car_down_img.blit(red_overlay, (0, 0))
broken_car_up_img.blit(red_overlay, (0, 0))

class Car:
    def __init__(self, road_id, lane_id, position, direction):
        self.road_id = road_id      # 1, 2, 3, 4 (identificador de carretera)
        self.lane_id = lane_id      # "left"/"upper" o "right"/"lower"
        self.position = position    # Índice en el arreglo
        self.direction = direction  # "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"
        self.status = "active"      # "active", "broken", "turning"
        self.turn_target = None     # Para cuando está girando: (road_id_destino, lane_id_destino, position_destino)
        self.repair_countdown = 0   # Contador para reparación si está averiado
        self.car_type = random.randint(1, 4)  # Tipo de coche (variación visual)
        self.turning_progress = 0   # Contador para controlar la animación del giro
        self.id = f"{road_id}_{lane_id}_{position}_{random.randint(1000, 9999)}"  # ID único para el coche
    
    def update(self, simulation):
        # Lógica principal de actualización según estado
        if self.status == "broken":
            self.update_broken()
            return False  # No hay cambio de posición
        elif self.status == "turning":
            return self.update_turning(simulation)
        else:
            return self.update_movement(simulation)
    
    def update_movement(self, simulation):
        """Implementa la regla 184 para este coche específico y maneja posibles giros"""
        next_position = None
        lane_array = self.get_lane_array(simulation)
        lane_length = len(lane_array)
        
        # Verificar si el coche está cerca del cruce y debe intentar girar
        is_near_intersection = self.is_near_intersection(simulation)
        should_attempt_turn = is_near_intersection and self.should_turn()
        
        # Si debería intentar girar, buscar posibles carriles de destino
        if should_attempt_turn:
            turn_target = self.find_turn_target(simulation)
            if turn_target:
                self.status = "turning"
                self.turn_target = turn_target
                self.turning_progress = 0
                return True  # Hemos iniciado un giro
        
        # Si no gira, aplicar la regla 184
        if self.direction == "left_to_right":
            # Mover de izquierda a derecha
            next_position = (self.position + 1) % lane_length if simulation.boundary_mode == "toroid" else self.position + 1
            # Verificar si puede avanzar (hay espacio adelante)
            can_move = next_position < lane_length and lane_array[next_position] == 0
            
            if can_move:
                self.position = next_position
                return True  # La posición cambió
                
        elif self.direction == "right_to_left":
            # Mover de derecha a izquierda
            next_position = (self.position - 1) % lane_length if simulation.boundary_mode == "toroid" else self.position - 1
            # Verificar si puede avanzar (hay espacio adelante)
            can_move = next_position >= 0 and lane_array[next_position] == 0
            
            if can_move:
                self.position = next_position
                return True  # La posición cambió
                
        elif self.direction == "top_to_bottom":
            # Mover de arriba a abajo
            next_position = (self.position + 1) % lane_length if simulation.boundary_mode == "toroid" else self.position + 1
            # Verificar si puede avanzar
            can_move = next_position < lane_length and lane_array[next_position] == 0
            
            if can_move:
                self.position = next_position
                return True  # La posición cambió
                
        elif self.direction == "bottom_to_top":
            # Mover de abajo a arriba
            next_position = (self.position - 1) % lane_length if simulation.boundary_mode == "toroid" else self.position - 1
            # Verificar si puede avanzar
            can_move = next_position >= 0 and lane_array[next_position] == 0
            
            if can_move:
                self.position = next_position
                return True  # La posición cambió
                
        # Verificar si el coche debe averiarse
        if random.random() < CAR_BREAKDOWN_PROB:
            self.break_down()
            
        return False  # No hubo cambio de posición
    
    def update_broken(self):
        """Actualiza el estado de un coche averiado"""
        # Actualizar contador de reparación
        if self.repair_countdown > 0:
            self.repair_countdown -= 1
        
        if self.repair_countdown <= 0:
            if random.random() < REPAIR_PROB:
                self.status = "active"
                return True  # El estado cambió
        return False
    
    def update_turning(self, simulation):
        """Maneja la lógica de giro en la intersección"""
        self.turning_progress += 1
        
        # Si el giro está completo
        if self.turning_progress >= 3:  # 3 pasos para completar el giro
            # Obtener datos del destino
            dest_road_id, dest_lane_id, dest_position = self.turn_target
            
            # Verificar si el destino está libre
            dest_lane = self.get_lane_array_by_ids(simulation, dest_road_id, dest_lane_id)
            
            if dest_position >= 0 and dest_position < len(dest_lane) and dest_lane[dest_position] == 0:
                # Eliminar el coche de su posición actual
                current_lane = self.get_lane_array(simulation)
                if 0 <= self.position < len(current_lane):
                    # Actualizar propiedades del coche
                    self.road_id = dest_road_id
                    self.lane_id = dest_lane_id
                    self.position = dest_position
                    self.status = "active"
                    
                    # Actualizar la dirección según la nueva carretera
                    if dest_road_id == 1:
                        self.direction = "right_to_left"
                    elif dest_road_id == 2:
                        self.direction = "left_to_right"
                    elif dest_road_id == 3:
                        self.direction = "top_to_bottom"
                    elif dest_road_id == 4:
                        self.direction = "bottom_to_top"
                    
                    # Incrementar contador de giros
                    simulation.turn_count += 1
                    return True
            
            # Si no pudo completar el giro, volver a estado activo
            self.status = "active"
            self.turn_target = None
            
        return False
    
    def break_down(self):
        """Avería el coche"""
        self.status = "broken"
        self.repair_countdown = REPAIR_ATTEMPTS
    
    def should_turn(self):
        """Evalúa si el coche debe girar al llegar a la intersección"""
        return random.random() < CAR_TURN_PROB
    
    def is_near_intersection(self, simulation):
        """Determina si el coche está cerca del cruce"""
        # Calculamos el rango de detección basado en CROSS_SIZE
        detection_range = (CROSS_SIZE // CELL_SIZE) // 2
        
        if self.road_id in [1, 2]:  # Carreteras horizontales
            # Distancia al centro del cruce
            distance = abs(self.position - simulation.cross_index_h)
            return distance <= detection_range
        else:  # Carreteras verticales
            distance = abs(self.position - simulation.cross_index_v)
            return distance <= detection_range
    
    def find_turn_target(self, simulation):
        """Determina un posible destino para el giro basado en la posición actual"""
        # Calculamos el rango de detección basado en CROSS_SIZE
        detection_range = (CROSS_SIZE // CELL_SIZE) // 2
        
        # Definimos los giros posibles basados en la road_id y lane_id según las nuevas reglas
        if self.road_id == 1:  # E→O
            if self.lane_id == "upper" and abs(self.position - simulation.cross_index_h) <= detection_range:
                # Giro desde carril superior 1 hacia carretera 4 (derecha)
                return (4, "right", simulation.cross_index_v)
        elif self.road_id == 2:  # O→E
            if self.lane_id == "lower" and abs(self.position - simulation.cross_index_h) <= detection_range:
                # Giro desde carril inferior 2 hacia carretera 3 (izquierda)
                return (3, "left", simulation.cross_index_v)
        elif self.road_id == 3:  # N→S
            if self.lane_id == "left" and abs(self.position - simulation.cross_index_v) <= detection_range:
                # Giro desde carril izquierdo 3 hacia carretera 1 (superior)
                return (1, "upper", simulation.cross_index_h)
        elif self.road_id == 4:  # S→N
            if self.lane_id == "right" and abs(self.position - simulation.cross_index_v) <= detection_range:
                # Giro desde carril derecho 4 hacia carretera 2 (inferior)
                return (2, "lower", simulation.cross_index_h)
    
        return None  # No hay giro posible
    
    def get_lane_array(self, simulation):
        """Obtiene el arreglo de carril correspondiente a este coche"""
        return self.get_lane_array_by_ids(simulation, self.road_id, self.lane_id)
    
    def get_lane_array_by_ids(self, simulation, road_id, lane_id):
        """Obtiene el arreglo de carril basado en road_id y lane_id"""
        if road_id == 1:  # Carretera 1 (E→O)
            if lane_id == "upper":
                return simulation.upper_lane_1
            else:  # "lower"
                return simulation.lower_lane_1
        elif road_id == 2:  # Carretera 2 (O→E)
            if lane_id == "upper":
                return simulation.upper_lane_2
            else:  # "lower"
                return simulation.lower_lane_2
        elif road_id == 3:  # Carretera 3 (N→S)
            if lane_id == "left":
                return simulation.left_lane_3
            else:  # "right"
                return simulation.right_lane_3
        elif road_id == 4:  # Carretera 4 (S→N)
            if lane_id == "left":
                return simulation.left_lane_4
            else:  # "right"
                return simulation.right_lane_4
        
        return None

class TrafficCrossSimulator:
    def __init__(self, boundary_mode="toroid"):
        # Cambiar los arrays por diccionarios de coches por posición
        self.cars = {
            "road1": {"upper": {}, "lower": {}},  # Carretera 1 (E→O)
            "road2": {"upper": {}, "lower": {}},  # Carretera 2 (O→E)
            "road3": {"left": {}, "right": {}},   # Carretera 3 (N→S)
            "road4": {"left": {}, "right": {}}    # Carretera 4 (S→N)
        }
        
        # Inicializar con coches distribuidos
        self._initialize_cars()
        
        # Índices de la celda central del cruce para cada carril
        # IMPORTANTE: Inicializamos estos valores antes de llamar a _initialize_limited_cars
        self.cross_index_h = NUM_CELLS_HORIZONTAL // 2  # Índice horizontal del centro del cruce
        self.cross_index_v = NUM_CELLS_VERTICAL // 2    # Índice vertical del centro del cruce
        
        # Constante para el máximo número de coches por vialidad
        self.MAX_CARS_PER_ROAD = 15
    
        # En lugar de usar densidad, colocamos exactamente 15 coches por cada tipo de vialidad
        # distribuidos uniformemente
        
        # 15 coches para la primera carretera (derecha a izquierda)
        self._initialize_limited_cars(self.upper_lane_1, 8, 1, "upper", "right_to_left")  # 8 en carril superior
        self._initialize_limited_cars(self.lower_lane_1, 7, 1, "lower", "right_to_left")  # 7 en carril inferior
        
        # 15 coches para la segunda carretera (izquierda a derecha)
        self._initialize_limited_cars(self.upper_lane_2, 8, 2, "upper", "left_to_right")  # 8 en carril superior
        self._initialize_limited_cars(self.lower_lane_2, 7, 2, "lower", "left_to_right")  # 7 en carril inferior
        
        # 15 coches para la tercera carretera (arriba a abajo)
        self._initialize_limited_cars(self.left_lane_3, 8, 3, "left", "top_to_bottom")   # 8 en carril izquierdo
        self._initialize_limited_cars(self.right_lane_3, 7, 3, "right", "top_to_bottom") # 7 en carril derecho
        
        # 15 coches para la cuarta carretera (abajo a arriba)
        self._initialize_limited_cars(self.left_lane_4, 8, 4, "left", "bottom_to_top")   # 8 en carril izquierdo
        self._initialize_limited_cars(self.right_lane_4, 7, 4, "right", "bottom_to_top") # 7 en carril derecho
        
        self.generation = 0
        self.boundary_mode = boundary_mode
        self.turn_count = 0  # Contador de giros realizados
        
        # Fuente para textos
        try:
            self.font = pygame.font.SysFont("Arial", 13)
        except:
            self.font = pygame.font.SysFont(None, 24)
        
        self.simulation_speed = 10  # Velocidad predeterminada
    
    def _initialize_cars(self):
        """
        Inicializa los carriles y diccionarios de coches
        """
        # Inicializar carriles horizontales
        self.upper_lane_1 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)  # Carril superior de primera carretera (derecha a izquierda)
        self.lower_lane_1 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)  # Carril inferior de primera carretera (derecha a izquierda)
        self.upper_lane_2 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)  # Carril superior de segunda carretera (izquierda a derecha)
        self.lower_lane_2 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)  # Carril inferior de segunda carretera (izquierda a derecha)
        
        # Inicializar carriles verticales
        self.left_lane_3 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)  # Carril izquierdo de tercera carretera (arriba a abajo)
        self.right_lane_3 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)  # Carril derecho de tercera carretera (arriba a abajo)
        self.left_lane_4 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)  # Carril izquierdo de cuarta carretera (abajo a arriba)
        self.right_lane_4 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)  # Carril derecho de cuarta carretera (abajo a arriba)
        
        # Inicializar diccionarios de coches descompuestos para cada carril
        self.broken_cars_upper_1 = {}  # Índices de coches descompuestos en upper_lane_1
        self.broken_cars_lower_1 = {}  # Índices de coches descompuestos en lower_lane_1
        self.broken_cars_upper_2 = {}  # Índices de coches descompuestos en upper_lane_2
        self.broken_cars_lower_2 = {}  # Índices de coches descompuestos en lower_lane_2
        self.broken_cars_left_3 = {}   # Índices de coches descompuestos en left_lane_3
        self.broken_cars_right_3 = {}  # Índices de coches descompuestos en right_lane_3
        self.broken_cars_left_4 = {}   # Índices de coches descompuestos en left_lane_4
        self.broken_cars_right_4 = {}  # Índices de coches descompuestos en right_lane_4
        
        # Inicializar estructuras para los coches como objetos
        self.car_objects = {
            "road1": {"upper": {}, "lower": {}},  # Carretera 1 (E→O)
            "road2": {"upper": {}, "lower": {}},  # Carretera 2 (O→E)
            "road3": {"left": {}, "right": {}},   # Carretera 3 (N→S)
            "road4": {"left": {}, "right": {}}    # Carretera 4 (S→N)
        }

    def _initialize_limited_cars(self, lane, num_cars, road_id=None, lane_id=None, direction=None):
        """
        Inicializa un carril con un número específico de coches distribuidos uniformemente
        y crea los correspondientes objetos Car
        
        Args:
            lane: El carril donde colocar los coches
            num_cars: Número exacto de coches a colocar
            road_id: Identificador de la carretera (1-4)
            lane_id: Identificador del carril ("upper", "lower", "left", "right")
            direction: Dirección del movimiento ("left_to_right", "right_to_left", etc)
        """
        lane_length = len(lane)
        
        # Si el carril es demasiado pequeño para el número de coches, colocamos menos
        if num_cars > lane_length:
            num_cars = lane_length
            
        # Calcular el espaciado entre los coches para distribuirlos uniformemente
        if num_cars > 1:
            spacing = lane_length // num_cars
        else:
            spacing = 1
            
        # Posiciones donde evitamos colocar coches (área de cruce)
        cross_area = []
        
        # Si es un carril horizontal
        if lane_length == NUM_CELLS_HORIZONTAL:
            cross_start = self.cross_index_h - 1
            cross_end = self.cross_index_h + 1
            cross_area = list(range(cross_start, cross_end + 1))
        # Si es un carril vertical
        else:
            cross_start = self.cross_index_v - 1
            cross_end = self.cross_index_v + 1
            cross_area = list(range(cross_start, cross_end + 1))
        
        # Colocar los coches de manera uniforme, evitando el cruce
        cars_placed = 0
        positions = []
        
        for i in range(0, lane_length, spacing):
            if cars_placed >= num_cars:
                break
            
            # No colocar coches en el área de cruce al iniciar
            if i not in cross_area:
                lane[i] = 1
                positions.append(i)
                cars_placed += 1
        
        # Si no se colocaron todos los coches debido al cruce, colocamos el resto
        # buscando espacios vacíos
        if cars_placed < num_cars:
            for i in range(lane_length):
                if cars_placed >= num_cars:
                    break
                    
                if lane[i] == 0 and i not in cross_area:
                    lane[i] = 1
                    positions.append(i)
                    cars_placed += 1
                    
        # Crear objetos Car para cada posición si se proporcionaron los parámetros necesarios
        if road_id is not None and lane_id is not None and direction is not None:
            for pos in positions:
                car = Car(road_id, lane_id, pos, direction)
                self.car_objects[f"road{road_id}"][lane_id][pos] = car
    
    def _get_all_cars(self):
        """
        Obtiene una lista plana de todos los objetos Car en la simulación
        """
        all_cars = []
        
        # Recorrer la estructura anidada para obtener todos los coches
        for road_id, lanes in self.car_objects.items():
            for lane_id, cars in lanes.items():
                all_cars.extend(cars.values())
        
        return all_cars

    def _rebuild_position_maps(self):
        """
        Reconstruye los mapas de posición basados en los objetos Car
        """
        # Reiniciar todos los carriles
        self.upper_lane_1.fill(0)
        self.lower_lane_1.fill(0)
        self.upper_lane_2.fill(0)
        self.lower_lane_2.fill(0)
        self.left_lane_3.fill(0)
        self.right_lane_3.fill(0)
        self.left_lane_4.fill(0)
        self.right_lane_4.fill(0)
        
        # Reiniciar los diccionarios de coches descompuestos
        self.broken_cars_upper_1 = {}
        self.broken_cars_lower_1 = {}
        self.broken_cars_upper_2 = {}
        self.broken_cars_lower_2 = {}
        self.broken_cars_left_3 = {}
        self.broken_cars_right_3 = {}
        self.broken_cars_left_4 = {}
        self.broken_cars_right_4 = {}
        
        # Asignar posiciones desde los objetos Car
        for car in self._get_all_cars():
            if car.status in ["active", "broken"]:  # Sólo considerar coches activos y averiados
                if car.road_id == 1:
                    if car.lane_id == "upper":
                        self.upper_lane_1[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_upper_1[car.position] = car.repair_countdown
                    else:  # lane_id == "lower"
                        self.lower_lane_1[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_lower_1[car.position] = car.repair_countdown
                elif car.road_id == 2:
                    if car.lane_id == "upper":
                        self.upper_lane_2[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_upper_2[car.position] = car.repair_countdown
                    else:  # lane_id == "lower"
                        self.lower_lane_2[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_lower_2[car.position] = car.repair_countdown
                elif car.road_id == 3:
                    if car.lane_id == "left":
                        self.left_lane_3[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_left_3[car.position] = car.repair_countdown
                    else:  # lane_id == "right"
                        self.right_lane_3[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_right_3[car.position] = car.repair_countdown
                elif car.road_id == 4:
                    if car.lane_id == "left":
                        self.left_lane_4[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_left_4[car.position] = car.repair_countdown
                    else:  # lane_id == "right"
                        self.right_lane_4[car.position] = 1
                        if car.status == "broken":
                            self.broken_cars_right_4[car.position] = car.repair_countdown
        
        # Los métodos antiguos (apply_rule_184_horizontal, apply_rule_184_vertical, etc.)
        # han sido reemplazados por la lógica en la clase Car y el nuevo método update
        # que utiliza objetos Car en lugar de arrays
    
    def _enforce_car_limit(self, lane1, lane2, max_cars, road_id=None, lane1_id=None, lane2_id=None):
        """
        Fuerza el límite de coches en un par de carriles.
        Si hay más coches que el límite, elimina algunos aleatoriamente
        pero evitando los coches descompuestos.
        
        Args:
            lane1: Primer carril (array NumPy)
            lane2: Segundo carril (array NumPy)
            max_cars: Número máximo de coches permitido en ambos carriles
            road_id: ID de la carretera (1-4) para actualizar objetos Car
            lane1_id: ID del primer carril ("upper", "lower", "left", "right")
            lane2_id: ID del segundo carril ("upper", "lower", "left", "right")
        """
        total_cars = np.sum(lane1) + np.sum(lane2)
        
        if total_cars > max_cars:
            excess = total_cars - max_cars
            
            # Recopilar índices de coches que pueden eliminarse
            # (evitando los descompuestos)
            indices_lane1 = [i for i in range(len(lane1)) if lane1[i] == 1]
            indices_lane2 = [i for i in range(len(lane2)) if lane2[i] == 1]
            
            # Mezclar índices para seleccionar aleatoriamente
            random.shuffle(indices_lane1)
            random.shuffle(indices_lane2)
            
            # Eliminar coches en exceso
            for _ in range(excess):
                if indices_lane1 and (not indices_lane2 or random.random() < 0.5):
                    idx = indices_lane1.pop()
                    lane1[idx] = 0
                    
                    # Eliminar también el objeto Car si se proporcionaron los IDs
                    if road_id is not None and lane1_id is not None:
                        road_key = f"road{road_id}"
                        if road_key in self.car_objects and lane1_id in self.car_objects[road_key]:
                            if idx in self.car_objects[road_key][lane1_id]:
                                del self.car_objects[road_key][lane1_id][idx]
                
                elif indices_lane2:
                    idx = indices_lane2.pop()
                    lane2[idx] = 0
                    
                    # Eliminar también el objeto Car si se proporcionaron los IDs
                    if road_id is not None and lane2_id is not None:
                        road_key = f"road{road_id}"
                        if road_key in self.car_objects and lane2_id in self.car_objects[road_key]:
                            if idx in self.car_objects[road_key][lane2_id]:
                                del self.car_objects[road_key][lane2_id][idx]
                else:
                    # No hay más coches que eliminar
                    break
    
    def draw(self):
        screen.blit(road_img, (0, 0))
        
        # Obtener tiempo para efectos visuales
        current_time = pygame.time.get_ticks()
        
        # ======= Dibujar autos en carreteras horizontales =======
        
        # Carretera 1 (derecha a izquierda)
        for i in range(NUM_CELLS_HORIZONTAL):
            x_pos = i * CELL_SIZE
            
            # Carril superior
            if self.upper_lane_1[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i) * 2)
                y_pos = UPPER_LANE_1_Y + offset_y
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_upper_1:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_left_img, (x_pos, y_pos))
                else:
                    screen.blit(car_left_img, (x_pos, y_pos))
            
            # Carril inferior
            if self.lower_lane_1[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 10) * 2)
                y_pos = LOWER_LANE_1_Y + offset_y
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_lower_1:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_left_img, (x_pos, y_pos))
                else:
                    screen.blit(car_left_img, (x_pos, y_pos))
        
        # Carretera 2 (izquierda a derecha)
        for i in range(NUM_CELLS_HORIZONTAL):
            x_pos = i * CELL_SIZE
            
            # Carril superior
            if self.upper_lane_2[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 20) * 2)
                y_pos = UPPER_LANE_2_Y + offset_y
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_upper_2:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(0, CELL_SIZE//2)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_right_img, (x_pos, y_pos))
                else:
                    screen.blit(car_right_img, (x_pos, y_pos))
            
            # Carril inferior
            if self.lower_lane_2[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 30) * 2)
                y_pos = LOWER_LANE_2_Y + offset_y
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_lower_2:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(0, CELL_SIZE//2)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_right_img, (x_pos, y_pos))
                else:
                    screen.blit(car_right_img, (x_pos, y_pos))
        
        # ======= Dibujar autos en carreteras verticales =======
        
        # Carretera 3 (arriba a abajo)
        for i in range(NUM_CELLS_VERTICAL):
            y_pos = i * CELL_SIZE
            
            # Carril izquierdo
            if self.left_lane_3[i] == 1:
                offset_x = int(math.sin(current_time / 500.0 + i + 40) * 2)
                x_pos = LEFT_LANE_3_X + offset_x
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_left_3:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(5, 15)
                        smoke_y = y_pos + random.randint(0, CELL_SIZE//2)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_down_img, (x_pos, y_pos))
                else:
                    screen.blit(car_down_img, (x_pos, y_pos))
            
            # Carril derecho
            if self.right_lane_3[i] == 1:
                offset_x = int(math.sin(current_time / 500.0 + i + 50) * 2)
                x_pos = RIGHT_LANE_3_X + offset_x
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_right_3:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(5, 15)
                        smoke_y = y_pos + random.randint(0, CELL_SIZE//2)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_down_img, (x_pos, y_pos))
                else:
                    screen.blit(car_down_img, (x_pos, y_pos))
        
        # Carretera 4 (abajo a arriba)
        for i in range(NUM_CELLS_VERTICAL):
            y_pos = i * CELL_SIZE
            
            # Carril izquierdo
            if self.left_lane_4[i] == 1:
                offset_x = int(math.sin(current_time / 500.0 + i + 60) * 2)
                x_pos = LEFT_LANE_4_X + offset_x
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_left_4:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(5, 15)
                        smoke_y = y_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_up_img, (x_pos, y_pos))
                else:
                    screen.blit(car_up_img, (x_pos, y_pos))
            
            # Carril derecho
            if self.right_lane_4[i] == 1:
                offset_x = int(math.sin(current_time / 500.0 + i + 70) * 2)
                x_pos = RIGHT_LANE_4_X + offset_x
                
                # Sombra
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_right_4:
                    # Efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(5, 15)
                        smoke_y = y_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car_up_img, (x_pos, y_pos))
                else:
                    screen.blit(car_up_img, (x_pos, y_pos))
        
        # Resaltar el área del cruce para mejor visualización
        # Calculamos el número de celdas basado en CROSS_SIZE
        cross_cells = CROSS_SIZE // CELL_SIZE  # Número de celdas que abarca el cruce
        cross_area = pygame.Surface((cross_cells * CELL_SIZE, cross_cells * CELL_SIZE), pygame.SRCALPHA)
        cross_area.fill((255, 255, 0, 50))  # Amarillo transparente

        # Corregir la posición para centrar exactamente en CROSS_X, CROSS_Y
        cross_x = CROSS_X - (cross_cells * CELL_SIZE) // 2
        cross_y = CROSS_Y - (cross_cells * CELL_SIZE) // 2

        screen.blit(cross_area, (cross_x, cross_y))
        
        # Mostrar información de depuración para los giros
        debug_text = self.font.render(f"Último giro: {self.turn_count} | Prob: {CAR_TURN_PROB}", True, BLACK)
        debug_bg = pygame.Surface((debug_text.get_width() + 10, debug_text.get_height() + 6))
        debug_bg.fill((220, 220, 220))
        debug_bg.set_alpha(180)
        screen.blit(debug_bg, (10, 30))
        screen.blit(debug_text, (15, 33))
        
        # Dibujar contador de generaciones
        gen_text = self.font.render(f"Generación: {self.generation}", True, BLACK)
        text_bg = pygame.Surface((gen_text.get_width() + 10, gen_text.get_height() + 6))
        text_bg.fill((220, 220, 220))
        text_bg.set_alpha(180)
        screen.blit(text_bg, (5, 2))
        screen.blit(gen_text, (10, 5))
        
        # Dibujar modo de frontera
        mode_text = self.font.render(f"Modo: {self.boundary_mode.capitalize()}", True, BLACK)
        mode_bg = pygame.Surface((mode_text.get_width() + 10, mode_text.get_height() + 6))
        mode_bg.fill((220, 220, 220))
        mode_bg.set_alpha(180)
        screen.blit(mode_bg, (WIDTH - mode_text.get_width() - 15, 2))
        screen.blit(mode_text, (WIDTH - mode_text.get_width() - 10, 5))
        
        # Mostrar contadores de coches por vialidad
        count_road1 = np.sum(self.upper_lane_1) + np.sum(self.lower_lane_1)
        count_road2 = np.sum(self.upper_lane_2) + np.sum(self.lower_lane_2)
        count_road3 = np.sum(self.left_lane_3) + np.sum(self.right_lane_3)
        count_road4 = np.sum(self.left_lane_4) + np.sum(self.right_lane_4)
        
        cars_text = self.font.render(f"Coches: O→E:{count_road2} E→O:{count_road1} N→S:{count_road3} S→N:{count_road4}", True, BLACK)
        cars_bg = pygame.Surface((cars_text.get_width() + 10, cars_text.get_height() + 6))
        cars_bg.fill((220, 220, 220))
        cars_bg.set_alpha(180)
        screen.blit(cars_bg, (WIDTH - cars_text.get_width() - 15, 30))
        screen.blit(cars_text, (WIDTH - cars_text.get_width() - 10, 33))
        
        # Mostrar contador de giros
        turns_text = self.font.render(f"Giros: {self.turn_count}", True, BLACK)
        turns_bg = pygame.Surface((turns_text.get_width() + 10, turns_text.get_height() + 6))
        turns_bg.fill((220, 220, 220))
        turns_bg.set_alpha(180)
        screen.blit(turns_bg, (WIDTH - turns_text.get_width() - 15, 58))
        screen.blit(turns_text, (WIDTH - turns_text.get_width() - 10, 61))
        
        # Instrucciones
        instructions = [
            "Espacio: Pausar/Reanudar",
            "T: Toroide",
            "N: Frontera nula",
            "R: Reiniciar",
            f"Arriba/Abajo: Vel({self.simulation_speed})"
        ]
        
        # Fondo para instrucciones
        total_width = 0
        for instruction in instructions:
            text = self.font.render(instruction, True, BLACK)
            total_width += text.get_width() + 20
        
        instruction_bg = pygame.Surface((total_width, 30))
        instruction_bg.fill((240, 240, 240))
        instruction_bg.set_alpha(180)
        screen.blit(instruction_bg, (200, 2))
        
        # Mostrar instrucciones
        x_offset = 210
        for instruction in instructions:
            text = self.font.render(instruction, True, BLACK)
            screen.blit(text, (x_offset, 8))
            x_offset += text.get_width() + 20
        
        # Dibujar la brújula en la esquina superior izquierda
        screen.blit(compass_img, (135, 90))  
        
    def update(self):
        """
        Actualiza el estado de la simulación para la siguiente generación
        usando los objetos Car
        """
        # Crear copia de seguridad de los objetos car
        car_objects_backup = {}
        for road_id, lanes in self.car_objects.items():
            car_objects_backup[road_id] = {}
            for lane_id, cars in lanes.items():
                car_objects_backup[road_id][lane_id] = cars.copy()
        
        # Actualizar la estructura car_objects con nuevas posiciones
        new_car_objects = {
            "road1": {"upper": {}, "lower": {}},
            "road2": {"upper": {}, "lower": {}},
            "road3": {"left": {}, "right": {}},
            "road4": {"left": {}, "right": {}}
        }
        
        # Crear lista temporal de todos los coches para actualización
        all_cars = self._get_all_cars()
        random.shuffle(all_cars)  # Aleatorizar orden para evitar favorecer direcciones
        
        # Actualizar cada coche individualmente
        for car in all_cars:
            car.update(self)
            # Añadir el coche a la nueva estructura en su nueva posición
            road_key = f"road{car.road_id}"
            if car.position not in new_car_objects[road_key][car.lane_id]:
                new_car_objects[road_key][car.lane_id][car.position] = car
        
        # Actualizar la estructura principal
        self.car_objects = new_car_objects
        
        # Reconstruir los mapas de posición basados en los objetos Car actualizados
        self._rebuild_position_maps()
        
        # Manejar fronteras nulas (inserción de coches nuevos)
        if self.boundary_mode == "null":
            self._handle_null_boundaries()
        
        # Incrementar contador de generaciones
        self.generation += 1
    
    def _handle_null_boundaries(self):
        """
        Maneja la inserción de coches nuevos en las fronteras cuando
        el modo de frontera es "null"
        """
        # Carretera 1 (derecha a izquierda, inserción por la derecha)
        road1_total = np.sum(self.upper_lane_1) + np.sum(self.lower_lane_1)
        if road1_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
            # Intentar insertar en el carril con menos autos primero
            if np.sum(self.upper_lane_1) <= np.sum(self.lower_lane_1) and self.upper_lane_1[-1] == 0:
                self.upper_lane_1[-1] = 1
                # Crear objeto Car para esta posición
                car = Car(1, "upper", NUM_CELLS_HORIZONTAL - 1, "right_to_left")
                self.car_objects["road1"]["upper"][NUM_CELLS_HORIZONTAL - 1] = car
            elif self.lower_lane_1[-1] == 0:
                self.lower_lane_1[-1] = 1
                # Crear objeto Car para esta posición
                car = Car(1, "lower", NUM_CELLS_HORIZONTAL - 1, "right_to_left")
                self.car_objects["road1"]["lower"][NUM_CELLS_HORIZONTAL - 1] = car
        
        # Carretera 2 (izquierda a derecha, inserción por la izquierda)
        road2_total = np.sum(self.upper_lane_2) + np.sum(self.lower_lane_2)
        if road2_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
            if np.sum(self.upper_lane_2) <= np.sum(self.lower_lane_2) and self.upper_lane_2[0] == 0:
                self.upper_lane_2[0] = 1
                # Crear objeto Car para esta posición
                car = Car(2, "upper", 0, "left_to_right")
                self.car_objects["road2"]["upper"][0] = car
            elif self.lower_lane_2[0] == 0:
                self.lower_lane_2[0] = 1
                # Crear objeto Car para esta posición
                car = Car(2, "lower", 0, "left_to_right")
                self.car_objects["road2"]["lower"][0] = car
        
        # Carretera 3 (arriba a abajo, inserción por arriba)
        road3_total = np.sum(self.left_lane_3) + np.sum(self.right_lane_3)
        if road3_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
            if np.sum(self.left_lane_3) <= np.sum(self.right_lane_3) and self.left_lane_3[0] == 0:
                self.left_lane_3[0] = 1
                # Crear objeto Car para esta posición
                car = Car(3, "left", 0, "top_to_bottom")
                self.car_objects["road3"]["left"][0] = car
            elif self.right_lane_3[0] == 0:
                self.right_lane_3[0] = 1
                # Crear objeto Car para esta posición
                car = Car(3, "right", 0, "top_to_bottom")
                self.car_objects["road3"]["right"][0] = car
        
        # Carretera 4 (abajo a arriba, inserción por abajo)
        road4_total = np.sum(self.left_lane_4) + np.sum(self.right_lane_4)
        if road4_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
            if np.sum(self.left_lane_4) <= np.sum(self.right_lane_4) and self.left_lane_4[-1] == 0:
                self.left_lane_4[-1] = 1
                # Crear objeto Car para esta posición
                car = Car(4, "left", NUM_CELLS_VERTICAL - 1, "bottom_to_top")
                self.car_objects["road4"]["left"][NUM_CELLS_VERTICAL - 1] = car
            elif self.right_lane_4[-1] == 0:
                self.right_lane_4[-1] = 1
                # Crear objeto Car para esta posición
                car = Car(4, "right", NUM_CELLS_VERTICAL - 1, "bottom_to_top")
                self.car_objects["road4"]["right"][NUM_CELLS_VERTICAL - 1] = car
    
    def handle_broken_cars(self):
        """
        Actualiza el estado de los coches averiados.
        Este método se mantiene por compatibilidad, pero ahora
        la lógica principal está en Car.update_broken()
        """
        # Ahora esta lógica está en el método update de cada objeto Car
        # y en el método _rebuild_position_maps
        pass
    
    def apply_rule_184_horizontal(self, lane, direction):
        """
        Este método se mantiene por compatibilidad, ahora la lógica
        está en el método update_movement de cada objeto Car
        """
        # Crear una copia del carril para el nuevo estado
        return lane.copy()
    
    def apply_rule_184_vertical(self, lane, direction):
        """
        Este método se mantiene por compatibilidad, ahora la lógica
        está en el método update_movement de cada objeto Car
        """
        # Crear una copia del carril para el nuevo estado
        return lane.copy()
    

def main():
    simulator = TrafficCrossSimulator(boundary_mode="null")
    clock = pygame.time.Clock()
    running = True
    paused = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_t:
                    simulator = TrafficCrossSimulator(boundary_mode="toroid")
                elif event.key == pygame.K_n:
                    simulator = TrafficCrossSimulator(boundary_mode="null")
                elif event.key == pygame.K_r:
                    simulator = TrafficCrossSimulator(simulator.boundary_mode)
                elif event.key == pygame.K_UP:
                    simulator.simulation_speed = min(simulator.simulation_speed + 2, 30)
                elif event.key == pygame.K_DOWN:
                    simulator.simulation_speed = max(simulator.simulation_speed - 2, 1)
        
        if not paused:
            simulator.update()
        
        simulator.draw()
        
        pygame.display.flip()
        clock.tick(simulator.simulation_speed)
    
    pygame.quit()

if __name__ == "__main__":
    main()