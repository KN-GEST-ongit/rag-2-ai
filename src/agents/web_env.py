from abc import ABC, abstractmethod
from collections import deque
from typing import final
from stable_baselines3.common.base_class import BaseAlgorithm

import numpy as np


class WebsocketAgent(ABC):
    def __init__(self, model: BaseAlgorithm, history_length: int = 1):
        if history_length < 1:
            raise ValueError("history_length must be an integer greater than or equal to 1")
        self.model = model
        self.states = deque(maxlen=history_length)

    def start(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def prepare_observation(self, data: dict) -> np.array:
        raise NotImplementedError

    @final
    def state_stack(self, observation: np.array) -> np.array:
        if len(self.states) == 0:
            for _ in range(self.states.maxlen):
                self.states.append(observation)
        else:
            self.states.append(observation)
        return np.array(self.states).flatten()

    @abstractmethod
    def return_prediction(self, data: dict) -> dict:
        raise NotImplementedError
