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

    def __init__(self, name:str, absorb_coeff:float, diffuse_coeff:float, fission_coeff:float, slow_fast, slow_epi=0.3): 
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

    def __init__(self, live, config:dict): 
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
        self.nominal_power_mw= 1000.0       # .MW
        self.power_level = 0.0              # Actual power in %
        self.current_power_mw = 0.0         # Actual power in MW 
        self.current_temperature = 300.0    # Temperature in Kelvin at t=0 (approx. 26.8°C)
        
        # Reactor informations to display 
        self.n_fissions = 0 
        self.fission_energy = 3.2 * 10**(-11)               # .Joules
        self.temp_history = [self.current_temperature]      # Initialisation with temperature at t=0 (parameters)
        self.power_history = [self.current_power_mw]        # Initialisation with power at t=0 (parameters)
        self.thermic_capacity = config["thermic_capacity"]
        self.temp_coolant = 300.0                           # Cooling water base temperature
        self.cooling_coef = self.thermic_capacity * 0.05    # Cooling water loss coefficient

        # === Controls Rods Parameters ===
        self.rod_active = config.get('rod_active', False)
        
        # Add control rods to a global list
        self.control_rods = []
        config_rods_list = config.get('control_rods', [])
        for rod_config in config_rods_list:
            self.control_rods.append(
                ControlRod(id = rod_config['id'], type=rod_config['type'])
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
                                        # 100.0 = OUT - 0.0 = IN
        self.reg_kp = 25.0              # Proportional gain for
        self.reg_ki = 10.0              # Integral gain
        self.reg_integral_error = 0.0   # Memory of the integral error
        self.power_setpoint = 1.0       # Target power level (1.0 = 100%)
        self.dt = 0.1                   # Time step for control rod updates (seconds)
        self.power_scaling_factor = 1.5e17

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
    def init_neutrons(self, config:dict): 
        # === 1. Create neutrons according to the associated law ===
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

        # === 0. Initialization of probabilities at the first turn ===
        if self.moderator:
            base_a = self.moderator.absorb_coeff
            base_f = self.moderator.fission_coeff
            base_d = self.moderator.diffuse_coeff
        else:
            base_a = self.a
            base_f = self.f
            base_d = self.d        

        for _ in range(self.n_iter):
            # === 1. Reset the counters ===
            self.n_fissions = 0

            # === 2. Calculate rods effects on the previous turn ===
            if self.rod_active:
                # 1 pcm = 1e-5 delta k/k
                # if rho_rods_pcm is negative, it means we have less fission reactions
                rho_rods_pcm = sum(rod.get_reactivity_pcm() for rod in self.control_rods)
                rho_rods_abs = rho_rods_pcm / 1e5
                reactivity_factor = 1.0 + rho_rods_abs
                if reactivity_factor < 0.0 : 
                    reactivity_factor = 0.0
            else:
                reactivity_factor = 1.0

            # Actualisation of the probabilities
            # Rod have not effect on diffus_coef
            current_f = base_f * reactivity_factor
            current_a = base_a + (base_f - current_f)   # To keep the same ratio between a and f

            # === 3. Simulate neutrons with new probabilities ===
            new_neutrons = []
            alive_neutrons = []

            for neutron in self.neutrons: 
                next_id, new_neutrons, alive_neutrons = self.update_neutron(neutron, next_id, new_neutrons, alive_neutrons, base_a, current_a, current_f, base_d)

            # Update population
            new_neutrons.extend(alive_neutrons)
            self.neutrons = new_neutrons

            # === 4. Physical measurement ===
            # We calculate : P(MW), P(%), T(K)
            self.update_temperature_and_power_level()

            # === 5. Rods pilotage ===
            if self.rod_active:
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
            
            # === 6. History and display ===
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
    def update_neutron(self, neutron:Neutron, next_id:int, new_neutrons:list, alive_neutrons:bool, base_a:float, current_a:float, current_f:float, base_d:float):
        # === 1. Check if neutron is alive ===
        if not neutron.is_alive: 
            return next_id, new_neutrons, alive_neutrons
        
        """
            Neutron react only if it's a thermal one. 
            In the other cases, it diffuse or it's absobrd by the reactor.
        """

        # === 2. Choose action based on his type ===
        if neutron.type == "thermal": 
            # Choose an action for a thermak one
            action = self.choose_action_thermal(current_a, current_f, base_d)

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
            action = self.choose_action_other(base_a, base_d)
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
        
        # === 4. Test if neutron is in the grid ===
        if self.is_in_the_grid(neutron.x, neutron.y): 
            alive_neutrons.append(neutron)
        
        return next_id, new_neutrons, alive_neutrons


    # ------------------------------------------------------------------
    # Choose which action to perform for a neutron at each iteration
    # Rods are only useful against thermal neutrons
    # For other types, the probabilities of fission and absorption remain unchanged
    # ------------------------------------------------------------------
    # Inputs: 
    #     - current_a : absorption probability
    #     - current_f : fission probability
    #     - base_a : base absorption probability for no thermal
    #     - base_d : diffusion probability
    # Returns:
    #     - 0 for diffusion, 1 for absorption, 2 for fission
    def choose_action_thermal(self, current_a:float, current_f:float, base_d:float):
        """
            Choose an action to perform depending on the moderator used. 
        """

        total = current_a + current_f + base_d
        d1 = base_d/total
        a1 = current_a/total
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


    def choose_action_other(self, base_a:float, base_d:float):
        total = base_a + base_d
        d1 = base_d/total
        u = npr.rand()
        if u < d1:
            return 0
        return 1

    
    # ------------------------------------------------------------------
    # Check if a position is within the grid
    # ------------------------------------------------------------------
    # Returns:
    #     - True if the position is inside the grid, False otherwise
    def is_in_the_grid(self, i:int, j:int): 
        return 0 <= i < self.n and 0 <= j < self.m


    # ------------------------------------------------------------------
    # Calculate current reactor power in MW & %
    # Calculate current reactor temperature of the reactor
    # ------------------------------------------------------------------
    def update_temperature_and_power_level(self):
        """
            Updates power (MW), power level (%), and temperature (K)
            Uses Newton's Law of Cooling
        """

        # === 1. Calculate generated power (MW) ===
        # (Energie totale) / (Temps)
        energy_joules_per_step = self.n_fissions * self.fission_energy          # .Joules
        power_watts_micro = energy_joules_per_step / self.dt                    # .Watts
        power_watts_generated = (power_watts_micro) * self.power_scaling_factor

        self.current_power_mw = power_watts_generated / 1e6                     # Conversion between W -> MW
        self.power_history.append(self.current_power_mw)

        # === 2. Update power level(%) for the regulator rod ===
        if self.nominal_power_mw > 0:
            self.power_level = self.current_power_mw / self.nominal_power_mw
        else:
            self.power_level = 0.0

        # === 3. Calculate cooling power (P_out) ===
        # P_out = h * (T_reacteur - T_eau)
        delta_T = self.current_temperature - self.temp_coolant
        power_watts_cooling = self.cooling_coef * delta_T

        # === 4. Temperature variation ===
        # P_net = P_in - P_out
        # dT = (P_net / C) * dt
        power_net_watts = power_watts_generated - power_watts_cooling
        dT_per_step = (power_net_watts / self.thermic_capacity) * self.dt

        self.current_temperature += dT_per_step
        self.temp_history.append(self.current_temperature)


    # ------------------------------------------------------------------
    # Display Reactor State
    # ------------------------------------------------------------------ 
    def display_reactor(self): 
        # === 1. Build grid ===
        grid = np.zeros((self.n, self.m))
        for neutron in self.neutrons: 
            if neutron.is_alive: 
                grid[neutron.x, neutron.y] += 1
        
        # === 2. Create the table to Live ===
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
        # === 1. Add neutron type on the grid ===
        for neutron in self.neutrons: 
            if neutron.is_alive: 
                grid[neutron.x][neutron.y][neutron.type] += 1
        
        # === 2. Calculate average type ===
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
        
        # === 3. Adding reactor infos on panel ===
        # Reactor infos
        total_neutrons = sum(1 for n in self.neutrons if n.is_alive)
        power = self.power_history[-1]
        temperature = self.temp_history[-1]
        
        # Rods infos
        if self.rod_active:
            rod_depth = "N/A"
            if self.regulation_rods:
                rod_depth = f"{100.0 - self.regulation_rods[0].position_percent:.2f}%" 
                print(f"reg {self.regulation_rods[0].position_percent:.2f}")
        else:
            rod_depth = "--SYSTEM OFF--"

        info_text = (
            f"[bold cyan]Temperature :[/bold cyan] {temperature} K\n"
            f"[bold yellow]Power :[/bold yellow] {power} MW\n"
            f"[bold magenta]Neutrons :[/bold magenta] {total_neutrons}\n"
            f"[bold green]Depth of regulating bars :[/bold green] {rod_depth}\n"
            f"[red]SCRAM bars used :[/red] {self.scram_triggered}\n"
        )

        info_panel = Panel(info_text, title="[bold white]Reactor State[/bold white]", border_style="bright_blue")

        # === 4. Compose different displays ===
        display = Group(
            Panel(table, title="[bold]Neutrons Distribution[/]"), 
            info_panel
        )
        # Display infos and reactor 
        self.live.update(display)
        sleep(0.2)


    # ------------------------------------------------------------------
    # Update control rods positions based on power error
    # ------------------------------------------------------------------
    def update_automatic_control_rods(self):
        if not self.regulation_rods:
            return "ALERT : Regulation rod undected."
        
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
        target_position = max(0.0, min(100.0, self.reg_base_position + kp + i_term))
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
            #-------------DEBUG#-------------
            print(f"!!! EMERGENCY SCRAM ACTIVATED !!!")
            print("scram_threshold", self.scram_threshold)
            print("scram_triggered", self.scram_triggered)
            #--------------------------------

            self.scram_triggered = True
            self.regulation_rods = None     # Disable autopilote
            
            for rod in self.control_rods:
                rod.target_position = 0.0   # Fully inserted