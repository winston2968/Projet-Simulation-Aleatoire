# ==========================================================================================
#                                 Random Generation Functions
# ==========================================================================================

from matplotlib import pyplot as plt
import numpy as np 
from numpy import random as npr

# Poisson random variable generation
# Input: 
#     - l : mean of the Poisson distribution
# Returns: 
#     - integer representing a random value from a Poisson-like distribution
def simul_poisson(l): 
    return int(np.ceil(-(1/l) * np.log(npr.rand())))

