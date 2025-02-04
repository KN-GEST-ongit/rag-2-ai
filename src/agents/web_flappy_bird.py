from src.agents.web_env import WebsocketAgent
from stable_baselines3.common.base_class import BaseAlgorithm

import numpy as np


class FlappyBirdAgent(WebsocketAgent):
    def __init__(self, model: BaseAlgorithm, history_length: int):
        super().__init__(model, history_length)
        self.min_values = np.array([0, -20, 0.5, 5, -50, 100], dtype=np.float32)
        self.max_values = np.array([600, 90, 1, 15, 1900, 500], dtype=np.float32)
        self.should_start = False

    def prepare_observation(self, data: dict) -> np.array:
        state = data['state']
        if not state['isGameStarted']:
            self.should_start = True
            self.states.clear()
        else:
            self.should_start = False

        nearest_obstacle = min(
            (o for o in state['obstacles'] if o["distanceX"] > 0),
            key=lambda o: o["distanceX"]
        )
        curr_observation = np.array([
            state['birdY'],
            state['birdSpeedY'],
            state['gravity'],
            state['jumpPowerY'],
            nearest_obstacle['distanceX'],
            nearest_obstacle['centerGapY']
        ])

        for i in range(6):
            if i == 1:
                if curr_observation[i] < 0:
                    curr_observation[i] = (curr_observation[i] + 20) / 20 - 1
                else:
                    curr_observation[i] = curr_observation[i] / 90
            elif i == 4:
                curr_observation[i] = 2 * ((curr_observation[i] - self.min_values[i]) /
                                           (self.max_values[i] - self.min_values[i])) - 1
            else:
                curr_observation[i] = ((curr_observation[i] - self.min_values[i]) /
                                       (self.max_values[i] - self.min_values[i]))

        return self.state_stack(curr_observation)

    def return_prediction(self, data: dict) -> dict:
        obs = self.prepare_observation(data)
        action, _states = self.model.predict(
            observation=obs,
            deterministic=True
        )
        return {'jump': 1} if self.should_start else {'jump': int(action)}
