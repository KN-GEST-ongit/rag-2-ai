from typing import List, Tuple, Type

import tornado.ioloop
from tornado.web import Application


def make_app(routes: List[Tuple[str, Type, dict]]) -> Application:
    return Application(routes, websocket_ping_interval=10, websocket_ping_timeout=30, )


def run_socket(port: int, routes: List[Tuple[str, Type, dict]]) -> None:
    app = make_app(routes)
    app.listen(port)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        tornado.ioloop.IOLoop.current().stop()
