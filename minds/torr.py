'''
Torr the ugly virus
'''
# Torr does a little of everything: eats, scouts, keeps track of known plants,
# charges, has mood swings and even builds make-believe fortifications.

import cells
import random
import math

class MessageType(object):
	ATTACK = 0
	PLANT = 1
	PLANTATTACK = 2

class AgentMind(object):

    def become_warrior(self):
        """ I'm a lover, not a warrior """

        self.isalover = False
        self.hungry += 110
        self.wanderlust = 0

    def __init__(self, args):

        # It is a matter of time before we snap
        self.bornbad = 60

        # inheritance
        if args != None:
            parent = args[0]

            # Crankiness starts off as the game age, but it cycles
            self.cycle = parent.cycle
            self.crankiness = parent.crankiness
            self.plants = parent.plants
            self.myplant = parent.myplant

        else:
            self.cycle = 0
            self.crankiness = 0
            self.myplant = False
            self.plants = set()

        # Our definitions of "starving", "hungry" and "horny"
        self.starving = 5
        self.hungry = 12
        self.horny = 41

        # How many children must a blob have
        self.birthcontrol = random.randrange(2, 16)
        self.children = 0

        # Dirt-shifting vars
        self.stonescarried = 0
        self.groundimpact = random.randrange(0, 10)

        self.pos = None
        self.prevpos = (0,0)
        self.nextpos = None

        self.dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        self.vector = random.choice(self.dirs)

        self.peers = 0

        self.attackalert = False
        self.myplant = False

        # Warrior to Lover ratios before and after the "bad" gene is triggered.
        # The first one's always a lover who constantly changes direction
        if args == None:
            self.isalover = True
            self.wanderlust = 100

        elif (((self.crankiness < self.bornbad) and (random.random() < 0.7)) or
            ((self.crankiness > self.bornbad) and (random.random() < 0.4))):

            self.isalover = True
            # Chance in 100 to change direction spontaneously while exploring
            self.wanderlust = random.randrange(0, 4)

        else:
            self.become_warrior()       
    
    def gimme_nextpos(self):

        mp = (mx, my) = self.pos
        mdp = (mdx, mdy) = self.vector

        nextpos = (mx + mdx, my + mdy)
        self.nextpos = nextpos

    def length(self, a, b):
        return int(math.sqrt((a * a) + (b * b)))

    def gimme_distance(self, target):

        mp = (mx, my) = self.pos
        return self.length(abs(mx - target[0]), abs(my - target[1]))

    def pickplant(self):
        """
        Chooses the closest plant
        """
        for tree in self.plants:
            if (self.gimme_distance((tree[0],tree[1])) <
                self.gimme_distance(self.myplant[:2])):

                self.myplant = (tree[0],tree[1],tree[2])
        
    def act(self, view, msg):

        # Time and attitude
        self.crankiness += 1

        if self.horny < 2401 and self.cycle > 0:
            self.hungry += (self.crankiness/10)
            # is this useful? no matter, I like the symbolism :p
            self.horny += (self.crankiness/10)

        if (self.crankiness == self.bornbad and self.isalover == True and
            (random.random() < 0.3)):
            self.become_warrior()

        if self.crankiness >= (self.bornbad * 1.5):
            self.cycle += 1
            self.crankiness = 0

        # Bearings
        me = view.get_me()
        self.pos = (mx, my) = me.get_pos()
        plants = view.get_plants()
        energy_here = view.get_energy().get(mx, my)
    
        # Parse messages
        for m in msg.get_messages():

            if m[0] == MessageType.ATTACK:
                if self.attackalert == False:
                    self.attackalert = ((m[1] + random.randrange(-15, 15)),
                                        (m[2] + random.randrange(-15, 15)))

                alertdistance = self.gimme_distance((m[1],m[2]))

                if alertdistance < self.gimme_distance(self.attackalert):
                    self.attackalert = ((m[1] + random.randrange(-15, 15)),
                                        (m[2] + random.randrange(-15, 15)))                    

            if m[0] == MessageType.PLANTATTACK:
                alertdistance = self.gimme_distance((m[1],m[2]))

                if alertdistance < self.gimme_distance(self.attackalert):
                    self.crankiness = self.bornbad - 3
                    self.attackalert = (m[1], m[2])

            if m[0] == MessageType.PLANT:
                self.plants.add((m[1],m[2],m[3]))

                if self.myplant == False:
                    self.myplant = (m[1],m[2],m[3])

                if (m[1],m[2]) == self.attackalert:
                    # Plant secured
                    self.attackalert = False

        # Socialize
        self.peers = 0
        for chum in view.get_agents():
            
            if chum.get_team() != me.get_team():
                msg.send_message((MessageType.ATTACK, mx, my))

                if (len(plants) > 0) :
                    pp = (px, py) = plants[0].get_pos()
                    msg.send_message((MessageType.PLANTATTACK, px, py))
                    if me.energy < 2490:
                        return cells.Action(cells.ACT_EAT)

                return cells.Action(cells.ACT_ATTACK, chum.get_pos())

            if chum.get_team() == me.get_team():
                self.peers += 1

        # Send plant updates
        if len(plants) > 0:
            ppos = (px, py) = plants[0].get_pos()
            self.myplant = (px, py, plants[0].eff)

            msg.send_message((MessageType.PLANT, px, py, plants[0].eff))


        # Eat to mate (or however it is we do it)
        if ((self.birthcontrol >= self.children) or
            (self.peers == 0 and len(plants) > 0)):

            if (me.energy >= self.horny):
                self.vector = random.choice(self.dirs)
                self.gimme_nextpos()
                self.children += 1

                return cells.Action(cells.ACT_SPAWN, (self.nextpos[0],
                                                      self.nextpos[1],
                                                      self))

            if (me.energy < self.horny) and energy_here > 5:
                return cells.Action(cells.ACT_EAT)

        # Eat if hungry
        hungry = (me.energy < self.hungry)
        if hungry and energy_here > 1 and me.energy < self.hungry:
            return cells.Action(cells.ACT_EAT)

        # Warriors respond to alerts
        if self.attackalert != False and not self.isalover:

            if self.gimme_distance(self.attackalert) < 4:
                self.attackalert = False

            elif self.pos != self.prevpos:
                self.prevpos = self.pos
                return cells.Action(cells.ACT_MOVE, self.attackalert)

            else:
                self.vector = random.choice(self.dirs)
                self.gimme_nextpos()
                self.prevpos = self.pos
                return cells.Action(cells.ACT_MOVE, self.nextpos)  

        # Build "fortifications"
        if ((self.stonescarried < self.groundimpact) and
            self.myplant != False and energy_here < 2):

            self.pickplant()
            plant_pos = (self.myplant[0], self.myplant[1])
            plant_dist = self.gimme_distance(plant_pos)

            if (me.loaded and 12 <= plant_dist <= 16 and
                abs(mx - plant_pos[0]) >= 10 and abs(my - plant_pos[1]) >= 10):

                self.stonescarried += 1
                return cells.Action(cells.ACT_DROP)

            elif me.loaded and plant_dist > 16:
                (px, py) = plant_pos
                pos = (px + random.randrange(-1,2),
                       py + random.randrange(-1,2))

                return cells.Action(cells.ACT_MOVE, pos)

            elif me.loaded:
                return cells.Action(cells.ACT_DROP)

            if (not me.loaded and me.energy > 40 and (random.random() < 0.4) and
                ((plant_dist < 12) or ((8 < plant_dist < 20) and
                (abs(mx - plant_pos[0]) < 10 or abs(my - plant_pos[1]) < 10)))):

                return cells.Action(cells.ACT_LIFT)


        # Exploration
        if (self.prevpos[0] == mx or
            self.prevpos[1] == my or 
            random.randrange(0,100) <= self.wanderlust):
            self.vector = random.choice(self.dirs)

        self.gimme_nextpos()
        self.prevpos = self.pos

        return cells.Action(cells.ACT_MOVE, self.nextpos)  
