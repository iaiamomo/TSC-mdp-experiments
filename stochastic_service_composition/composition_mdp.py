"""This module implements the algorithm to compute the system-target MDP."""
import time
from collections import deque
from typing import Deque, Dict, List, Set, Tuple

from mdp_dp_rl.processes.mdp import MDP
from pythomata import SimpleDFA

from stochastic_service_composition.services import Service, build_system_service
from stochastic_service_composition.target import Target
from stochastic_service_composition.types import Action, State, MDPDynamics

COMPOSITION_MDP_INITIAL_STATE = 0
COMPOSITION_MDP_INITIAL_ACTION = "initial"
COMPOSITION_MDP_UNDEFINED_ACTION = "undefined"
DEFAULT_GAMMA = 0.9

COMPOSITION_MDP_SINK_STATE = -1


def composition_mdp(
    target: Target, *services: Service, gamma: float = DEFAULT_GAMMA
) -> MDP:
    """
    Compute the composition MDP.

    :param target: the target service.
    :param services: the community of services.
    :param gamma: the discount factor.
    :return: the composition MDP.
    """

    system_service = build_system_service(*services)

    initial_state = COMPOSITION_MDP_INITIAL_STATE
    # one action per service (1..n) + the initial action (0)
    actions: Set[Action] = set(range(len(services)))
    initial_action = COMPOSITION_MDP_INITIAL_ACTION
    actions.add(initial_action)

    # add an 'undefined' action for sink states
    actions.add(COMPOSITION_MDP_UNDEFINED_ACTION)

    transition_function: MDPDynamics = {}

    visited = set()
    to_be_visited = set()
    queue: Deque = deque()

    # add initial transitions
    transition_function[initial_state] = {}
    initial_transition_dist = {}
    symbols_from_initial_state = target.policy[target.initial_state].keys()
    for symbol in symbols_from_initial_state:
        next_state = (system_service.initial_state, target.initial_state, symbol)
        next_prob = target.policy[target.initial_state][symbol]
        initial_transition_dist[next_state] = next_prob
        queue.append(next_state)
        to_be_visited.add(next_state)
    transition_function[initial_state][initial_action] = (initial_transition_dist, 0.0)  # type: ignore

    while len(queue) > 0:
        current_state = queue.popleft()
        to_be_visited.remove(current_state)
        visited.add(current_state)
        current_system_state, current_target_state, current_symbol = current_state

        transition_function[current_state] = {}
        # index system symbols (action, service_id) by symbol
        system_symbols: List[Tuple[Action, int]] = list(
            system_service.transition_function[current_system_state].keys()
        )
        system_symbols_by_symbols: Dict[Action, Set[int]] = {}
        for action, service_id in system_symbols:
            system_symbols_by_symbols.setdefault(action, set()).add(service_id)

        for i in system_symbols_by_symbols.get(current_symbol, set()):
            next_transitions = {}
            # TODO check if it is needed
            if current_symbol not in target.transition_function[current_target_state]:
                continue
            next_reward = (
                target.reward[current_target_state][current_symbol]
                if (current_symbol, i)
                in system_service.transition_function[current_system_state]
                else 0
            )
            next_target_state = target.transition_function[current_target_state][
                current_symbol
            ]
            next_system_states, next_system_reward = system_service.transition_function[
                current_system_state
            ][(current_symbol, i)]
            for next_symbol, next_prob in target.policy.get(next_target_state, {}).items():
                for next_system_state, next_system_prob in next_system_states.items():
                    next_state = (next_system_state, next_target_state, next_symbol)
                    if next_prob * next_system_prob == 0.0:
                        continue
                    next_transitions[next_state] = next_prob * next_system_prob
                    if next_state not in visited and next_state not in to_be_visited:
                        to_be_visited.add(next_state)
                        queue.append(next_state)
            transition_function[current_state][i] = (  # type: ignore
                next_transitions,  # type: ignore
                next_reward + next_system_reward,
            )

        # states without outgoing transitions are sink states.
        # add loop transitions with
        # - 'undefined' action
        # - probability 1
        # - reward 0
        if len(transition_function[current_state]) == 0:
            transition_function.setdefault(current_state, {})
            transition_function[current_state][COMPOSITION_MDP_UNDEFINED_ACTION] = (
                {current_state: 1.0},
                0.0,
            )  # type: ignore
        # TODO check correctness
        # if next state distribution is empty, add loops

    return MDP(transition_function, gamma)


