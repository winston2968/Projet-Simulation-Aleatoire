# ==========================================================================================
#                             Statistical Simulation Experiments 
# ==========================================================================================

from matplotlib import pyplot as plt
import numpy as np 
from numpy import random as npr
from rich.live import Live
from rich.table import Table
from time import sleep
from Reactor import Reactor


# ==========================================================================================
#                          Visualization and Statistical Analysis Tools
# ==========================================================================================


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
# Output:
#     - A matplotlib figure displaying the population curve.
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
# Output:
#     - A heatmap representing the mean occupancy of each cell in the grid.
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
# Output:
#     - A matplotlib plot showing neutron trajectories.
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


# ==========================================================================================
#                        Statistical Analysis: Extinction and Mean Lifetime
# ==========================================================================================


# ---------------------------------------
# Estimate the Extinction Probability
# ---------------------------------------
# Description:
#     Runs multiple independent simulations and computes the probability
#     that the neutron population eventually goes extinct.
# Inputs:
#     - config : dictionary containing simulation parameters
#     - n_runs : number of independent simulations to perform
# Behavior:
#     - Runs the reactor simulation n_runs times without display.
#     - Counts the proportion of simulations where the neutron population
#       reaches zero by the end of the simulation.
# Output:
#     - Float value representing the estimated extinction probability.
def extinction_probability(config, n_runs=20): 
    extinct = 0 
    for _ in range(n_runs): 
        reactor = Reactor(None, config)
        history = reactor.simulate()
        if len(history[-1]) == 0: 
            extinct += 1
    return extinct / n_runs 


# ---------------------------------------
# Compute the Mean Time to Extinction
# ---------------------------------------
# Description:
#     Estimates the average number of generations required for the neutron
#     population to go extinct.
# Inputs:
#     - config : dictionary containing simulation parameters
#     - n_runs : number of independent simulations to perform
# Behavior:
#     - Runs n_runs simulations.
#     - Records the iteration index (generation) where extinction occurs.
#     - Prints the iteration index for each completed run.
# Output:
#     - Mean extinction time (float) across all runs, or infinity if no extinction occurred.
def mean_times_to_extinction(config, n_runs=20): 
    times = []
    for i in range(n_runs): 
        reactor = Reactor(None, config)
        history = reactor.simulate()
        # Get the extinction time 
        for t, state in enumerate(history): 
            if len(state) == 0:
                times.append(t)
                break 
        print("Iteration:", i)
    return np.mean(times) if times else np.inf


# ---------------------------------------
# Combined Plot Function
# ---------------------------------------
# Description:
#     Runs a single simulation and generates all three main visualizations:
#     - Neutron count over generations,
#     - Spatial distribution of neutrons,
#     - Individual neutron trajectories.
# Inputs:
#     - config  : dictionary containing simulation parameters
#     - n_runs  : number of independent runs (used for label consistency)
# Output:
#     - Displays the three matplotlib plots sequentially.
def plot_infos(config, n_runs): 
    reactor = Reactor(None, config)
    history = reactor.simulate()
    plot_neutron_count(history)
    plot_spatial_distribution(config, history)
    plot_trajectories(history, 10)



# ==========================================================================================
#                             Simulation Configuration and Execution
# ==========================================================================================

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


# ---------------------------------------
# Run the Experiment
# ---------------------------------------
# Description:
#     Executes the reactor simulation with the given configuration
#     and generates all the associated plots for analysis.
plot_infos(config, n_runs=20)
