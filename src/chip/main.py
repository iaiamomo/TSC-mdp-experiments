#!/usr/bin/env python
# coding: utf-8
import time, json
from datetime import datetime
from memory_profiler import profile
from stochastic_service_composition.declare_utils import *
from stochastic_service_composition.composition_mdp import composition_mdp
from stochastic_service_composition.composition_mdp import comp_mdp
from mdp_dp_rl.algorithms.dp.dp_analytic import DPAnalytic
from src.chip.utils import print_policy_data
from src.chip.setup import *
import os
import pickle


# create folder if not exists
if not os.path.exists('experimental_results'):
    os.makedirs('experimental_results')

config_json = json.load(open('config.json', 'r'))
mode = config_json['mode']
size = config_json['size']
gamma = config_json['gamma']
serialize = config_json['serialize']

now = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")

directory = f"experimental_results"
file_name = f"{directory}/{now}_time_profiler_{mode}_{size}_{gamma}.txt"
fp_compMDP = f"{directory}/{now}_memory_profiler_composition_{mode}_{size}_{gamma}.log"
fp_DPAnalytic = f"{directory}/{now}_memory_profiler_policy_{mode}_{size}_{gamma}.log"

# AUTOMATA
@profile(stream=open(fp_compMDP, "w+"))
def execute_composition_automata(target, services):
    mdp = composition_mdp(target, *services, gamma=gamma)
    return mdp

# LTLf
@profile(stream=open(fp_compMDP, "w+"))
def execute_composition_ltlf(declare_automaton, services):
    mdp = comp_mdp(declare_automaton, services, gamma=gamma)
    return mdp

# POLICY
@profile(stream=open(fp_DPAnalytic, "w+"))
def execute_policy(mdp):
    mdp.gamma = gamma
    opn = DPAnalytic(mdp, 1e-4)
    opt_policy = opn.get_optimal_policy_vi()
    return opt_policy
    
def main():
    to_write = f"Mode: {mode}\nSize: {size}\nGamma: {gamma}\nSerialize: {serialize}"
    with open(file_name, "w+") as f:
        f.write(f"{to_write}\n")
    print(to_write)

    all_services = process_services(size)
    target = target_service_automata() if mode == "automata" else target_service_ltlf()

    to_write = f"Tot_services: {len(all_services)}"
    with open(file_name, "a") as f:
        f.write(f"{to_write}\n")
    print(to_write)
    
    print("Services created.\nStarting composition...")

    # AUTOMATA
    if mode == "automata":
        # check if the pickle file exists and has size > 0
        if serialize and os.path.isfile(f'mdp_{mode}_{size}.pkl') and os.path.getsize(f'mdp_{mode}_{size}.pkl') > 0:
            print("MDP already computed. Importing from pickle file...")
            #import the mdp from the pickle file
            with open(f'mdp_{mode}_{size}.pkl', 'rb') as f:
                mdp = pickle.load(f)
            elapsed1 = 0
        else:
            print("MDP not computed yet. Computing...")
            now = time.time_ns()
            mdp = execute_composition_automata(target, all_services)
            elapsed1 = (time.time_ns() - now) / 10 ** 9
            if serialize:
                #save mdp into a pickle file
                try:
                    with open(f'mdp_{mode}_{size}.pkl', 'wb') as f:
                        pickle.dump(mdp, f, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        states = len(mdp.all_states)
        with open(file_name, "a") as f:
            to_write = f"MDP states: {states}\nComposition elapsed time: {elapsed1} s\n"
            f.write(to_write)
        print("Number of states: ", states)
        print("Composition MDP computed.\nStarting computing policy...")
        now = time.time_ns()
        opt_policy = execute_policy(mdp)
        elapsed2 = (time.time_ns() - now) / 10 ** 9
        with open(file_name, "a") as f:
            to_write = f"Policy elapsed time: {elapsed2} s\n"
            f.write(to_write)
    # LTLf
    elif mode == "ltlf":
        # check if the pickle file exists and has size > 0
        if serialize and os.path.isfile(f'mdp_{mode}_{size}.pkl') and os.path.getsize(f'mdp_{mode}_{size}.pkl') > 0:
            print("MDP already computed. Importing from pickle file...")
            #import the mdp from the pickle file
            with open(f'mdp_{mode}_{size}.pkl', 'rb') as f:
                mdp = pickle.load(f)
            elapsed1 = 0
        else:
            print("MDP not computed yet. Computing...")
            now = time.time_ns()
            mdp = execute_composition_ltlf(target, all_services)
            elapsed1 = (time.time_ns() - now) / 10 ** 9
            if serialize:
                #save mdp into a pickle file
                try:
                    with open(f'mdp_{mode}_{size}.pkl', 'wb') as f:
                        pickle.dump(mdp, f, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        states = len(mdp.all_states)
        with open(file_name, "a") as f:
            to_write = f"MDP states: {states}\nComposition elapsed time: {elapsed1} s\n"
            f.write(to_write)
        print("Number of states: ", states)
        print("Composition MDP computed.\nStarting computing policy...")
        now = time.time_ns()
        opt_policy = execute_policy(mdp)
        elapsed2 = (time.time_ns() - now) / 10 ** 9
        with open(file_name, "a") as f:
            to_write = f"Policy elapsed time: {elapsed2} s\n"
            f.write(to_write)
    
    print("Policy computed.")

    #print("Writing policy...")
    #print_policy_data(opt_policy, file_name=file_name)

    print("Done.")
            
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        with open(file_name, "w+") as f:
            to_write = f"Execution failed: {e}"
            f.write(to_write)
