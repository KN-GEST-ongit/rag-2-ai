from src.agents.web_env import WebsocketAgent
from stable_baselines3.common.base_class import BaseAlgorithm
from src.utils import normalize_observation

import numpy as np


class CrossyRoadAgent(WebsocketAgent):
    def __init__(self, model: BaseAlgorithm, history_length: int = 1):
        super().__init__(model, history_length)

        self.min_values = np.array([-8.0] + [-1.0] * 20, dtype=np.float32)
        self.max_values = np.array([12.0] + [1.0] * 20, dtype=np.float32)

        self.low = np.array([-1.0] * 21, dtype=np.float32)
        self.high = np.array([1.0] * 21, dtype=np.float32)

    def prepare_observation(self, data: dict) -> np.array:
        state = data['state']
        px = state.get('playerX', 0)
        pz = state.get('playerZ', 0)
        lanes = state.get('lanes', [])

        vision_grid = []
        for dz in [2, 1, 0, -1]:
            lane = next((l for l in lanes if l['z'] == pz + dz), None)
            for dx in [-2, -1, 0, 1, 2]:
                if not lane:
                    vision_grid.append(-1.0)
                else:
                    is_safe_tile = self.is_safe(px + dx, lane)
                    vision_grid.append(1.0 if is_safe_tile else -1.0)

        curr_observation = np.array([px] + vision_grid, dtype=np.float32)

        return self.state_stack(curr_observation)

    def return_prediction(self, data: dict) -> dict:
        is_game_over = data.get('state', {}).get('isGameOver', False)

        if is_game_over:
            if not getattr(self, 'waiting_for_reset', False):
                self.waiting_for_reset = True
                return {'move': 0, 'action': 1}
            else:
                return {'move': 0, 'action': 0}

        self.waiting_for_reset = False

        obs = self.prepare_observation(data)

        action, _states = self.model.predict(
            observation=obs,
            deterministic=True
        )

        return {'move': int(action), 'action': 0}

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