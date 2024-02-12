import socket
import unittest
import threading

from MoriEchoPy.Server import MoriEchoServer


class TestServer(unittest.TestCase):
    def test_run_server(self) -> None:
        server = MoriEchoServer(address="localhost", port=31216)

        server_thread = threading.Thread(target=server.run)
        server_thread.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 31216))

        message = b"\x00\x04\xff\x00"
        client.sendall(message)

        # Incomplete, just tests connection
        client.recv(1)
        client.close()

        server.shutdown()

        server_thread.join()


if __name__ == "__main__":
    unittest.main()
