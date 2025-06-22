# Pygame Traffic Simulation

This project simulates a moving car using Pygame. The simulation represents cars with '1' and empty spaces with '0'. The car moves along a road, and the simulation updates its position based on defined rules.

## Project Structure

```
pygame-traffic-simulation
├── src
│   ├── main.py            # Entry point of the application
│   ├── simulation.py      # Manages the state of the simulation
│   ├── visualization.py    # Handles rendering using Pygame
│   └── utils
│       └── constants.py   # Contains constants used throughout the project
├── assets
│   ├── car.png            # Image asset for the car
│   └── road.png           # Image asset for the road background
├── requirements.txt       # Lists dependencies required for the project
└── README.md              # Documentation for the project
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pygame-traffic-simulation
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the simulation, execute the following command:
```
python src/main.py
```

## Assets

Make sure to include the necessary image assets (`car.png` and `road.png`) in the `assets` directory for the simulation to display correctly.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.