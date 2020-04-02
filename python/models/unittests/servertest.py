import unittest
import models.server


class ServerTests(unittest.TestCase):
    def test_schema(self):
        test = models.server.Server({
            "server": 123456,
            "daytime": {
                "hour": 8,
                "minute": 30
            },
            "nighttime": {
                "hour": 20,
                "minute": 0
            }
        })
        test.save()
        x = models.server.Server.find_one({"server": 123456})
        print(x)
        test.remove()


if __name__ == '__main__':
    unittest.main()
