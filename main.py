from scripts.define_routes import define_routes
from src.socket import run_socket


def main():
    routes = define_routes()
    run_socket(port=8001, routes=routes)


if __name__ == '__main__':
    main()
