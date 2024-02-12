from dataclasses import dataclass
import struct
from typing import Optional
from MoriEchoPy.Messages.MessageHeader import MessageHeader


@dataclass
class MessageEchoRequest:
    header: MessageHeader
    payload_size: int
    cipher_message: Optional[bytearray]

    @staticmethod
    def total_size_min() -> int:
        return MessageHeader.header_size() + MessageEchoRequest.message_size_min()

    @staticmethod
    def message_size_min() -> int:
        return 2

    @staticmethod
    def parse_message(header: MessageHeader, data: bytearray) -> "MessageEchoRequest":
        if header.total_size < MessageEchoRequest.total_size_min():
            raise ValueError("Message too short.")

        if len(data) < MessageEchoRequest.message_size_min():
            raise ValueError("Message too short.")

        payload_size: int = struct.unpack("<H", data[0:2])[0]

        return MessageEchoRequest(header, payload_size, None)

    def total_size(self) -> int:
        return MessageHeader.header_size() + self.message_size()

    def message_size(self) -> int:
        return MessageEchoRequest.message_size_min() + self.payload_size

    def parse_payload(self, data: bytearray) -> None:
        if self.header.total_size != self.total_size():
            raise ValueError("Message size mismatch.")

        if len(data) != self.message_size():
            raise ValueError("Message size mismatch.")

        self.cipher_message = data[2:]
