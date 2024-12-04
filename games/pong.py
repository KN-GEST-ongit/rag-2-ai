import json
import random

from Rag2WebsocketHandler import Rag2WebsocketHandler


class PongWebSocketHandler(Rag2WebsocketHandler):
    def send_data(self, receivedData):
        move = random.choice([0, 1, -1])
        self.write_message(json.dumps({'move': move}))
