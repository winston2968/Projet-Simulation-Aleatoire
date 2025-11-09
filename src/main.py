import numpy as np 
from rich.live import Live
from ReactorV2 import ReactorV2


# Configuration parameters for a class II Reactor
config = {
    'n' : 15, 
    'm' : 15, 
    'n_initial' : 300, 
    'd' : 0.5,
    'a' : 0.1,
    'f' : 0.6,
    'l' : 3,
    'thermic_capacity' : 1e7, 
    'loss_factor' : 0.1,
    'n_iter' : 50, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : True, 
    'colorized' : True, 
    'thermalization_probs': {'fast_to_epi': 0.5, 'epi_to_thermal': 0.5}, 
    'moderator' : 'heavy_water', #graphite, light_water, heavy_water
    'initial_distribution' : 'normal', #center, uniform, normal
    'verbose' : False
}



with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()



# ==================== TODO ====================
# 
# - [DONE] rajouter répartition aléatoire des neutrons au départ 
# - (Axel) calculer la température moyenne à chaque iter 
# - changer loi du nb de neutrons générées lors de la fission 
# - intégrer les barres de contrôle
# -         Ces barres pourraient être introduites automatiquement dans le réacteur si la réacteur dépasse une 
# -         certaine température ou un certain nombre de neutrons
# - (Axel) exporter trajectoire dans un fichier 
#
#
# - (passer en 3D et en continu)