def comp_mdp(
    dfa: SimpleDFA, services: Service, gamma: float = DEFAULT_GAMMA
) -> MDP:
    """
    Compute the composition MDP.

    :param target: the target service.
    :param services: the community of services.
    :param gamma: the discount factor.
    :return: the composition MDP.
    """
    dfa = dfa.trim()
    system_service = build_system_service(*services)

    transition_function: MDPDynamics = {}

    visited = set()
    to_be_visited = set()
    queue: Deque = deque()

    # add initial transitions
    initial_state = (system_service.initial_state, dfa.initial_state)
    queue.append(initial_state)
    to_be_visited.add(initial_state)
    # aggiungo gli stati del system service alla lista degli stati da visitare
    for system_service_state in system_service.states:
        if system_service_state == system_service.initial_state:
            continue
        # includo solo gli stati del system service che hanno come valore "re", "av" o "br" (solo ready/available e broken)
        if not all(elem in ["re", "av", "br"] for elem in system_service_state):
            continue
        new_initial_state = (system_service_state, dfa.initial_state)
        queue.append(new_initial_state)
        to_be_visited.add(new_initial_state)

    # json con id del servizio e azione che può fare
    # es. {0: {'p_d'}, 1: {'p_s'}, 2: {'cr_m'}, stop_state: {'cr_m'}, 4: {'ph_l'}}
    service_id_to_target_action = {
        service_id: set(dfa.alphabet).intersection(service.actions)
        for service_id, service in enumerate(services)
    }

    # json con azione target e id dei servizi che possono eseguirla
    # es. {'p_d': {0}, 'p_s': {1}, 'cr_m': {2, 3}, 'ph_l': {4}}
    target_action_to_service_id = {}
    for service_id, supported_actions in service_id_to_target_action.items():
        # controllo che l'attore può fare solo un'azione
        assert len(supported_actions) == 1
        supported_action = list(supported_actions)[0]
        target_action_to_service_id.setdefault(supported_action, set()).add(service_id)

    mdp_sink_state_used = False
    # per ogni stato che devo visitare
    while len(queue) > 0:
        cur_state = queue.popleft()
        to_be_visited.remove(cur_state)
        visited.add(cur_state)

        cur_system_state, cur_dfa_state = cur_state
        trans_dist = {}

        # ricavo le transition del system service dallo stato corrente
        next_system_state_trans = system_service.transition_function[
            cur_system_state
        ].items()
        
        # optimization: filter services, consider only the ones that can do the next DFA action
        # ricavo le azioni che il DFA può fare dallo stato corrente
        next_dfa_actions = set(dfa.transition_function.get(cur_dfa_state, {}).keys())
        
        # ricavo solo i servizi che possono fare l'azione successiva
        allowed_services = set()
        for next_dfa_action in next_dfa_actions:
            allowed_services.update(target_action_to_service_id[next_dfa_action])
        
        if len(allowed_services) == 0:
            mdp_sink_state_used = True
            trans_dist[COMPOSITION_MDP_UNDEFINED_ACTION] = ({COMPOSITION_MDP_SINK_STATE: 1}, 0.0)
        else:
            # iterate over all available actions of system service
            # in case symbol is in DFA available actions, progress DFA state component
            # es. ('ph_l', 4) -> ({('re', 're', 're', 're', 'do'): 0.95, ('re', 're', 're', 're', 'br'): 0.05}, -1.0)
            for (symbol, service_id), next_state_info in next_system_state_trans:

                if service_id not in allowed_services:
                    # this service id cannot do any of the next dfa actions
                    continue

                # es. ({('re', 're', 're', 're', 'do'): 0.95, ('re', 're', 're', 're', 'br'): 0.05}, -1.0)
                next_system_state_distr, reward_vector = next_state_info
                system_reward = reward_vector   # es. -1.0

                # if symbol is a tau action, next dfa state remains the same
                if symbol not in dfa.alphabet:
                    next_dfa_state = cur_dfa_state
                    goal_reward = 0.0
                # if there are no outgoing transitions from DFA state:
                elif cur_dfa_state not in dfa.transition_function:
                    mdp_sink_state_used = True
                    trans_dist[COMPOSITION_MDP_UNDEFINED_ACTION] = ({COMPOSITION_MDP_SINK_STATE: 1}, 0.0)
                    continue
                # symbols not in the transition function of the target
                # are considered as "other"; however, when we add the
                # MDP transition, we will label it with the original
                # symbol.
                elif symbol in dfa.transition_function[cur_dfa_state]:
                    symbol_to_next_dfa_states = dfa.transition_function[cur_dfa_state]
                    next_dfa_state = symbol_to_next_dfa_states[symbol]
                    goal_reward = 1.0 if dfa.is_accepting(next_dfa_state) else 0.0
                else:
                    # if invalid target action, skip
                    continue
                final_rewards = (goal_reward + system_reward)

                for next_system_state, prob in next_system_state_distr.items():
                    assert prob > 0.0
                    next_state = (next_system_state, next_dfa_state)
                    trans_dist.setdefault((symbol, service_id), ({}, final_rewards))[0][
                        next_state
                    ] = prob
                    if next_state not in visited and next_state not in to_be_visited:
                        queue.append(next_state)
                        to_be_visited.add(next_state)

        transition_function[cur_state] = trans_dist

    if mdp_sink_state_used:
        transition_function[COMPOSITION_MDP_SINK_STATE] = {COMPOSITION_MDP_UNDEFINED_ACTION: ({COMPOSITION_MDP_SINK_STATE: 1.0}, 0.0)}

    result = MDP(transition_function, gamma)
    result.initial_state = initial_state
    return result

