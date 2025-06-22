import pygame
import numpy as np
import random
import os
import math

# Inicializar pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 1500, 140
CELL_SIZE = 60
NUM_CELLS = 50
UPPER_LANE_Y = 10
LOWER_LANE_Y = 70
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
pygame.display.set_caption("Simulador de Tráfico Regla 184")

# Cargar imágenes
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
road_img = pygame.image.load(os.path.join(parent_dir, "./assets/carril.png"))
# Crear versiones mejoradas de los coches
car_img = pygame.image.load(os.path.join(parent_dir, "./assets/1_left.png"))
car_img = pygame.transform.scale(car_img, (CELL_SIZE, CELL_SIZE))

# Versión mejorada para autos descompuestos - copia profunda para no modificar el original
broken_car_img = car_img.copy()

# Aplicar un tinte rojo a los autos descompuestos
red_overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
red_overlay.fill((255, 0, 0, 100))
broken_car_img.blit(red_overlay, (0, 0))

road_img = pygame.transform.scale(road_img, (WIDTH, HEIGHT))

class TrafficSimulator:
    def __init__(self, boundary_mode="toroid"):
        # Inicializar carriles (0 = vacío, 1 = auto)
        self.upper_lane = np.zeros(NUM_CELLS, dtype=int)
        self.lower_lane = np.zeros(NUM_CELLS, dtype=int)
        
        # Distribuir autos de manera más uniforme para evitar atascos
        # Esto crea un patrón más fluido desde el principio
        density = 0.3  # 30% de ocupación
        
        # Usamos un espaciado aproximadamente uniforme
        spacing = int(1/density)
        offset = random.randint(0, spacing-1)
        
        for i in range(NUM_CELLS):
            # Carril superior
            if (i + offset) % spacing == 0:
                self.upper_lane[i] = 1
            
            # Carril inferior - usamos un offset diferente para evitar patrones idénticos
            lower_offset = (offset + spacing//2) % spacing
            if (i + lower_offset) % spacing == 0:
                self.lower_lane[i] = 1
        
        # Añadir algo de aleatoriedad para romper patrones rígidos
        for i in range(NUM_CELLS):
            if random.random() < 0.1:  # 10% de probabilidad de cambiar
                self.upper_lane[i] = 1 - self.upper_lane[i]  # Invierte el estado
            if random.random() < 0.1:
                self.lower_lane[i] = 1 - self.lower_lane[i]
        
        self.broken_cars_upper = {}  # Posición -> generaciones restantes
        self.broken_cars_lower = {}  # Posición -> generaciones restantes
        
        self.generation = 0
        self.boundary_mode = boundary_mode  # "toroid" o "null"
        
        # Intentar cargar una fuente que soporte Unicode
        try:
            self.font = pygame.font.SysFont("Arial", 18)  # Arial suele soportar más símbolos
        except:
            self.font = pygame.font.SysFont(None, 24)  # Fuente por defecto si no se encuentra Arial
            
        # Añadir atributo para la velocidad de simulación
        self.simulation_speed = 10  # Velocidad predeterminada
    
    def apply_rule_184(self, lane):
        """Aplicar Regla 184 al carril y retornar el nuevo estado."""
        new_lane = np.zeros_like(lane)
        
        for i in range(len(lane)):
            if self.boundary_mode == "toroid":
                left = lane[(i - 1) % len(lane)]
                center = lane[i]
                right = lane[(i + 1) % len(lane)]
            else:  # frontera nula
                left = lane[i - 1] if i > 0 else 0
                center = lane[i]
                right = lane[i + 1] if i < len(lane) - 1 else 0
            
            # Tabla de búsqueda para Regla 184
            # 111 -> 0
            # 110 -> 1
            # 101 -> 0
            # 100 -> 1
            # 011 -> 1
            # 010 -> 0
            # 001 -> 1
            # 000 -> 0
            pattern = (left << 2) | (center << 1) | right
            rule_output = {
                0: 0, 1: 1, 2: 0, 3: 1,
                4: 1, 5: 0, 6: 1, 7: 0
            }
            new_lane[i] = rule_output[pattern]
        
        # En modo toroide, garantizamos que los coches que salen por la derecha 
        # aparecen por la izquierda manteniendo el número total de coches
        if self.boundary_mode == "toroid":
            if np.sum(lane) != np.sum(new_lane):
                # Si hay un coche que desaparece, lo insertamos al inicio
                if lane[-1] == 1 and new_lane[-1] == 0 and new_lane[0] == 0:
                    new_lane[0] = 1
    
        return new_lane
    
    def handle_broken_cars(self):
        # Procesar autos descompuestos en el carril superior
        broken_cars_to_remove_upper = []
        for pos, remaining in list(self.broken_cars_upper.items()):
            if remaining <= 1:
                # Intento de reparación del auto
                if random.random() < REPAIR_PROB:
                    # Auto reparado, permanece en el carril
                    pass
                else:
                    # Auto es remolcado
                    self.upper_lane[pos] = 0
                broken_cars_to_remove_upper.append(pos)
            else:
                self.broken_cars_upper[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_upper:
            del self.broken_cars_upper[pos]
        
        # Procesar autos descompuestos en el carril inferior
        broken_cars_to_remove_lower = []
        for pos, remaining in list(self.broken_cars_lower.items()):
            if remaining <= 1:
                # Intento de reparación del auto
                if random.random() < REPAIR_PROB:
                    # Auto reparado, permanece en el carril
                    pass
                else:
                    # Auto es remolcado
                    self.lower_lane[pos] = 0
                broken_cars_to_remove_lower.append(pos)
            else:
                self.broken_cars_lower[pos] = remaining - 1
        
        for pos in broken_cars_to_remove_lower:
            del self.broken_cars_lower[pos]
    
    def update(self):
        self.generation += 1
        
        # Procesar primero los autos descompuestos
        self.handle_broken_cars()
        
        # Calcular nuevos carriles sin considerar cambios de carril primero
        new_upper_lane = self.apply_rule_184(self.upper_lane)
        new_lower_lane = self.apply_rule_184(self.lower_lane)
        
        # Ahora verificar cambios de carril y averías de autos
        # Necesitamos almacenarlos para aplicarlos todos a la vez después de aplicar la regla
        upper_to_lower = []  # Posiciones en carril superior que mueven al inferior
        lower_to_upper = []  # Posiciones en carril inferior que mueven al superior
        new_breakdowns_upper = []  # Nuevas averías en carril superior
        new_breakdowns_lower = []  # Nuevas averías en carril inferior
        
        # Revisar carril superior para cambios de carril y averías
        for i in range(NUM_CELLS):
            if new_upper_lane[i] == 1 and i not in self.broken_cars_upper:
                # Verificar si el coche está bloqueado por uno descompuesto adelante
                is_blocked = False
                if i < NUM_CELLS - 1 and i + 1 in self.broken_cars_upper:
                    is_blocked = True
                
                if is_blocked:
                    # Coche bloqueado por uno descompuesto
                    decision = random.random()
                    if decision < 0.2:
                        # Decide esperar (20% probabilidad)
                        pass
                    elif decision < 0.7 and new_lower_lane[i] == 0:  # 50% de probabilidad de cambiar carril
                        # Intenta cambiar de carril
                        upper_to_lower.append(i)
                else:
                    # Comportamiento normal si no está bloqueado
                    if random.random() < CAR_CHANGE_LANE_PROB and new_lower_lane[i] == 0:
                        upper_to_lower.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_upper.append(i)
        
        # Revisar carril inferior para cambios de carril y averías
        for i in range(NUM_CELLS):
            if new_lower_lane[i] == 1 and i not in self.broken_cars_lower:
                # Verificar si el coche está bloqueado por uno descompuesto adelante
                is_blocked = False
                if i < NUM_CELLS - 1 and i + 1 in self.broken_cars_lower:
                    is_blocked = True
                
                if is_blocked:
                    # Coche bloqueado por uno descompuesto
                    decision = random.random()
                    if decision < 0.2:
                        # Decide esperar (20% probabilidad)
                        pass
                    elif decision < 0.7 and new_upper_lane[i] == 0:  # 50% de probabilidad de cambiar carril
                        # Intenta cambiar de carril
                        lower_to_upper.append(i)
                else:
                    # Comportamiento normal si no está bloqueado
                    if random.random() < CAR_CHANGE_LANE_PROB and new_upper_lane[i] == 0:
                        lower_to_upper.append(i)
                    elif random.random() < CAR_BREAKDOWN_PROB:
                        new_breakdowns_lower.append(i)
        
        # Aplicar cambios de carril
        for i in upper_to_lower:
            new_upper_lane[i] = 0
            new_lower_lane[i] = 1
        
        for i in lower_to_upper:
            new_lower_lane[i] = 0
            new_upper_lane[i] = 1
        
        # Aplicar nuevas averías
        for i in new_breakdowns_upper:
            self.broken_cars_upper[i] = REPAIR_ATTEMPTS
        
        for i in new_breakdowns_lower:
            self.broken_cars_lower[i] = REPAIR_ATTEMPTS
        
        # Manejar inserciones en frontera nula si es necesario
        if self.boundary_mode == "null":
            # Insertamos autos al inicio con probabilidad ajustada para mantener flujo
            if random.random() < CAR_INSERTION_PROB:
                # Elegir el carril con menos autos para equilibrar
                upper_count = np.sum(new_upper_lane)
                lower_count = np.sum(new_lower_lane)
                
                # Limitamos la inserción basada en la densidad deseada
                total_cells = NUM_CELLS * 2  # Total de celdas en ambos carriles
                current_density = (upper_count + lower_count) / total_cells
                
                if current_density < 0.3:  # Solo insertar si la densidad es menor al 30%
                    # Si ambos tienen espacio al inicio
                    if new_upper_lane[0] == 0 and new_lower_lane[0] == 0:
                        if upper_count <= lower_count:
                            new_upper_lane[0] = 1
                        else:
                            new_lower_lane[0] = 1
                    # Si solo el carril superior tiene espacio
                    elif new_upper_lane[0] == 0:
                        new_upper_lane[0] = 1
                    # Si solo el carril inferior tiene espacio
                    elif new_lower_lane[0] == 0:
                        new_lower_lane[0] = 1
    
        # Asegurarnos que los autos descompuestos permanezcan en su lugar
        for pos in self.broken_cars_upper:
            new_upper_lane[pos] = 1
        
        for pos in self.broken_cars_lower:
            new_lower_lane[pos] = 1
        
        self.upper_lane = new_upper_lane
        self.lower_lane = new_lower_lane
    
    def draw(self):
        screen.blit(road_img, (0, 0))
        
        # Obtener tiempo para efectos visuales
        current_time = pygame.time.get_ticks()
        
        # Dibujar autos en el carril superior con leve efecto de movimiento
        for i in range(NUM_CELLS):
            if self.upper_lane[i] == 1:
                # Pequeña oscilación vertical para efecto natural
                offset_y = int(math.sin(current_time / 500.0 + i) * 2)
                x_pos = i * CELL_SIZE
                y_pos = UPPER_LANE_Y + offset_y
                
                # Dibujar sombra debajo del auto para efecto de profundidad
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_upper:
                    # Para autos descompuestos, añadir efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                        
                    screen.blit(broken_car_img, (x_pos, y_pos))
                else:
                    screen.blit(car_img, (x_pos, y_pos))
        
        # Dibujar autos en el carril inferior con leve efecto de movimiento
        for i in range(NUM_CELLS):
            if self.lower_lane[i] == 1:
                # Pequeña oscilación vertical para efecto natural
                offset_y = int(math.sin(current_time / 500.0 + i + 10) * 2)
                x_pos = i * CELL_SIZE
                y_pos = LOWER_LANE_Y + offset_y
                
                # Dibujar sombra debajo del auto para efecto de profundidad
                shadow = pygame.Surface((CELL_SIZE - 10, 10))
                shadow.fill((30, 30, 30))
                shadow.set_alpha(100)
                screen.blit(shadow, (x_pos + 5, y_pos + CELL_SIZE - 5))
                
                if i in self.broken_cars_lower:
                    # Para autos descompuestos, añadir efecto de humo
                    for _ in range(3):
                        smoke_x = x_pos + random.randint(CELL_SIZE//2, CELL_SIZE)
                        smoke_y = y_pos + random.randint(5, 15)
                        smoke_size = random.randint(5, 10)
                        smoke_alpha = random.randint(50, 150)
                        smoke = pygame.Surface((smoke_size, smoke_size))
                        smoke.fill(WHITE)
                        smoke.set_alpha(smoke_alpha)
                        screen.blit(smoke, (smoke_x, smoke_y))
                        
                    screen.blit(broken_car_img, (x_pos, y_pos))
                else:
                    screen.blit(car_img, (x_pos, y_pos))
        
        # Dibujar contador de generaciones con efecto de resaltado
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

        # Instrucciones - mostradas horizontalmente con fondo semi-transparente
        instructions = [
            "Espacio: Pausar/Reanudar",
            "T: Toroide",
            "N: Frontera nula",
            "R: Reiniciar",
            f"↑/↓: Vel({self.simulation_speed})"
        ]
        
        # Crear un fondo semi-transparente para todas las instrucciones
        total_width = 0
        for instruction in instructions:
            text = self.font.render(instruction, True, BLACK)  # Usar self.font en lugar de simulator.font
            total_width += text.get_width() + 20
        
        instruction_bg = pygame.Surface((total_width, 30))
        instruction_bg.fill((240, 240, 240))
        instruction_bg.set_alpha(180)
        screen.blit(instruction_bg, (200, 2))
        
        # Mostrar instrucciones en línea horizontal
        x_offset = 210  # Posición inicial después del contador de generaciones
        for instruction in instructions:
            text = self.font.render(instruction, True, BLACK)  # Usar self.font en lugar de simulator.font
            screen.blit(text, (x_offset, 8))
            x_offset += text.get_width() + 20  # Espacio entre instrucciones

def main():
    simulator = TrafficSimulator(boundary_mode="toroid")  # Modo predeterminado
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
                    simulator = TrafficSimulator(boundary_mode="toroid")
                elif event.key == pygame.K_n:
                    simulator = TrafficSimulator(boundary_mode="null")
                elif event.key == pygame.K_r:
                    simulator = TrafficSimulator(simulator.boundary_mode)
                elif event.key == pygame.K_UP:
                    # Aumentar la velocidad de simulación
                    simulator.simulation_speed = min(simulator.simulation_speed + 2, 30)
                elif event.key == pygame.K_DOWN:
                    # Disminuir la velocidad de simulación
                    simulator.simulation_speed = max(simulator.simulation_speed - 2, 1)
        
        if not paused:
            simulator.update()
        
        simulator.draw()
        
        pygame.display.flip()
        clock.tick(simulator.simulation_speed)  # Usar simulator.simulation_speed
    
    pygame.quit()

if __name__ == "__main__":
    main()