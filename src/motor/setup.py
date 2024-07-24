from stochastic_service_composition.services import build_service_from_transitions, Service
from stochastic_service_composition.target import build_target_from_transitions
from stochastic_service_composition.declare_utils import *
import logaut
import pylogics.parsers.ldl
from stochastic_service_composition.dfa_target import from_symbolic_automaton_to_declare_automaton

LOW_PROB = 0.05

# probabilities of being broken after an action
DEFAULT_BROKEN_PROB = LOW_PROB
BROKEN_PROB = 0.5
HIGH_BROKEN_PROB = 0.7

# default probability of being unemployable after the configuration
DEFAULT_UNEMPLOYABLE_PROB = LOW_PROB
HIGH_UNEMPLOYABLE_PROB = 0.5

# costs of the machines that perform their job in different countries
DEFAULT_USA_REWARD = -1.0
HIGH_DEFAULT_USA_REWARD = -5.0
UK_REWARD = -6.8
CHINA_REWARD = -11.7
RUSSIA_REWARD = -9.12 
BRAZIL_REWARD = -6.7
BELGIUM_REWARD = -7.6
CANADA_REWARD = -1.8
AUSTRIA_REWARD = -8.38
CHILE_REWARD = -7.8

# default reward when the service becomes broken
DEFAULT_BROKEN_REWARD = -20.0


# actions terms
RETRIEVE_STATOR = "ret_s"
RETRIEVE_ROTOR = "ret_r"
RETRIEVE_INVERTER = "ret_i"
RUNNING = "run"
ASSEMBLE = "ass"
PAINTING = "pai"
ELECTRIC_TEST = "el_t"
STATIC_TEST = "st_t"

ALL_SYMBOLS = [
    RETRIEVE_STATOR,
    RETRIEVE_ROTOR,
    RETRIEVE_INVERTER,
    RUNNING,
    ASSEMBLE,
    ELECTRIC_TEST,
    PAINTING,
    STATIC_TEST
]

ALL_SYMBOLS_SET = set(ALL_SYMBOLS)


# service names
WAREHOUSE_STATOR_USA = "wh_s_usa"
WAREHOUSE_STATOR_UK = "wh_s_uk"
WAREHOUSE_STATOR_CHINA = "wh_s_ch"

WAREHOUSE_ROTOR_CHINA = "wh_r_chi"
WAREHOUSE_ROTOR_RUSSIA = "wh_r_ru"
WAREHOUSE_ROTOR_USA = "wh_r_usa"
WAREHOUSE_ROTOR_BRAZIL = "wh_r_br"

WAREHOUSE_INVERTER_USA = "wh_i_usa"
WAREHOUSE_INVERTER_CHILE = "wh_i_chi"
WAREHOUSE_INVERTER_BRAZIL = "wh_i_br"

RUNNING1_SERVICE_NAME = "run_1"
RUNNING2_SERVICE_NAME = "run_2"
RUNNING3_SERVICE_NAME = "run_3"

ASSEMBLE1_SERVICE_NAME = "ass_1"
ASSEMBLE2_SERVICE_NAME = "ass_2"
ASSEMBLE3_SERVICE_NAME = "ass_3"

PAINTING1_SERVICE_NAME = "pai_1"
PAINTING2_SERVICE_NAME = "pai_2"
PAINTING3_SERVICE_NAME = "pai_3"

EL_TEST1_SERVICE_NAME = "el_t_1"
EL_TEST2_SERVICE_NAME = "el_t_2"
EL_TEST3_SERVICE_NAME = "el_t_3"

ST_TEST1_SERVICE_NAME = "st_t_1"
ST_TEST2_SERVICE_NAME = "st_t_2"
ST_TEST3_SERVICE_NAME = "st_t_3"


def build_generic_service_one_state(
    service_name: str,
    operation_names: Set[str],
    action_reward: float,
) -> Service:
    '''1-state service: ready'''
    transitions = {
        "re": {
            operation_name: ({"re": 1.0}, action_reward) for operation_name in operation_names
        },
    }
    final_states = {"re"}
    initial_state = "re"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


def build_generic_breakable_service(service_name: str, action_name: str, broken_prob: float, broken_reward: float, action_reward: float):
    '''3-states service: available, broken, done'''
    assert 0.0 <= broken_prob <= 1.0
    deterministic_prob = 1.0
    success_prob = deterministic_prob - broken_prob
    transitions = {
        "av": {
            action_name: ({"do": success_prob, "br": broken_prob}, action_reward),
        },
        "br": {
            f"ch_{action_name}": ({"av": 1.0}, broken_reward),
        },
        "do": {
            f"ch_{action_name}": ({"av": 1.0}, 0.0),
        }
    }
    final_states = {"av"}
    initial_state = "av"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


