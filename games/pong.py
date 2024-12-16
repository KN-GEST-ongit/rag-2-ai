import json
import random

from Rag2WebsocketHandler import Rag2WebsocketHandler


class PongWebSocketHandler(Rag2WebsocketHandler):
    def send_data(self, receivedData):
        move = random.choice([0, 1, -1])
        self.write_message(json.dumps({'move': move})) #test

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

class HappyJumpBot(Rag2WebsocketHandler):
    def send_data(self, receivedData):
        state = receivedData['state']
        if not state.get('isGameStarted', False):
            self.write_message(json.dumps({'start': 1}))
            print("Gra jeszcze się nie rozpoczęła. Wysyłam komendę START.")
            return

        # Pozycje gracza
        player_x = state['playerX']
        player_y = state['playerY']
        player_speed_y = state['playerSpeedY']
        platforms = state['platforms']

        move = 0  # -1: w lewo, 1: w prawo, 0: stop
        jump = 0  # 0: nie skacz, 1: skacz

        # Znajdowanie najbliższej platformy powyżej lub poniżej gracza
        closest_platform = None
        min_distance = float('inf')
        for platform in platforms:
            if platform['y'] > player_y:  # Platforma poniżej gracza
                distance = abs(platform['y'] - player_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_platform = platform

        # Decyzje bota
        if closest_platform:
            platform_x = closest_platform['x']
            platform_y = closest_platform['y']

            # Ruch w poziomie (również w powietrzu)
            if player_x < platform_x - 5:  # Celuj trochę na środek platformy
                move = 1  # Idź w prawo
            elif player_x > platform_x + 5:
                move = -1  # Idź w lewo
            else:
                move = 0  # Gracz jest wystarczająco nad platformą

            # Skakanie, jeśli platforma jest wystarczająco blisko
            if (platform_y - player_y) < 100 and player_speed_y >= 0:  # Platforma wyżej i gracz spada
                jump = 1

        # Wysyłanie akcji do serwera
        self.write_message(json.dumps({'move': move, 'jump': jump}))