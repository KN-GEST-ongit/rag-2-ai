import json
import random  # to test

from src.handlers import BaseHandler


class PongBot(BaseHandler):
    def send_prediction(self, data: dict):
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

        self.write_message(json.dumps({'move': move, 'start': 1}))


class FlappybirdBot(BaseHandler):
    def send_prediction(self, data: dict):
        state = data['state']
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

        self.write_message(json.dumps({'jump': jump}))


class SkiJumpBot(BaseHandler):
    def send_prediction(self, data: dict):
        state = data['state']

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


class HappyJumpBot(BaseHandler):
    def send_prediction(self, data: dict):
        state = data['state']
        move = 0
        jump = 0

        if not state['isGameStarted']:
            jump = 1
        else:
            platforms_below = [p for p in state['platforms'] if p['y'] > state['playerY']]

            if platforms_below:
                nearest_platform = min(platforms_below, key=lambda p: p['y'])
                player_left, player_right = state['playerX'], state['playerX'] + 30
                platform_left, platform_right = nearest_platform['x'], nearest_platform['x'] + 100

                #Ruch bota, jeśli występuje przynajmniej jedna platforma ruchoma
                if state['movingPlatforms'] > 0:
                    platform_offset = nearest_platform['directionX'] * state['platformSpeed']
                    platform_left += platform_offset
                    platform_right += platform_offset

                if state['playerSpeedY'] < 0:
                    if platform_left > player_right:
                        move = 1
                    elif platform_right < player_left:
                        move = -1
                else:
                    if platform_left > player_right:
                        move = 1
                        if abs(player_right - platform_left) <= 3:
                            jump = 1
                    elif platform_right < player_left:
                        move = -1
                        if abs(player_left - platform_right) <= 3:
                            jump = 1
                    else:
                        jump = int(state['playerSpeedY'] > 0)
            else:
                jump = 1

        self.write_message(json.dumps({'jump': jump, 'move': move}))