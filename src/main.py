import pygame
import os
import sys
import traceback
from simulation import TrafficSimulation
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, ROAD_COLOR, GRID_WIDTH, GRID_HEIGHT, DENSITY

def main():
    try:
        pygame.init()
        
        # Ruta relativa en donde están las imágenes
        assets_dir = r"./assets"
        
        print(f"Verificando directorio de assets: {assets_dir}")
        # Verificar que el directorio assets existe
        if not os.path.exists(assets_dir):
            print(f"Error: No se encuentra el directorio de assets en: {assets_dir}")
            print("Por favor, asegúrate de que este directorio existe y contiene las imágenes necesarias")
            # Intentar crear el directorio
            os.makedirs(assets_dir, exist_ok=True)
            print(f"Se ha creado el directorio: {assets_dir}")
            print("Por favor, coloca las imágenes necesarias en este directorio.")
            input("Presiona Enter para salir...")
            return
        
        # Verificar que las imágenes existen
        required_images = ['carretera.png', '1_left.png', '2_right.png']
        missing_images = []
        
        for img in required_images:
            img_path = os.path.join(assets_dir, img)
            print(f"Verificando imagen: {img_path}")
            if not os.path.exists(img_path):
                missing_images.append(img)
        
        if missing_images:
            print(f"Error: No se encuentran las siguientes imágenes en {assets_dir}:")
            for img in missing_images:
                print(f" - {img}")
            print("Por favor, asegúrate de que todas las imágenes necesarias estén presentes.")
            input("Presiona Enter para salir...")
            return
        
        print("Todas las imágenes encontradas correctamente.")
            
        # Configurar la ruta de assets como variable global
        global ASSETS_PATH
        ASSETS_PATH = assets_dir
        
        print("Inicializando pantalla...")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Traffic Simulation - Rule 184")

        clock = pygame.time.Clock()
        
        print(f"Creando simulación con parámetros: width={GRID_WIDTH}, height={GRID_HEIGHT}, density={DENSITY}, assets_path={assets_dir}")
        simulation = TrafficSimulation(GRID_WIDTH, GRID_HEIGHT, DENSITY, assets_dir)

        print("Iniciando bucle principal...")
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            simulation.update()
            screen.fill(ROAD_COLOR)
            simulation.render(screen)
            pygame.display.flip()
            clock.tick(10)  # Velocidad de actualización

        pygame.quit()
        print("Programa terminado correctamente.")
    
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
        print("\nDetalles del error:")
        for line in traceback.format_exc().splitlines():
            print(line)
        
        # Mantener la ventana abierta para leer el error
        input("\nPresiona Enter para salir...")
        
        if pygame.get_init():
            pygame.quit()

if __name__ == "__main__":
    main()