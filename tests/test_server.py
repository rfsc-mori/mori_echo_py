import unittest

from MoriEchoPy.server import run_server


class TestServer(unittest.TestCase):
    def test_run_server(self):
        self.assertEqual(run_server(), None)


if __name__ == "__main__":
    unittest.main()
