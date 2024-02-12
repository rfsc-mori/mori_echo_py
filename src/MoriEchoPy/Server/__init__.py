import selectors
import signal
import socket
import threading
from types import FrameType
from uuid import UUID
from MoriEchoPy.Logging import server as Logger
from MoriEchoPy.Session import MoriEchoSession
from MoriEchoPy.Messages.MessageEchoRequest import MessageEchoRequest
from MoriEchoPy.Messages.MessageHeader import MessageHeader
from MoriEchoPy.Messages.MessageLoginRequest import MessageLoginRequest
from MoriEchoPy.Messages.MessageType import MessageType
from typing import cast, Callable, Optional, Self


class MoriEchoServer:
    __stop_event: threading.Event

    __sessions: dict[UUID, MoriEchoSession]

    __listen_socket: socket.socket
    __selector: selectors.DefaultSelector

    def run(self) -> None:
        self.__stop_event.clear()

        while self.is_running():
            try:
                events = self.__selector.select()
            except OSError as e:
                if e.errno == 9:  # Bad file descriptor: Socket closed -> stop
                    break
                else:
                    raise e

            for key, _ in events:
                event_data: MoriEchoServer.__EventData = key.data
                event_data.handler(cast(socket.socket, key.fileobj), event_data)

        for session in self.__sessions.values():
            if self.__selector.get_key(session.client_socket):
                self.__selector.unregister(session.client_socket)
                session.client_socket.close()

                Logger.info(
                    "Client %(uuid)s disconnected.",
                    {"uuid": session.uuid},
                )

        self.__sessions.clear()

        self.__selector.unregister(self.__listen_socket)
        self.__selector.close()

    def is_running(self) -> bool:
        running = not self.__stop_event.is_set()

        return running

    def shutdown(self) -> None:
        if self.__stop_event:
            self.__stop_event.set()

        self.__listen_socket.shutdown(socket.SHUT_RDWR)

    class __EventData:
        def __init__(
            self,
            handler: Callable[[socket.socket, Self], None],
        ) -> None:
            self.handler = handler

    class __ClientData(__EventData):
        def __init__(
            self,
            handler: Callable[[socket.socket, Self], None],
            session: MoriEchoSession,
        ) -> None:
            super().__init__(handler)
            self.session = session

    def __init__(self, address: str, port: int) -> None:
        signal.signal(signal.SIGINT, self.__stop_handler)
        signal.signal(signal.SIGTERM, self.__stop_handler)

        self.__listen_socket = socket.socket()
        self.__listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__listen_socket.bind((address, port))
        self.__listen_socket.listen()
        self.__listen_socket.setblocking(False)

        self.__selector = selectors.DefaultSelector()
        self.__selector.register(
            self.__listen_socket, selectors.EVENT_READ, self.__EventData(self.__accept)
        )

        self.__stop_event = threading.Event()

        self.__sessions = {}

        Logger.info(
            "Listening on port %(port)d",
            {"port": self.__listen_socket.getsockname()[1]},
        )

    def __stop_handler(self, _signal_number: int, _frame: Optional[FrameType]) -> None:
        self.shutdown()

    def __accept(self, listen_socket: socket.socket, _event_data: __EventData) -> None:
        if not self.is_running():
            return

        client, _addr = listen_socket.accept()
        client.setblocking(False)

        session = MoriEchoSession(client)
        self.__sessions[session.uuid] = session

        self.__selector.register(
            client,
            selectors.EVENT_READ,
            self.__ClientData(self.__read, session),
        )

        Logger.info(
            "New client connected: %(uuid)s",
            {"uuid": session.uuid},
        )

    def __read(self, client_socket: socket.socket, client_data: __ClientData) -> None:
        if not self.is_running():
            return

        try:
            if not client_data.session.header:
                self.__read_header(client_socket, client_data.session)
            else:
                self.__read_message(client_socket, client_data.session)
        except socket.error as e:
            self.__close_client(client_socket, client_data.session)

            Logger.error(
                "Dropping client %(uuid)s. Reason: %(error)s",
                {"uuid": client_data.session.uuid, "error": e},
            )
        except ValueError as e:
            self.__close_client(client_socket, client_data.session)

            Logger.error(
                "Dropping client %(uuid)s. Reason: %(error)s",
                {"uuid": client_data.session.uuid, "error": e},
            )

    def __read_header(
        self, client_socket: socket.socket, session: MoriEchoSession
    ) -> None:
        header_size = MessageHeader.header_size()
        expected_size = header_size - len(session.header_buffer)

        recv_data = client_socket.recv(expected_size)

        if recv_data:
            session.header_buffer += recv_data

            if len(session.header_buffer) > header_size:
                session.message_buffer = session.header_buffer[header_size:]
                session.header_buffer = session.header_buffer[:header_size]

            if len(session.header_buffer) == header_size:
                session.header = MessageHeader.parse(session.header_buffer)
                print(session.header)
                session.header_buffer.clear()
        else:
            self.__client_disconnected(client_socket, session)

    def __read_message(
        self,
        client_socket: socket.socket,
        session: MoriEchoSession,
    ) -> None:
        assert session.header

        if session.logged_in:
            if session.header.type == MessageType.LOGIN_REQUEST:
                raise ValueError("The client is already logged in.")
        else:
            if session.header.type != MessageType.LOGIN_REQUEST:
                raise ValueError("The client is not logged in.")

        message: Optional[MessageLoginRequest | MessageEchoRequest] = None

        match session.header.type:
            case MessageType.LOGIN_REQUEST:
                message = self.__read_login_request(client_socket, session)

                if message:
                    session.logged_in = True
                    print("Authenticated user: ", message.username)
            case MessageType.ECHO_REQUEST:
                message = self.__read_echo_request(client_socket, session)

                if message:
                    print("Received echo request: ", message.cipher_message)
            case _:
                raise ValueError("Invalid message type.")

    def __close_client(
        self, client_socket: socket.socket, session: MoriEchoSession
    ) -> None:
        if self.__selector.get_key(session.client_socket):
            self.__selector.unregister(client_socket)
            client_socket.close()

        self.__sessions.pop(session.uuid)

    def __client_disconnected(
        self, client_socket: socket.socket, session: MoriEchoSession
    ) -> None:
        self.__close_client(client_socket, session)
        Logger.info(
            "Client %(uuid)s disconnected.",
            {"uuid": session.uuid},
        )

    def __read_login_request(
        self, client_socket: socket.socket, session: MoriEchoSession
    ) -> Optional[MessageLoginRequest]:
        assert session.header

        message_size = MessageLoginRequest.message_size()
        expected_size = message_size - len(session.message_buffer)

        recv_data = client_socket.recv(expected_size)

        if recv_data:
            session.message_buffer += recv_data

            if len(session.message_buffer) > message_size:
                session.header_buffer = session.message_buffer[message_size:]
                session.message_buffer = session.message_buffer[:message_size]

            if len(session.message_buffer) == message_size:
                message = MessageLoginRequest.parse(
                    session.header, session.message_buffer
                )
                session.message_buffer.clear()

                return message
        else:
            self.__client_disconnected(client_socket, session)

        return None

    def __read_echo_request(
        self, client_socket: socket.socket, session: MoriEchoSession
    ) -> Optional[MessageEchoRequest]:
        assert session.header

        message_size = MessageEchoRequest.message_size_min()
        expected_size = message_size - len(session.message_buffer)

        message: Optional[MessageEchoRequest] = None

        if len(session.message_buffer) >= message_size:
            message = MessageEchoRequest.parse_message(
                session.header, session.message_buffer
            )
            message_size = message.message_size()
            expected_size = message_size - len(session.message_buffer)

        recv_data = client_socket.recv(expected_size)

        if recv_data:
            session.message_buffer += recv_data

            if len(session.message_buffer) > message_size:
                session.header_buffer = session.message_buffer[message_size:]
                session.message_buffer = session.message_buffer[:message_size]

            if len(session.message_buffer) == message_size:
                if not message:
                    message = MessageEchoRequest.parse_message(
                        session.header, session.message_buffer
                    )

                message.parse_payload(session.message_buffer)
                session.message_buffer.clear()

                return message
        else:
            self.__client_disconnected(client_socket, session)

        return None
