import json

from Rag2WebsocketHandler import Rag2WebsocketHandler


class PongWebSocketHandler(Rag2WebsocketHandler):
    def send_data(self, data):
        if data['playerId'] == 0:
            if data['state']['ballY'] < data['state']['leftPaddleY'] + 50:
                move = 1
            else:
                move = -1
        else:
            if data['state']['ballY'] < data['state']['rightPaddleY'] + 50:
                move = 1
            else:
                move = -1
        self.write_message(json.dumps({'move': move}))
