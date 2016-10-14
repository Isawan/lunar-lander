# -*- coding: utf-8 -*-
import numpy as np
import time,pygame,sys,math,random
import matplotlib.pyplot as plt

pygame.init()

# Simulation constants
INIT_HEIGHT = 100.0
MASS_PER_THRUST = 0.01 # Constant determining force per kg of fuel used
MAX_THRUST = 5000.0
timestep = 0.1
g = np.array([0,-1])
angle_tol = math.pi / 6
vel_tol = 2

# GUI constants
WIDTH = 720
HEIGHT = 480
PANEL_WIDTH = 120
PANEL_HEIGHT = HEIGHT
VIEW_WIDTH = WIDTH - PANEL_WIDTH
VIEW_HEIGHT = HEIGHT
ZOOM_HEIGHT = 1000

BLACK = (0,0,0)
RED = (255,0,0)

#coords for plotting at the end
height = []
times = []

# Resources
shipim = pygame.image.load('ship.png')
bigship = pygame.image.load('bigship.png')
damagedship = pygame.image.load('damagedship.png')
bigdamagedship = pygame.image.load('bigdamagedship.png')
panelim = pygame.image.load('panel.png')
sky = pygame.image.load('sky.png')
ground = pygame.image.load('ground.png')
lever = pygame.image.load('lever.png')
flag = pygame.image.load('flag.png')
number = [0]*10
for i in range(10):
    number[i] = pygame.image.load(str(i)+'.png')

# Set up background
background = pygame.Surface((VIEW_WIDTH,VIEW_HEIGHT))
background.blit(sky,(0,0))
background.blit(ground,(0,HEIGHT-ground.get_height()))

class Ship:
    def __init__(self,pos,angle,mass,fuel):
        self.mass = mass
        self.fuel = fuel
        self.capacity = fuel
        self.pos = np.array(pos)
        self.vel = np.array([0,0])
        # Mass of fuel per second used.
        self.thrust = 0
        self.direction = np.array([0,1])
        self.angle = angle
        self.angvel = 0
    
    @property
    def total_mass(self):
        return self.mass + self.fuel
        
    @property
    def acc(self):
        gforce = self.total_mass * g 
        thrust_force = self.direction * self.thrust
        total_force = gforce + thrust_force
        return total_force / self.total_mass

    def _solve_position(self,dt):
        newvel = self.vel + self.acc * dt
        newpos = self.pos + self.vel * dt
        self.vel = newvel
        self.pos = newpos

    def _solve_rotation(self,dt):
        angle = self.angle + self.angvel * dt
        self.angle = angle
        self.direction = np.array([-math.sin(angle),math.cos(angle)])
        
    def _solve_used_fuel(self,dt):
        self.fuel -= self.thrust * dt * MASS_PER_THRUST
        if self.fuel <= 0:
            self.thrust = 0
            self.fuel = 0

    def change_thrust(self, amount):
        self.thrust += amount
        if self.thrust < 0:
            self.thrust = 0
        if self.thrust > MAX_THRUST:
            self.thrust = MAX_THRUST

    def change_rotation(self,amount):
       if self.fuel == 0:
           return
       self.angvel += amount

    def step(self,dt):
        self._solve_position(dt)
        self._solve_rotation(dt)
        self._solve_used_fuel(dt)
        

    # Object represented as a string. For testing.
    def __str__(self):
        return 'total mass: ' + str(self.total_mass) + '\n' +  \
                'ship mass: ' + str(self.mass) + '\n' + \
                'fuel remaining: ' + str(self.fuel) + '\n' + \
                'fuel capacity: ' + str(self.capacity) + '\n' + \
                'position: ' + str(self.pos) + '\n' + \
                'velocity: ' + str(self.vel) + '\n' + \
                'acceleration: ' + str(self.acc) + '\n' + \
                'angle: ' + str(self.angle) + '\n' + \
                'angular velocity: ' + str(self.angvel) + '\n' + \
                'thrust: ' + str(self.thrust) +  '\n'

def draw_view(view,ship,shipim):
    # Draw background
    view.blit(background,(0,0))
    # Transform world coords to screen coords
    r = 1.2 * INIT_HEIGHT/HEIGHT
    x = int(ship.pos[0]/r) + VIEW_WIDTH/2
    y = HEIGHT - int(ship.pos[1]/r) - shipim.get_height() - ground.get_height()
    
    rotship = pygame.transform.rotate(shipim,math.degrees(ship.angle))
    
    # Draw ship
    view.blit(rotship,(x,y)) 

