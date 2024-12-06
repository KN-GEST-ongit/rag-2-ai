from src.agents.web_env import WebsocketAgent
from stable_baselines3.common.base_class import BaseAlgorithm

import numpy as np


class PongAgent(WebsocketAgent):
    def __init__(self, model: BaseAlgorithm, history_length: int):
        super().__init__(model, history_length)
        self.min_values = np.array([0, 0, 0, 0, -100, -100], dtype=np.float32)
        self.max_values = np.array([600, 600, 1000, 600, 100, 100], dtype=np.float32)
        self.action_map = {0: -1, 1: 0, 2: 1}

    def prepare_observation(self, data: dict) -> np.array:
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

        curr_observation[:4] = ((curr_observation[:4] - self.min_values[:4]) /
                                (self.max_values[:4] - self.min_values[:4]))

        curr_observation[4:] = 2 * ((curr_observation[4:] - self.min_values[4:]) /
                                    (self.max_values[4:] - self.min_values[4:])) - 1

        return self.state_stack(curr_observation)

    def return_prediction(self, data: dict) -> dict:
        obs = self.prepare_observation(data)
        action, _states = self.model.predict(
            observation=obs,
            deterministic=True
        )
        move = self.action_map[int(action)]
        return {'move': move, 'start': 1}
