import numpy as np
import pygame
import os
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, LANE_CHANGE_PROBABILITY, CAR_SIZE

class TrafficSimulation:
    def __init__(self, width, height, density=0.5, assets_path=None):
        """
        Inicializa la simulación de tráfico bidireccional con la Regla 184 y carriles dobles.
        
        Args:
            width: Ancho de la cuadrícula (número de celdas)
            height: Altura de la simulación (número de pasos de tiempo)
            density: Densidad inicial de vehículos (0-1)
            assets_path: Ruta al directorio de assets
        """
        self.width = width
        self.height = height
        self.density = density
        self.assets_path = assets_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
        
        # Inicializar dos carriles dobles
        # Carril superior: dos carriles de derecha a izquierda
        self.upper_lane1 = np.zeros(width, dtype=int)  # Carril superior interno
        self.upper_lane2 = np.zeros(width, dtype=int)  # Carril superior externo
        
        # Carril inferior: dos carriles de izquierda a derecha
        self.lower_lane1 = np.zeros(width, dtype=int)  # Carril inferior interno
        self.lower_lane2 = np.zeros(width, dtype=int)  # Carril inferior externo
        
        # Colocar vehículos aleatoriamente según la densidad
        for i in range(width):
            if np.random.random() < density:
                # Colocamos en uno u otro carril del mismo sentido
                if np.random.random() < 0.5:
                    self.upper_lane1[i] = 1
                else:
                    self.upper_lane2[i] = 1
                    
            if np.random.random() < density:
                # Colocamos en uno u otro carril del mismo sentido
                if np.random.random() < 0.5:
                    self.lower_lane1[i] = 1
                else:
                    self.lower_lane2[i] = 1
        
        # Para la animación
        self.current_step = 0
        
        # Cargar imágenes con la ruta absoluta
        try:
            self.road_img = pygame.image.load(os.path.join(self.assets_path, 'carretera.png'))
            self.road_img = pygame.transform.scale(self.road_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            self.car_upper_img = pygame.image.load(os.path.join(self.assets_path, '1_left.png'))
            self.car_upper_img = pygame.transform.scale(self.car_upper_img, (CELL_SIZE, CELL_SIZE))
            
            self.car_lower_img = pygame.image.load(os.path.join(self.assets_path, '2_right.png'))
            self.car_lower_img = pygame.transform.scale(self.car_lower_img, (CELL_SIZE, CELL_SIZE))
            
            print("Imágenes cargadas y escaladas correctamente")
        except pygame.error as e:
            print(f"Error al cargar imágenes: {e}")
            print(f"Ruta de assets utilizada: {self.assets_path}")
            print("Asegúrate de que las imágenes existen y tienen el formato correcto.")
            raise
    
    def apply_rule184(self, lane, reverse=False):
        """
        Aplica la regla 184 al carril.
        
        Args:
            lane: Estado actual del carril
            reverse: Si True, aplica la regla para movimiento de derecha a izquierda
        
        Returns:
            Nuevo estado del carril
        """
        new_lane = np.copy(lane)
        size = len(lane)
        
        if not reverse:  # izquierda a derecha
            for i in range(size):
                # Para la regla 184: un carro se mueve a la derecha si hay espacio
                if lane[i] == 1 and lane[(i+1) % size] == 0:
                    new_lane[i] = 0
                    new_lane[(i+1) % size] = 1
                elif lane[i] == 1 and lane[(i+1) % size] == 1:
                    new_lane[i] = 1  # El carro se queda en su lugar si hay otro carro adelante
        else:  # derecha a izquierda
            for i in range(size-1, -1, -1):
                # Para la regla 184 inversa: un carro se mueve a la izquierda si hay espacio
                if lane[i] == 1 and lane[(i-1) % size] == 0:
                    new_lane[i] = 0
                    new_lane[(i-1) % size] = 1
                elif lane[i] == 1 and lane[(i-1) % size] == 1:
                    new_lane[i] = 1  # El carro se queda en su lugar si hay otro carro adelante
        
        return new_lane
    
    def handle_lane_changes(self, lane1, lane2, reverse=False):
        """
        Maneja los cambios de carril entre carriles del mismo sentido.
        
        Args:
            lane1: Primer carril
            lane2: Segundo carril
            reverse: Si True, los vehículos van de derecha a izquierda
            
        Returns:
            Tupla con los nuevos estados de ambos carriles
        """
        new_lane1 = np.copy(lane1)
        new_lane2 = np.copy(lane2)
        size = len(lane1)
        
        for i in range(size):
            # Probabilidad de cambio de carril del 0.2%
            if np.random.random() < LANE_CHANGE_PROBABILITY:
                # Intentar cambio de carril 1 a carril 2
                if lane1[i] == 1 and lane2[i] == 0:
                    # Verificar si hay espacio para el cambio:
                    # En el carril destino no debe haber auto en posición actual ni en adyacentes
                    if (lane2[(i-1) % size] == 0 and lane2[(i+1) % size] == 0):
                        new_lane1[i] = 0
                        new_lane2[i] = 1
                
                # Intentar cambio de carril 2 a carril 1
                elif lane2[i] == 1 and lane1[i] == 0:
                    # Verificar si hay espacio para el cambio:
                    # En el carril destino no debe haber auto en posición actual ni en adyacentes
                    if (lane1[(i-1) % size] == 0 and lane1[(i+1) % size] == 0):
                        new_lane2[i] = 0
                        new_lane1[i] = 1
        
        return new_lane1, new_lane2
    
    def update(self):
        """Actualiza la simulación aplicando la regla 184 y manejando cambios de carril"""
        # Primero, intentar cambios de carril
        # (Esto se implementará más adelante)
        
        # Luego, aplicar regla 184 para el movimiento en cada carril
        self.upper_lane1 = self.apply_rule184(self.upper_lane1, reverse=True)
        self.upper_lane2 = self.apply_rule184(self.upper_lane2, reverse=True)
        self.lower_lane1 = self.apply_rule184(self.lower_lane1, reverse=False)
        self.lower_lane2 = self.apply_rule184(self.lower_lane2, reverse=False)
        
        self.current_step += 1

    def render(self, screen):
        """
        Dibuja el estado actual de la simulación en la pantalla de pygame.
        
        Args:
            screen: Superficie de pygame donde dibujar
        """
        # Dibujar la carretera como fondo
        screen.blit(self.road_img, (0, 0))
        
        # Posiciones Y para cada carril (valores exactos proporcionados)
        # Primer doble carril (superior, dirección derecha a izquierda)
        upper_lane1_y = 0  # Primer carril del doble carril superior
        upper_lane2_y = 59.1  # Segundo carril del doble carril superior
        
        # Segundo doble carril (inferior, dirección izquierda a derecha)
        lower_lane1_y = 175.8  # Primer carril del doble carril inferior
        lower_lane2_y = 234.9  # Segundo carril del doble carril inferior
        
        # Centrar verticalmente en el carril (el alto de cada carril es 67.1px)
        upper_lane1_y_centered = upper_lane1_y + (67.1 / 2) - (CAR_SIZE / 2)
        upper_lane2_y_centered = upper_lane2_y + (67.1 / 2) - (CAR_SIZE / 2)
        lower_lane1_y_centered = lower_lane1_y + (67.1 / 2) - (CAR_SIZE / 2)
        lower_lane2_y_centered = lower_lane2_y + (67.1 / 2) - (CAR_SIZE / 2)
        
        # Dibujar vehículos en carril superior (derecha a izquierda)
        for i in range(self.width):
            # Posición X basada en el índice de la celda y el tamaño de celda
            x = i * CELL_SIZE
            
            if self.upper_lane1[i] == 1:
                screen.blit(self.car_upper_img, (x, upper_lane1_y_centered))
            if self.upper_lane2[i] == 1:
                screen.blit(self.car_upper_img, (x, upper_lane2_y_centered))
        
        # Dibujar vehículos en carril inferior (izquierda a derecha)
        for i in range(self.width):
            # Posición X basada en el índice de la celda y el tamaño de celda
            x = i * CELL_SIZE
            
            if self.lower_lane1[i] == 1:
                screen.blit(self.car_lower_img, (x, lower_lane1_y_centered))
            if self.lower_lane2[i] == 1:
                screen.blit(self.car_lower_img, (x, lower_lane2_y_centered))
        
        # Mostrar estadísticas
        font = pygame.font.SysFont('Arial', 16)
        text = font.render(f"Step: {self.current_step} | Density: {self.density}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        # Dibujar grid (opcional, para debugging)
        if False:  # Cambiar a True para ver el grid
            for i in range(self.width + 1):
                pygame.draw.line(screen, (100, 100, 100), (i * CELL_SIZE, 0), (i * CELL_SIZE, SCREEN_HEIGHT), 1)