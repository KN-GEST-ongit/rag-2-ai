from scripts.paths.algos_paths import ars_path, ppo_path, trpo_path

import os


env_path = os.path.join(
    'WebsocketFlappyBird-v0',
    'WebsocketFlappyBird-v0_200000_steps.zip'
)

ars_fb_path = os.path.join(ars_path, env_path)
ppo_fb_path = os.path.join(ppo_path, env_path)
trpo_fb_path = os.path.join(trpo_path, env_path)