def build_complex_breakable_service(service_name: str, action_name: str, broken_prob: float, unemployable_prob: float, broken_reward: float, action_reward: float) -> Service:
    '''5-states service: ready, configured, executing, broken, repaired'''
    assert 0.0 <= broken_prob <= 1.0
    deterministic_prob = 1.0
    configure_success_prob = deterministic_prob - unemployable_prob
    op_success_prob = deterministic_prob - broken_prob
    transitions = {
        "re": { # current state
            f"con_{action_name}": # action
                (
                    {
                        "con": deterministic_prob # next state : prob
                    },
                    0.0
                ),
        },
        "con": {
            f"che_{action_name}":
                (
                    {
                    "ex": configure_success_prob,
                    "br": unemployable_prob
                    } if unemployable_prob > 0.0 else {"ex": configure_success_prob},
                    0.0
                ),
        },
        "ex": {
            action_name: # operation
                (
                    {
                        "re": op_success_prob,
                        "br": broken_prob
                    } if broken_prob > 0.0 else {"re": op_success_prob},
                    action_reward
                ),
        },
        "br": {
            f"res_{action_name}":
                (
                    {
                        "rep": deterministic_prob
                    },
                    broken_reward
                ),
        },
        "rep": {
            f"rep_{action_name}":
                (
                    {
                        "re": deterministic_prob
                    },
                    0.0
                ),
        },

    }
    final_states = {"re"}
    initial_state = "re"
    return build_service_from_transitions(transitions, initial_state, final_states)  # type: ignore


