from typing import List, Tuple, Type
from src.api import RoutesHandler
from src.bots import PongBot, FlappybirdBot, SkiJumpBot, HappyJumpBot, PacManBot
from src.handlers import AiHandler
from src.agents.web_pong import PongAgent
from src.agents.web_flappy_bird import FlappyBirdAgent
from src.agents.web_happy_jump import HappyJumpAgent
from scripts.load_models import (
    dqn_pong,
    ppo_pong,
    a2c_pong,
    trpo_pong,
    qrdqn_pong,
    ars_fb,
    ppo_fb,
    trpo_fb,
    dqn_hj,
    ppo_hj,
    trpo_hj
)


def define_routes() -> List[Tuple[str, Type, dict]]:
    routes = []
    pong_routes = [
        (r"/ws/pong/pong-bot/", PongBot),
        # # DO NOT UNCOMMENT
        # (r"/ws/pong/pong-a2c/", AiHandler, dict(
        #     agent=PongAgent(a2c_pong, 3)
        # )),
        (r"/ws/pong/pong-dqn/", AiHandler, dict(
            agent=PongAgent(dqn_pong, 3)
        )),
        (r"/ws/pong/pong-ppo/", AiHandler, dict(
            agent=PongAgent(ppo_pong, 3)
        )),
        # # DO NOT UNCOMMENT
        # (r"/ws/pong/pong-qrdqn/", AiHandler, dict(
        #     agent=PongAgent(qrdqn_pong, 3)
        # )),
        (r"/ws/pong/pong-trpo/", AiHandler, dict(
            agent=PongAgent(trpo_pong, 3)
        ))
    ]

    flappybird_routes = [
        (r"/ws/flappybird/flappybird-bot/", FlappybirdBot),
        (r"/ws/flappybird/flappybird-ars/", AiHandler, dict(
            agent=FlappyBirdAgent(ars_fb, 1)
        )),
        (r"/ws/flappybird/flappybird-ppo/", AiHandler, dict(
            agent=FlappyBirdAgent(ppo_fb, 3)
        )),
        (r"/ws/flappybird/flappybird-trpo/", AiHandler, dict(
            agent=FlappyBirdAgent(trpo_fb, 3)
        ))
    ]

    skijump_routes = [
        (r"/ws/skijump/skijump-bot/", SkiJumpBot)
    ]

    happyjump_routes = [
        (r"/ws/happyjump/happyjump-bot/", HappyJumpBot),
        (r"/ws/happyjump/happyjump-dqn/", AiHandler, dict(
            agent=HappyJumpAgent(dqn_hj, 3)
        )),
        (r"/ws/happyjump/happyjump-ppo/", AiHandler, dict(
            agent=HappyJumpAgent(ppo_hj, 3)
        )),
        (r"/ws/happyjump/happyjump-trpo/", AiHandler, dict(
            agent=HappyJumpAgent(trpo_hj, 3)
        )),
    ]

    pacman_routes = [
        (r"/ws/pacman/pacman-bot/", PacManBot)
    ]

    pong_endpoint = (r"/ws/pong/routes/", RoutesHandler, dict(routes=pong_routes))
    flappybird_endpoint = (r"/ws/flappybird/routes/", RoutesHandler, dict(routes=flappybird_routes))
    skijump_endpoint = (r"/ws/skijump/routes/", RoutesHandler, dict(routes=skijump_routes))
    happyjump_endpoint = (r"/ws/happyjump/routes/", RoutesHandler, dict(routes=happyjump_routes))
    pacman_endpoint = (r"/ws/pacman/routes/", RoutesHandler, dict(routes=pacman_routes))

    routes += pong_routes
    routes += flappybird_routes
    routes += skijump_routes
    routes += happyjump_routes
    routes += pacman_routes

    routes.append(pong_endpoint)
    routes.append(flappybird_endpoint)
    routes.append(skijump_endpoint)
    routes.append(happyjump_endpoint)
    routes.append(pacman_endpoint)

    return routes
