# ==========================================================================================
#                                 Random & Export Functions
# ==========================================================================================

# Poisson random variable generation
# Input: 
#     - l : mean of the Poisson distribution
# Returns: 
#     - integer representing a random value from a Poisson-like distribution
def simul_poisson(l): 
    import numpy as np 
    from numpy import random as npr
    return int(np.ceil(-(1/l) * np.log(npr.rand())))


# ---------------------------- CSV Export -----------------------------------
def export_data(reactor, output_folder="statistics_output"):
    from datetime import datetime
    import os

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    # Export folder check
    statistics_path_folder = os.path.join("statistics", output_folder)
    if not os.path.exists(statistics_path_folder):
        os.makedirs(statistics_path_folder)
        print(f"+ Created folder : {statistics_path_folder}")

    # Export folder for this simulation check
    export_simulation_folder = os.path.join(statistics_path_folder, timestamp)
    if not os.path.exists(export_simulation_folder):
        os.makedirs(export_simulation_folder)
        print(f"+ Created folder for this simulation : {export_simulation_folder}")

    # File name configuration
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    history_filename = f"reactor_history_{timestamp}.csv"
    neutrons_filename = f"neutrons_trajectories_{timestamp}.csv"
    history_path = os.path.join(export_simulation_folder, history_filename)
    neutrons_path = os.path.join(export_simulation_folder, neutrons_filename)

    # Launch export
    print(f"========== Exporting Data ({timestamp}) ==========")
    export_react_traj(reactor, history_path)
    export_neutrons_traj(reactor.history, neutrons_path)
    print("========== Export Done ==========")


"""
def export_reactor(config, write_history, write_neutrons, output_folder='data_export'): 
    from ReactorV2 import ReactorV2
    from rich.live import Live 
    import os
    from datetime import datetime

    # Export folder check
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"+ Created folder: {output_folder}")
    

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    history_file = os.path.join(output_folder, f"reactor_history_{timestamp}.csv")
    neutrons_file = os.path.join(output_folder, f"neutrons_trajectories_{timestamp}.csv")

    # Simulate reactor
    print(f"========== Exporting Datas ({timestamp})==========")
    print("+ Launching simulation...")
    with Live(refresh_per_second=10) as live: 
        reactorV2 = ReactorV2(live, config)
        history = reactorV2.simulate()
    temp = reactorV2.temp_history
    power = reactorV2.power_history 
    print("+ Simulation Done")

    # Export data
    if write_history: 
        print("+ Exporting reactor trajectory...")
        export_react_traj(history, temp, power, history_file)
        print("+ Done")
    if write_neutrons: 
        print("+ Exporting neutrons trajectories...")
        export_neutrons_traj(history, neutrons_file)
        print("+ Done")
"""


# -----------------------------------------
# Simulate Reactor and export trajectory 
# -----------------------------------------
def export_react_traj(reactor, path): 
    #from ReactorV2 import ReactorV2
    import pandas as pd 

    print(f"+ Exporting reactor metrics to {path}")
    
    min_len = min(len(reactor.history), len(reactor.power_history), len(reactor.temp_history))

    # Creating data to export 
    data = {
        "time_step": list(range(min_len)),
        "nb_neutrons": [len(snap) for snap in reactor.history[:min_len]],
        "power_mw": reactor.power_history[:min_len],
        "temperature_k": reactor.temp_history[:min_len]
    }
    
     # Add info on control rods
    if reactor.rod_active and reactor.regulation_rods:
        # not yet
        pass

    # Write in .CSV file 
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)


# -----------------------------------------------
# Simulate Reactor and export neutron trajectory 
# -----------------------------------------------
def export_neutrons_traj(history, path): 
    import csv

    print(f"+ Exporting detailed trajectories to {path}")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["time_step", "neutron_id", "x", "y", "type"])
        writer.writeheader()
        
        for t, snapshot in enumerate(history):
            for neutron_id, (x, y, neutron_type) in snapshot.items():
                writer.writerow({
                    "time_step": t,
                    "neutron_id": neutron_id,
                    "x": x,
                    "y": y,
                    "type": neutron_type
                })