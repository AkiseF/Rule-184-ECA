import pygame
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, CAR_WIDTH, CAR_HEIGHT, ROAD_COLOR

class Visualization:
    def __init__(self, simulation):
        self.simulation = simulation
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Traffic Simulation")
        self.clock = pygame.time.Clock()

    def draw_car(self, x, y):
        car_image = pygame.image.load('assets/car.png')
        car_image = pygame.transform.scale(car_image, (CAR_WIDTH, CAR_HEIGHT))
        self.screen.blit(car_image, (x, y))

    def draw_road(self):
        self.screen.fill(ROAD_COLOR)

    def update(self):
        self.draw_road()
        for i in range(self.simulation.width):
            if self.simulation.lane1[i] == 1:
                self.draw_car(i * CAR_WIDTH, SCREEN_HEIGHT // 2)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.simulation.update()  # Update the simulation state
            self.update()
            self.clock.tick(150)

        pygame.quit()