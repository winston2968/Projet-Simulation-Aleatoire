# ==========================================================================================
#                             Statistical Simulation Experiments 
# ==========================================================================================

from matplotlib import pyplot as plt
import numpy as np 
from numpy import random as npr
from rich.live import Live
from rich.table import Table
from time import sleep
from reactor import Reactor


# ---------------------------------------
# Plot the Number of Neutrons per Generation
# ---------------------------------------
# Description:
#     This function plots the evolution of the total number of neutrons
#     over successive generations (iterations) of the simulation.
# Inputs:
#     - history : list of neutron states (dictionaries {id: (x, y)}) at each iteration
# Behavior:
#     - Computes the total number of neutrons for each recorded generation.
#     - Displays a line plot showing the change in neutron count over time.
def plot_neutron_count(history): 
    plt.plot([i for i in range(len(history))], [len(state) for state in history])
    plt.title("Number of Neutrons per Generation")
    plt.xlabel("Generations")
    plt.ylabel("Number of Neutrons")
    plt.show()


# ---------------------------------------
# Plot the Spatial Distribution of Neutrons
# ---------------------------------------
# Description:
#     This function visualizes the average spatial distribution of neutrons
#     over all iterations of the simulation.
# Inputs:
#     - config  : dictionary containing grid configuration (n, m)
#     - history : list of neutron states (dictionaries {id: (x, y)}) at each iteration
# Behavior:
#     - Builds a 2D histogram of neutron positions accumulated over time.
#     - Displays the result as a heatmap, where color intensity indicates
#       how frequently a cell was occupied by a neutron.
def plot_spatial_distribution(config, history): 
    grid_sum = np.zeros((config['n'], config['m']))
    for state in history: 
        for (_,(x,y)) in state.items(): 
            grid_sum[x, y] += 1
    plt.imshow(grid_sum, cmap='hot', origin='lower')
    plt.colorbar(label='Occupation Frequency')
    plt.title('Average Spatial Distribution of Neutrons')
    plt.xlabel('x position')
    plt.ylabel('y position')
    plt.show()


# ---------------------------------------
# Plot Individual Neutron Trajectories
# ---------------------------------------
# Description:
#     This function plots the trajectories of selected neutrons across
#     successive generations.
# Inputs:
#     - history : list of neutron states (dictionaries {id: (x, y)}) at each iteration
#     - n_traj  : number of individual neutron trajectories to display
# Behavior:
#     - Tracks the movement of the first n_traj neutrons that appear in the
#       initial state and plots their paths over time.
def plot_trajectories(history, n_traj=5):
    trajectories = {i: [] for i in list(history[0].keys())[:n_traj]}
    for state in history:
        for i in trajectories:
            if i in state:
                trajectories[i].append(state[i])
    plt.figure()
    for i, traj in trajectories.items():
        xs, ys = zip(*traj)
        plt.plot(xs, ys, marker='.')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Neutron Trajectories')
    plt.grid(True)
    plt.show()


def extinction_probability(config, n_runs=100): 
    extinct = 0 
    for _ in range(n_runs): 
        reactor = Reactor(None, config)
        history = reactor.simulate()
        if len(history[-1]) == 0: 
            extinct += 1
    return extinct / n_runs 

def mean_times_to_extinction(config, n_runs=100): 
    times = []
    for i in range(n_runs): 
        reactor = Reactor(None, config)
        history = reactor.simulate()
        # Get the extinction time 
        for t,state in enumerate(history): 
            if len(state) == 0 :
                times.append(t)
                break 
        print("Iteration : ", i)
    return np.mean(times) if times else np.inf

def average_growth_rate(config, n_runs=20):
    growth_rates = []
    sizes = []
    for i in range(n_runs): 
        reactor = Reactor(None, config)
        history = reactor.simulate()
        sizes = np.array([len(state) for state in history if len(state) > 0])
        if len(sizes) > 2 :
            g = np.mean(sizes[1:] / sizes[:-1])
            growth_rates.append(g)
        print("Iteration : ", i)
    return growth_rates



# ---------------------------------------
# Simulation Configuration
# ---------------------------------------
# Description:
#     This section defines the parameters used to initialize and run the
#     nuclear reactor simulation.
# Parameters:
#     - n, m        : grid size (rows × columns)
#     - n_initial   : initial number of neutrons
#     - d, a, f     : diffusion, absorption, and fission probabilities
#     - l           : parameter controlling number of new neutrons created during fission
#     - n_iter      : number of simulation iterations (generations)
#     - max_speed   : maximum movement step per iteration
#     - toric       : whether the grid has toric (wrap-around) boundaries
#     - display     : if True, display the grid in real-time using Rich
config = {
    'n' : 10, 
    'm' : 10, 
    'n_initial' : 10, 
    'd' : 0.5, 
    'a' : 0.2, 
    'f' : 0.5, 
    'l' : 10,
    'n_iter' : 20, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : False
}



# with Live(refresh_per_second=10) as live:
#     reactor = Reactor(live, config)
#     history = reactor.simulate()

# Visualization of simulation results
# plot_neutron_count(history)
# plot_spatial_distribution(config, history)
# plot_trajectories(history, 10)


# Sweep over fission probabilities
fs = np.linspace(0.1, 0.9, 9)
proba_ext = []
growth_rates = []

for f in fs:
    config['f'] = f
    config['a'] = 1 - f - 0.1  # keep diffusion small constant
    p_ext = extinction_probability(config, n_runs=10)
    # g_mean = average_growth_rate(config, n_runs=20)
    proba_ext.append(p_ext)
    # growth_rates.append(g_mean)

print('figure')
plt.figure()
plt.plot(fs, proba_ext, 'o-', label="Extinction probability")
# plt.plot(fs, growth_rates, 's-', label="Average growth rate")
plt.xlabel('Fission probability f')
plt.legend()
plt.show()
