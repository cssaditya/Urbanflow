import pygame
import sys
import random
import time
from threading import Thread

# Initialize pygame
pygame.init()

# Define screen dimensions
WIDTH, HEIGHT = 1500, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Traffic Simulator")

# Define colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
FARM_GREEN = (34, 139, 34)  # Green color for farms
ASH = (178, 190, 181)  # Ash color (light gray)
BLUE = (0, 0, 255)  # Blue color

# Load bike images
bike_images = [
    pygame.image.load(f'bike{i}.png') for i in range(1, 6)
]

# Load car images
car_images = [
    pygame.image.load(f'car{i}.png') for i in range(1, 7)
]

# Load truck images
truck_images = [
    pygame.image.load(f'bus{i}.png') for i in range(1, 3)  # Assuming 3 truck images
]

# Define font
font = pygame.font.SysFont(None, 35)

# Traffic Light Class with dynamic timing
class TrafficLight:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.state = 'RED'  # Initial state is RED
        self.direction = direction  # Direction for the traffic light

    def change_state(self, state):
        self.state = state

    def draw(self):
        # Draw the traffic light base (rectangular shape)
        pygame.draw.rect(screen, ASH, (self.x - 15, self.y - 50, 30, 100))  # Base
        # Draw the three lights
        light_radius = 10
        light_spacing = 30
        # Red light
        color = RED if self.state == 'RED' else BLACK
        pygame.draw.circle(screen, color, (self.x, self.y - 30), light_radius)
        # Yellow light
        color = YELLOW if self.state == 'ORANGE' else BLACK
        pygame.draw.circle(screen, color, (self.x, self.y), light_radius)
        # Green light
        color = GREEN if self.state == 'GREEN' else BLACK
        pygame.draw.circle(screen, color, (self.x, self.y + 30), light_radius)



