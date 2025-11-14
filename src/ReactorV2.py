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
from controlRod import ControlRod

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

        # === Reactor parameters ===
        self.nominal_power_mw= 1000.0       #.MW
        self.power_level = 0.0              # Actual power in %
        self.current_power_mw = 0.0         # Actual power in MW 
        self.current_temperature = 300.0    #Temperature in Kelvin at t=0 (approx. 26.8°C)
        
        # Reactor informations to display 
        self.n_fissions = 0 
        self.fission_energy = 3.2 * 10**(-11)           # .Joules
        self.temp_history = [self.current_temperature]  # Initialisation with temperature at t=0 (parameters)
        self.power_history = [self.current_power_mw]    # Initialisation with power at t=0 (parameters)
        self.thermic_capacity = config["thermic_capacity"]
        self.loss_factor = config['loss_factor']

#--------------------------------EN TRAVAUX-----------------------------------------------
        # === Controls Rods Parameters ===
        self.rod_active = config.get('rod_active', False)   # If we want to use control rod (no implemented yet)

        self.control_rods = []
        config_rods_list = config.get('control_rods', [])
        for rod_config in config_rods_list:
            self.control_rods.append(
                ControlRod(id = rod_config['id'], type=rod_config['type'], x_pos=rod_config['x_pos'])   ############MODIF
            )
        
        # To simplify, we will only use these two types of bars
        self.regulation_rods = [rod for rod in self.control_rods if rod.type == 'regulation']
        self.scram_rods = [rod for rod in self.control_rods if rod.type == 'scram']
        
        # This is the threshold beyond which the emergency bars activate
        # It represente 1.5 * max_power
        self.scram_threshold = config.get('scram_threshold', 1.5)
        self.scram_triggered = False    # Flag to indicate if scram has been triggered

        # !!! We have to ajust this parameters !!!
        self.reg_base_position = 50.0   # Base position for regulation rods (in percent)
        self.reg_kp = 10.0              # Proportional gain for
        self.reg_ki = 1.0               # Integral gain
        self.reg_integral_error = 0.0   # Memory of the integral error
        self.power_setpoint = 1.0       # Target power level (1.0 = 100%)
        self.dt = 0.1                   # Time step for control rod updates (seconds)
        self.power_scaling_factor = 1.5e17
