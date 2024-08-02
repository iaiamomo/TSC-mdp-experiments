import matplotlib.pyplot as plt
import pandas as pd

if __name__ == "__main__":
    df = pd.read_csv("experimental_results.csv")
    print(df)

    case_studies = ["ceramic", "chip", "motor"]
    dimensions = ["xsmall", "small", "medium", "large"]
    modes = ["automata", "ltlf"]
    gammas = [0.1, 0.3, 0.6, 0.9]


    for case_study in case_studies:

        mems = {}
        services = {}
        states = {}
        times_comp = {}
        times_gamma_pol = {}
        for mode in modes:
            mems[mode] = []
            services[mode] = []
            states[mode] = []
            times_comp[mode] = []
            for dimension in dimensions:
                mems[mode].append(df[(df["case_study"] == case_study) & (df["mode"] == mode) & (df["dimension"] == dimension) & (df["gamma"] == 0.9)]["mem_tot"].values[0])
                services[mode].append(df[(df["case_study"] == case_study) & (df["mode"] == mode) & (df["dimension"] == dimension) & (df["gamma"] == 0.9)]["n_services"].values[0])
                states[mode].append(df[(df["case_study"] == case_study) & (df["mode"] == mode) & (df["dimension"] == dimension) & (df["gamma"] == 0.9)]["n_states"].values[0])
                times_comp[mode].append(df[(df["case_study"] == case_study) & (df["mode"] == mode) & (df["dimension"] == dimension) & (df["gamma"] == 0.9)]["comp_time"].values[0])
            times_gamma_pol[mode] = {}
            for gamma in gammas:
                times_gamma_pol[mode][gamma] = []
                for dimension in dimensions:
                    times_gamma_pol[mode][gamma].append(df[(df["case_study"] == case_study) & (df["mode"] == mode) & (df["dimension"] == dimension) & (df["gamma"] == gamma)]["policy_time"].values[0])
        
        plt.figure(f"Memory usage - automata - {case_study}")
        plt.title(f'Memory usage - automata - {case_study}')
        plt.plot(services['automata'], mems['automata'], '-o', label='Automata')
        plt.xticks(services['automata'])
        plt.xlabel('Number of services')
        plt.ylabel('Memory (MiB)')
        plt.grid()
        plt.show(block=False)

        plt.figure(f"Memory usage - ltlf -{case_study}")
        plt.title(f'Memory usage - ltlf - {case_study}')
        plt.plot(services['ltlf'], mems['ltlf'], '-o', label='LTLf')
        plt.xticks(services['ltlf'])
        plt.xlabel('Number of services')
        plt.ylabel('Memory (MiB)')
        plt.grid()
        plt.show(block=False)
        
        fig = plt.figure(f"Memory usage - {case_study}")

        color = 'tab:red'
        ax1 = fig.add_subplot(111)
        ax1.set_title(f'Memory usage - {case_study}')
        lns1 = ax1.plot(services['automata'], mems['automata'], '-o', color=color, label='Automata')
        ax1.set_xticks(services['automata'])
        ax1.set_xlabel('Number of services')
        ax1.set_ylabel('Memory (MiB)')
        ax1.tick_params(axis='y', labelcolor=color)

        color = 'tab:blue'
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        lns2 = ax2.plot(services['ltlf'], mems['ltlf'], '-o', color=color, label='LTLf')
        ax2.set_ylabel('')
        ax2.tick_params(axis='y', labelcolor=color)

        lns = lns1+lns2
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        ax1.grid()
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.savefig(f'mem_usage_{case_study}.png')
        plt.show(block=False)

        time_comp_automata = times_comp['automata']
        time_comp_ltlf = times_comp['ltlf']
        time_pol_automata = times_gamma_pol["automata"]
        time_pol_ltlf = times_gamma_pol["ltlf"]

        tot_time_automata = [sum(x) for x in zip(time_comp_automata, time_pol_automata[0.9])]
        tot_time_ltlf = [sum(x) for x in zip(time_comp_ltlf, time_pol_ltlf[0.9])]

        plt.figure(f"Solution computation time - {case_study}")
        plt.title(f'Stochastic policy approaches - Time consumption - {case_study}')
        plt.plot(services['automata'], tot_time_automata, '-o', label='Automa (λ=0.9)')
        plt.plot(services['ltlf'], tot_time_ltlf, '-o', label='LTLf (λ=0.9)')
        plt.xticks(services['automata'])
        plt.xlabel('Number of services')
        plt.ylabel('Time (s)')
        plt.legend()
        plt.grid()
        plt.savefig(f'time_consumption_{case_study}.png')
        plt.show(block=False)

        plt.figure(f"Policy computation time - LTLf - {case_study}")
        plt.title(f'Policy computation time - LTLf - {case_study}')
        colors = ['tab:orange', 'tab:purple', 'tab:cyan', 'tab:brown']
        line_styles = [(5, (10, 3)), (0, (5, 10)), (0, (5, 1)), 'dashdot']
        for gamma in time_pol_ltlf.keys():
            y_values = time_pol_ltlf[gamma]
            plt.plot(services['ltlf'], y_values, '-o', label=f'λ={gamma}', color=colors.pop(0), linestyle=line_styles.pop(0))
        plt.xticks(services['ltlf'])
        plt.xlabel('Number of services')
        plt.ylabel('Time (s)')
        plt.legend()
        plt.grid()
        plt.savefig(f'time_pol_ltlf_{case_study}.png')
        plt.show(block=False)