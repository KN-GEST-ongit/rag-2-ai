from typing import List, Tuple, Type
from src.api import RoutesHandler
from src.bots import PongBot, FlappybirdBot, SkijumpBot
from src.handlers import AiHandler
from src.agents.web_pong import PongAgent
from src.agents.web_flappy_bird import FlappyBirdAgent
from scripts.load_models import (
    dqn_pong,
    ppo_pong,
    a2c_pong,
    ppo_fb,
    trpo_fb
)


def define_routes() -> List[Tuple[str, Type, dict]]:
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
        (r"/ws/flappybird/flappybird-ppo/", AiHandler, dict(
            agent=FlappyBirdAgent(ppo_fb, 3)
        )),
        (r"/ws/flappybird/flappybird-trpo/", AiHandler, dict(
            agent=FlappyBirdAgent(trpo_fb, 3)
        )),
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
