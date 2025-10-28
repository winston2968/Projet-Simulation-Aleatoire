# ==========================================================================================
#                                 Random Generation Functions
# ==========================================================================================

from matplotlib import pyplot as plt
import numpy as np 
from numpy import random as npr
from main_nuclear import is_in_the_grid

# Poisson random variable generation
# Input: 
#     - l : mean of the Poisson distribution
# Returns: 
#     - integer representing a random value from a Poisson-like distribution
def simul_poisson(l): 
    return int(np.ceil(-(1/l) * np.log(npr.rand())))


# Choose which action to perform for a neutron at each iteration
# Inputs: 
#     - d : diffusion probability
#     - a : absorption probability
#     - f : fission probability
# Returns:
#     - 0 for diffusion, 1 for absorption, 2 for fission
def choose_action(d, a, f):
    total = d + a + f
    d, a, f = d/total, a/total, f/total
    u = npr.rand()
    l = [d, d+a, 1.0]
    x = 0
    while u > l[x]:
        x += 1
    return x


# Generate a new direction for diffusion
# Returns:
#     - dx, dy : integers in [-1, 0, 1] representing the change in x and y
#               - ensures that dx and dy are not both zero (the neutron moves)
def new_direction(): 
    while True:
        dx, dy = npr.choice([-1, 1]), npr.choice([-1,1])
        if dx != 0 or dy != 0:
            return dx, dy


# Compute the new position of a neutron based on its current state and action probabilities
# Inputs:
#     - state : dictionary containing current neutrons {id: (x,y)}
#     - pos : tuple (x,y) representing the current position of the neutron
#     - d, a, f : probabilities for diffusion, absorption, and fission
#     - l : parameter for Poisson distribution in fission
#     - n, m : size of the grid
#     - max_speed : maximum number of cells the neutron can move during diffusion
# Returns:
#     - new_pos : tuple (new_x, new_y) or (False, False) if absorbed
#     - new_neutrons : dictionary of newly created neutrons during fission {id: (x,y)}
def new_position(state, pos, d, a, f, l, n, m, max_speed=1): 
    x, y = pos
    action = choose_action(d, a, f)
    new_pos = (x, y)
    new_neutrons = {}

    # Diffusion
    if action == 0:  # diffusion
        dx, dy = new_direction()
        step_x = dx * npr.randint(1, max_speed+1)
        step_y = dy * npr.randint(1, max_speed+1)
        new_x = x + step_x
        new_y = y + step_y
        new_pos = (new_x, new_y)

    # Absorption
    elif action == 1:
        new_pos = (False, False)

    # Fission
    elif action == 2:
        n_new = simul_poisson(l)  # Poisson-like random number
        for i in range(len(state), len(state) + n_new):
            new_neutrons[i] = (x, y)

    return new_pos, new_neutrons
