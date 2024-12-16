import tornado.ioloop
import tornado.web
import tornado.websocket

from games.pong import PongWebSocketHandler, PongBot, HappyJumpBot

def make_app():
    return tornado.web.Application([
        (r"/ws/pong/", PongWebSocketHandler), #http://localhost:8001/ws/pong/
        (r"/ws/pong-bot/", PongBot), #http://localhost:8001/ws/pong-bot/
        (r"/ws/happyjump-bot/", HappyJumpBot),  #http://localhost:8001/ws/happyjump-bot/
    ])


def run():
    app = make_app()
    app.listen(8001)
    print("Started")
    tornado.ioloop.IOLoop.current().start()


run()
