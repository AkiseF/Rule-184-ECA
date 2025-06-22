import pygame
import numpy as np
import random
import os
import math

# Inicializar pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 1500, 280  # Aumentar altura para 4 carriles (2 carreteras)
CELL_SIZE = 60
NUM_CELLS = 50
# Posiciones Y para los 4 carriles
UPPER_LANE_1_Y = 10   # Carril superior de primera carretera
LOWER_LANE_1_Y = 70   # Carril inferior de primera carretera
UPPER_LANE_2_Y = 150  # Carril superior de segunda carretera
LOWER_LANE_2_Y = 210  # Carril inferior de segunda carretera

CAR_CHANGE_LANE_PROB = 0.2
CAR_BREAKDOWN_PROB = 0.05
CAR_INSERTION_PROB = 0.1
REPAIR_ATTEMPTS = 20
REPAIR_PROB = 0.5

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Crear la ventana
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Tráfico Doble Carretera - Regla 184")

# Cargar imágenes
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
road_img = pygame.image.load(os.path.join(parent_dir, "./assets/doble_carril.png"))
road_img = pygame.transform.scale(road_img, (WIDTH, HEIGHT))

# Coches para la primera carretera (derecha a izquierda)
car1_img = pygame.image.load(os.path.join(parent_dir, "./assets/1_right.png"))
car1_img = pygame.transform.scale(car1_img, (CELL_SIZE, CELL_SIZE))

# Coches para la segunda carretera (izquierda a derecha)
car2_img = pygame.image.load(os.path.join(parent_dir, "./assets/3_right.png"))
car2_img = pygame.transform.scale(car2_img, (CELL_SIZE, CELL_SIZE))

# Versiones para coches descompuestos
broken_car1_img = car1_img.copy()
broken_car2_img = car2_img.copy()

# Aplicar tinte rojo a los autos descompuestos
red_overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
red_overlay.fill((255, 0, 0, 100))
broken_car1_img.blit(red_overlay, (0, 0))
broken_car2_img.blit(red_overlay, (0, 0))

