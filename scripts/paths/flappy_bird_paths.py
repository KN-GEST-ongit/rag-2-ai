from scripts.paths.algos_paths import ppo_path, trpo_path

import os


env_path = os.path.join(
    'WebsocketFlappyBird-v0',
    'WebsocketFlappyBird-v0_200000_steps.zip'
)

ppo_fb_path = os.path.join(ppo_path, env_path)
trpo_fb_path = os.path.join(trpo_path, env_path)
