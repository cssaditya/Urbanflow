import random
import time
import threading
import pygame
import sys

# Default values of signal timers
defaultGo = {0:10, 1:10, 2:10, 3:10}
defaultStop = 150
defaultSlow = 5

trafficLights = []
totalLights = 4
activeGreen = 0   # Indicates which signal is green currently
nextActive = (activeGreen+1)%totalLights    # Indicates which signal will turn green next
activeYellow = 0   # Indicates whether yellow signal is on or off 

vehicleSpeeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'bike':2.5}  # average speeds of vehicles

# Coordinates of vehicles' start
startX = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
startY = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

allVehicles = {'right': {0:[], 1:[], 2:[], 'passed':0}, 'down': {0:[], 1:[], 2:[], 'passed':0}, 'left': {0:[], 1:[], 2:[], 'passed':0}, 'up': {0:[], 1:[], 2:[], 'passed':0}}
vehicleCategories = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionMap = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
lightPositions = [(530,230),(810,230),(810,570),(530,570)]
timerPositions = [(530,210),(810,210),(810,550),(530,550)]

# Coordinates of stop lines
stopMarkers = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStops = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
haltGap = 25    # stopping gap
moveGap = 25   # moving gap

# set allowed vehicle types here
permittedVehicles = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowedTypes = []
turnedVehicles = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
straightVehicles = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
turnAngle = 3
midPoints = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
# set random or default green signal time here 
randomGoTimer = True
# set random green signal time range here 
randomGoRange = [10,20]

pygame.init()
simulationGroup = pygame.sprite.Group()

class LightController:
    def __init__(self, stop, slow, go):
        self.stop = stop
        self.slow = slow
        self.go = go
        self.displayText = ""
        
