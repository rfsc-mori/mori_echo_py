import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s",
)

general = logging.getLogger("general")
server = logging.getLogger("server")
