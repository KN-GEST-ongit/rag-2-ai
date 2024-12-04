import json
import random

from Rag2WebsocketHandler import Rag2WebsocketHandler


class PongWebSocketHandler(Rag2WebsocketHandler):
    def send_data(self, receivedData):
        move = random.choice([0, 1, -1])
        self.write_message(json.dumps({'move': move, 'start': 1}))

class PongBot(Rag2WebsocketHandler):
    def send_data(self, receivedData):
        if receivedData['playerId'] == 0:
            if receivedData['state']['ballY'] < receivedData['state']['leftPaddleY'] + 50:
                move = 1
            else:
                move = -1
        else:
            if receivedData['state']['ballY'] < receivedData['state']['rightPaddleY'] + 50:
                move = 1
            else:
                move = -1
        self.write_message(json.dumps({'move': move}))
