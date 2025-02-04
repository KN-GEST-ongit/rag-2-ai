from stable_baselines3 import DQN, PPO, A2C
from sb3_contrib import ARS, TRPO, QRDQN
from scripts.paths.pong_paths import dqn_pong_path, ppo_pong_path, a2c_pong_path, trpo_pong_path, qrdqn_pong_path
from scripts.paths.flappy_bird_paths import ars_fb_path, ppo_fb_path, trpo_fb_path
from scripts.paths.happy_jump_paths import dqn_hj_path, ppo_hj_path, trpo_hj_path

# Pong
dqn_pong = DQN.load(path=dqn_pong_path)
ppo_pong = PPO.load(path=ppo_pong_path)
a2c_pong = A2C.load(path=a2c_pong_path)
trpo_pong = TRPO.load(path=trpo_pong_path)
qrdqn_pong = QRDQN.load(path=qrdqn_pong_path)


# Flappy Bird
ars_fb = ARS.load(path=ars_fb_path)
ppo_fb = PPO.load(path=ppo_fb_path)
trpo_fb = TRPO.load(path=trpo_fb_path)

# Happy Jump
dqn_hj = DQN.load(path=dqn_hj_path)
ppo_hj = PPO.load(path=ppo_hj_path)
trpo_hj = TRPO.load(path=trpo_hj_path)
