import glob
import pandas as pd

if __name__ == "__main__":
    case_studies = ["ceramic", "chip", "motor"]
    dimensions = ["xsmall", "small", "medium", "large"]
    modes = ["automata", "ltlf"]
    gammas = [0.1, 0.3, 0.6, 0.9]

    results = []
    for case_study in case_studies:
        for mode in modes:
            for dimension in dimensions:
                mem_comp = 0
                time_comp = 0
                n_services = 0
                n_states = 0
                for gamma in gammas:
                    fn_comp = glob.glob(f"../{case_study}/experimental_results/*memory_profiler_composition_{mode}_{dimension}_{gamma}.log")[0]
                    fn_policy = glob.glob(f"../{case_study}/experimental_results/*memory_profiler_policy_{mode}_{dimension}_{gamma}.log")[0]
                    fn_time = glob.glob(f"../{case_study}/experimental_results/*time_profiler_{mode}_{dimension}_{gamma}.txt")[0]
                    with open(fn_comp, 'r') as file:
                        file_lines = file.readlines()
                    if mem_comp == 0:
                        mem_comp = float(file_lines[7].split()[1].strip())
                    with open(fn_time, 'r') as file:
                        file_lines = file.readlines()
                    if n_services == 0:
                        n_services = int(file_lines[4].split(":")[1].strip())
                    if n_states == 0:
                        n_states = int(file_lines[5].split(":")[1].strip())
                    if time_comp == 0:
                        time_comp = float(file_lines[6].split(":")[1][:-2].strip())
                    time_policy = float(file_lines[7].split(":")[1][:-2].strip())

                    results.append([case_study, dimension, mode, gamma, n_services, n_states, mem_comp, time_comp, time_policy])

    df = pd.DataFrame(results, columns=["case_study", "dimension", "mode", "gamma", "n_services", "n_states", "mem_tot", "comp_time", "policy_time"])
    print(df)
    df.to_csv("experimental_results.csv", sep=",", index=False)
