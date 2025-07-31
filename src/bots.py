import json

from src.handlers import BaseHandler
import random
import heapq
from collections import deque


class PongBot(BaseHandler):
    def choose_move(self, data: dict):
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

        return {'move': move, 'start': 1}


class FlappybirdBot(BaseHandler):
    def choose_move(self, data: dict):
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

        return {'jump': jump}


class SkiJumpBot(BaseHandler):
    def choose_move(self, data: dict):
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

        return {'space': space, 'up': up, 'down': down}


class HappyJumpBot(BaseHandler):
    def choose_move(self, data: dict):
        state = data['state']
        move = 0
        jump = 0

        if not state['isGameStarted']:
            jump = 1
        else:
            lower_platform = min(
                (p for p in state['platforms'] if p['y'] > state['playerY']),
                key=lambda p: p['y'],
                default=None
            )
            if lower_platform is not None:
                player_left, player_right = state['playerX'], state['playerX'] + 30
                platform_left, platform_right = lower_platform['x'], lower_platform['x'] + 100

                if state['movingPlatforms'] > 0:
                    platform_offset = lower_platform['directionX'] * state['platformSpeed']
                    platform_left += platform_offset
                    platform_right += platform_offset

                if state['playerSpeedY'] < 0:
                    if platform_left >= player_right:
                        move = 1
                    elif platform_right <= player_left:
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

        return {'jump': jump, 'move': move}


class PacManBot(BaseHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_positions = set()
        self.path = []
        self.current_target = None
        self.recent_positions = deque(maxlen=6)
        self.walls_initialized = False
        self.last_game_started = False
        self.last_level = None

    def reset_state(self):
        self.visited_positions.clear()
        self.path.clear()
        self.current_target = None
        self.recent_positions.clear()
        self.walls_initialized = False

    def _check_game_end(self, state):
        game_started = state.get('isGameStarted', False)
        if self.last_game_started and not game_started:
            return True
        self.last_game_started = game_started
        return False

    def choose_move(self, data: dict):
        state = data['state']

        if self._check_game_end(state):
            self.reset_state()

        game_map = state['map']
        tile_size = state['tileSize']
        game_started = state.get('isGameStarted', False)
        current_level = state.get('level')

        if self.last_level is not None and current_level != self.last_level:
            self.reset_state()
        self.last_level = current_level

        if not game_started:
            return {"move": 1}

        pacman_x, pacman_y = state['pacmanX'], state['pacmanY']
        pacman_row, pacman_col = int(pacman_y // tile_size), int(pacman_x // tile_size)

        directions = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}
        self.recent_positions.append((pacman_row, pacman_col))

        power_mode = state.get('isPowerMode', False)
        enemies = [(int(e['y'] // tile_size), int(e['x'] // tile_size)) for e in state.get('enemies', [])]

        if not self.walls_initialized:
            for r, row in enumerate(game_map):
                for c, tile in enumerate(row):
                    if tile == 1:
                        self.visited_positions.add((r, c))
            self.walls_initialized = True

        self.visited_positions.add((pacman_row, pacman_col))

        def is_walkable(r, c):
            return 0 <= r < len(game_map) and 0 <= c < len(game_map[0]) and game_map[r][c] != 1

        def is_safe(r, c):
            if not is_walkable(r, c):
                return False
            if power_mode:
                return True
            return all(abs(er - r) + abs(ec - c) > 1.5 for er, ec in enemies)

        def dijkstra_find_path(sr, sc):
            pq = [(0, sr, sc, [])]
            visited = set()
            while pq:
                cost, r, c, path = heapq.heappop(pq)
                if (r, c) in visited:
                    continue
                visited.add((r, c))
                if (r, c) not in self.visited_positions and is_safe(r, c):
                    self.current_target = (r, c)
                    return path
                for move, (dr, dc) in directions.items():
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in visited and is_walkable(nr, nc) and is_safe(nr, nc):
                        heapq.heappush(pq, (cost + 1, nr, nc, path + [move]))
            return []

        if len(self.recent_positions) >= 3:
            last3 = list(self.recent_positions)[-3:]
            if last3.count(last3[0]) == 3:
                self.path.clear()
                self.current_target = None

        if self.current_target is None or self.current_target == (pacman_row, pacman_col) or not self.path:
            self.current_target = None
            self.path = dijkstra_find_path(pacman_row, pacman_col)

        if self.path:
            move = self.path.pop(0)
            return {'move': move}

        possible_moves = [m for m, (dr, dc) in directions.items() if is_safe(pacman_row + dr, pacman_col + dc)]
        if possible_moves:
            return {'move': random.choice(possible_moves)}

        return {'move': 0}
