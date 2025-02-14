import tornado.ioloop
import tornado.web
import tornado.websocket

from games.pong import PongWebSocketHandler


app = tornado.web.Application([
        (r"/ws/pong/", PongWebSocketHandler) #http://localhost:8001/ws/pong/
      ]) 
app.listen(8001)

print("Started")
tornado.ioloop.IOLoop.current().start()

