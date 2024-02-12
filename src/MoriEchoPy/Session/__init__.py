from typing import Optional
from uuid import UUID, uuid4
import socket

from MoriEchoPy.Messages.MessageHeader import MessageHeader


class MoriEchoSession:
    client_socket: socket.socket

    uuid: UUID = uuid4()
    logged_in: bool = False

    header_buffer: bytearray = bytearray()
    message_buffer: bytearray = bytearray()

    header: Optional[MessageHeader] = None

    def __init__(self, client_socket: socket.socket) -> None:
        self.client_socket = client_socket
