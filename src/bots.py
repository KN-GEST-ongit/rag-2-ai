import json

from src.handlers import BaseHandler


class PongBot(BaseHandler):
    async def send_message(self, message):
        data = json.loads(message)
        player = data['playerId']
        state = data['state']

        if player == 0:
            if state['ballY'] < state['leftPaddleY'] + 50:
                move = 1
            else:
                move = -1
        else:
            if state['ballY'] < state['rightPaddleY'] + 50:
                move = 1
            else:
                move = -1

        await self.write_message(json.dumps({'move': move, 'start': 1}))


class FlappybirdBot(BaseHandler):
    async def send_message(self, message):
        state = json.loads(message)['state']
        jump = 0

        if not state['isGameStarted']:
            jump = 1
        else:
            nearest_obstacle = min(
                (o for o in state['obstacles'] if o["distanceX"] > 0),
                key=lambda o: o["distanceX"]
            )
            if state['birdY'] > nearest_obstacle['centerGapY']:
                jump = 1

        await self.write_message(json.dumps({'jump': jump}))


class SkijumpBot(BaseHandler):
    async def send_message(self, message):
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

        await self.write_message(json.dumps({'space': space, 'up': up, 'down': down}))
