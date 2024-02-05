from MoriEchoPy.Logging import general as Logger
from MoriEchoPy.Server import MoriEchoServer


def main() -> None:
    Logger.info("MoriEchoPy TCP Echo Server started.")

    server = MoriEchoServer(address="localhost", port=31216)
    server.run()

    Logger.info("MoriEchoPy TCP Echo Server exiting...")