class DoubleRoadTrafficSimulator:
    def __init__(self, boundary_mode="toroid"):
        # Inicializar carriles (0 = vacío, 1 = auto)
        # Primera carretera (dirección: derecha a izquierda)
        self.upper_lane_1 = np.zeros(NUM_CELLS, dtype=int)
        self.lower_lane_1 = np.zeros(NUM_CELLS, dtype=int)
        
        # Segunda carretera (dirección: izquierda a derecha)
        self.upper_lane_2 = np.zeros(NUM_CELLS, dtype=int)
        self.lower_lane_2 = np.zeros(NUM_CELLS, dtype=int)
        
        # Distribuir autos de manera uniforme
        density = 0.3  # 30% de ocupación
        spacing = int(1/density)
        
        # Colocar coches en primera carretera
        offset1 = random.randint(0, spacing-1)
        for i in range(NUM_CELLS):
            if (i + offset1) % spacing == 0:
                self.upper_lane_1[i] = 1
            
            lower_offset1 = (offset1 + spacing//2) % spacing
            if (i + lower_offset1) % spacing == 0:
                self.lower_lane_1[i] = 1
        
        # Colocar coches en segunda carretera
        offset2 = random.randint(0, spacing-1)
        for i in range(NUM_CELLS):
            if (i + offset2) % spacing == 0:
                self.upper_lane_2[i] = 1
            
            lower_offset2 = (offset2 + spacing//2) % spacing
            if (i + lower_offset2) % spacing == 0:
                self.lower_lane_2[i] = 1
        
        # Añadir aleatoriedad para romper patrones rígidos
        for i in range(NUM_CELLS):
            if random.random() < 0.1:
                self.upper_lane_1[i] = 1 - self.upper_lane_1[i]
            if random.random() < 0.1:
                self.lower_lane_1[i] = 1 - self.lower_lane_1[i]
            if random.random() < 0.1:
                self.upper_lane_2[i] = 1 - self.upper_lane_2[i]
            if random.random() < 0.1:
                self.lower_lane_2[i] = 1 - self.lower_lane_2[i]
        
        # Autos descompuestos
        self.broken_cars_upper_1 = {}
        self.broken_cars_lower_1 = {}
        self.broken_cars_upper_2 = {}
        self.broken_cars_lower_2 = {}
        
        self.generation = 0
        self.boundary_mode = boundary_mode
        
        # Fuente para textos
        try:
            self.font = pygame.font.SysFont("Arial", 18)
        except:
            self.font = pygame.font.SysFont(None, 24)
        
        self.simulation_speed = 10  # Velocidad predeterminada
    
    def apply_rule_184_left_to_right(self, lane):
        """Aplicar Regla 184 para movimiento de izquierda a derecha"""
        new_lane = np.zeros_like(lane)
        
        for i in range(len(lane)):
            if self.boundary_mode == "toroid":
                left = lane[(i - 1) % len(lane)]
                center = lane[i]
                right = lane[(i + 1) % len(lane)]
            else:
                left = lane[i - 1] if i > 0 else 0
                center = lane[i]
                right = lane[i + 1] if i < len(lane) - 1 else 0
            
            # Tabla de búsqueda para Regla 184 (izquierda a derecha)
            pattern = (left << 2) | (center << 1) | right
            rule_output = {
                0: 0, 1: 1, 2: 0, 3: 1,
                4: 1, 5: 0, 6: 1, 7: 0
            }
            new_lane[i] = rule_output[pattern]
        
        # En modo toroide, mantener el número de coches
        if self.boundary_mode == "toroid":
            if np.sum(lane) != np.sum(new_lane):
                # Si hay un coche que desaparece por la derecha, insertarlo por la izquierda
                if lane[-1] == 1 and new_lane[-1] == 0 and new_lane[0] == 0:
                    new_lane[0] = 1
        
        return new_lane
    
    def apply_rule_184_right_to_left(self, lane):
        """Aplicar Regla 184 para movimiento de derecha a izquierda (inverso)"""
        # Para simular movimiento de derecha a izquierda, invertimos el arreglo,
        # aplicamos la regla estándar y volvemos a invertir
        reversed_lane = np.flip(lane)
        new_reversed_lane = self.apply_rule_184_left_to_right(reversed_lane)
        new_lane = np.flip(new_reversed_lane)
        
        return new_lane
    
    def handle_broken_cars(self):
        # Procesar autos descompuestos en todos los carriles
        
        # Primera carretera (carril superior)
        broken_cars_to_remove_upper_1 = []
        for pos, remaining in list(self.broken_cars_upper_1.items()):
            if remaining <= 1:
                if random.random() < REPAIR_PROB:
                    pass  # Auto reparado
                else:
                    self.upper_lane_1[pos] = 0  # Auto remolcado
                broken_cars_to_remove_upper_1.append(pos)
            else:
                self.broken_cars_upper_1[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_upper_1:
            del self.broken_cars_upper_1[pos]
        
        # Primera carretera (carril inferior)
        broken_cars_to_remove_lower_1 = []
        for pos, remaining in list(self.broken_cars_lower_1.items()):
            if remaining <= 1:
                if random.random() < REPAIR_PROB:
                    pass  # Auto reparado
                else:
                    self.lower_lane_1[pos] = 0  # Auto remolcado
                broken_cars_to_remove_lower_1.append(pos)
            else:
                self.broken_cars_lower_1[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_lower_1:
            del self.broken_cars_lower_1[pos]
        
        # Segunda carretera (carril superior)
        broken_cars_to_remove_upper_2 = []
        for pos, remaining in list(self.broken_cars_upper_2.items()):
            if remaining <= 1:
                if random.random() < REPAIR_PROB:
                    pass  # Auto reparado
                else:
                    self.upper_lane_2[pos] = 0  # Auto remolcado
                broken_cars_to_remove_upper_2.append(pos)
            else:
                self.broken_cars_upper_2[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_upper_2:
            del self.broken_cars_upper_2[pos]
        
        # Segunda carretera (carril inferior)
        broken_cars_to_remove_lower_2 = []
        for pos, remaining in list(self.broken_cars_lower_2.items()):
            if remaining <= 1:
                if random.random() < REPAIR_PROB:
                    pass  # Auto reparado
                else:
                    self.lower_lane_2[pos] = 0  # Auto remolcado
                broken_cars_to_remove_lower_2.append(pos)
            else:
                self.broken_cars_lower_2[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_lower_2:
            del self.broken_cars_lower_2[pos]
    
    def update(self):
        self.generation += 1
        
        # Procesar autos descompuestos
        self.handle_broken_cars()
        
        # Calcular nuevos estados para cada carril
        # Primera carretera (derecha a izquierda)
        new_upper_lane_1 = self.apply_rule_184_right_to_left(self.upper_lane_1)
        new_lower_lane_1 = self.apply_rule_184_right_to_left(self.lower_lane_1)
        
        # Segunda carretera (izquierda a derecha)
        new_upper_lane_2 = self.apply_rule_184_left_to_right(self.upper_lane_2)
        new_lower_lane_2 = self.apply_rule_184_left_to_right(self.lower_lane_2)
        
        # Verificar cambios de carril y averías en primera carretera
        upper_to_lower_1 = []
        lower_to_upper_1 = []
        new_breakdowns_upper_1 = []
        new_breakdowns_lower_1 = []
        
        # Primera carretera, carril superior
        for i in range(NUM_CELLS):
            if new_upper_lane_1[i] == 1 and i not in self.broken_cars_upper_1:
                # Verificar si coche está bloqueado
                is_blocked = False
                # En carril derecha-izquierda, verificamos la celda anterior (a la izquierda)
                if i > 0 and i - 1 in self.broken_cars_upper_1:
                    is_blocked = True
                
                if is_blocked:
                    decision = random.random()
                    if decision < 0.2:
                        # Decide esperar (20% probabilidad)
                        pass
                    elif decision < 0.7 and new_lower_lane_1[i] == 0:
                        # Intenta cambiar de carril (50% probabilidad)
                        upper_to_lower_1.append(i)
                else:
                    # Comportamiento normal
                    if random.random() < CAR_CHANGE_LANE_PROB and new_lower_lane_1[i] == 0:
                        upper_to_lower_1.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_upper_1.append(i)
        
        # Primera carretera, carril inferior
        for i in range(NUM_CELLS):
            if new_lower_lane_1[i] == 1 and i not in self.broken_cars_lower_1:
                is_blocked = False
                if i > 0 and i - 1 in self.broken_cars_lower_1:
                    is_blocked = True
                
                if is_blocked:
                    decision = random.random()
                    if decision < 0.2:
                        pass
                    elif decision < 0.7 and new_upper_lane_1[i] == 0:
                        lower_to_upper_1.append(i)
                else:
                    if random.random() < CAR_CHANGE_LANE_PROB and new_upper_lane_1[i] == 0:
                        lower_to_upper_1.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_lower_1.append(i)
        
        # Verificar cambios de carril y averías en segunda carretera
        upper_to_lower_2 = []
        lower_to_upper_2 = []
        new_breakdowns_upper_2 = []
        new_breakdowns_lower_2 = []
        
        # Segunda carretera, carril superior
        for i in range(NUM_CELLS):
            if new_upper_lane_2[i] == 1 and i not in self.broken_cars_upper_2:
                # En carril izquierda-derecha, verificamos la celda siguiente
                is_blocked = False
                if i < NUM_CELLS - 1 and i + 1 in self.broken_cars_upper_2:
                    is_blocked = True
                
                if is_blocked:
                    decision = random.random()
                    if decision < 0.2:
                        pass
                    elif decision < 0.7 and new_lower_lane_2[i] == 0:
                        upper_to_lower_2.append(i)
                else:
                    if random.random() < CAR_CHANGE_LANE_PROB and new_lower_lane_2[i] == 0:
                        upper_to_lower_2.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_upper_2.append(i)
        
        # Segunda carretera, carril inferior
        for i in range(NUM_CELLS):
            if new_lower_lane_2[i] == 1 and i not in self.broken_cars_lower_2:
                is_blocked = False
                if i < NUM_CELLS - 1 and i + 1 in self.broken_cars_lower_2:
                    is_blocked = True
                
                if is_blocked:
                    decision = random.random()
                    if decision < 0.2:
                        pass
                    elif decision < 0.7 and new_upper_lane_2[i] == 0:
                        lower_to_upper_2.append(i)
                else:
                    if random.random() < CAR_CHANGE_LANE_PROB and new_upper_lane_2[i] == 0:
                        lower_to_upper_2.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_lower_2.append(i)
        
        # Aplicar cambios de carril
        # Primera carretera
        for i in upper_to_lower_1:
            new_upper_lane_1[i] = 0
            new_lower_lane_1[i] = 1
        
        for i in lower_to_upper_1:
            new_lower_lane_1[i] = 0
            new_upper_lane_1[i] = 1
        
        # Segunda carretera
        for i in upper_to_lower_2:
            new_upper_lane_2[i] = 0
            new_lower_lane_2[i] = 1
        
        for i in lower_to_upper_2:
            new_lower_lane_2[i] = 0
            new_upper_lane_2[i] = 1
        
        # Aplicar nuevas averías
        # Primera carretera
        for i in new_breakdowns_upper_1:
            self.broken_cars_upper_1[i] = REPAIR_ATTEMPTS
        
        for i in new_breakdowns_lower_1:
            self.broken_cars_lower_1[i] = REPAIR_ATTEMPTS
        
        # Segunda carretera
        for i in new_breakdowns_upper_2:
            self.broken_cars_upper_2[i] = REPAIR_ATTEMPTS
        
        for i in new_breakdowns_lower_2:
            self.broken_cars_lower_2[i] = REPAIR_ATTEMPTS
        
        # Manejar inserciones en frontera nula
        if self.boundary_mode == "null":
            # Primera carretera (inserciones por la derecha)
            if random.random() < CAR_INSERTION_PROB:
                upper_count = np.sum(new_upper_lane_1)
                lower_count = np.sum(new_lower_lane_1)
                total_cells = NUM_CELLS * 2
                current_density = (upper_count + lower_count) / total_cells
                
                if current_density < 0.3:
                    if new_upper_lane_1[-1] == 0 and new_lower_lane_1[-1] == 0:
                        if upper_count <= lower_count:
                            new_upper_lane_1[-1] = 1
                        else:
                            new_lower_lane_1[-1] = 1
                    elif new_upper_lane_1[-1] == 0:
                        new_upper_lane_1[-1] = 1
                    elif new_lower_lane_1[-1] == 0:
                        new_lower_lane_1[-1] = 1
            
            # Segunda carretera (inserciones por la izquierda)
            if random.random() < CAR_INSERTION_PROB:
                upper_count = np.sum(new_upper_lane_2)
                lower_count = np.sum(new_lower_lane_2)
                total_cells = NUM_CELLS * 2
                current_density = (upper_count + lower_count) / total_cells
                
                if current_density < 0.3:
                    if new_upper_lane_2[0] == 0 and new_lower_lane_2[0] == 0:
                        if upper_count <= lower_count:
                            new_upper_lane_2[0] = 1
                        else:
                            new_lower_lane_2[0] = 1
                    elif new_upper_lane_2[0] == 0:
                        new_upper_lane_2[0] = 1
                    elif new_lower_lane_2[0] == 0:
                        new_lower_lane_2[0] = 1
        
        # Asegurar que los autos descompuestos permanezcan en su lugar
        for pos in self.broken_cars_upper_1:
            new_upper_lane_1[pos] = 1
        
        for pos in self.broken_cars_lower_1:
            new_lower_lane_1[pos] = 1
        
        for pos in self.broken_cars_upper_2:
            new_upper_lane_2[pos] = 1
        
        for pos in self.broken_cars_lower_2:
            new_lower_lane_2[pos] = 1
        
        # Actualizar estado de los carriles
        self.upper_lane_1 = new_upper_lane_1
        self.lower_lane_1 = new_lower_lane_1
        self.upper_lane_2 = new_upper_lane_2
        self.lower_lane_2 = new_lower_lane_2
    
    def draw(self):
        screen.blit(road_img, (0, 0))
        
        # Obtener tiempo para efectos visuales
        current_time = pygame.time.get_ticks()
        
        # Dibujar autos en la primera carretera (derecha a izquierda)
        # Carril superior
        for i in range(NUM_CELLS):
            if self.upper_lane_1[i] == 1:
                # Oscilación vertical para efecto natural
                offset_y = int(math.sin(current_time / 500.0 + i) * 2)
                x_pos = i * CELL_SIZE
                y_pos = UPPER_LANE_1_Y + offset_y
                
                # Sombra debajo del auto
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_upper_1:
                    # Efecto de humo para autos descompuestos
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                    
                    screen.blit(broken_car1_img, (x_pos, y_pos))
                else:
                    screen.blit(car1_img, (x_pos, y_pos))
        
        # Carril inferior
        for i in range(NUM_CELLS):
            if self.lower_lane_1[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 10) * 2)
                x_pos = i * CELL_SIZE
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
                    
                    screen.blit(broken_car1_img, (x_pos, y_pos))
                else:
                    screen.blit(car1_img, (x_pos, y_pos))
        
        # Dibujar autos en la segunda carretera (izquierda a derecha)
        # Carril superior
        for i in range(NUM_CELLS):
            if self.upper_lane_2[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 20) * 2)
                x_pos = i * CELL_SIZE
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
                    
                    screen.blit(broken_car2_img, (x_pos, y_pos))
                else:
                    screen.blit(car2_img, (x_pos, y_pos))
        
        # Carril inferior
        for i in range(NUM_CELLS):
            if self.lower_lane_2[i] == 1:
                offset_y = int(math.sin(current_time / 500.0 + i + 30) * 2)
                x_pos = i * CELL_SIZE
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
                    
                    screen.blit(broken_car2_img, (x_pos, y_pos))
                else:
                    screen.blit(car2_img, (x_pos, y_pos))
        
        # Dibujar líneas de carril con efecto de movimiento
        if self.generation % 4 < 2:
            lane_marker_color = (255, 255, 255)
        else:
            lane_marker_color = (220, 220, 220)
        
        # Líneas divisorias en primera carretera
        center_y_1 = (UPPER_LANE_1_Y + LOWER_LANE_1_Y + CELL_SIZE) // 2
        for i in range(NUM_CELLS):
            # En primera carretera el movimiento es de derecha a izquierda
            marker_offset_1 = (self.generation * 2) % CELL_SIZE
            marker_x_1 = i * CELL_SIZE + marker_offset_1
            if marker_x_1 >= 0 and marker_x_1 < WIDTH:
                pygame.draw.rect(screen, lane_marker_color, (marker_x_1, center_y_1, CELL_SIZE//2, 5))
        
        # Líneas divisorias en segunda carretera
        center_y_2 = (UPPER_LANE_2_Y + LOWER_LANE_2_Y + CELL_SIZE) // 2
        for i in range(NUM_CELLS):
            # En segunda carretera el movimiento es de izquierda a derecha
            marker_offset_2 = (self.generation * 2) % CELL_SIZE
            marker_x_2 = i * CELL_SIZE - marker_offset_2
            if marker_x_2 >= 0 and marker_x_2 < WIDTH:
                pygame.draw.rect(screen, lane_marker_color, (marker_x_2, center_y_2, CELL_SIZE//2, 5))
        
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
    simulator = DoubleRoadTrafficSimulator(boundary_mode="toroid")
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
                    simulator = DoubleRoadTrafficSimulator(boundary_mode="toroid")
                elif event.key == pygame.K_n:
                    simulator = DoubleRoadTrafficSimulator(boundary_mode="null")
                elif event.key == pygame.K_r:
                    simulator = DoubleRoadTrafficSimulator(simulator.boundary_mode)
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