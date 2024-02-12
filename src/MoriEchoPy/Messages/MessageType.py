from enum import Enum


class MessageType(Enum):
    LOGIN_REQUEST = 0
    LOGIN_RESPONSE = 1
    ECHO_REQUEST = 2
    ECHO_RESPONSE = 3
