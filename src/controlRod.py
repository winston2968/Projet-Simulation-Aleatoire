# ==========================================================================================
#                                      Control Rod
# ==========================================================================================

import numpy as np 

type_rod = {
    'regulation' : {'total_worth_pcm' : -100, 'max_speed' : 5.0},
    'scram' : {'total_worth_pcm' : -25000, 'max_speed' : 100.0}
}

class ControlRod:

    def __init__(self, id, x_pos, type='regulation'):   #MODIF
        """
            Model a control bar in a nuclear reactor
        """

        self.id = id
        self.x_pos = x_pos  #MODIF
        self.type = type  # 'regulation', 'compensation', 'scram'

        # === 1. Attributes specific to the type of control rod ===
        if type not in type_rod:
            raise ValueError(f"Unknown control rod type: {type}")
        
        # Maximum reactivity value in pcm
        self.total_worth_pcm = type_rod[type]['total_worth_pcm']
        # Speed of the control rod movement in cm/s
        self.max_speed = type_rod[type]['max_speed']

        # === 2. Dynamic attributes ===
        # 100.0 = fully withdrawn
        # 0.0 = fully inserted
        self.position_percent = 100.0   # current position
        self.target_position = 100.0    # target position


    # ------------------------------------------------------------------
    # Calculate if the neutron will be absorbed by the rod
    # ------------------------------------------------------------------
    # Inputs: 
    #     - neutron_x & neutron_y : neutron coordinates 
    #     - grid_height : height of the grid
    # Returns:
    #     - False if not, True if yes
    def is_neutron_absorbed(self, neutron_x, neutron_y, grid_height):
        # === 1. Check position x ===
        if neutron_x != self.x_pos:
            return False
        
        # === 2. Calculate the depth of the bar ====
        # (100% = OUT = 0 case)
        # (0% = IN = grid_height cases)
        insertion_fraction = (100.0 - self.position_percent) / 100.0
        depth = insertion_fraction * grid_height

        # === 3. Check position y ===
        # We assume that the bar enters from the top, y=0
        if neutron_y < depth:
            return True
            
        return False

    # ------------------------------------------------------------------
    # Calculate & moove the bar to the target position based on it's speed
    # ------------------------------------------------------------------
    # Inputs: 
    #     - dt : time interval between to step
    # Returns:
    #     - Update position percent
    def step(self, dt):
        # === 1. Calculate power error in the reactor ===
        error = self.target_position - self.position_percent
        max_move = self.max_speed * dt

        # === 2. Update the position percent ===
        if abs(error) < max_move:
            # Reach target position
            self.position_percent = self.target_position
        elif error > 0:
            # Move rod up
            self.position_percent += max_move
        else:
            # Move rod down
            self.position_percent -= max_move
        
        # === 3. Clamp position between 0 and 100% ===
        self.position_percent = max(0.0, min(100.0, self.position_percent))

    # ------------------------------------------------------------------
    # Calculate the reactivity worth of the control rod based on its position & S approximation
    # ------------------------------------------------------------------
    # Returns:
    #     - Update the total absorption to it's position 
    def get_reactivity_pcm(self):
        # Conversion percent (100=OUT, 0=IN) to fraction (0=OUT, 1=IN)
        fraction_inserted = (100.0 - self.position_percent) / 100.0

        # S-curve formula (cosinus) (simplified, normalized from 0 to 1)
        # f(x) = 0.5 * (1 - cos(pi * x))
        s_curve_factor = 0.5 * (1 - np.cos(np.pi * fraction_inserted))
        
        # Reactivity is : the total "weight" * efficiency
        return self.total_worth_pcm * s_curve_factor