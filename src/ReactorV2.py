# ==========================================================================================
#                                      Reactor Class (v2)
# ==========================================================================================

import numpy as np 
import numpy.random as npr 
from time import sleep 
from rich.table import Table
from rich import box 
from rich.text import Text
from rich.panel import Panel 
from rich.console import Group 
from os import system 

from utils import simul_poisson
from Neutron import Neutron

class Moderator: 
    """
    Slow down neutrons depending on its efficiency.
    """

    def __init__(self, name, absorb_coeff, diffuse_coeff, fission_coeff, slow_fast=0.5, slow_epi=0.3): 
        self.name = name 
        self.absorb_coeff = absorb_coeff
        self.diffuse_coeff = diffuse_coeff
        self.fission_coeff = fission_coeff
        self.slow_fast = slow_fast 
        self.slow_epi = slow_epi 


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
        self.live = live
        self.toric = config['toric']
        self.display = config['display']
        self.colorized = config['colorized']
        self.thermalization_probs = config['thermalization_probs']
        self.verbose = config['verbose']
        self.history = []

        # Reactor informations to display 
        self.n_fissions = 0 
        self.fission_energy = 3.2 * 10**(-11)
        self.temp_history = [0]
        self.power_history = [0]
        self.thermic_capacity = config["thermic_capacity"]
        self.loss_factor = config['loss_factor']
        
        
        # Different moderator properties 
        MODERATORS = {
            "light_water": Moderator("light_water", absorb_coeff=1.0, diffuse_coeff=1.2, fission_coeff=0.8, slow_fast=0.3, slow_epi=0.5),
            "graphite":   Moderator("graphite",   absorb_coeff=0.6, diffuse_coeff=1.0, fission_coeff=0.9, slow_fast=0.15, slow_epi=0.3),
            "heavy_water": Moderator("heavy_water", absorb_coeff=0.3, diffuse_coeff=1.1, fission_coeff=1.0, slow_fast=0.25, slow_epi=0.4),
        }
        if config['moderator'] in MODERATORS.keys(): 
            self.moderator = MODERATORS[config['moderator']]
        else : 
            self.moderator = None 


        # Save neutron differents states to display grid 
        self.neutron_states = {"fast" : 0, "thermal" : 1, "epithermal" : 2}

        # Init neutrons position 
        self.init_neutrons(config)

        """
            We instanciate Neutrons list with only fast and epithermal neutrons with will need to 
            slow down to produce fission reactions. 
        """

    # ------------------------------------------------------------------
    # Init Neutron Position
    # ------------------------------------------------------------------
    def init_neutrons(self, config): 

        # Create neutrons according to the associated law
        self.neutrons = []

        if config['initial_distribution'] == 'center':
            self.neutrons = [
                Neutron(n, self.n // 2, self.m // 2, self.thermalization_probs, "fast") for n in range(self.n_initial)
            ]
        elif config['initial_distribution'] == 'uniform':    
            for n in range(self.n_initial):
                # A coordinate is randomly pull from the grid
                start_x = npr.randint(0, self.n)
                start_y = npr.randint(0, self.m)

                self.neutrons.append(
                    Neutron(n, start_x, start_y, self.thermalization_probs, "fast")
                )
        elif config['initial_distribution'] == 'normal':
            """
                We center the distribution in the middle of the grid with a small std
                The neutrons will be in [7 - 3, 7 + 3] = [4, 10]
                This creates a central cluster approximately 7 squares wide
            """
            
            mean_x, mean_y = self.n//2, self.m//2   # If the reactor remains a square, we can simplify (to optimize the code) : mean_x = mean_y & std_x = std_y
            std_x, std_y = 1, 1

            for n in range(self.n_initial):
                raw_x = int(np.round(npr.normal(mean_x, std_x)))    # Round up to the nearest integer
                raw_y = int(np.round(npr.normal(mean_y, std_y)))

                start_x = np.clip(raw_x, 0, self.n - 1)     # Clip to be sure to be in the grid
                start_y = np.clip(raw_y, 0, self.m - 1)

                self.neutrons.append(
                    Neutron(n, start_x, start_y, self.thermalization_probs, "fast")
            )
        else :
            raise ValueError("Initial distribution not recognized. Choose between 'center', 'uniform' or 'normal'.")


    # ------------------------------------------------------------------
    # Simulate a ReactorV2 process
    # ------------------------------------------------------------------
    def simulate(self): 
        next_id = len(self.neutrons)

        for _ in range(self.n_iter): 
            new_neutrons = []
            alive_neutrons = []

            for neutron in self.neutrons: 
                next_id, new_neutrons, alive_neutrons = self.update_neutron(neutron, next_id, new_neutrons, alive_neutrons)

            # Update population
            #------------
            new_neutrons.extend(alive_neutrons) # More efficient
            self.neutrons = new_neutrons
            #self.neutrons = new_neutrons + alive_neutrons
            #------------

            # Record history 
            state_snapshot = {n.id : (n.x,n.y,n.type) for n in self.neutrons}
            self.history.append(state_snapshot)

            # Update reactor infos
            self.update_power()
            self.update_temperature()

            if self.display == True: 
                if self.colorized:
                    self.display_reactor_colorized()
                else:
                    self.display_reactor()
            if self.verbose: 
                system('clear')
                print("=========== Running Class II Reactor ===========")
                print("Iteration : ", len(self.history))
                print("Nb of neutrons : ", len(self.history[-1]))

        return self.history
    
    # ------------------------------------------------------------------
    # Update neutron position/state at each iteration
    # ------------------------------------------------------------------
    def update_neutron(self, neutron, next_id, new_neutrons, alive_neutrons):
        # Check if neutron is alive
        if not neutron.is_alive: 
            return next_id, new_neutrons, alive_neutrons
        
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
                return next_id, new_neutrons, alive_neutrons 

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
                return next_id, new_neutrons, alive_neutrons 

        # Update internal neutron state
        neutron.evolve(self.moderator)

        # Applic toric 
        if self.toric: 
            neutron.x %= self.n 
            neutron.y %= self.m
        
        if self.is_in_the_grid(neutron.x, neutron.y): 
            alive_neutrons.append(neutron)
        
        return next_id, new_neutrons, alive_neutrons



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
        """
        Choose an action to perform depending on the 
        moderator used. 
        """
        if self.moderator is None :
            total = self.d + self.a + self.f
            d1, a1 = self.d/total, self.a/total
            u = npr.rand()
            if u < d1: 
                # Diffuse
                return 0 
            elif u < a1 + d1: 
                # Absorb 
                return 1 
            # Fission
            self.n_fissions += 1
            return 2
        else: 
            a,d,f = self.moderator.absorb_coeff, self.moderator.diffuse_coeff, self.moderator.fission_coeff
            total = a + d + f 
            d1, a1 = d/total, a/total 
            u = npr.rand()
            if u < d1: 
                # Diffuse
                return 0
            elif u < a1:
                # Absorb  
                return 1 
            # Fission
            self.n_fissions += 1
            return 2 
            
    
    def choose_action_other(self): 
        if self.moderator is None : 
            total = self.d + self.a
            d1 = self.d/total
            u = npr.rand()
            if u < d1: 
                return 0 
            return 1
        else: 
            a,d = self.moderator.absorb_coeff, self.moderator.diffuse_coeff
            total = a + d 
            d1 = d/total 
            u = npr.rand()
            if u < d1 : 
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


    # ------------------------------------------------------------------
    # Calculate current reactor power
    # ------------------------------------------------------------------
    def update_power(self):
        self.power_history.append((self.n_fissions * self.fission_energy) / 1e6)


    # ------------------------------------------------------------------
    # Calculate current reactor temperature of the reactor 
    # ------------------------------------------------------------------
    def update_temperature(self):
        self.temp_history.append((self.power_history[-1] * (1 - self.loss_factor)) / self.thermic_capacity)


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
            "fast": "#B22222",
            "epithermal": "#FFD700",
            "thermal": "#1E90FF"
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
        
        # Adding reactor infos on panel 
        total_neutrons = sum(1 for n in self.neutrons if n.is_alive)
        power = self.power_history[-1]
        temperature = self.temp_history[-1]
        control_depth = getattr(self, "control_depth", 0)
        info_text = (
            f"[bold cyan]Temperature :[/bold cyan] {temperature} K\n"
            f"[bold yellow]Power :[/bold yellow] {power} MW\n"
            f"[bold magenta]Neutrons :[/bold magenta] {total_neutrons}\n"
            f"[bold green]Depth of bars :[/bold green] {control_depth:.2f}\n"
        )
        info_panel = Panel(info_text, title="[bold white]Reactor State[/bold white]", border_style="bright_blue")

        # Compose different displays 
        display = Group(
            Panel(table, title="[bold]Neutrons Distribution[/]"), 
            info_panel
        )
        # Display infos and reactor 
        self.live.update(display)
        sleep(0.2)





