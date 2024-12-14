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

    async def send_message(self, message):
        data = json.loads(message)
        action = self.agent.return_prediction(data)
        await self.write_message(json.dumps(action))
