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
        self.safe_distance = 1.75
        self.game_map = None
        self.is_power_mode_on = False
        self.enemies = None
        self.directions = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}

    def reset_state(self) -> None:
        self.visited_positions.clear()
        self.path.clear()
        self.current_target = None
        self.recent_positions.clear()
        self.walls_initialized = False
        self.game_map = None
        self.is_power_mode_on = False
        self.enemies = None

    def _check_game_end(self, state: dict) -> bool:
        game_started = state.get('isGameStarted', False)
        if self.last_game_started and not game_started:
            return True
        self.last_game_started = game_started
        return False

    def is_walkable(self, walkable_row: int, walkable_column: int) -> bool:
        return (0 <= walkable_row < len(self.game_map) and 0 <= walkable_column < len(self.game_map[0])
                and self.game_map[walkable_row][walkable_column] != 1)

    def is_safe(self, safe_row: int, safe_column: int, enemies: list) -> bool:
        if not self.is_walkable(safe_row, safe_column):
            return False
        if self.is_power_mode_on:
            return True
        return all(abs(enemy_row - safe_row) + abs(enemy_column - safe_column) > self.safe_distance
                   for enemy_row, enemy_column in enemies)

    def dijkstra_find_path(self, start_row: int, start_column: int) -> list:
        pq = [(0, start_row, start_column, [])]
        visited = set()
        while pq:
            cost, dij_row, dij_column, path = heapq.heappop(pq)
            if (dij_row, dij_column) in visited:
                continue
            visited.add((dij_row, dij_column))
            if ((dij_row, dij_column) not in self.visited_positions
                    and self.is_safe(dij_row, dij_column, self.enemies)):
                self.current_target = (dij_row, dij_column)
                return path
            for dij_move, (direction_row, direction_column) in self.directions.items():
                next_row, next_column = dij_row + direction_row, dij_column + direction_column
                if ((next_row, next_column) not in visited and
                        self.is_walkable(next_row, next_column)
                        and self.is_safe(next_row, next_column, self.enemies)):
                    heapq.heappush(pq, (cost + 1, next_row, next_column, path + [dij_move]))
        return []

    def choose_move(self, data: dict):
        state = data['state']

        if self._check_game_end(state):
            self.reset_state()

        self.game_map = state['map']
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

        self.recent_positions.append((pacman_row, pacman_col))

        self.is_power_mode_on = state.get('isPowerMode', False)
        self.enemies = [(int(enemy['y'] // tile_size), int(enemy['x'] // tile_size))
                        for enemy in state.get('enemies', [])]

        if not self.walls_initialized:
            for r, row in enumerate(self.game_map):
                for c, tile in enumerate(row):
                    if tile == 1:
                        self.visited_positions.add((r, c))
            self.walls_initialized = True

        self.visited_positions.add((pacman_row, pacman_col))

        if len(self.recent_positions) >= 3:
            last3 = list(self.recent_positions)[-3:]
            if last3.count(last3[0]) == 3:
                self.path.clear()
                self.current_target = None

        if self.current_target is None or self.current_target == (pacman_row, pacman_col) or not self.path:
            self.current_target = None
            self.path = self.dijkstra_find_path(pacman_row, pacman_col)

        if self.path:
            move = self.path.pop(0)
            return {'move': move}

        possible_moves = [possible_move for possible_move, (direction_row, direction_column)
                          in self.directions.items() if self.is_safe(pacman_row + direction_row,
                                                                     pacman_col + direction_column, self.enemies)]
        if possible_moves:
            return {'move': random.choice(possible_moves)}

        return {'move': 0}


class CrossyRoadBot(BaseHandler):
    def choose_move(self, data: dict):
        state = data['state']

        if state.get('isGameOver'):
            return {'move': 0, 'action': 1}

        if state.get('isMoving') or state.get('moveCooldown', 0) > 0:
            return {'move': 0, 'action': 0}

        px = state['playerX']
        pz = state['playerZ']
        lanes = state['lanes']

        current_lane = next((l for l in lanes if l['z'] == pz), None)
        next_lane = next((l for l in lanes if l['z'] == pz + 1), None)
        prev_lane = next((l for l in lanes if l['z'] == pz - 1), None)

        if not current_lane or not next_lane:
            return {'move': 0, 'action': 0}

        danger_here = not self.is_safe(px, current_lane)
        left_safe = self.is_safe(px - 1, current_lane)
        right_safe = self.is_safe(px + 1, current_lane)

        if current_lane.get('type') == 'water':
            if px > 9 and left_safe:
                return {'move': 3, 'action': 0}
            if px < -5 and right_safe:
                return {'move': 4, 'action': 0}

        if self.is_safe(px, next_lane):
            return {'move': 1, 'action': 0}

        if danger_here:
            if prev_lane and self.is_safe(px, prev_lane):
                return {'move': 2, 'action': 0}
            if left_safe:
                return {'move': 3, 'action': 0}
            if right_safe:
                return {'move': 4, 'action': 0}

        next_lane_type = next_lane.get('type')

        if next_lane_type in ['grass', 'water']:
            if left_safe and self.is_safe(px - 1, next_lane):
                return {'move': 3, 'action': 0}
            if right_safe and self.is_safe(px + 1, next_lane):
                return {'move': 4, 'action': 0}

        return {'move': 0, 'action': 0}

    def is_safe(self, target_px, lane):
        if target_px < -8 or target_px > 12:
            return False

        lane_type = lane.get('type')
        obstacles = lane.get('obstacles', [])

        if lane_type == 'grass':
            for obs in obstacles:
                if obs.get('type') == 'tree':
                    if abs(obs.get('x', 0) - target_px) < 0.6:
                        return False
            return True

        if lane_type == 'road':
            lookahead_frames = 20

            for obs in obstacles:
                width = obs.get('width', 1.5)
                speed = obs.get('speed', 0)
                direction = obs.get('direction', 1)

                collision_threshold = (width / 2) + 0.2

                for frame in range(lookahead_frames):
                    future_x = obs.get('x', 0) + (speed * direction * frame)

                    if future_x > 20:
                        future_x -= 40
                    elif future_x < -20:
                        future_x += 40

                    if abs(future_x - target_px) < collision_threshold:
                        return False

            return True

        if lane_type == 'water':
            on_log = False
            for obs in obstacles:
                if obs.get('type') == 'log':
                    width = obs.get('width', 3.0)
                    safe_threshold = (width / 2) - 0.3

                    if abs(obs.get('x', 0) - target_px) < safe_threshold:
                        on_log = True
                        break
            return on_log

        return True