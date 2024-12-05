import json
from collections import deque
from typing import Callable

import numpy as np
from stable_baselines3.common.base_class import BaseAlgorithm

from src.api import BaseHandler
from src.env_sim.general import state_stack, action_map


class AiHandler(BaseHandler):

    def initialize(
            self,
            model: BaseAlgorithm,
            obs_funct: Callable[[dict], np.array],
            move_first: int,
            move_last: int,
            history_length: int = 1
    ):
        if history_length < 1:
            raise ValueError("history_length must be an integer greater than or equal to 1")

        self.model = model
        self.prepare_obs = obs_funct
        self.states = deque(maxlen=history_length)
        self.move_first = move_first
        self.move_last = move_last

    def after_close(self):
        self.states.clear()

    def send_message(self, message):
        data = json.loads(message)
        obs = self.prepare_obs(data)
        obs = state_stack(obs=obs, states=self.states)
        action, _states = self.model.predict(
            observation=obs,
            deterministic=True
        )
        move = action_map(
            action=int(action),
            first=self.move_first,
            last=self.move_last
        )
        if move is not None:
            self.write_message(json.dumps({'move': move, 'start': 1}))
