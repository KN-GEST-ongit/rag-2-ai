from src.agents.web_env import WebsocketAgent
from stable_baselines3.common.base_class import BaseAlgorithm
from src.utils import normalize_observation

import numpy as np


class HappyJumpAgent(WebsocketAgent):
    def __init__(self, model: BaseAlgorithm, history_length: int):
        super().__init__(model, history_length)
        self.min_values = np.array([0, 0, -5, -20, -1, 0, 0, -1, 0, 0], dtype=np.float32)
        self.max_values = np.array([400, 600, 5, 50, 1, 400, 600, 1, 400, 600], dtype=np.float32)
        self.low = np.array([0, 0, -1, -1, -1, 0, 0, -1, 0, 0], dtype=np.float32)
        self.high = np.ones(10, dtype=np.float32)

    def prepare_observation(self, data: dict):
        state = data['state']
        upper_platform = max(
            (p for p in state['platforms'] if p['y'] < state['playerY']),
            key=lambda p: p['y'],
            default={'directionX': 0, 'x': 200, 'y': 0}
        )
        lower_platform = min(
            (p for p in state['platforms'] if p['y'] > state['playerY']),
            key=lambda p: p['y'],
            default={'directionX': 0, 'x': 200, 'y': 600}
        )
        curr_observation = np.array([
            state['playerX'],
            state['playerY'],
            state['playerSpeedX'],
            state['playerSpeedY'],
            upper_platform['directionX'],
            upper_platform['x'],
            upper_platform['y'],
            lower_platform['directionX'],
            lower_platform['x'],
            lower_platform['y']
        ])
        curr_observation = normalize_observation(
            curr_observation,
            self.min_values,
            self.max_values,
            self.low,
            self.high
        )
        return self.state_stack(curr_observation)

    def return_prediction(self, data: dict) -> dict:
        obs = self.prepare_observation(data)
        action, _states = self.model.predict(
            observation=obs,
            deterministic=True
        )
        return {'jump': 1, 'move': int(action)}
