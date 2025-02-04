from scripts.paths.algos_paths import dqn_path, ppo_path, trpo_path

import os

env_path = os.path.join(
    'WebsocketHappyJump-v0',
    'WebsocketHappyJump-v0_200000_steps.zip'
)

dqn_hj_path = os.path.join(dqn_path, env_path)
ppo_hj_path = os.path.join(ppo_path, env_path)
trpo_hj_path = os.path.join(trpo_path, env_path)