def draw_panel(panel,ship,bigship):
    panel.fill(BLACK)
    flen = 466 - 296
    fw = 101-80
    fh = flen * (ship.fuel / ship.capacity)
    if ship.fuel > 0:
        pygame.draw.rect(panel,RED,(80,466-fh,fw,fh))

    # Draw background
    panel.blit(panelim,(0,0))
    

    # Draw counters
    # String representation of values to 2 d.p. with leading zeroes for
    # string of length 7.
    pos = "{0:.2f}".format(abs(ship.pos[1])).zfill(7)
    vel = "{0:.2f}".format(np.linalg.norm(ship.vel)).zfill(7)
    acc = "{0:.2f}".format(np.linalg.norm(ship.acc)).zfill(7)
    # Check values are within expected range. Crash the program if false.
    assert(len(pos) == 7)
    assert(len(vel) == 7)
    assert(len(acc) == 7)
    
    # Position of top left corner of each counter in panel
    ovel = np.array([45,140])
    opos = np.array([45,157])
    oacc = np.array([45,123])

    def draw_number(panel,value,origin):
        spacing = np.array([8,0])
        for ii in range(7):
            if ii == 4: continue # Ignore decimal point
            panel.blit(number[int(value[ii])], origin + spacing*ii )

    draw_number(panel,pos,opos)
    draw_number(panel,vel,ovel)
    draw_number(panel,acc,oacc)
    
    # Draw ship rotation
    # Centre of circle
    orot = np.array([60,61])

    # Rotate the ship image
    rship = pygame.transform.rotate(bigship,math.degrees(ship.angle))

    # Find corner to draw image from
    corner = orot - np.array([rship.get_width(),rship.get_height()])/2
    panel.blit(rship,corner)

    # Draw thrust lever
    levlen = 463-300
    xlev = 21 - lever.get_width()/2
    ylev = 463 - levlen * (ship.thrust / MAX_THRUST) - lever.get_height()/2
    panel.blit(lever,(xlev,ylev))


# Initialise visual surfaces
screen = pygame.display.set_mode((WIDTH,HEIGHT))
view = pygame.Surface((VIEW_WIDTH,VIEW_HEIGHT))
panel = pygame.Surface((PANEL_WIDTH,PANEL_HEIGHT))

# Initialise ship
ship = Ship([0,INIT_HEIGHT],random.uniform(-math.pi/4,math.pi/4),1000,400)

# Initialise gameloop variables.
oldtime = starttime = time.clock()
running = True
success = False

while running:
    newtime = time.clock()
    # Ensure timestep match with real world.
    if newtime - oldtime < timestep:
        continue
    
    # Handle inputs
    pressed = False
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_UP:
                ship.change_thrust(100)
            if e.key == pygame.K_DOWN:
                ship.change_thrust(-100)
            if e.key == pygame.K_LEFT:
                ship.change_rotation(0.1)
            if e.key == pygame.K_RIGHT:
                ship.change_rotation(-0.1)
        if e.type == pygame.MOUSEBUTTONDOWN:
            pressed = True
    # Check slider input
    pressed = pressed or pygame.mouse.get_pressed()[0]
    if pressed == True:
        mpos = pygame.mouse.get_pos()
        # Check within slider rectangle
        if mpos[0] > 5 + VIEW_WIDTH and mpos[0] < 37 + VIEW_WIDTH \
                and mpos[1] < 463 and mpos[1] > 300:
                    ship.thrust = MAX_THRUST * (463-mpos[1]) / (463 - 300)
        #Check slightly above slider rectangle to max properly
        if mpos[0] > 5 + VIEW_WIDTH and mpos[0] < 37 + VIEW_WIDTH \
                and mpos[1] < 480 and mpos[1] >= 463:
                    ship.thrust = 0
        #Check slightly below slider rectangle to zero properly
        if mpos[0] > 5 + VIEW_WIDTH and mpos[0] < 37 + VIEW_WIDTH \
                and mpos[1] > 280 and mpos[1] <= 300:
                    ship.thrust = MAX_THRUST
   
    # Simulate
    ship.step(timestep)
    #Record
    height.append(ship.pos[1])
    times.append(newtime-starttime)

    # Check end condition
    if ship.pos[1] <= 0:
        ship.pos[1] = 0
        running = False
        # Check success
        angle = ship.angle % (2*math.pi)
        success = np.linalg.norm(ship.vel) < vel_tol and \
        ( angle < angle_tol or 2*math.pi-angle < angle_tol)

    
    # Draw
    draw_view(view,ship,shipim)
    draw_panel(panel,ship,bigship)
    screen.blit(view,(0,0))
    screen.blit(panel,(VIEW_WIDTH,0))
    pygame.display.update()

    oldtime = newtime

# Success. Draw flag.
if success:
    pygame.time.wait(1000)
    r = 1.2 * INIT_HEIGHT/HEIGHT
    view.blit(flag,(int(ship.pos[0]/r) + VIEW_WIDTH/2 - 10,HEIGHT-ground.get_height()-38))
    screen.blit(view,(0,0))
    pygame.display.update()
    
# Crash land. Draw damaged ship.
else:
    draw_view(view,ship,damagedship)
    draw_panel(panel,ship,bigdamagedship)
    screen.blit(view,(0,0))
    screen.blit(panel,(VIEW_WIDTH,0))
    pygame.display.update()

# Wait for program exit. Not sure why but anaconda crashes without this bit
# of cleanup code. Not an issue on linux system.
exit_clicked = False
while not exit_clicked:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit_clicked = True
            pygame.quit()

# Plot the altitude over height
times = np.array(times)
height = np.array(height)
plt.figure()
plt.plot(times,height)
plt.xlabel('Time [s]')
plt.ylabel('Altitude [m]')
plt.title('Altitude over time')
plt.show()


