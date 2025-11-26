from rich.live import Live
from ReactorV2 import ReactorV2
from utils import export_data

# Configuration parameters for a class II Reactor
config = {
    # === Simulation settings ===
    'n_iter' : 20,
    'n_initial' : 200,  # Number of neutrons in the initial state
    'a' : 0.1,          # proba for absorption
    'f' : 0.6,          # proba for fission
    'd' : 0.5,          # proba for diffusion
    'l' : 1.1,          # Parameter of the fish law
    # === Reactor settings ===
    'n' : 15, 
    'm' : 15,
    'thermic_capacity' : 1e7,
    'toric' : False,
    'moderator' : 'heavy_water',        # 'graphite', 'light_water', 'heavy_water'
    'initial_distribution' : 'uniform', # 'center', 'uniform', 'normal'
    # === Neutrons settings ===
    'max_speed' : 2,
    'thermalization_probs': {'fast_to_epi': 0.5, 'epi_to_thermal': 0.5}, 
    # === Display settings ===
    'display' : True, 
    'colorized' : True,
    'verbose' : False,
    # === Control rods settings ===
    'rod_active' : True,
    'scram_threshold' : 1.5,    # Threshold for emergency scram
    'control_rods' : [          # Initialisation of rods
        {'id': 'RE01', 'type': 'regulation'},
        {'id': 'SC01', 'type': 'scram'}
    ]
}

with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()

# Data export
#export_data(reactorV2, config)

# ==================== TODO ====================
# 
# - [DONE] rajouter répartition aléatoire des neutrons au départ 
# - [DONE] calculer la température moyenne à chaque iter  
# - [DONE] intégrer les barres de contrôle
# - [IN PROGRESS] implémenter l'algo des branchements - Marco
# - [DONE] exporter trajectoire dans un fichier 