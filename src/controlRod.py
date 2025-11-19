# ==========================================================================================
#                                      Control Rod
# ==========================================================================================

import numpy as np 

type_rod = {
    'regulation' : {'total_worth_pcm' : -1000, 'max_speed' : 10},
    'scram' : {'total_worth_pcm' : -20000, 'max_speed' : 100.0}
}

class ControlRod:

    def __init__(self, id:str, type:str):
        """
            Model a control bar in a nuclear reactor
        """

        self.id = id
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
    # Move the control rod towards its target position based on its speed
    # ------------------------------------------------------------------
    def step(self, dt:float):
        # === 1. Calculate distance error ===
        error = self.target_position - self.position_percent
        max_move = self.max_speed * dt

        # === 2. Update new position percent ===
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
    # Calculate the reactivity worth of the control rod based on its position
    # Use S approximation
    # ------------------------------------------------------------------
    def get_reactivity_pcm(self):
        # Conversion percent (100=OUT, 0=IN) to fraction (0=OUT, 1=IN)
        fraction_inserted = (100.0 - self.position_percent) / 100.0

        # S-curve formula (cosinus) (simplified, normalized from 0 to 1)
        # f(x) = 0.5 * (1 - cos(pi * x))
        s_curve_factor = 0.5 * (1 - np.cos(np.pi * fraction_inserted))
        
        # Reactivity is the total "weight" * efficiency
        return self.total_worth_pcm * s_curve_factor