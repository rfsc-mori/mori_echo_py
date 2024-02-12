from dataclasses import dataclass
import struct

from MoriEchoPy.Messages.MessageType import MessageType


@dataclass
class MessageHeader:
    total_size: int
    type: MessageType
    sequence: int

    @staticmethod
    def header_size() -> int:
        return 2 + 1 + 1

    @staticmethod
    def header_size_max() -> int:
        return 65535

    @staticmethod
    def parse(data: bytearray) -> "MessageHeader":
        if len(data) < MessageHeader.header_size():
            raise ValueError("Message too short.")

        total_size: int = struct.unpack("<H", data[0:2])[0]
        type: int = struct.unpack("B", data[2:3])[0]
        sequence: int = struct.unpack("B", data[3:4])[0]

        if total_size < MessageHeader.header_size():
            raise ValueError("Message too short.")

        if total_size > MessageHeader.header_size_max():
            raise ValueError("Message too short.")

        return MessageHeader(total_size, MessageType(type), sequence)
