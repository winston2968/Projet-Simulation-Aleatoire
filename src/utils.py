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
    # We take min (5,.) because the fission can produce max 5 neutrons
    # We take max(2,.) beacause the fission cant produce less than 2 neutrons
    return min(5, max(2, int(np.ceil(-(1/l) * np.log(npr.rand())))))


# ---------------------------- CSV Export --------------------------------------------------
import pandas as pd

def export_data(reactor, config, output_folder="statistics_output"):
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
    settings_filename = f"settings_{timestamp}.csv"
    history_filename = f"reactor_history_{timestamp}.csv"
    fission_filename = f"fission_stat_{timestamp}.csv"
    neutrons_filename = f"neutrons_trajectories_{timestamp}.csv"
    settings_path = os.path.join(export_simulation_folder, settings_filename)
    history_path = os.path.join(export_simulation_folder, history_filename)
    fission_path = os.path.join(export_simulation_folder, fission_filename)
    neutrons_path = os.path.join(export_simulation_folder, neutrons_filename)

    # Launch export
    print(f"========== Exporting Data ({timestamp}) ==========")
    export_react_traj(reactor, history_path)
    export_neutrons_traj(reactor.history, neutrons_path)
    export_settings(reactor, config, settings_path)
    print("========== Export Done ==========")


# -----------------------------------------
# Export trajectory 
# -----------------------------------------
def export_react_traj(reactor, path:str):
    print(f"+ Exporting reactor metrics to {path}")
    
    if not reactor.fission_stat_history:
        print("No fission stats to export.")
        return
    
    min_len = min(len(reactor.history), len(reactor.power_history), len(reactor.temp_history))

    # Creating data to export 
    data = {
        "time_step": list(range(min_len)),
        "nb_neutrons": [len(snap) for snap in reactor.history[:min_len]],
        "power_mw": reactor.power_history[:min_len],
        "temperature_k": reactor.temp_history[:min_len],
        "time_step": list(range(len(reactor.fission_stat_history)))
    }

    # Add rod history
    if reactor.rod_active and reactor.rod_history and min_len > 0 :
        data["rod_active"] = reactor.rod_active
        data["scram_triggered"] = reactor.scram_triggered
        first_record = reactor.rod_history[0]
        rod_ids = first_record.keys()
        for rod_id in rod_ids:
            column_name = f"pos_{rod_id}"
            data[column_name] = [snap[rod_id] for snap in reactor.rod_history[:min_len]]

    for nb in [2, 3, 4, 5]:
        data[f"fissions_prod_{nb}"] = []

    for step_stats in reactor.fission_stat_history:
        for nb in [2, 3, 4, 5]:
            count = step_stats.get(nb, 0)
            data[f"fissions_prod_{nb}"].append(count)

    # Write in .CSV file 
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print("+ Done.")


# -----------------------------------------------
# Export neutron trajectory 
# -----------------------------------------------
def export_neutrons_traj(history, path:str): 
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
    print("+ Done.")


# -----------------------------------------------
# Export settings
# -----------------------------------------------
def export_settings(reactor, config:dict, path:str):
    print(f"+ Exporting simulation settings to {path}")

    all_data = config.copy()

    reactor_state = {
        "--- REACTOR INTERNAL STATE ---": "",
        "final_nominal_power_mw": reactor.nominal_power_mw,
        "final_power_level": reactor.power_level,
        "final_current_power_mw": reactor.current_power_mw,
        "final_current_temperature": reactor.current_temperature,
        "final_n_fissions": reactor.n_fissions,
        "physics_fission_energy": reactor.fission_energy,
        "physics_temp_coolant": reactor.temp_coolant,
        "physics_cooling_coef": reactor.cooling_coef,
        "rod_active": reactor.rod_active,
        "--- REGULATION SETTINGS ---": "",
        "scram_threshold": reactor.scram_threshold,
        "scram_triggered": reactor.scram_triggered,
        "reg_base_position": reactor.reg_base_position,
        "reg_kp": reactor.reg_kp,
        "reg_ki": reactor.reg_ki,
        "reg_integral_error": reactor.reg_integral_error,
        "power_setpoint": reactor.power_setpoint,
        "dt": reactor.dt,
        "power_scaling_factor": reactor.power_scaling_factor
    }

    all_data.update(reactor_state)
    df = pd.DataFrame.from_dict(all_data, orient='index', columns=['value'])
    df.index.name = 'parameter'

    df.to_csv(path, encoding='utf-8')
    print("+ Done.")