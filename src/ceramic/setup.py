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
PROVISIONING = "pro"
MOULDING = "moul"
DRYING = "dry"
FIRST_BAKING = "f_bak"
ENAMELLING = "ena"
PAINT = "paint"
SECOND_BAKING = "s_bak"
SHIPPING = "ship"


ALL_SYMBOLS = [
    PROVISIONING,
    MOULDING,
    DRYING,
    FIRST_BAKING,
    ENAMELLING,
    PAINT,
    SECOND_BAKING,
    SHIPPING
]

ALL_SYMBOLS_SET = set(ALL_SYMBOLS)


# service names
PROVISION1_SERVICE_NAME_USA = "pro1_usa"
PROVISION2_SERVICE_NAME_USA = "pro2_usa"
PROVISION3_SERVICE_NAME_USA = "pro3_usa"
PROVISION3_SERVICE_NAME_USA = "pro3_usa"

MOULD1_SERVICE_NAME_USA = "moul1_usa"
MOULD2_SERVICE_NAME_USA = "moul2_usa"
MOULD3_SERVICE_NAME_USA = "moul3_usa"
MOULD4_SERVICE_NAME_USA = "moul4_usa"

DRYER1_SERVICE_NAME_USA = "dry1_usa"
DRYER2_SERVICE_NAME_USA = "dry2_usa"
DRYER3_SERVICE_NAME_USA = "dry3_usa"
DRYER4_SERVICE_NAME_USA = "dry4_usa"

F_BAKE1_SERVICE_NAME_USA = "f_bak1_usa"
F_BAKE2_SERVICE_NAME_USA = "f_bak2_usa"
F_BAKE3_SERVICE_NAME_USA = "f_bak3_usa"
F_BAKE4_SERVICE_NAME_USA = "f_bak4_usa"

ENAMEL1_SERVICE_NAME_USA = "enam1_usa"
ENAMEL2_SERVICE_NAME_USA = "enam2_usa"
ENAMEL3_SERVICE_NAME_USA = "enam3_usa"
ENAMEL4_SERVICE_NAME_USA = "enam4_usa"

PAINTER1_SERVICE_NAME_USA = "pain1_usa"
PAINTER2_SERVICE_NAME_USA = "pain2_usa"
PAINTER3_SERVICE_NAME_USA = "pain3_usa"
PAINTER4_SERVICE_NAME_USA = "pain4_usa"

S_BAK1_SERVICE_NAME_USA = "s_bak1_usa"
S_BAK2_SERVICE_NAME_USA = "s_bak2_usa"
S_BAK3_SERVICE_NAME_USA = "s_bak3_usa"
S_BAK4_SERVICE_NAME_USA = "s_bak4_usa"

