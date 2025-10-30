
# ==========================================================================================
#                                      Neutron Class 
# ==========================================================================================

import numpy as np 
import numpy.random as npr 


class Neutron: 
    """
        Define neutron type to allows the reactor to contain different neutron types. 
        Each neutron type will react differently with his environement and allow us to 
        simulate different reators types. 
    """

    def __init__(self, id, x, y,thermalization_probs, type="fast", speed=1.0):
        self.x = x 
        self.y = y 
        self.id = id 
        self.speed = speed 
        self.type = type # "thermal", "fast", "epithermal"
        
        # Probability to change state 
        self.thermalization_probs = thermalization_probs

        # Tajectory history for plotting 
        self.traj = [(self.x, self.y)]

        # Time memory 
        self.age = 0 
        self.is_alive = True 

    # -----------------------
    # Diffusion Behavior
    # ----------------------- 
    def diffuse(self, max_speed): 
        dx, dy = self.random_direction()
        step_x = dx * npr.randint(1, max_speed + 1) * self.speed 
        step_y = dy * npr.randint(1, max_speed + 1) * self.speed 
        self.x += int(step_x) 
        self.y += int(step_y) 


    # -----------------------
    # Direction Draw
    # ----------------------- 
    @staticmethod
    def random_direction(): 
        while True: 
            dx = npr.choice([-1, 0, 1]) 
            dy = npr.choice([-1, 0, 1])
            if dx != 0 or dy != 0: 
                return dx, dy 

    # -----------------------
    # Evolution Step 
    # ----------------------- 
    def evolve(self, moderator=None): 
        """
        Update the neutron internal property over time depending on the moderator 
        used in the reactor or just with a thermalisation prob. 
        """
        if moderator is None : 
            self.age += 1
            self.speed *= 0.98 

            if self.type == "fast" and npr.rand() < self.thermalization_probs['fast_to_epi']: 
                self.type = "epithermal"

            elif self.type == "epithermal" and npr.rand() < self.thermalization_probs['epi_to_thermal'] :
                self.type = "thermal" 
        
        else: 
            if self.type == "fast" and npr.rand() < moderator.slow_fast:
                self.type = "epithermal"
            elif self.type == "epithermal" and npr.rand() < moderator.slow_epi:
                self.type = "thermal"