from dataclasses import dataclass
from MoriEchoPy.Messages.MessageHeader import MessageHeader


@dataclass
class MessageLoginRequest:
    header: MessageHeader
    username: bytearray
    password: bytearray

    @staticmethod
    def total_size() -> int:
        return MessageHeader.header_size() + MessageLoginRequest.message_size()

    @staticmethod
    def message_size() -> int:
        return 32 + 32

    @staticmethod
    def parse(header: MessageHeader, data: bytearray) -> "MessageLoginRequest":
        if header.total_size != MessageLoginRequest.total_size():
            raise ValueError("Message size mismatch.")

        if len(data) != MessageLoginRequest.message_size():
            raise ValueError("Message size mismatch.")

        # Expected null-terminators are ignored at the end of the string.
        username = data[0:31].split(b"\x00")[0]
        password = data[32:63].split(b"\x00")[0]

        return MessageLoginRequest(header, username, password)
