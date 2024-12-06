import os

from typing import List, Tuple, Type
from stable_baselines3 import DQN, PPO, A2C
from src.api import RoutesHandler
from src.bots import PongBot, FlappybirdBot, SkijumpBot
from src.handlers import AiHandler
from src.agents.web_pong import PongAgent


def define_routes() -> List[Tuple[str, Type, dict]]:
    dqn_path = os.path.join('ready-models', 'dqn')
    ppo_path = os.path.join('ready-models', 'ppo')
    a2c_path = os.path.join('ready-models', 'a2c')

    dqn_pong_path = os.path.join(
        dqn_path,
        'WebsocketPong-v0',
        'WebsocketPong-v0_200000_steps.zip'
    )
    dqn_pong = DQN.load(path=dqn_pong_path)

    ppo_pong_path = os.path.join(
        ppo_path,
        'WebsocketPong-v0',
        'WebsocketPong-v0_200000_steps.zip'
    )
    ppo_pong = PPO.load(path=ppo_pong_path)

    a2c_pong_path = os.path.join(
        a2c_path,
        'WebsocketPong-v0',
        'WebsocketPong-v0_200000_steps.zip'
    )
    a2c_pong = A2C.load(path=a2c_pong_path)

    routes = []
    pong_routes = [
        (r"/ws/pong/pong-dqn/", AiHandler, dict(
            agent=PongAgent(dqn_pong, 3)
        )),
        (r"/ws/pong/pong-ppo/", AiHandler, dict(
            agent=PongAgent(ppo_pong, 3)
        )),
        (r"/ws/pong/pong-a2c/", AiHandler, dict(
            agent=PongAgent(a2c_pong, 3)
        )),
        (r"/ws/pong/pong-bot/", PongBot),
    ]
    flappybird_routes = [
        (r"/ws/flappybird/flappybird-bot/", FlappybirdBot),
    ]
    skijump_routes = [
        (r"/ws/skijump/skijump-bot/", SkijumpBot)
    ]

    pong_endpoint = (r"/ws/pong/routes/", RoutesHandler, dict(routes=pong_routes))
    flappybird_endpoint = (r"/ws/flappybird/routes/", RoutesHandler, dict(routes=flappybird_routes))
    skijump_endpoint = (r"/ws/skijump/routes/", RoutesHandler, dict(routes=skijump_routes))

    routes += pong_routes
    routes += flappybird_routes
    routes += skijump_routes

    routes.append(pong_endpoint)
    routes.append(flappybird_endpoint)
    routes.append(skijump_endpoint)

    return routes
