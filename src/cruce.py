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
NUM_CELLS_HORIZONTAL = 50  # Número de celdas horizontales
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
CAR_CHANGE_LANE_PROB = 0.1    # Reducido para menos caos
CAR_BREAKDOWN_PROB = 0.02     # Reducido para observar mejor
CAR_INSERTION_PROB = 0.05     # Reducido para menor densidad
CAR_TURN_PROB = 0.2          # Probabilidad de dar vuelta en el cruce
REPAIR_ATTEMPTS = 20
REPAIR_PROB = 0.5

# Posición del cruce (centro del cruce)
CROSS_X = 400
CROSS_Y = 400
CROSS_WIDTH = 80
CROSS_HEIGHT = 80

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

# Coches para las cuatro direcciones
car_left_img = pygame.image.load(os.path.join(parent_dir, "./assets/1_left.png"))  # Derecha a izquierda
car_right_img = pygame.image.load(os.path.join(parent_dir, "./assets/2_right.png"))  # Izquierda a derecha
car_down_img = pygame.image.load(os.path.join(parent_dir, "./assets/3_down.png"))  # Arriba a abajo
car_up_img = pygame.image.load(os.path.join(parent_dir, "./assets/4_up.png"))  # Abajo a arriba

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

class TrafficCrossSimulator:
    def __init__(self, boundary_mode="toroid"):
        # Inicializar carriles horizontales (0 = vacío, 1 = auto)
        # Primera carretera (dirección: derecha a izquierda)
        self.upper_lane_1 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)
        self.lower_lane_1 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)
        
        # Segunda carretera (dirección: izquierda a derecha)
        self.upper_lane_2 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)
        self.lower_lane_2 = np.zeros(NUM_CELLS_HORIZONTAL, dtype=int)
        
        # Tercera carretera (dirección: arriba a abajo)
        self.left_lane_3 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)
        self.right_lane_3 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)
        
        # Cuarta carretera (dirección: abajo a arriba)
        self.left_lane_4 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)
        self.right_lane_4 = np.zeros(NUM_CELLS_VERTICAL, dtype=int)
        
        # Autos descompuestos
        self.broken_cars_upper_1 = {}  # Derecha a izquierda, carril superior
        self.broken_cars_lower_1 = {}  # Derecha a izquierda, carril inferior
        self.broken_cars_upper_2 = {}  # Izquierda a derecha, carril superior
        self.broken_cars_lower_2 = {}  # Izquierda a derecha, carril inferior
        self.broken_cars_left_3 = {}   # Arriba a abajo, carril izquierdo
        self.broken_cars_right_3 = {}  # Arriba a abajo, carril derecho
        self.broken_cars_left_4 = {}   # Abajo a arriba, carril izquierdo
        self.broken_cars_right_4 = {}  # Abajo a arriba, carril derecho
        
        # Índices de la celda central del cruce para cada carril
        # IMPORTANTE: Inicializamos estos valores antes de llamar a _initialize_limited_cars
        self.cross_index_h = NUM_CELLS_HORIZONTAL // 2  # Índice horizontal del centro del cruce
        self.cross_index_v = NUM_CELLS_VERTICAL // 2    # Índice vertical del centro del cruce
        
        # Constante para el máximo número de coches por vialidad
        self.MAX_CARS_PER_ROAD = 15
    
        # En lugar de usar densidad, colocamos exactamente 15 coches por cada tipo de vialidad
        # distribuidos uniformemente
        
        # 15 coches para la primera carretera (derecha a izquierda)
        self._initialize_limited_cars(self.upper_lane_1, 8)  # 8 en carril superior
        self._initialize_limited_cars(self.lower_lane_1, 7)  # 7 en carril inferior
        
        # 15 coches para la segunda carretera (izquierda a derecha)
        self._initialize_limited_cars(self.upper_lane_2, 8)  # 8 en carril superior
        self._initialize_limited_cars(self.lower_lane_2, 7)  # 7 en carril inferior
        
        # 15 coches para la tercera carretera (arriba a abajo)
        self._initialize_limited_cars(self.left_lane_3, 8)   # 8 en carril izquierdo
        self._initialize_limited_cars(self.right_lane_3, 7)  # 7 en carril derecho
        
        # 15 coches para la cuarta carretera (abajo a arriba)
        self._initialize_limited_cars(self.left_lane_4, 8)   # 8 en carril izquierdo
        self._initialize_limited_cars(self.right_lane_4, 7)  # 7 en carril derecho
        
        self.generation = 0
        self.boundary_mode = boundary_mode
        self.turn_count = 0  # Contador de giros realizados
        
        # Fuente para textos
        try:
            self.font = pygame.font.SysFont("Arial", 13)
        except:
            self.font = pygame.font.SysFont(None, 24)
        
        self.simulation_speed = 10  # Velocidad predeterminada
    
    def _initialize_lane(self, lane, spacing, offset):
        """Inicializar un carril con coches espaciados uniformemente"""
        for i in range(len(lane)):
            if (i + offset) % spacing == 0:
                lane[i] = 1
    
    def _initialize_limited_cars(self, lane, num_cars):
        """
        Inicializa un carril con un número específico de coches distribuidos uniformemente
        
        Args:
            lane: El carril donde colocar los coches
            num_cars: Número exacto de coches a colocar
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
        for i in range(0, lane_length, spacing):
            if cars_placed >= num_cars:
                break
            
            # No colocar coches en el área de cruce al iniciar
            if i not in cross_area:
                lane[i] = 1
                cars_placed += 1
        
        # Si no se colocaron todos los coches debido al cruce, colocamos el resto
        # buscando espacios vacíos
        if cars_placed < num_cars:
            for i in range(lane_length):
                if cars_placed >= num_cars:
                    break
                    
                if lane[i] == 0 and i not in cross_area:
                    lane[i] = 1
                    cars_placed += 1
    
    def apply_rule_184_horizontal(self, lane, direction="left_to_right"):
        """Aplicar Regla 184 para movimiento horizontal"""
        new_lane = np.zeros_like(lane)
        
        if direction == "left_to_right":
            # Movimiento de izquierda a derecha
            for i in range(len(lane)):
                if self.boundary_mode == "toroid":
                    left = lane[(i - 1) % len(lane)]
                    center = lane[i]
                    right = lane[(i + 1) % len(lane)]
                else:
                    left = lane[i - 1] if i > 0 else 0
                    center = lane[i]
                    right = lane[i + 1] if i < len(lane) - 1 else 0
                
                # Regla de movimiento: avanzar si hay espacio adelante
                if center == 1 and right == 0:
                    new_lane[i] = 0  # El coche avanza, esta celda queda vacía
                elif center == 0 and left == 1:
                    new_lane[i] = 1  # Un coche llega desde la izquierda
                else:
                    new_lane[i] = center  # La celda mantiene su estado
        else:
            # Movimiento de derecha a izquierda
            for i in range(len(lane) - 1, -1, -1):
                if self.boundary_mode == "toroid":
                    right = lane[(i + 1) % len(lane)]
                    center = lane[i]
                    left = lane[(i - 1) % len(lane)]
                else:
                    right = lane[i + 1] if i < len(lane) - 1 else 0
                    center = lane[i]
                    left = lane[i - 1] if i > 0 else 0
                
                # Regla de movimiento: avanzar si hay espacio adelante
                if center == 1 and left == 0:
                    new_lane[i] = 0  # El coche avanza, esta celda queda vacía
                elif center == 0 and right == 1:
                    new_lane[i] = 1  # Un coche llega desde la derecha
                else:
                    new_lane[i] = center  # La celda mantiene su estado
        
        return new_lane
    
    def apply_rule_184_vertical(self, lane, direction="top_to_bottom"):
        """Aplicar Regla 184 para movimiento vertical"""
        new_lane = np.zeros_like(lane)
        
        if direction == "top_to_bottom":
            # Movimiento de arriba a abajo
            for i in range(len(lane)):
                if self.boundary_mode == "toroid":
                    top = lane[(i - 1) % len(lane)]
                    center = lane[i]
                    bottom = lane[(i + 1) % len(lane)]
                else:
                    top = lane[i - 1] if i > 0 else 0
                    center = lane[i]
                    bottom = lane[i + 1] if i < len(lane) - 1 else 0
                
                # Regla de movimiento: avanzar si hay espacio adelante
                if center == 1 and bottom == 0:
                    new_lane[i] = 0  # El coche avanza, esta celda queda vacía
                elif center == 0 and top == 1:
                    new_lane[i] = 1  # Un coche llega desde arriba
                else:
                    new_lane[i] = center  # La celda mantiene su estado
        else:
            # Movimiento de abajo a arriba
            for i in range(len(lane) - 1, -1, -1):
                if self.boundary_mode == "toroid":
                    bottom = lane[(i + 1) % len(lane)]
                    center = lane[i]
                    top = lane[(i - 1) % len(lane)]
                else:
                    bottom = lane[i + 1] if i < len(lane) - 1 else 0
                    center = lane[i]
                    top = lane[i - 1] if i > 0 else 0
                
                # Regla de movimiento: avanzar si hay espacio adelante
                if center == 1 and top == 0:
                    new_lane[i] = 0  # El coche avanza, esta celda queda vacía
                elif center == 0 and bottom == 1:
                    new_lane[i] = 1  # Un coche llega desde abajo
                else:
                    new_lane[i] = center  # La celda mantiene su estado
        
        return new_lane
    
    def handle_broken_cars(self):
        """Procesar autos descompuestos en todos los carriles"""
        # Definir una función auxiliar para procesar cada diccionario de autos averiados
        def process_broken_cars(broken_dict, lane):
            to_remove = []
            for pos, remaining in list(broken_dict.items()):
                if remaining <= 1:
                    if random.random() < REPAIR_PROB:
                        pass  # Auto reparado
                    else:
                        lane[pos] = 0  # Auto remolcado
                    to_remove.append(pos)
                else:
                    broken_dict[pos] = remaining - 1
            
            for pos in to_remove:
                del broken_dict[pos]
        
        # Procesar cada carril
        process_broken_cars(self.broken_cars_upper_1, self.upper_lane_1)
        process_broken_cars(self.broken_cars_lower_1, self.lower_lane_1)
        process_broken_cars(self.broken_cars_upper_2, self.upper_lane_2)
        process_broken_cars(self.broken_cars_lower_2, self.lower_lane_2)
        process_broken_cars(self.broken_cars_left_3, self.left_lane_3)
        process_broken_cars(self.broken_cars_right_3, self.right_lane_3)
        process_broken_cars(self.broken_cars_left_4, self.left_lane_4)
        process_broken_cars(self.broken_cars_right_4, self.right_lane_4)
    
    def is_cross_area(self, i, lane_type):
        """Determinar si una celda está en el área del cruce"""
        if lane_type in ["upper_1", "lower_1", "upper_2", "lower_2"]:
            # Carriles horizontales
            cross_start = self.cross_index_h - 1
            cross_end = self.cross_index_h + 1
            return cross_start <= i <= cross_end
        else:
            # Carriles verticales
            cross_start = self.cross_index_v - 1
            cross_end = self.cross_index_v + 1
            return cross_start <= i <= cross_end
    
    def can_enter_cross(self, lane_type):
        """Determinar si un vehículo puede entrar al cruce (siempre es True ahora que no hay semáforo)"""
        return True
    
    def is_cross_clear(self, i_h, i_v, new_lanes):
        """
        Verifica si el cruce está suficientemente despejado para un giro.
        Modificamos para permitir más giros, solo verificando los puntos clave.
        """
        # Solo verificar la celda destino y una celda adicional en la dirección de movimiento
        # para evitar colisiones inmediatas
        
        # Para giros a carretera 1 (upper_lane_1)
        if new_lanes['upper_1'][self.cross_index_h] == 1:
            return False
            
        # Para giros a carretera 2 (upper_2)
        elif new_lanes['upper_2'][self.cross_index_h] == 1:
            return False
            
        # Para giros a carretera 3 (left_lane_3)
        elif new_lanes['left_3'][self.cross_index_v] == 1:
            return False
            
        # Para giros a carretera 4 (right_4)
        elif new_lanes['right_4'][self.cross_index_v] == 1:
            return False
        
        return True
    
    def update(self):
        self.generation += 1
        
        # Procesar autos descompuestos
        self.handle_broken_cars()
        
        # Calcular nuevos estados para cada carril sin considerar giros aún
        # Carriles horizontales
        new_upper_lane_1 = self.apply_rule_184_horizontal(self.upper_lane_1, "right_to_left")
        new_lower_lane_1 = self.apply_rule_184_horizontal(self.lower_lane_1, "right_to_left")
        new_upper_lane_2 = self.apply_rule_184_horizontal(self.upper_lane_2, "left_to_right")
        new_lower_lane_2 = self.apply_rule_184_horizontal(self.lower_lane_2, "left_to_right")
        
        # Carriles verticales
        new_left_lane_3 = self.apply_rule_184_vertical(self.left_lane_3, "top_to_bottom")
        new_right_lane_3 = self.apply_rule_184_vertical(self.right_lane_3, "top_to_bottom")
        new_left_lane_4 = self.apply_rule_184_vertical(self.left_lane_4, "bottom_to_top")
        new_right_lane_4 = self.apply_rule_184_vertical(self.right_lane_4, "bottom_to_top")
        
        # Crear un diccionario con todos los carriles para facilitar el manejo
        new_lanes = {
            'upper_1': new_upper_lane_1,
            'lower_1': new_lower_lane_1,
            'upper_2': new_upper_lane_2,
            'lower_2': new_lower_lane_2,
            'left_3': new_left_lane_3,
            'right_3': new_right_lane_3,
            'left_4': new_left_lane_4,
            'right_4': new_right_lane_4
        }
        
        # -- Manejar los giros en el cruce --
        
        # Lista para almacenar los giros a realizar
        turns = []
        # Lista para almacenar averías (necesitas inicializar esta lista)
        new_breakdowns = []
        
        # --- SIMPLIFICAR LA LÓGICA DE GIROS ---
        
        # 1. Giro desde carril inferior 1 hacia carretera 4 (derecha)
        if (new_lower_lane_1[self.cross_index_h] == 1 and
            new_right_lane_4[self.cross_index_v] == 0 and
            random.random() < CAR_TURN_PROB):
            turns.append(("lower_1_to_right_4", self.cross_index_h, self.cross_index_v))
            new_lower_lane_1[self.cross_index_h] = 0
        
        # 2. Giro desde carril inferior 2 hacia carretera 3 (izquierda)
        if (new_lower_lane_2[self.cross_index_h] == 1 and
            new_left_lane_3[self.cross_index_v] == 0 and
            random.random() < CAR_TURN_PROB):
            turns.append(("lower_2_to_left_3", self.cross_index_h, self.cross_index_v))
            new_lower_lane_2[self.cross_index_h] = 0
        
        # 3. Giro desde carril izquierdo 3 hacia carretera 1 (superior)
        if (new_left_lane_3[self.cross_index_v] == 1 and
            new_upper_lane_1[self.cross_index_h] == 0 and
            random.random() < CAR_TURN_PROB):
            turns.append(("left_3_to_upper_1", self.cross_index_h, self.cross_index_v))
            new_left_lane_3[self.cross_index_v] = 0
        
        # 4. Giro desde carril derecho 4 hacia carretera 2 (superior)
        if (new_right_lane_4[self.cross_index_v] == 1 and
            new_upper_lane_2[self.cross_index_h] == 0 and
            random.random() < CAR_TURN_PROB):
            turns.append(("right_4_to_upper_2", self.cross_index_h, self.cross_index_v))
            new_right_lane_4[self.cross_index_v] = 0
        
        # Aquí deberías agregar la lógica para determinar los coches que se averían
        # Por ejemplo:
        
        # Verificar averías en carreteras horizontales
        for i in range(NUM_CELLS_HORIZONTAL):
            # Carretera 1
            if new_upper_lane_1[i] == 1 and i not in self.broken_cars_upper_1:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("upper_1", i))
        
            if new_lower_lane_1[i] == 1 and i not in self.broken_cars_lower_1:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("lower_1", i))
        
            # Carretera 2
            if new_upper_lane_2[i] == 1 and i not in self.broken_cars_upper_2:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("upper_2", i))
        
            if new_lower_lane_2[i] == 1 and i not in self.broken_cars_lower_2:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("lower_2", i))
        
        # Verificar averías en carreteras verticales
        for i in range(NUM_CELLS_VERTICAL):
            # Carretera 3
            if new_left_lane_3[i] == 1 and i not in self.broken_cars_left_3:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("left_3", i))
        
            if new_right_lane_3[i] == 1 and i not in self.broken_cars_right_3:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("right_3", i))
        
            # Carretera 4
            if new_left_lane_4[i] == 1 and i not in self.broken_cars_left_4:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("left_4", i))
        
            if new_right_lane_4[i] == 1 and i not in self.broken_cars_right_4:
                if random.random() < CAR_BREAKDOWN_PROB:
                    new_breakdowns.append(("right_4", i))
        
        # Aplicar giros en el cruce
        for turn, i_h, i_v in turns:
            if turn == "lower_1_to_right_4":
                new_right_lane_4[i_v] = 1
                self.turn_count += 1
            elif turn == "lower_2_to_left_3":
                new_left_lane_3[i_v] = 1
                self.turn_count += 1
            elif turn == "left_3_to_upper_1":
                new_upper_lane_1[i_h] = 1
                self.turn_count += 1
            elif turn == "right_4_to_upper_2":
                new_upper_lane_2[i_h] = 1
                self.turn_count += 1
    
        # Aplicar nuevas averías
        for lane, i in new_breakdowns:
            if lane == "upper_1":
                self.broken_cars_upper_1[i] = REPAIR_ATTEMPTS
            elif lane == "lower_1":
                self.broken_cars_lower_1[i] = REPAIR_ATTEMPTS
            elif lane == "upper_2":
                self.broken_cars_upper_2[i] = REPAIR_ATTEMPTS
            elif lane == "lower_2":
                self.broken_cars_lower_2[i] = REPAIR_ATTEMPTS
            elif lane == "left_3":
                self.broken_cars_left_3[i] = REPAIR_ATTEMPTS
            elif lane == "right_3":
                self.broken_cars_right_3[i] = REPAIR_ATTEMPTS
            elif lane == "left_4":
                self.broken_cars_left_4[i] = REPAIR_ATTEMPTS
            elif lane == "right_4":
                self.broken_cars_right_4[i] = REPAIR_ATTEMPTS
        
        # Manejar inserciones en frontera nula de manera más ordenada
        if self.boundary_mode == "null":
            # Carretera 1 (derecha a izquierda, inserción por la derecha)
            road1_total = np.sum(new_upper_lane_1) + np.sum(new_lower_lane_1)
            if road1_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
                # Intentar insertar en el carril con menos autos primero
                if np.sum(new_upper_lane_1) <= np.sum(new_lower_lane_1) and new_upper_lane_1[-1] == 0:
                    new_upper_lane_1[-1] = 1
                elif new_lower_lane_1[-1] == 0:
                    new_lower_lane_1[-1] = 1
            
            # Carretera 2 (izquierda a derecha, inserción por la izquierda)
            road2_total = np.sum(new_upper_lane_2) + np.sum(new_lower_lane_2)
            if road2_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
                if np.sum(new_upper_lane_2) <= np.sum(new_lower_lane_2) and new_upper_lane_2[0] == 0:
                    new_upper_lane_2[0] = 1
                elif new_lower_lane_2[0] == 0:
                    new_lower_lane_2[0] = 1
            
            # Carretera 3 (arriba a abajo, inserción por arriba)
            road3_total = np.sum(new_left_lane_3) + np.sum(new_right_lane_3)
            if road3_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
                if np.sum(new_left_lane_3) <= np.sum(new_right_lane_3) and new_left_lane_3[0] == 0:
                    new_left_lane_3[0] = 1
                elif new_right_lane_3[0] == 0:
                    new_right_lane_3[0] = 1
            
            # Carretera 4 (abajo a arriba, inserción por abajo)
            road4_total = np.sum(new_left_lane_4) + np.sum(new_right_lane_4)
            if road4_total < self.MAX_CARS_PER_ROAD and random.random() < CAR_INSERTION_PROB * 0.3:
                if np.sum(new_left_lane_4) <= np.sum(new_right_lane_4) and new_left_lane_4[-1] == 0:
                    new_left_lane_4[-1] = 1
                elif new_right_lane_4[-1] == 0:
                    new_right_lane_4[-1] = 1
        
        # Asegurar que los autos descompuestos permanezcan en su lugar
        for pos in self.broken_cars_upper_1:
            new_upper_lane_1[pos] = 1
        for pos in self.broken_cars_lower_1:
            new_lower_lane_1[pos] = 1
        for pos in self.broken_cars_upper_2:
            new_upper_lane_2[pos] = 1
        for pos in self.broken_cars_lower_2:
            new_lower_lane_2[pos] = 1
        for pos in self.broken_cars_left_3:
            new_left_lane_3[pos] = 1
        for pos in self.broken_cars_right_3:
            new_right_lane_3[pos] = 1
        for pos in self.broken_cars_left_4:
            new_left_lane_4[pos] = 1
        for pos in self.broken_cars_right_4:
            new_right_lane_4[pos] = 1
        
        # Forzar el límite estricto de 15 coches por vialidad
        # Si hay más de 15, eliminar algunos aleatoriamente
        self._enforce_car_limit(new_upper_lane_1, new_lower_lane_1, self.MAX_CARS_PER_ROAD)
        self._enforce_car_limit(new_upper_lane_2, new_lower_lane_2, self.MAX_CARS_PER_ROAD)
        self._enforce_car_limit(new_left_lane_3, new_right_lane_3, self.MAX_CARS_PER_ROAD)
        self._enforce_car_limit(new_left_lane_4, new_right_lane_4, self.MAX_CARS_PER_ROAD)
        
        # Actualizar estado de los carriles
        self.upper_lane_1 = new_upper_lane_1
        self.lower_lane_1 = new_lower_lane_1
        self.upper_lane_2 = new_upper_lane_2
        self.lower_lane_2 = new_lower_lane_2
        self.left_lane_3 = new_left_lane_3
        self.right_lane_3 = new_right_lane_3
        self.left_lane_4 = new_left_lane_4
        self.right_lane_4 = new_right_lane_4
    
    def _enforce_car_limit(self, lane1, lane2, max_cars):
        """
        Fuerza el límite de coches en un par de carriles.
        Si hay más coches que el límite, elimina algunos aleatoriamente
        pero evitando los coches descompuestos.
        
        Args:
            lane1: Primer carril
            lane2: Segundo carril
            max_cars: Número máximo de coches permitido en ambos carriles
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
                elif indices_lane2:
                    idx = indices_lane2.pop()
                    lane2[idx] = 0
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
        cross_area = pygame.Surface((CELL_SIZE*3, CELL_SIZE*3), pygame.SRCALPHA)
        cross_area.fill((255, 255, 0, 50))  # Amarillo transparente
        
        # Corregir la posición para centrar exactamente en CROSS_X, CROSS_Y (400, 400)
        cross_x = CROSS_X - (CELL_SIZE * 1.5)  # Centrar horizontalmente (1.5 celdas a la izquierda)
        cross_y = CROSS_Y - (CELL_SIZE * 1.5)  # Centrar verticalmente (1.5 celdas arriba)
        
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