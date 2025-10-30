import numpy as np 
from rich.live import Live
from ReactorV2 import ReactorV2


# Configuration parameters for a class II Reactor
config = {
    'n' : 15, 
    'm' : 15, 
    'n_initial' : 10, 
    'd' : 0.5,
    'a' : 0.1,
    'f' : 0.6,
    'l' : 3,
    'n_iter' : 200, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : True, 
    'colorized' : True, 
    'thermalization_probs': {'fast_to_epi': 0.5, 'epi_to_thermal': 0.5}, 
    'moderator' : None
}



with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()