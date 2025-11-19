from rich.live import Live
from ReactorV2 import ReactorV2


# Configuration parameters for a class II Reactor
config = {
    # === Simulation settings ===
    'n_iter' : 500, # = 50 seconds
    'n_initial' : 200,
    'a' : 0.1,
    'f' : 0.6,
    'd' : 0.5,
    'l' : 1.1,
    # === Reactor settings ===
    'n' : 15, 
    'm' : 15,
    'thermic_capacity' : 1e7, 
    'loss_factor' : 0.1,
    'toric' : False,
    'moderator' : 'heavy_water', # 'graphite', 'light_water', 'heavy_water'
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



# ==================== TODO ====================
# 
# - [DONE] rajouter répartition aléatoire des neutrons au départ 
# - [DONE] calculer la température moyenne à chaque iter  
# - [DONE] intégrer les barres de contrôle
# - implémenter l'algo des branchements - Marco
# - (Axel) exporter trajectoire dans un fichier 
#
# - (passer en 3D et en continu)