class MovingVehicle(pygame.sprite.Sprite):
    def __init__(self, track, vehicleType, dirIndex, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.track = track
        self.vehicleType = vehicleType
        self.speed = vehicleSpeeds[vehicleType]
        self.dirIndex = dirIndex
        self.direction = direction
        self.x = startX[direction][track]
        self.y = startY[direction][track]
        self.passed = 0
        self.willTurn = will_turn
        self.hasTurned = 0
        self.rotation = 0
        allVehicles[direction][track].append(self)
        self.position = len(allVehicles[direction][track]) - 1
        self.passedIndex = 0
        imagePath = "images/" + direction + "/" + vehicleType + ".png"
        self.originalImg = pygame.image.load(imagePath)
        self.image = pygame.image.load(imagePath)

        if(len(allVehicles[direction][track])>1 and allVehicles[direction][track][self.position-1].passed==0):   
            if(direction=='right'):
                self.stopPos = allVehicles[direction][track][self.position-1].stopPos 
                - allVehicles[direction][track][self.position-1].image.get_rect().width 
                - haltGap         
            elif(direction=='left'):
                self.stopPos = allVehicles[direction][track][self.position-1].stopPos 
                + allVehicles[direction][track][self.position-1].image.get_rect().width 
                + haltGap
            elif(direction=='down'):
                self.stopPos = allVehicles[direction][track][self.position-1].stopPos 
                - allVehicles[direction][track][self.position-1].image.get_rect().height 
                - haltGap
            elif(direction=='up'):
                self.stopPos = allVehicles[direction][track][self.position-1].stopPos 
                + allVehicles[direction][track][self.position-1].image.get_rect().height 
                + haltGap
        else:
            self.stopPos = defaultStops[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            adjustment = self.image.get_rect().width + haltGap    
            startX[direction][track] -= adjustment
        elif(direction=='left'):
            adjustment = self.image.get_rect().width + haltGap
            startX[direction][track] += adjustment
        elif(direction=='down'):
            adjustment = self.image.get_rect().height + haltGap
            startY[direction][track] -= adjustment
        elif(direction=='up'):
            adjustment = self.image.get_rect().height + haltGap
            startY[direction][track] += adjustment
        simulationGroup.add(self)

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def advance(self):
        if(self.direction=='right'):
            if(self.passed==0 and self.x+self.image.get_rect().width>stopMarkers[self.direction]):
                self.passed = 1
                allVehicles[self.direction]['passed'] += 1
                if(self.willTurn==0):
                    straightVehicles[self.direction][self.track].append(self)
                    self.passedIndex = len(straightVehicles[self.direction][self.track]) - 1
            if(self.willTurn==1):
                if(self.track == 1):
                    if(self.passed==0 or self.x+self.image.get_rect().width<stopMarkers[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stopPos or (activeGreen==0 and activeYellow==0) or self.passed==1) and (self.position==0 or self.x+self.image.get_rect().width<(allVehicles[self.direction][self.track][self.position-1].x - moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):               
                            self.x += self.speed
                    else:
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, self.rotation)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or (self.y>(turnedVehicles[self.direction][self.track][self.passedIndex-1].y + turnedVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().height + moveGap))):
                                self.y -= self.speed
                elif(self.track == 2):
                    if(self.passed==0 or self.x+self.image.get_rect().width<midPoints[self.direction]['x']):
                        if((self.x+self.image.get_rect().width<=self.stopPos or (activeGreen==0 and activeYellow==0) or self.passed==1) and (self.position==0 or self.x+self.image.get_rect().width<(allVehicles[self.direction][self.track][self.position-1].x - moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):                 
                            self.x += self.speed
                    else:
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, -self.rotation)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or ((self.y+self.image.get_rect().height)<(turnedVehicles[self.direction][self.track][self.passedIndex-1].y - moveGap))):
                                self.y += self.speed
            else: 
                if(self.passed == 0):
                    if((self.x+self.image.get_rect().width<=self.stopPos or (activeGreen==0 and activeYellow==0)) and (self.position==0 or self.x+self.image.get_rect().width<(allVehicles[self.direction][self.track][self.position-1].x - moveGap))):                
                        self.x += self.speed
                else:
                    if((self.passedIndex==0) or (self.x+self.image.get_rect().width<(straightVehicles[self.direction][self.track][self.passedIndex-1].x - moveGap))):                 
                        self.x += self.speed
        elif(self.direction=='down'):
            if(self.passed==0 and self.y+self.image.get_rect().height>stopMarkers[self.direction]):
                self.passed = 1
                allVehicles[self.direction]['passed'] += 1
                if(self.willTurn==0):
                    straightVehicles[self.direction][self.track].append(self)
                    self.passedIndex = len(straightVehicles[self.direction][self.track]) - 1
            if(self.willTurn==1):
                if(self.track == 1):
                    if(self.passed==0 or self.y+self.image.get_rect().height<stopMarkers[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stopPos or (activeGreen==1 and activeYellow==0) or self.passed==1) and (self.position==0 or self.y+self.image.get_rect().height<(allVehicles[self.direction][self.track][self.position-1].y - moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, self.rotation)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or ((self.x + self.image.get_rect().width) < (turnedVehicles[self.direction][self.track][self.passedIndex-1].x - moveGap))):
                                self.x += self.speed
                elif(self.track == 2):
                    if(self.passed==0 or self.y+self.image.get_rect().height<midPoints[self.direction]['y']):
                        if((self.y+self.image.get_rect().height<=self.stopPos or (activeGreen==1 and activeYellow==0) or self.passed==1) and (self.position==0 or self.y+self.image.get_rect().height<(allVehicles[self.direction][self.track][self.position-1].y - moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, -self.rotation)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or (self.x>(turnedVehicles[self.direction][self.track][self.passedIndex-1].x + turnedVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().width + moveGap))): 
                                self.x -= self.speed
            else: 
                if(self.passed == 0):
                    if((self.y+self.image.get_rect().height<=self.stopPos or (activeGreen==1 and activeYellow==0)) and (self.position==0 or self.y+self.image.get_rect().height<(allVehicles[self.direction][self.track][self.position-1].y - moveGap))):                
                        self.y += self.speed
                else:
                    if((self.passedIndex==0) or (self.y+self.image.get_rect().height<(straightVehicles[self.direction][self.track][self.passedIndex-1].y - moveGap))):                
                        self.y += self.speed
        elif(self.direction=='left'):
            if(self.passed==0 and self.x<stopMarkers[self.direction]):
                self.passed = 1
                allVehicles[self.direction]['passed'] += 1
                if(self.willTurn==0):
                    straightVehicles[self.direction][self.track].append(self)
                    self.passedIndex = len(straightVehicles[self.direction][self.track]) - 1
            if(self.willTurn==1):
                if(self.track == 1):
                    if(self.passed==0 or self.x>stopMarkers[self.direction]-70):
                        if((self.x>=self.stopPos or (activeGreen==2 and activeYellow==0) or self.passed==1) and (self.position==0 or self.x>(allVehicles[self.direction][self.track][self.position-1].x + allVehicles[self.direction][self.track][self.position-1].image.get_rect().width + moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, self.rotation)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or ((self.y + self.image.get_rect().height) <(turnedVehicles[self.direction][self.track][self.passedIndex-1].y  -  moveGap))):
                                self.y += self.speed
                elif(self.track == 2):
                    if(self.passed==0 or self.x>midPoints[self.direction]['x']):
                        if((self.x>=self.stopPos or (activeGreen==2 and activeYellow==0) or self.passed==1) and (self.position==0 or self.x>(allVehicles[self.direction][self.track][self.position-1].x + allVehicles[self.direction][self.track][self.position-1].image.get_rect().width + moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):                
                            self.x -= self.speed
                    else:
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, -self.rotation)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or (self.y>(turnedVehicles[self.direction][self.track][self.passedIndex-1].y + turnedVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().height +  moveGap))):
                                self.y -= self.speed
            else: 
                if(self.passed == 0):
                    if((self.x>=self.stopPos or (activeGreen==2 and activeYellow==0)) and (self.position==0 or self.x>(allVehicles[self.direction][self.track][self.position-1].x + allVehicles[self.direction][self.track][self.position-1].image.get_rect().width + moveGap))):                
                        self.x -= self.speed
                else:
                    if((self.passedIndex==0) or (self.x>(straightVehicles[self.direction][self.track][self.passedIndex-1].x + straightVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().width + moveGap))):                
                        self.x -= self.speed
        elif(self.direction=='up'):
            if(self.passed==0 and self.y<stopMarkers[self.direction]):
                self.passed = 1
                allVehicles[self.direction]['passed'] += 1
                if(self.willTurn==0):
                    straightVehicles[self.direction][self.track].append(self)
                    self.passedIndex = len(straightVehicles[self.direction][self.track]) - 1
            if(self.willTurn==1):
                if(self.track == 1):
                    if(self.passed==0 or self.y>stopMarkers[self.direction]-60):
                        if((self.y>=self.stopPos or (activeGreen==3 and activeYellow==0) or self.passed == 1) and (self.position==0 or self.y>(allVehicles[self.direction][self.track][self.position-1].y + allVehicles[self.direction][self.track][self.position-1].image.get_rect().height +  moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, self.rotation)
                            self.x -= 2
                            self.y -= 1.2
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or (self.x>(turnedVehicles[self.direction][self.track][self.passedIndex-1].x + turnedVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().width + moveGap))):
                                self.x -= self.speed
                elif(self.track == 2):
                    if(self.passed==0 or self.y>midPoints[self.direction]['y']):
                        if((self.y>=self.stopPos or (activeGreen==3 and activeYellow==0) or self.passed == 1) and (self.position==0 or self.y>(allVehicles[self.direction][self.track][self.position-1].y + allVehicles[self.direction][self.track][self.position-1].image.get_rect().height +  moveGap) or allVehicles[self.direction][self.track][self.position-1].hasTurned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.hasTurned==0):
                            self.rotation += turnAngle
                            self.image = pygame.transform.rotate(self.originalImg, -self.rotation)
                            self.x += 1
                            self.y -= 1
                            if(self.rotation==90):
                                self.hasTurned = 1
                                turnedVehicles[self.direction][self.track].append(self)
                                self.passedIndex = len(turnedVehicles[self.direction][self.track]) - 1
                        else:
                            if(self.passedIndex==0 or (self.x<(turnedVehicles[self.direction][self.track][self.passedIndex-1].x - turnedVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().width - moveGap))):
                                self.x += self.speed
            else: 
                if(self.passed == 0):
                    if((self.y>=self.stopPos or (activeGreen==3 and activeYellow==0)) and (self.position==0 or self.y>(allVehicles[self.direction][self.track][self.position-1].y + allVehicles[self.direction][self.track][self.position-1].image.get_rect().height + moveGap))):                
                        self.y -= self.speed
                else:
                    if((self.passedIndex==0) or (self.y>(straightVehicles[self.direction][self.track][self.passedIndex-1].y + straightVehicles[self.direction][self.track][self.passedIndex-1].image.get_rect().height + moveGap))):                
                        self.y -= self.speed 

# Initialization of signals with default values
def setup():
    minTime = randomGoRange[0]
    maxTime = randomGoRange[1]
    if(randomGoTimer):
        light1 = LightController(0, defaultSlow, random.randint(minTime,maxTime))
        trafficLights.append(light1)
        light2 = LightController(light1.stop+light1.slow+light1.go, defaultSlow, random.randint(minTime,maxTime))
        trafficLights.append(light2)
        light3 = LightController(defaultStop, defaultSlow, random.randint(minTime,maxTime))
        trafficLights.append(light3)
        light4 = LightController(defaultStop, defaultSlow, random.randint(minTime,maxTime))
        trafficLights.append(light4)
    else:
        light1 = LightController(0, defaultSlow, defaultGo[0])
        trafficLights.append(light1)
        light2 = LightController(light1.slow+light1.go, defaultSlow, defaultGo[1])
        trafficLights.append(light2)
        light3 = LightController(defaultStop, defaultSlow, defaultGo[2])
        trafficLights.append(light3)
        light4 = LightController(defaultStop, defaultSlow, defaultGo[3])
        trafficLights.append(light4)
    cycleLights()

def cycleLights():
    global activeGreen, activeYellow, nextActive
    while(trafficLights[activeGreen].go>0):   # while the timer of current green signal is not zero
        updateTimers()
        time.sleep(1)
    activeYellow = 1   # set yellow signal on
    # reset stop coordinates of lanes and vehicles 
    for i in range(0,3):
        for vehicle in allVehicles[directionMap[activeGreen]][i]:
            vehicle.stopPos = defaultStops[directionMap[activeGreen]]
    while(trafficLights[activeGreen].slow>0):  # while the timer of current yellow signal is not zero
        updateTimers()
        time.sleep(1)
    activeYellow = 0   # set yellow signal off
    
    # reset all signal times of current signal to default/random times
    if(randomGoTimer):
        trafficLights[activeGreen].go = random.randint(randomGoRange[0],randomGoRange[1])
    else:
        trafficLights[activeGreen].go = defaultGo[activeGreen]
    trafficLights[activeGreen].slow = defaultSlow
    trafficLights[activeGreen].stop = defaultStop
       
    activeGreen = nextActive # set next signal as green signal
    nextActive = (activeGreen+1)%totalLights    # set next green signal
    trafficLights[nextActive].stop = trafficLights[activeGreen].slow+trafficLights[activeGreen].go    # set the red time of next to next signal as (yellow time + green time) of next signal
    cycleLights()  

# Update values of the signal timers after every second
def updateTimers():
    for i in range(0, totalLights):
        if(i==activeGreen):
            if(activeYellow==0):
                trafficLights[i].go-=1
            else:
                trafficLights[i].slow-=1
        else:
            trafficLights[i].stop-=1

# Generating vehicles in the simulation
def createVehicles():
    while(True):
        vehicleType = random.choice(allowedTypes)
        laneNum = random.randint(1,2)
        will_turn = 0
        if(laneNum == 1):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        elif(laneNum == 2):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        temp = random.randint(0,99)
        dirIndex = 0
        dist = [25,50,75,100]
        if(temp<dist[0]):
            dirIndex = 0
        elif(temp<dist[1]):
            dirIndex = 1
        elif(temp<dist[2]):
            dirIndex = 2
        elif(temp<dist[3]):
            dirIndex = 3
        MovingVehicle(laneNum, vehicleCategories[vehicleType], dirIndex, directionMap[dirIndex], will_turn)
        time.sleep(1)

class Simulation:
    global allowedTypes
    i = 0
    for vehicleType in permittedVehicles:
        if(permittedVehicles[vehicleType]):
            allowedTypes.append(i)
        i += 1
    thread1 = threading.Thread(name="setup",target=setup, args=())    # initialization
    thread1.daemon = True
    thread1.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("TRAFFIC SIMULATION")

    # Loading signal images and font
    stopSignal = pygame.image.load('images/signals/red.png')
    slowSignal = pygame.image.load('images/signals/yellow.png')
    goSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    thread2 = threading.Thread(name="createVehicles",target=createVehicles, args=())    # Generating vehicles
    thread2.daemon = True
    thread2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        for i in range(0,totalLights):  # display signal and set timer according to current status: green, yello, or red
            if(i==activeGreen):
                if(activeYellow==1):
                    trafficLights[i].displayText = trafficLights[i].slow
                    screen.blit(slowSignal, lightPositions[i])
                else:
                    trafficLights[i].displayText = trafficLights[i].go
                    screen.blit(goSignal, lightPositions[i])
            else:
                if(trafficLights[i].stop<=10):
                    trafficLights[i].displayText = trafficLights[i].stop
                else:
                    trafficLights[i].displayText = "---"
                screen.blit(stopSignal, lightPositions[i])
        timerTexts = ["","","",""]

        # display signal timer
        for i in range(0,totalLights):  
            timerTexts[i] = font.render(str(trafficLights[i].displayText), True, white, black)
            screen.blit(timerTexts[i],timerPositions[i])

        # display the vehicles
        for vehicle in simulationGroup:  
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.advance()
        pygame.display.update()


Simulation()