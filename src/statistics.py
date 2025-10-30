# ==========================================================================================
#                             Statistical Simulation Experiments 
# ==========================================================================================

import numpy as np 
from rich.live import Live
from ReactorV2 import ReactorV2
from matplotlib import pyplot as plt


# ==========================================================================================
#                          Visualization and Statistical Analysis Tools
# ==========================================================================================

# --------------------------------------------
# Extract neutrons trajectories from history
# --------------------------------------------
def get_trajectories(history): 
    pass

# --------------------------------------------
# Calculate the nb of neutrons by generations
# --------------------------------------------
def get_neutrons_count(history): 
    n_neutrons = []
    for period in history: 
        n_neutrons.append(len(period))
    return n_neutrons

# --------------------------------------------
# Plot the Number of Neutrons per Generation
# --------------------------------------------
def plot_neutron_count(history): 
    n_neutrons = get_neutrons_count(history)
    plt.plot([i for i in range(len(n_neutrons))], n_neutrons)
    plt.title("Number of Neutrons per Generation")
    plt.xlabel("Generations")
    plt.ylabel("Number of Neutrons")
    plt.show()


def plot_k_value(history): 
    n_neutrons = get_neutrons_count(history)
    plt.plot([i for i in range(len(n_neutrons) -1)], [n_neutrons[i] / n_neutrons[i+1] for i in range(len(n_neutrons) - 1)])
    plt.xlabel("Generations")
    plt.ylabel("k values")
    plt.title("k value evolution by generation")
    plt.show()




# -------------------------------------------
# Plot the Spatial Distribution of Neutrons
# -------------------------------------------
def plot_spatial_distribution(config, history): 
    grid_sum = np.zeros((config['n'], config['m']))
    for state in history:
        for id in state: 
            grid_sum[state[id][0],state[id][1]] += 1 

    plt.imshow(grid_sum, cmap='hot', origin='lower')
    plt.colorbar(label='Occupation Frequency')
    plt.title('Average Spatial Distribution of Neutrons')
    plt.xlabel('x position')
    plt.ylabel('y position')
    plt.show()


# ---------------------------------------
# Plot Individual Neutron Trajectories
# ---------------------------------------
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
def extinction_probability(config, n_runs=20): 
    extinct = 0 
    for _ in range(n_runs): 
        reactor = ReactorV2(None, config)
        history = reactor.simulate()
        if len(history[-1]) == 0: 
            extinct += 1
    return extinct / n_runs 


# ---------------------------------------
# Compute the Mean Time to Extinction
# ---------------------------------------
def mean_times_to_extinction(config, n_runs=20): 
    times = []
    for _ in range(n_runs): 
        reactor = ReactorV2(None, config)
        history = reactor.simulate()
        # Get the extinction time 
        for t,state in enumerate(history): 
            if len(state) == 0:
                times.append(t)
                break 
    return np.mean(times) if times else np.inf


# ---------------------------------------
# Combined Plot Function
# ---------------------------------------
def plot_infos(config, n_runs=20): 
    reactor = ReactorV2(None, config)
    history = reactor.simulate()
    plot_neutron_count(history)
    plot_spatial_distribution(config, history)
    plot_k_value(history)



# ---------------------------------------
# Run the Experiment
# ---------------------------------------

# Configuration parameters for a class II Reactor
config = {
    'n' : 15, 
    'm' : 15, 
    'n_initial' : 10, 
    'd' : 0.5,
    'a' : 0.1,
    'f' : 0.6,
    'l' : 3,
    'n_iter' : 100, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : True, 
    'colorized' : True, 
    'thermalization_probs': {'fast_to_epi': 0.5, 'epi_to_thermal': 0.5}, 
    'moderator' : 'graphite', 
    'verbose' : True
}

with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()

plot_infos(config)