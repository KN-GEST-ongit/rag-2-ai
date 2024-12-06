from collections import deque

import numpy as np


class Test:
    def __init__(self):
        pass

def action_map(action: int, first: int, last: int) -> int:
    num_actions = last - first + 1
    return first + action % num_actions


def state_stack(obs: dict, states: deque) -> np.array:
    if len(states) == 0:
        for _ in range(states.maxlen):
            states.append(obs)
    else:
        states.append(obs)

    return np.array(states).flatten()
