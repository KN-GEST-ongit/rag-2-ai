from scripts.paths.algos_paths import a2c_path, dqn_path, ppo_path, trpo_path, qrdqn_path

import os

env_path = os.path.join(
    'WebsocketPong-v0',
    'WebsocketPong-v0_200000_steps.zip'
)

dqn_pong_path = os.path.join(dqn_path, env_path)
ppo_pong_path = os.path.join(ppo_path, env_path)
a2c_pong_path = os.path.join(a2c_path, env_path)
trpo_pong_path = os.path.join(trpo_path, env_path)
qrdqn_pong_path = os.path.join(qrdqn_path, env_path)