SHIPPING1_SERVICE_NAME_USA = "ship1_usa"
SHIPPING2_SERVICE_NAME_USA = "ship2_usa"
SHIPPING3_SERVICE_NAME_USA = "ship3_usa"
SHIPPING4_SERVICE_NAME_USA = "ship4_usa"


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
    if dimension == "xsmall": # 8 services
        all_services = [
            build_generic_service_one_state(PROVISION1_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(DRYER1_SERVICE_NAME_USA, DRYING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(ENAMEL1_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(S_BAK1_SERVICE_NAME_USA, SECOND_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(SHIPPING1_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD),
        ]
    elif dimension == "small": # 12
        all_services = [
            build_generic_service_one_state(PROVISION1_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_complex_breakable_service(DRYER1_SERVICE_NAME_USA, DRYING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(ENAMEL1_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(ENAMEL2_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(S_BAK1_SERVICE_NAME_USA, SECOND_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(SHIPPING1_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(SHIPPING2_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD-1),
        ]
    elif dimension == "medium": # 16
        all_services = [
            build_generic_service_one_state(PROVISION1_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-1),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-2),
            
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(DRYER1_SERVICE_NAME_USA, DRYING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_generic_service_one_state(ENAMEL1_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(ENAMEL2_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD-1),
            
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(S_BAK1_SERVICE_NAME_USA, SECOND_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(SHIPPING1_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(SHIPPING2_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD-1),
            build_generic_service_one_state(SHIPPING2_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD-2),
        ]
    elif dimension == "large": # 20
        all_services = [
            build_generic_service_one_state(PROVISION1_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-1),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-2),
            build_generic_service_one_state(PROVISION2_SERVICE_NAME_USA, {PROVISIONING}, DEFAULT_USA_REWARD-3),
            
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(MOULD1_SERVICE_NAME_USA, MOULDING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(DRYER1_SERVICE_NAME_USA, DRYING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_complex_breakable_service(DRYER1_SERVICE_NAME_USA, DRYING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, HIGH_DEFAULT_USA_REWARD),
            
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            build_generic_breakable_service(F_BAKE1_SERVICE_NAME_USA, FIRST_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-2),
            
            build_generic_service_one_state(ENAMEL1_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(ENAMEL2_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD-1),
            build_generic_service_one_state(ENAMEL2_SERVICE_NAME_USA, {ENAMELLING}, DEFAULT_USA_REWARD-2),
            
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            build_generic_breakable_service(PAINTER1_SERVICE_NAME_USA, PAINT, DEFAULT_BROKEN_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD-1),
            
            build_complex_breakable_service(S_BAK1_SERVICE_NAME_USA, SECOND_BAKING, DEFAULT_BROKEN_PROB, DEFAULT_UNEMPLOYABLE_PROB, DEFAULT_BROKEN_REWARD, DEFAULT_USA_REWARD),
            
            build_generic_service_one_state(SHIPPING1_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD),
            build_generic_service_one_state(SHIPPING2_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD-1),
            build_generic_service_one_state(SHIPPING2_SERVICE_NAME_USA, {SHIPPING}, DEFAULT_USA_REWARD-2),
        ]
    return all_services


# no loop in the automa
def target_service_automata():
    '''Builds the target service automaton for the given dimension of the problem.'''
    transition_function = {
        "s0": {PROVISIONING: ("s1", 1.0, 0), },

        "s1": {MOULDING: ("s2", 1.0, 0), },
        "s2": {f"ch_{MOULDING}": ("s3", 1.0, 0), },

        "s3": {f"con_{DRYING}": ("s4", 1.0, 0), },
        "s4": {f"che_{DRYING}": ("s5", 1.0, 0), },
        "s5": {f"{DRYING}": ("s6", 1.0, 0), },        
        
        "s6": {FIRST_BAKING: ("s7", 1.0, 0), },
        "s7": {f"ch_{FIRST_BAKING}": ("s8", 1.0, 0), },
        
        "s8": {ENAMELLING: ("s9", 1.0, 0), },
        
        "s9": {PAINT: ("s10", 1.0, 0), },
        "s10": {f"ch_{PAINT}": ("s11", 1.0, 0), },
        
        "s11": {f"con_{SECOND_BAKING}": ("s12", 1.0, 0), },
        "s12": {f"che_{SECOND_BAKING}": ("s13", 1.0, 0), },
        "s13": {f"{SECOND_BAKING}": ("s14", 1.0, 0), },
        
        "s14": {SHIPPING: ("s15", 1.0, 0.0), },
        
        "s15": {"no_op": ("s16", 1.0, 0.0), },
    }

    initial_state = "s0"
    final_states = {"s16"}

    return build_target_from_transitions(
        transition_function, initial_state, final_states
    )


def target_service_ltlf():
    '''Builds the target service LTLf formula from the DECLARE constraints and symbols.'''
    # declare process specification
    declare_constraints = [
        exactly_once(PROVISIONING),
        exactly_once(MOULDING),
        exactly_once(DRYING),
        exactly_once(FIRST_BAKING),
        exactly_once(ENAMELLING),
        exactly_once(PAINT),
        exactly_once(SECOND_BAKING),
        exactly_once(SHIPPING),

        alt_succession(PROVISIONING, MOULDING),
        alt_succession(MOULDING, DRYING),
        alt_succession(DRYING, FIRST_BAKING),
        alt_succession(FIRST_BAKING, ENAMELLING),
        alt_succession(ENAMELLING, PAINT),
        alt_succession(PAINT, SECOND_BAKING),
        alt_succession(SECOND_BAKING, SHIPPING),

        build_declare_assumption(ALL_SYMBOLS_SET)
    ]
    formula_str = " & ".join(map(lambda s: f"({s})", declare_constraints))
    formula = pylogics.parsers.parse_ltl(formula_str)
    automaton = logaut.core.ltl2dfa(formula, backend="lydia")
    declare_automaton = from_symbolic_automaton_to_declare_automaton(automaton, ALL_SYMBOLS_SET)
    return declare_automaton

