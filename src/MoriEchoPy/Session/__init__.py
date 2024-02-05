import uuid
import socket


class MoriEchoSession:
    def __init__(self, client_socket: socket.socket) -> None:
        self.client_socket = client_socket
        self.uuid = uuid.uuid4()
