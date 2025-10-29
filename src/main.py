import numpy as np 
import numpy.random as npr 
from time import sleep 
from rich.live import Live
from rich.table import Table
from utils import simul_poisson

from Reactor import Reactor
from ReactorV2 import ReactorV2
from Neutron import Neutron



config = {
    'n' : 10, 
    'm' : 10, 
    'n_initial' : 10, 
    'd' : 0.5, 
    'a' : 0.2, 
    'f' : 0.5, 
    'l' : 10,
    'n_iter' : 50, 
    'max_speed' : 2, 
    'toric' : False, 
    'display' : True
}

with Live(refresh_per_second=10) as live: 
    reactorV2 = ReactorV2(live, config)
    history = reactorV2.simulate()