#---------------------------------------------------------------------------------------------

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

                start_x = np.clip(raw_x, 0, self.n - 1)             # Clip to be sure to be in the grid
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

        """
        base_a = self.a
        base_f = self.f

        # Initialization of probabilities at the first turn
        current_a = self.a
        current_f = self.f
        """


        for _ in range(self.n_iter):
            # 1. Reset the counters
            self.n_fissions = 0

            """
            # 2. Calculate rods effects on the previous turn
            # 1 pcm = 1e-5 delta k/k
            # if rho_rods_pcm is negative, it means we have less fission reactions
            rho_rods_pcm = sum(rod.get_reactivity_pcm() for rod in self.control_rods)
            rho_rods_abs = rho_rods_pcm / 1e5
            reactivity_factor = 1.0 + rho_rods_abs
            if reactivity_factor < 0.0 : 
                reactivity_factor = 0.0

            # Actualisation of the probabilities
            current_f = base_f * reactivity_factor
            current_a = base_a + (base_f - current_f)   # To keep the same ratio between a and f
            """


            # 3. Simulate neutrons with new probabilities
            new_neutrons = []
            alive_neutrons = []

            for neutron in self.neutrons: 
                #next_id, new_neutrons, alive_neutrons = self.update_neutron(neutron, next_id, new_neutrons, alive_neutrons, current_a, current_f)
                next_id, new_neutrons, alive_neutrons = self.update_neutron(neutron, next_id, new_neutrons, alive_neutrons)

            # Update population
            new_neutrons.extend(alive_neutrons)
            self.neutrons = new_neutrons

            # 4. Physical measurement
            # We calculate : P(MW), P(%), T(K)
            self.update_temperature_and_power_level()

            # 5. Rods pilotage
            # Check scram level
            self.check_emergency_scram()

            # Launch automatic pilote
            self.update_automatic_control_rods()
            
            #-------------------DEBUG-------------------
            for rod in self.control_rods:
                print(f"target position {rod.id}", rod.target_position)
                print(f"current position {rod.id}", rod.position_percent)
            #------------------------------------------

            # Move the bars accordingly
            # Their new position will be taken into account in the next round
            for rod in self.control_rods:
                rod.step(self.dt)
            
            # 6. History and display
            state_snapshot = {n.id : (n.x,n.y,n.type) for n in self.neutrons}
            self.history.append(state_snapshot)

            if self.display == True: 
                if self.colorized:
                    self.display_reactor_colorized()
                else:
                    self.display_reactor()
            
            if self.verbose: 
                system('clear')
                print("=========== Running Class II Reactor ===========")
                print(f"Iteration : {len(self.history)} / {self.n_iter}")
                print(f"Nb of neutrons : {len(self.neutrons)}")
        return self.history
    
    # ------------------------------------------------------------------
    # Update neutron position/state at each iteration
    # current_a & current_f are the new probabilities
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Update neutron position/state at each iteration
    # ------------------------------------------------------------------
    # Inputs: 
    #     - neutron : neutron we will update
    #     - next_id : id of the new generation
    #     - new_neutrons : list containing the new neutrons
    #     - alive_neutrons : neutrons still alive
    # Returns:
    #     - 0 for diffusion, 1 for absorption, 2 for fission
    #def update_neutron(self, neutron, next_id, new_neutrons, alive_neutrons, current_a, current_f):
    def update_neutron(self, neutron, next_id, new_neutrons, alive_neutrons):
        # === 1. Check if neutron is alive ===
        if not neutron.is_alive: 
            return next_id, new_neutrons, alive_neutrons
        
        """
            Neutron react only if it's a thermal one. 
            In the other cases, it diffuse or it's absobrd by the reactor.
        """

        for rod in self.control_rods:
            if rod.is_neutron_absorbed(neutron.x, neutron.y, self.n):
                neutron.is_alive = False
                return next_id, new_neutrons, alive_neutrons



        # === 2. Choose action based on his type ===
        if neutron.type == "thermal": 
            # Choose an action for a thermal one 
            action = self.choose_action_thermal()
            #action = self.choose_action_thermal(current_a, current_f)   ###### MODIFICATION ICI ######

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
            #action = self.choose_action_other(current_a)    ###### MODIFICATION ICI ######
            if action == 0: 
                # Diffusion 
                neutron.diffuse(self.max_speed)
            
            elif action == 1: 
                # Absorption 
                neutron.is_alive = False 
                return next_id, new_neutrons, alive_neutrons 

        # === 3. Update internal neutron state ===
        neutron.evolve(self.moderator)

        # Applic toric 
        if self.toric: 
            neutron.x %= self.n 
            neutron.y %= self.m
        
        # === 4. Test if the neutron is in the grid ===
        if self.is_in_the_grid(neutron.x, neutron.y): 
            alive_neutrons.append(neutron)
        
        return next_id, new_neutrons, alive_neutrons


    # ------------------------------------------------------------------
    # Choose which action to perform for a neutron at each iteration
    # ------------------------------------------------------------------
    # Inputs: 
    #     - d : diffusion probability
    #     - current_a : absorption probability
    #     - current_f : fission probability
    # Returns:
    #     - 0 for diffusion, 1 for absorption, 2 for fission
    #def choose_action_thermal(self, current_a, current_f):      ###### MODIFICATION ICI ######
    def choose_action_thermal(self):
        """
            Choose an action to perform depending on the moderator used. 
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
            #a, d, f = current_a, self.moderator.diffuse_coeff, current_f            #######MODIFICATION ICI#########
            total = a + d + f 
            d1, a1 = d/total, a/total 
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
            
    
    #def choose_action_other(self, current_a):      ###### MODIFICATION ICI ######
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
            #a, d = current_a, self.moderator.diffuse_coeff           ###### MODIFICATION ICI ######
            total = a + d 
            d1 = d/total 
            u = npr.rand()
            if u < d1 : 
                return 0 
            return 1

    
    # ------------------------------------------------------------------
    # Check if a position is within the grid
    # ------------------------------------------------------------------
    # Inputs:
    #     - x, y : coordinates to check
    #     - n, m : size of the grid
    # Returns:
    #     - True if the position is inside the grid, False otherwise
    def is_in_the_grid(self, i, j): 
        return 0 <= i < self.n and 0 <= j < self.m

    # ------------------------------------------------------------------
    # New function to calculate :
    # Calculate current reactor power in MW & %
    # Calculate current reactor temperature of the reactor
    # ------------------------------------------------------------------
    def update_temperature_and_power_level(self):
        """
            Updates power (MW), power level (%), and temperature (K)
        """

        # === 1. Calculate power (MW) ===
        # (Energie totale) / (Temps)
        energy_joules_per_step = self.n_fissions * self.fission_energy          # .Joules
        power_watts_micro = energy_joules_per_step / self.dt                    # .Watts

        #------------------TEST--------------
        # les valeurs sont trop basses donc j'ai utilisé un facteur 
        # multiplicateur pour augmenter la puissance et voir ce que ca donne
        power_watts = power_watts_micro * self.power_scaling_factor
        #------------------------------------

        self.current_power_mw = power_watts / 1e6                       # Conversion between W -> MW
        self.power_history.append(self.current_power_mw)

        # === 2. Maj power level(%) for the regulator rod ===
        if self.nominal_power_mw > 0:
            self.power_level = self.current_power_mw / self.nominal_power_mw
        else:
            self.power_level = 0.0

        # === 3. Maj temperature (based on power in watts) ===
        power_net_watts = power_watts * (1 - self.loss_factor)

        # === 4. Temperature variation ===
        # dT = (P_net / C) * dt
        dT_per_step = (power_net_watts / self.thermic_capacity) * self.dt

        self.current_temperature += dT_per_step
        self.temp_history.append(self.current_temperature)


    """
    # ------------------------------------------------------------------
    # Calculate current reactor power
    # ------------------------------------------------------------------
    def update_power(self):
        self.power_history.append((self.n_fissions * self.fission_energy) / 1e6)


    # ------------------------------------------------------------------
    # Calculate current reactor temperature of the reactor 
    # ------------------------------------------------------------------
    def update_temperature(self):
        if not self.power_history:
            self.temp_history.append(self.current_temperature)
            return
        
        # Power in watts (pwoer_history is in MW)
        power_watts = (self.power_history[-1] * 1e6) * (1 - self.loss_factor)

        # Temperature variation (dT/dt)
        dT_per_step = (power_watts / self.thermic_capacity) * self.dt

        # New temperature
        self.current_temperature += dT_per_step
        self.temp_history.append(self.current_temperature)
        # ---------Previous version---------
        #self.temp_history.append((self.power_history[-1] * (1 - self.loss_factor)) / self.thermic_capacity)

    """

    # ------------------------------------------------------------------
    # Display Reactor State
    # ------------------------------------------------------------------ 
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
    
  
    # ------------------------------------------------------------------
    # Display Reactor State with colors 
    # ------------------------------------------------------------------
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
        
        #-----------------------------------------------
        rod_depth = "N/A"
        if self.regulation_rods:
            rod_depth = f"{100.0 - self.regulation_rods[0].position_percent:.2f}%" 
            print(f"reg {self.regulation_rods[0].position_percent:.2f}")
        #-----------------------------------------------

        info_text = (
            f"[bold cyan]Temperature :[/bold cyan] {temperature} K\n"
            f"[bold yellow]Power :[/bold yellow] {power} MW\n"
            f"[bold magenta]Neutrons :[/bold magenta] {total_neutrons}\n"
            f"[bold green]Depth of regulating bars :[/bold green] {rod_depth}\n"
            f"[red]SCRAM bars used :[/red] {self.scram_triggered}\n"
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

# -----------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Update control rods positions based on power error
    # ------------------------------------------------------------------
    def update_automatic_control_rods(self):
        if not self.regulation_rods:
            return "ALERT : No control bar was detected"
        
        # === 1. Calculate error between current power and target power ===
        error = self.power_setpoint - self.power_level
        print("test power error", error)

        # === 2. Simple proportional control ===
        kp = self.reg_kp * error

        # === 3. Integral term (with anti-windup) ===
        self.reg_integral_error += error * self.dt
        self.reg_integral_error = max(-1.0, min(1.0, self.reg_integral_error))
        i_term = self.reg_ki * self.reg_integral_error

        # === 4. Calculate new target position for regulation rods ===
        target_position = self.reg_base_position + kp + i_term
        print("test target_position", target_position)

        # === 5. Send instruction to each regulation rod ===
        clamped_target = max(0.0, min(100.0, target_position))
        print("test clamped_target", clamped_target)
        for rod in self.regulation_rods:
            rod.target_position = clamped_target

    # ------------------------------------------------------------------
    # Check if an emergency scram is needed based on reactor conditions
    # If so, insert scram rods fully and immediately
    # ------------------------------------------------------------------
    def check_emergency_scram(self):
        if not self.scram_rods:
            return "ALERT : emergency scram undected."

        if self.power_level > self.scram_threshold and not self.scram_triggered:
            print("!!! EMERGENCY SCRAM ACTIVATED !!!")
            
            #-------------DEBUG--------
            print("scram_threshold", self.scram_threshold)
            print("scram_triggered", self.scram_triggered)
            #--------------------------

            self.scram_triggered = True

            for rod in self.scram_rods:
                rod.target_position = 0.0  # Fully inserted

            #--------------TEST------------
            self.regulation_rods = None  # Disable regulation rods after scram
            #------------------------------