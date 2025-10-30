import numpy as np 
import numpy.random as npr 
from time import sleep 
from rich.live import Live
from rich.table import Table
from rich import box 
from utils import simul_poisson

from Reactor import Reactor
from ReactorV2 import ReactorV2
from Neutron import Neutron



config = {
    'n' : 15, 
    'm' : 15, 
    'n_initial' : 10, 
    'd' : 0.5, 
    'a' : 0.1, 
    'f' : 0.6, 
    'l' : 20,
    'n_iter' : 200, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : True, 
    'colorized' : True, 
    'thermalization_probs': {'fast_to_epi': 0.5, 'epi_to_thermal': 0.5}
}

with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()