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

        message = b"This is an unit test message."
        client.sendall(message)

        recv_message = bytearray()
        expected_recv_size = len(message)

        while expected_recv_size > 0:
            received = client.recv(expected_recv_size)
            expected_recv_size -= len(received)
            recv_message += received

        self.assertEqual(recv_message, message)

        client.close()

        server.shutdown()

        server_thread.join()


if __name__ == "__main__":
    unittest.main()
