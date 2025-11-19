# ==========================================================================================
#                                 Random Generation Functions
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

def export_reactor(config, neutron_path, history_path, write_history, write_neutrons): 
    from ReactorV2 import ReactorV2
    from rich.live import Live 

    # Simulate reactor 
    print("========== Exporting Datas ==========")
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
        export_react_traj(history, temp, power, history_path)
        print("+ Done")
    if write_neutrons: 
        print("+ Exporting neutrons trajectories...")
        export_neutrons_traj(history, neutron_path)
        print("+ Done")


# -----------------------------------------
# Simulate Reactor and export trajectory 
# -----------------------------------------
def export_react_traj(history, temp, power, path): 
    from ReactorV2 import ReactorV2
    import pandas as pd 

    # Creating data to export 
    data = {
        "Iter" : [], 
        "Nb Neutrons" : [], 
        "Power" : [], 
        "Temperature" : []
    }
    for index, snapshot in enumerate(history):
        nb_neutrons = len(snapshot)
        data["Iter"].append(index + 1)
        data["Nb Neutrons"].append(nb_neutrons)
        data["Power"].append(power[index])
        data["Temperature"].append(temp[index])
    
    # Write in .CSV file 
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)


# -----------------------------------------------
# Simulate Reactor and export neutron trajectory 
# -----------------------------------------------
def export_neutrons_traj(history, path): 
    import csv

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


