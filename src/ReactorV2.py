# ==========================================================================================
#                                      Reactor Class (v2)
# ==========================================================================================

import numpy as np 
import numpy.random as npr 
from time import sleep 
from rich.table import Table
from rich import box 
from rich.text import Text

from utils import simul_poisson

from Neutron import Neutron


class ReactorV2: 
    """
        Creates a new type of reactor implementing neutron agents. Each neutron evolves 
        separately with is own parameters. 
    """

    def __init__(self, live, config): 
        self.n = config['n'] 
        self.m = config['m']
        self.n_initial = config['n_initial']
        self.d = config['d']
        self.a = config['a']
        self.f = config['f']
        self.l = config['l']
        self.n_iter = config['n_iter'] 
        self.max_speed = config['max_speed']
        self.state = {i: (self.n // 2 + 1 , self.m // 2 + 1) for i in range(self.n_initial)} 
        self.live = live
        self.toric = config['toric']
        self.display = config['display']
        self.colorized = config['colorized']
        self.thermalization_probs = config['thermalization_probs']

        # Create neutrons 
        self.neutrons = [
            Neutron(i, self.n // 2, self.m // 2, self.thermalization_probs, npr.choice(["fast", "epithermal"])) for i in range(self.n_initial)
        ]

        # Save neutron differents states to display grid 
        self.neutron_states = {"fast" : 0, "thermal" : 1, "epithermal" : 2}

        """
            We instanciate Neutrons list with only fast and epithermal neutrons with will need to 
            slow down to produce fission reactions. 
        """

    # ------------------------------------------------------------------
    # Simulate a ReactorV2 process
    # ------------------------------------------------------------------
    def simulate(self): 
        history = []
        next_id = len(self.neutrons)

        for _ in range(self.n_iter): 
            new_neutrons = []
            alive_neutrons = []

            for neutron in self.neutrons: 
                
                # Check if neutron is alive
                if not neutron.is_alive: 
                    continue 
                
                """
                Neutron react only if it's a thermal one. 
                In the other cases, it diffuse or it's absobrd by the reactor.
                """

                if neutron.type == "thermal": 
                    # Choose an action for a thermak one 
                    action = self.choose_action_thermal()

                    if action == 0: 
                        # Diffusion 
                        neutron.diffuse(self.max_speed)
                    
                    elif action == 1: 
                        # Absorption 
                        neutron.is_alive = False 
                        continue 

                    else :
                        n_new = simul_poisson(self.l)
                        for _ in range(n_new): 
                            new_neutrons.append(
                                Neutron(next_id, neutron.x, neutron.y, self.thermalization_probs, type='fast', speed=1.0)
                            )
                            next_id += 1
                else : 
                    action = self.choose_action_other()

                    if action == 0: 
                        # Diffusion 
                        neutron.diffuse(self.max_speed)
                    
                    elif action == 1: 
                        # Absorption 
                        neutron.is_alive = False 
                        continue 

                # Update internal neutron state
                neutron.evolve()

                # Applic toric 
                if self.toric: 
                    neutron.x %= self.n 
                    neutron.y %= self.m
                
                if self.is_in_the_grid(neutron.x, neutron.y): 
                    alive_neutrons.append(neutron)
                
            # Update population 
            self.neutrons = new_neutrons + alive_neutrons

            # Record history 
            state_snapshot = {n.id : (n.x,n.y,n.type) for n in self.neutrons}
            history.append(state_snapshot)

            if self.display == True: 
                if self.colorized:
                    self.display_reactor_colorized()
                else:
                    self.display_reactor()
        return history
            



    # ------------------------------------------------------------------
    # Choose which action to perform for a neutron at each iteration
    # ------------------------------------------------------------------
    # Inputs: 
    #     - d : diffusion probability
    #     - a : absorption probability
    #     - f : fission probability
    # Returns:
    #     - 0 for diffusion, 1 for absorption, 2 for fission
    def choose_action_thermal(self): 
        total = self.d + self.a + self.f
        d1, a1 = self.d/total, self.a/total
        u = npr.rand()
        if u < d1: 
            return 0 
        elif u < a1 + d1: 
            return 1 
        return 2
    
    def choose_action_other(self): 
        total = self.d + self.a
        d1 = self.d/total
        u = npr.rand()
        if u < d1: 
            return 0 
        return 1
    
    # -----------------------------------------
    # Check if a position is within the grid
    # -----------------------------------------
    # Inputs:
    #     - x, y : coordinates to check
    #     - n, m : size of the grid
    # Returns:
    #     - True if the position is inside the grid, False otherwise
    def is_in_the_grid(self, i, j): 
        return 0 <= i < self.n and 0 <= j < self.m

    # -----------------------
    # Display Reactor State
    # ----------------------- 
    def display_reactor(self): 
        # Build grid 
        grid = np.zeros((self.n, self.m))
        for neutron in self.neutrons: 
            if neutron.is_alive: 
                grid[neutron.x, neutron.y] += 1
        
        # Create the table to Live
        table = Table(show_header=False, show_lines=True)
        for line in grid:
            table.add_row(*[str(int(x)) if x > 0 else ' ' for x in line])
        self.live.update(table)
        sleep(0.2)
    
    # -------------------------------------
    # Display Reactor State with colors 
    # -------------------------------------
    def display_reactor_colorized(self): 
        grid = [[{"fast" : 0, "thermal" : 0, "epithermal" : 0} for _ in range(self.n)] for _ in range(self.m)]
        # Add neutron type on the grid 
        for neutron in self.neutrons: 
            if neutron.is_alive: 
                grid[neutron.x][neutron.y][neutron.type] += 1
        
        # Calculate average type 
        table = Table(show_header=False, show_lines=True, box=box.SQUARE)
        color = {
            "fast": "red",
            "epithermal": "yellow",
            "thermal": "blue"
        }

        for i in range(self.n): 
            row = []
            for j in range(self.m): 
                total = sum(grid[i][j].values())
                if total == 0 : 
                    row.append(' ')
                else :
                    # Find dominant type 
                    dominant = max(grid[i][j], key=grid[i][j].get)
                    text = Text(str(total), style=f"bold {color[dominant]}")
                    row.append(text)
            table.add_row(*row)
        self.live.update(table)
        sleep(0.2)



