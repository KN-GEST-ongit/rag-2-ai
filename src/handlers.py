from src.api import BaseHandler
from src.agents.web_env import WebsocketAgent
from collections import deque
from typing import Callable

import numpy as np
import json


class AiHandler(BaseHandler):

    def initialize(
            self,
            agent: WebsocketAgent,
    ):
        self.agent = agent

    def after_close(self):
        self.agent.states.clear()

    def choose_move(self, data: dict) -> dict:
        return self.agent.return_prediction(data)
