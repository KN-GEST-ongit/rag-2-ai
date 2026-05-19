from scripts.paths.algos_paths import ppo_path, trpo_path

import os

env_path = os.path.join(
    'WebsocketCrossyRoad-v0',
    'WebsocketCrossyRoad-v0_300000_steps.zip'
)

ppo_cr_path = os.path.join(ppo_path, env_path)
trpo_cr_path = os.path.join(trpo_path, env_path)