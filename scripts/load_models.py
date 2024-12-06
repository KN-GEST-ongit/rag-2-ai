from stable_baselines3 import DQN, PPO, A2C
from sb3_contrib import TRPO
from scripts.paths.pong_paths import dqn_pong_path, ppo_pong_path, a2c_pong_path
from scripts.paths.flappy_bird_paths import ppo_fb_path, trpo_fb_path

# Pong
dqn_pong = DQN.load(path=dqn_pong_path)
ppo_pong = PPO.load(path=ppo_pong_path)
a2c_pong = A2C.load(path=a2c_pong_path)

# Flappy Bird
ppo_fb = PPO.load(path=ppo_fb_path)
trpo_fb = TRPO.load(path=trpo_fb_path)
