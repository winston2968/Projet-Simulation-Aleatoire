# ==========================================================================================
#                                      Control Rod
# ==========================================================================================

import numpy as np 

typeRod = {
    'regulation' : {'totalWorthPcm' : -100, 'maxSpeed' : 5.0},
    'compensation' : {'totalWorthPcm' : -1000, 'maxSpeed' : 0.2},
    'scram' : {'totalWorthPcm' : -2000, 'maxSpeed' : 100.0}
}

class ControlRod:

    def __init__(self, id, type='regulation'):
        """
            Model a control bar in a nuclear reactor
        """

        self.id = id
        self.type = type  # 'regulation', 'compensation', 'scram'

        # === 1. Attributes specific to the type of control rod ===
        if type not in typeRod:
            raise ValueError(f"Unknown control rod type: {type}")
        
        # Maximum reactivity value in pcm
        self.totalWorthPcm = typeRod[type]['totalWorthPcm']
        # Speed of the control rod movement in cm/s
        self.maxSpeed = typeRod[type]['maxSpeed']

        # === 2. Dynamic attributes ===
        # 100.0 = fully withdrawn
        # 0.0 = fully inserted
        self.positionPercent = 100.0   # current position
        self.targetPosition = 100.0    # target position


    def step(self, dt):
        """
            Move the control rod towards its target position based on its speed
        """

        error = self.targetPosition - self.positionPercent
        maxMove = self.maxSpeed * dt

        if abs(error) < maxMove:
            # Reach target position
            self.positionPercent = self.targetPosition
        elif error > 0:
            # Move rod up
            self.positionPercent += maxMove
        else:
            # Move rod down
            self.positionPercent -= maxMove
        
        # Clamp position between 0 and 100%
        self.positionPercent = max(0.0, min(100.0, self.positionPercent))

    def get_reactivity_pcm(self):
        """
            Calculate the reactivity worth of the control rod based on its position
            Use S approximation
        """

        # Conversion percent (100=OUT, 0=IN) to fraction (0=OUT, 1=IN)
        fractionInserted = (100.0 - self.positionPercent) / 100.0

        # S-curve formula (cosinus) (simplified, normalized from 0 to 1)
        # f(x) = 0.5 * (1 - cos(pi * x))
        sCurveFactor = 0.5 * (1 - np.cos(np.pi * fractionInserted))
        
        # Reactivity is the total "weight" * efficiency
        return self.totalWorthPcm * sCurveFactor