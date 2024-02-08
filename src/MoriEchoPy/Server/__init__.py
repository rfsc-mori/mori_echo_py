import selectors
import signal
import socket
from types import FrameType
from uuid import UUID
from MoriEchoPy.Logging import server as Logger
from MoriEchoPy.Session import MoriEchoSession
from typing import cast, Callable, Optional, Self


class MoriEchoServer:
    def run(self) -> None:
        self.__running = True

        while self.__running:
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
            session.client_socket.close()

        self.__sessions.clear()

    def stop(self) -> None:
        self.__running = False

        self.__listen_socket.close()
        self.__selector.close()

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
        self.__listen_socket.bind((address, port))
        self.__listen_socket.listen()
        self.__listen_socket.setblocking(False)

        self.__selector = selectors.DefaultSelector()
        self.__selector.register(
            self.__listen_socket, selectors.EVENT_READ, self.__EventData(self.__accept)
        )

        self.__running = False

        self.__sessions: dict[UUID, MoriEchoSession] = {}

        Logger.info(
            "Listening on port %(port)d",
            {"port": self.__listen_socket.getsockname()[1]},
        )

    def __stop_handler(self, _signal_number: int, _frame: Optional[FrameType]) -> None:
        self.stop()

    def __accept(self, listen_socket: socket.socket, _event_data: __EventData) -> None:
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

    def __read(self, client: socket.socket, event_data: __ClientData) -> None:
        try:
            client_data = client.recv(1000)

            if client_data:
                client.send(client_data)
            else:
                self.__close_client(client, event_data.session)

                Logger.info(
                    "Client %(uuid)s disconnected.",
                    {"uuid": event_data.session.uuid},
                )
        except socket.error as e:
            self.__close_client(client, event_data.session)

            Logger.error(
                "Dropping client %(uuid)s. Reason: %(error)s",
                {"uuid": event_data.session.uuid, "error": e},
            )

    def __close_client(self, client: socket.socket, session: MoriEchoSession) -> None:
        self.__selector.unregister(client)
        client.close()

        self.__sessions.pop(session.uuid)
