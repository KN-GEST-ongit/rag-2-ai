import numpy as np


def prepare_pong_obs(data: dict) -> np.array:
    min_values = np.array([0, 0, 0, 0, -100, -100], dtype=np.float32)
    max_values = np.array([600, 600, 1000, 600, 100, 100], dtype=np.float32)

    player = data['playerId']
    state = data['state']
    if player == 0:
        curr_observation = np.array([
            state['leftPaddleY'],
            state['rightPaddleY'],
            state['ballX'],
            state['ballY'],
            state['ballSpeedX'],
            state['ballSpeedY'],
        ], dtype=np.float32)
    else:
        curr_observation = np.array([
            state['rightPaddleY'],
            state['leftPaddleY'],
            1000 - state['ballX'],
            state['ballY'],
            -state['ballSpeedX'],
            state['ballSpeedY'],
        ], dtype=np.float32)

    curr_observation[:4] = ((curr_observation[:4] - min_values[:4]) / (max_values[:4] - min_values[:4]))

    curr_observation[4:] = 2 * ((curr_observation[4:] - min_values[4:]) / (max_values[4:] - min_values[4:])) - 1

    return curr_observation