def process_services(dimension):
    '''Builds all the services for the given dimension of the problem.'''
    if dimension == "xsmall": # 8
        all_services = [
            build_generic_service_one_state(WAREHOUSE_INVERTER_USA, {RETRIEVE_INVERTER}, DEFAULT_USA_REWARD),

            build_generic_service_one_state(WAREHOUSE_ROTOR_USA, {RETRIEVE_ROTOR}, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(WAREHOUSE_STATOR_USA, {RETRIEVE_STATOR}, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(ASSEMBLE1_SERVICE_NAME, ASSEMBLE, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),

            build_generic_breakable_service(RUNNING1_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(PAINTING1_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(EL_TEST1_SERVICE_NAME, ELECTRIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(ST_TEST1_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
        ]
    elif dimension == "small": # 12
        all_services = [
            build_generic_service_one_state(WAREHOUSE_INVERTER_USA, {RETRIEVE_INVERTER}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_INVERTER_CHILE, {RETRIEVE_INVERTER}, CHILE_REWARD),

            build_generic_service_one_state(WAREHOUSE_ROTOR_USA, {RETRIEVE_ROTOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_RUSSIA, {RETRIEVE_ROTOR}, RUSSIA_REWARD),
            
            build_generic_service_one_state(WAREHOUSE_STATOR_USA, {RETRIEVE_STATOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_STATOR_UK, {RETRIEVE_STATOR}, UK_REWARD),
            
            build_complex_breakable_service(ASSEMBLE1_SERVICE_NAME, ASSEMBLE, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),

            build_generic_breakable_service(RUNNING1_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(RUNNING2_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(PAINTING1_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(EL_TEST1_SERVICE_NAME, ELECTRIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(ST_TEST1_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
        ]
    elif dimension == "medium": # 16
        all_services = [
            build_generic_service_one_state(WAREHOUSE_INVERTER_USA, {RETRIEVE_INVERTER}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_INVERTER_CHILE, {RETRIEVE_INVERTER}, CHILE_REWARD),
            build_generic_service_one_state(WAREHOUSE_INVERTER_BRAZIL, {RETRIEVE_INVERTER}, BRAZIL_REWARD),

            build_generic_service_one_state(WAREHOUSE_ROTOR_USA, {RETRIEVE_ROTOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_RUSSIA, {RETRIEVE_ROTOR}, RUSSIA_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_BRAZIL, {RETRIEVE_ROTOR}, BRAZIL_REWARD),
            
            build_generic_service_one_state(WAREHOUSE_STATOR_USA, {RETRIEVE_STATOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_STATOR_UK, {RETRIEVE_STATOR}, UK_REWARD),
            
            build_complex_breakable_service(ASSEMBLE1_SERVICE_NAME, ASSEMBLE, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(RUNNING1_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(RUNNING2_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(PAINTING1_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(PAINTING2_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(EL_TEST1_SERVICE_NAME, ELECTRIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(ST_TEST1_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(ST_TEST2_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
        ]
    elif dimension == "large": # 20
        all_services = [
            build_generic_service_one_state(WAREHOUSE_INVERTER_USA, {RETRIEVE_INVERTER}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_INVERTER_CHILE, {RETRIEVE_INVERTER}, CHILE_REWARD),
            build_generic_service_one_state(WAREHOUSE_INVERTER_BRAZIL, {RETRIEVE_INVERTER}, BRAZIL_REWARD),

            build_generic_service_one_state(WAREHOUSE_ROTOR_USA, {RETRIEVE_ROTOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_RUSSIA, {RETRIEVE_ROTOR}, RUSSIA_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_BRAZIL, {RETRIEVE_ROTOR}, BRAZIL_REWARD),
            build_generic_service_one_state(WAREHOUSE_ROTOR_CHINA, {RETRIEVE_ROTOR}, CHINA_REWARD),
            
            build_generic_service_one_state(WAREHOUSE_STATOR_USA, {RETRIEVE_STATOR}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(WAREHOUSE_STATOR_UK, {RETRIEVE_STATOR}, UK_REWARD),
            build_generic_service_one_state(WAREHOUSE_STATOR_CHINA, {RETRIEVE_STATOR}, CHINA_REWARD),
            
            build_complex_breakable_service(ASSEMBLE1_SERVICE_NAME, ASSEMBLE, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_complex_breakable_service(ASSEMBLE2_SERVICE_NAME, ASSEMBLE, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(RUNNING1_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(RUNNING2_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            build_generic_breakable_service(RUNNING3_SERVICE_NAME, RUNNING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-2),
            
            build_generic_breakable_service(PAINTING1_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(PAINTING2_SERVICE_NAME, PAINTING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(EL_TEST1_SERVICE_NAME, ELECTRIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(ST_TEST1_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(ST_TEST2_SERVICE_NAME, STATIC_TEST, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
        ]
    return all_services


# no loop in the automa
def target_service_automata():
    '''Builds the target service automaton for the given dimension of the problem.'''
    transition_function = {
        "s0": {RETRIEVE_INVERTER: ("s1", 1.0, 0), },
        "s1": {RETRIEVE_ROTOR: ("s2", 1.0, 0), },
        "s2": {RETRIEVE_STATOR: ("s3", 1.0, 0), },

        "s3": {f"con_{ASSEMBLE}": ("s4", 1.0, 0), },
        "s4": {f"che_{ASSEMBLE}": ("s5", 1.0, 0), },
        "s5": {f"{ASSEMBLE}": ("s6", 1.0, 0), },

        "s6": {RUNNING: ("s7", 1.0, 0), },
        "s7": {f"ch_{RUNNING}": ("s8", 1.0, 0), },

        "s8": {PAINTING: ("s9", 1.0, 0), },
        "s9": {f"ch_{PAINTING}": ("s10", 1.0, 0), },

        "s10": {f"con_{ELECTRIC_TEST}": ("s11", 1.0, 0), },
        "s11": {f"che_{ELECTRIC_TEST}": ("s12", 1.0, 0), },
        "s12": {f"{ELECTRIC_TEST}": ("s13", 1.0, 0), },

        "s13": {"no_op": ("s14", 1.0, 0), },
    }

    initial_state = "s0"
    final_states = {"s14"}

    return build_target_from_transitions(
        transition_function, initial_state, final_states
    )

def target_service_ltlf():
    '''Builds the target service LTLf formula from the DECLARE constraints and symbols.'''
    # declare process specification
    declare_constraints = [
        exactly_once(RETRIEVE_STATOR),
        exactly_once(RETRIEVE_ROTOR),
        exactly_once(RETRIEVE_INVERTER),
        exactly_once(RUNNING),
        exactly_once(ASSEMBLE),

        absence_2(ELECTRIC_TEST),
        absence_2(PAINTING),
        absence_2(STATIC_TEST),

        alt_succession(RETRIEVE_STATOR, ASSEMBLE),
        alt_succession(RETRIEVE_ROTOR, ASSEMBLE),
        alt_succession(RETRIEVE_INVERTER, ASSEMBLE),

        alt_succession(ASSEMBLE, RUNNING),

        alt_precedence(ASSEMBLE, PAINTING),
        alt_precedence(ASSEMBLE, ELECTRIC_TEST),
        alt_precedence(ASSEMBLE, STATIC_TEST),

        not_coexistence(ELECTRIC_TEST, STATIC_TEST),

        build_declare_assumption(ALL_SYMBOLS_SET)
    ]
    formula_str = " & ".join(map(lambda s: f"({s})", declare_constraints))
    formula = pylogics.parsers.parse_ltl(formula_str)
    automaton = logaut.core.ltl2dfa(formula, backend="lydia")
    declare_automaton = from_symbolic_automaton_to_declare_automaton(automaton, ALL_SYMBOLS_SET)
    return declare_automaton

