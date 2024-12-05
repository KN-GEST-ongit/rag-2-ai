import json

from src.handlers import BaseHandler


class PongBot(BaseHandler):
    def send_message(self, message):
        data = json.loads(message)

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

        self.write_message(json.dumps({'move': move, 'start': 1}))


class FlappybirdBot(BaseHandler):
    def send_message(self, message):
        data = json.loads(message)['state']
        jump = 0

        if not data['isGameStarted']:
            jump = 1
        else:
            obstacles = data['obstacles']
            lowestDist = 1000
            lowestDistIndex = 0
            for i in range(0, len(obstacles)):
                dist = obstacles[i]['distanceX']
                if lowestDist > dist > 60:
                    lowestDist = dist
                    lowestDistIndex = i

            if data['birdY'] > obstacles[lowestDistIndex]['centerGapY']:
                jump = 1

        self.write_message(json.dumps({'jump': jump}))


class SkijumpBot(BaseHandler):
    def send_message(self, message):
        state = json.loads(message)['state']

        space = 0
        up = 0
        down = 0

        if not state['isMoving'] or state['jumperHeightAboveGround'] < 10:
            space = 1
        else:
            if abs(state['jumperX'] - 250) < 12:
                space = 1

        if state['jumperInclineRad'] < 0.7:
            up = 1

        self.write_message(json.dumps({'space': space, 'up': up, 'down': down}))