# Function to draw the X road layout (updated to include divider)
def draw_x_road():
    road_width = 200  # Increased road width
    pygame.draw.rect(screen, BLACK, (WIDTH//2 - road_width//2, 0, road_width, HEIGHT))  # Vertical road
    pygame.draw.rect(screen, BLACK, (0, HEIGHT//2 - road_width//2, WIDTH, road_width))  # Horizontal road
    # Vertical road stripes
    draw_lane_stripes(WIDTH//2 - road_width//2, 0, WIDTH//2 - road_width//2, HEIGHT)
    # Horizontal road stripes
    draw_lane_stripes(0, HEIGHT//2 - road_width//2, WIDTH, HEIGHT//2 - road_width//2)

# Function to draw parallel dashed lane stripes (updated to span the entire road)
def draw_lane_stripes(x1, y1, x2, y2):
    stripe_length = 30
    stripe_gap = 15
    if x1 == x2:  # Vertical road
        y = y1
        while y < y2:
            pygame.draw.rect(screen, WHITE, (x1 + 84, y, 10, stripe_length))  # Adjusted x position
            y += stripe_length + stripe_gap
    elif y1 == y2:  # Horizontal road
        x = x1
        while x < x2:
            pygame.draw.rect(screen, WHITE, (x, y1 + 84, stripe_length, 10))  # Adjusted y position
            x += stripe_length + stripe_gap

        
# Add these variables at the top of your code
last_uturn_time = time.time()  # Track the last time a U-turn was performed
uturn_interval = 7  # U-turn interval in seconds

last_right_turn_time= time.time()
right_turn_interval= 11

# Add this to the Vehicle class
class Vehicle:
    def __init__(self, x, y, direction, vehicle_type):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 2
        self.vehicle_type = vehicle_type  # 'BIKE', 'CAR', 'TRUCK'
        self.delay = 0  # Delay to stop at signals
        self.has_crossed_baseline = False  # 🚀 FIXED: Added missing attribute
        self.is_making_uturn = False  # Track if the vehicle is making a U-turn
        self.is_making_right_turn = False  # Track if the vehicle is making a right turn
        self.lane_offset = 0  # Track lane offset for U-turn

        # Select random image based on type
        if self.vehicle_type == 'BIKE':
            self.image = random.choice(bike_images)
            self.image = pygame.transform.scale(self.image, (40, 60))
        elif self.vehicle_type == 'CAR':
            self.image = random.choice(car_images)
            self.image = pygame.transform.scale(self.image, (50, 70))
        elif self.vehicle_type == 'TRUCK':
            self.image = random.choice(truck_images)
            self.image = pygame.transform.scale(self.image, (60, 80))  

        # Rotate the vehicle image based on direction
        if self.direction == 'SOUTH':
            self.image = pygame.transform.rotate(self.image, 180)
        elif self.direction == 'EAST':
            self.image = pygame.transform.rotate(self.image, 270)
        elif self.direction == 'WEST':
            self.image = pygame.transform.rotate(self.image, 90)

    def perform_right_turn(self):
        # Define the new direction after the right turn
        if self.direction == 'NORTH':
            self.direction = 'EAST'  # Turn right from NORTH to EAST
            self.lane_offset = 90  # Move to the right lane
        elif self.direction == 'EAST':
            self.direction = 'SOUTH'  # Turn right from EAST to SOUTH
            self.lane_offset = -70  # Move to the right lane
        elif self.direction == 'SOUTH':
            self.direction = 'WEST'  # Turn right from SOUTH to WEST
            self.lane_offset = 90  # Move to the right lane
        elif self.direction == 'WEST':
            self.direction = 'NORTH'  # Turn right from WEST to NORTH
            self.lane_offset = -70  # Move to the right lane

        # Adjust position to align with the new lane
        if self.direction in ['NORTH', 'SOUTH']:
            self.x += self.lane_offset  # Move horizontally into the right lane
        elif self.direction in ['EAST', 'WEST']:
            self.y += self.lane_offset  # Move vertically into the right lane

        # Rotate the vehicle image for the new direction
        if self.direction == 'NORTH':
            self.image = pygame.transform.rotate(self.image, 270)
        if self.direction == 'SOUTH':
            self.image = pygame.transform.rotate(self.image, 270)
        elif self.direction == 'EAST':
            self.image = pygame.transform.rotate(self.image, 270)
        elif self.direction == 'WEST':
            self.image = pygame.transform.rotate(self.image, 270)

        self.is_making_right_turn = False  # Reset right turn flag
       

    def move(self):
        if self.is_making_uturn:
            self.perform_uturn()
        elif self.is_making_right_turn:
            self.perform_right_turn()
        else:
            # Move the vehicle based on its current direction
            if self.direction == 'NORTH':
                self.y -= self.speed
            elif self.direction == 'SOUTH':
                self.y += self.speed
            elif self.direction == 'EAST':
                self.x += self.speed
            elif self.direction == 'WEST':
                self.x -= self.speed
                

    def perform_uturn(self):
        # Define U-turn behavior
        if self.direction == 'NORTH':
            self.direction = 'SOUTH'
            self.lane_offset = 120  # Move to the opposite lane
        elif self.direction == 'SOUTH':
            self.direction = 'NORTH'
            self.lane_offset = -120  # Move to the opposite lane
        elif self.direction == 'EAST':
            self.direction = 'WEST'
            self.lane_offset = 120  # Move to the opposite lane
        elif self.direction == 'WEST':
            self.direction = 'EAST'
            self.lane_offset = -120  # Move to the opposite lane

        # Adjust position to align with the new lane
        if self.direction in ['NORTH', 'SOUTH']:
            self.x += self.lane_offset
        elif self.direction in ['EAST', 'WEST']:
            self.y += self.lane_offset

        self.image = pygame.transform.rotate(self.image, 180)

        self.is_making_uturn = False  # Reset U-turn flag
        
    

    def draw(self):
        screen.blit(self.image, (self.x, self.y))  # Draw the vehicle image
        
def check_uturn_condition(vehicle):
    global last_uturn_time
    current_time = time.time()

    # Check if the vehicle is at the intersection
    if is_in_intersection(vehicle):
        # Check if the beside lane is empty
        if is_beside_lane_empty(vehicle):
            # Only allow 1 vehicle to make a U-turn every 10 seconds
            if current_time - last_uturn_time >= uturn_interval:
                # Randomly decide if this vehicle should make a U-turn
                if random.random() < 0.1:  # 10% chance for a U-turn
                    vehicle.is_making_uturn = True
                    last_uturn_time = current_time  # Update the last U-turn time


def is_beside_lane_empty(vehicle):
    # Define the range to check for vehicles in the beside lane
    lane_offset = 120  # Distance to the beside lane
    if vehicle.direction in ['NORTH', 'SOUTH']:
        # Check for vehicles in the beside lane (horizontal)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.x - (vehicle.x + lane_offset)) < 60 and abs(other_vehicle.y - vehicle.y) < 60:
                return False
    elif vehicle.direction in ['EAST', 'WEST']:
        # Check for vehicles in the beside lane (vertical)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.y - (vehicle.y + lane_offset)) < 60 and abs(other_vehicle.x - vehicle.x) < 60:
                return False
    return True

def check_right_turn_condition(vehicle):
    global last_right_turn_time
    current_time = time.time()

    # Check if the vehicle is at the intersection
    if is_in_intersection(vehicle):
        # Check if the right lane is empty
        if is_right_lane_empty(vehicle):
            # Only allow 1 vehicle to make a right turn every 10 seconds
            if current_time - last_right_turn_time >= uturn_interval:
                # Randomly decide if this vehicle should make a right turn
                if random.random() < 0.5:  # 50% chance for a right turn (for testing)
                    vehicle.is_making_right_turn = True
                    last_right_turn_time = current_time  # Update the last right turn time

def is_right_lane_empty(vehicle):
    # Define the range to check for vehicles in the right lane
    lane_offset = 120  # Distance to the right lane
    if vehicle.direction == 'NORTH':
        # Check for vehicles in the right lane (EAST direction)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.x - (vehicle.x + lane_offset)) < 60 and abs(other_vehicle.y - vehicle.y) < 60:
                return False
    elif vehicle.direction == 'EAST':
        # Check for vehicles in the right lane (SOUTH direction)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.y - (vehicle.y + lane_offset)) < 60 and abs(other_vehicle.x - vehicle.x) < 60:
                return False
    elif vehicle.direction == 'SOUTH':
        # Check for vehicles in the right lane (WEST direction)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.x - (vehicle.x - lane_offset)) < 60 and abs(other_vehicle.y - vehicle.y) < 60:
                return False
    elif vehicle.direction == 'WEST':
        # Check for vehicles in the right lane (NORTH direction)
        for other_vehicle in vehicles:
            if other_vehicle != vehicle and abs(other_vehicle.y - (vehicle.y - lane_offset)) < 60 and abs(other_vehicle.x - vehicle.x) < 60:
                return False
    return True

# Function to check if a vehicle has crossed the baseline
def has_crossed_baseline(vehicle):
    road_width = 200  # Width of the road
    intersection_margin = road_width // 2  # Distance from the center to the edge of the intersection

    if vehicle.direction == 'NORTH':
        return vehicle.y < HEIGHT // 2 - intersection_margin 
    elif vehicle.direction == 'SOUTH':
        return vehicle.y > HEIGHT // 2 + intersection_margin 
    elif vehicle.direction == 'EAST':
        return vehicle.x > WIDTH // 2 + intersection_margin 
    elif vehicle.direction == 'WEST':
        return vehicle.x < WIDTH // 2 - intersection_margin 
    return False

# Function to check if a vehicle has completely crossed the intersection
def has_completely_crossed(vehicle):
    if vehicle.direction == 'NORTH':
        return vehicle.y < 0  # Completely crossed the top edge
    elif vehicle.direction == 'SOUTH':
        return vehicle.y > HEIGHT  # Completely crossed the bottom edge
    elif vehicle.direction == 'EAST':
        return vehicle.x > WIDTH  # Completely crossed the right edge
    elif vehicle.direction == 'WEST':
        return vehicle.x < 0  # Completely crossed the left edge
    return False

# Function to check if a vehicle is in the intersection
def is_in_intersection(vehicle):
    road_width = 200  # Width of the road
    intersection_margin = road_width // 2  # Distance from the center to the edge of the intersection

    if vehicle.direction == 'NORTH':
        return HEIGHT // 2 - intersection_margin <= vehicle.y <= HEIGHT // 2 + intersection_margin
    elif vehicle.direction == 'SOUTH':
        return HEIGHT // 2 - intersection_margin <= vehicle.y <= HEIGHT // 2 + intersection_margin
    elif vehicle.direction == 'EAST':
        return WIDTH // 2 - intersection_margin <= vehicle.x <= WIDTH // 2 + intersection_margin
    elif vehicle.direction == 'WEST':
        return WIDTH // 2 - intersection_margin <= vehicle.x <= WIDTH // 2 + intersection_margin
    return False

# Function to check vehicle traffic light status (updated)
def check_vehicle_traffic_light(vehicle, green_direction):
    global first_vehicle_to_cross, vehicles_allowed_after_crossing, vehicles_crossed_after_first

    # Check if the vehicle is in the intersection
    in_intersection = is_in_intersection(vehicle)

    # If the light is green and the vehicle is in the correct direction, allow it to move
    for light in traffic_lights.values():
        
        if light.state == 'GREEN' and light.direction == green_direction:
            if vehicle.direction == green_direction:
                vehicle.delay = 0  # Green light in front, move
                return  # Exit the function early to avoid unnecessary checks

    # If the light is yellow, allow vehicles already in the intersection to continue
    for light in traffic_lights.values():
        if light.state != 'RED':
            if has_crossed_baseline(vehicle) or is_in_intersection(vehicle):
                vehicle.delay = 0  # Vehicle is in the intersection, keep moving
            else:
                vehicle.delay = 15  # Vehicle is approaching, stop
            return

    # If the light is red, stop vehicles in the corresponding direction
    for light in traffic_lights.values():
        if light.state == 'RED' and light.direction == vehicle.direction:
            vehicle.delay = 20  # Red light, wait for 20 seconds
            return

    # If the light is not green, check if the vehicle has crossed the baseline
    if has_crossed_baseline(vehicle):
        if first_vehicle_to_cross is None:
            first_vehicle_to_cross = vehicle  # Track the first vehicle to cross
            vehicles_crossed_after_first = 0  # Reset the counter
        vehicle.delay = 0  # No delay, keep moving
    else:
        # If there is a vehicle that has crossed the baseline, allow only 2 more vehicles to cross
        if first_vehicle_to_cross is not None:
            if vehicles_crossed_after_first < vehicles_allowed_after_crossing:
                vehicle.delay = 0  # Allow the vehicle to move
                vehicle.speed = 4  # Increase speed for the last 2 vehicles
                vehicles_crossed_after_first += 1  # Increment the counter
            else:
                vehicle.delay = 20  # Stop other vehicles
        else:
            # Normal traffic light logic for non-green lights
            for light in traffic_lights.values():
                if light.state == 'ORANGE':
                    vehicle.delay = 15  # Orange light, wait for 15 seconds
                elif light.state == 'RED' and (light.direction == vehicle.direction):
                    vehicle.delay = 20  # Red light, wait for 20 seconds

    # If the first vehicle has completely crossed the intersection, reset the tracker
    if first_vehicle_to_cross is not None and has_completely_crossed(first_vehicle_to_cross):
        first_vehicle_to_cross = None
        vehicles_crossed_after_first = 0  # Reset the counter

# Function to check if a new vehicle can be placed without overlapping
def can_place_vehicle(x, y, direction):
    for vehicle in vehicles:
        if direction == 'NORTH' or direction == 'SOUTH':
            # Check vertical overlap with a buffer zone
            if abs(vehicle.x - x) < 60 and abs(vehicle.y - y) < 120:
                return False
        elif direction == 'EAST' or direction == 'WEST':
            # Check horizontal overlap with a buffer zone
            if abs(vehicle.x - x) < 120 and abs(vehicle.y - y) < 60:
                return False
    return True

# Function to generate vehicles for all directions
def generate_vehicles():
    if len(vehicles) < 100:  # Limit total vehicles to 100
        # Randomly choose a direction (NORTH, SOUTH, EAST, WEST)
        direction = random.choice(['NORTH', 'SOUTH', 'EAST', 'WEST'])
        vehicle_type = random.choice(['BIKE', 'CAR', 'TRUCK'])

        # Define spawn positions based on direction
        if direction == 'NORTH':
            x = WIDTH // 2 - 100
            y = HEIGHT
        elif direction == 'SOUTH':
            x = WIDTH // 2 + 30
            y = 0
        elif direction == 'EAST':
            x = 0
            y = HEIGHT // 2 - 90
        elif direction == 'WEST':
            x = WIDTH
            y = HEIGHT // 2 + 30

        # Spawn the vehicle if there is no overlap
        if can_place_vehicle(x, y, direction):
            vehicles.append(Vehicle(x, y, direction, vehicle_type))

# Function to control traffic lights
def control_traffic_lights():
    global current_green, cycle_index
    while True:
        for direction, light in traffic_lights.items():
            if direction == current_green:
                light.change_state('GREEN')
                time.sleep(20)  # Green light for 20 seconds
                light.change_state('ORANGE')
                time.sleep(5)   # Orange light for 5 seconds
                light.change_state('RED')
            else:
                light.change_state('RED')
        # Cycle to the next direction
        cycle_index = (cycle_index + 1) % 4
        current_green = traffic_light_cycle[cycle_index]




# Button class for UI
class Button:
    def __init__(self, x, y, width, height, color, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Main game loop
running = True
current_green = 'WEST'  # Start with West as green
traffic_light_cycle = ['WEST', 'EAST', 'NORTH', 'SOUTH']  # Traffic light cycle order
cycle_index = 0  # Current index in the traffic light cycle

# Set up traffic lights
traffic_lights = {
    'NORTH': TrafficLight(WIDTH//2 -150, 200, 'NORTH'),
    'SOUTH': TrafficLight(WIDTH//2+ 150, HEIGHT - 200, 'SOUTH'),
    'EAST': TrafficLight(WIDTH - 600, HEIGHT//2 - 200, 'EAST'),
    'WEST': TrafficLight(600, HEIGHT//2 + 200, 'WEST')
}

# List to hold vehicles
vehicles = []

# Start traffic light control thread
traffic_light_thread = Thread(target=control_traffic_lights)
traffic_light_thread.daemon = True
traffic_light_thread.start()

# Create buttons
stop_button = Button(10, 10, 100, 50, BLACK, "Stop")
#start_button = Button(120, 10, 100, 50, BLACK, "Start")
resume_button = Button(120, 10, 100, 50, BLACK, "Resume")
fast_forward_button = Button(230, 10, 150, 50, BLACK, "Fast Forward")
slow_down_button=Button(400,10,150,50,BLACK,"Slow down")

# Simulation control variables
simulation_paused = False
simulation_speed = 2  # 1x speed by default

# Main loop
while running:
    screen.fill(FARM_GREEN)  # Green farm background
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if stop_button.is_clicked(pos):
                simulation_paused = True  # Pause the simulation
            #elif start_button.is_clicked(pos):
                #simulation_paused = False  # Start the simulation
            elif resume_button.is_clicked(pos):
                simulation_paused = False  # Resume the simulation
            elif fast_forward_button.is_clicked(pos):
                simulation_speed = 2*simulation_speed  # Double speed
            elif slow_down_button.is_clicked(pos) and simulation_speed>=2:
                simulation_speed//=2
                

    # Generate vehicles (only if simulation is not paused)
    if not simulation_paused:
        generate_vehicles()

    # Draw the road and traffic lights (always draw, even if paused)
    draw_x_road()
    for light in traffic_lights.values():
        light.draw()

    # Move and draw vehicles (only if simulation is not paused)
    if not simulation_paused:
        for vehicle in vehicles[:]:
            if not vehicle.has_crossed_baseline:
                vehicle.has_crossed_baseline = has_crossed_baseline(vehicle)
            
            check_vehicle_traffic_light(vehicle, current_green)
            

            #check_right_turn_condition(vehicle)  # Check if the vehicle should make a right turn
        
            check_uturn_condition(vehicle)  # Check if the vehicle should make a U-turn
            
            if vehicle.delay > 0:
                vehicle.delay -= 1
            else:
                vehicle.move()
            vehicle.draw()

            # Remove vehicles that have gone off screen
            if vehicle.direction == 'NORTH' and vehicle.y < 0:
                vehicles.remove(vehicle)
            elif vehicle.direction == 'SOUTH' and vehicle.y > HEIGHT:
                vehicles.remove(vehicle)
            elif vehicle.direction == 'EAST' and vehicle.x > WIDTH:
                vehicles.remove(vehicle)
            elif vehicle.direction == 'WEST' and vehicle.x < 0:
                vehicles.remove(vehicle)
    else:
        # If simulation is paused, just draw the vehicles without moving them
        for vehicle in vehicles:
            vehicle.draw()

    # Draw buttons (always draw, even if paused)
    stop_button.draw()
    resume_button.draw()
    fast_forward_button.draw()
    slow_down_button.draw()

    pygame.display.flip()
    pygame.time.Clock().tick(30 * simulation_speed)  # Adjust simulation speed
pygame.quit()
sys.exit()
