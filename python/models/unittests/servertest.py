import unittest

from schemer import ValidationException

import models.server


def bad_input(inputstring):
    test = models.server.Server({
        "server": 123456,
        "daytime": inputstring,
        "nighttime": "06:00",
        "warning": 60
    })
    test.save()
    test.remove()


def bad_warning(warning):
    test = models.server.Server({
        "server": 123456,
        "daytime": "12:30",
        "nighttime": "06:00",
        "warning": warning
    })
    test.save()
    test.remove()


class MyServerTest(unittest.TestCase):

    def test_good_time(self):
        test = models.server.Server({
            "server": 123456,
            "daytime": "14:00",
            "nighttime": "06:00",
            "warning": 60
        })
        test.save()
        x = models.server.Server.find_one({"server": 123456})
        self.assertIsNotNone(x)
        test.remove()

    def test_bad_time(self):
        self.assertRaises(ValidationException, bad_input, "26:43")

    def test_no_time(self):
        self.assertRaises(ValidationException, bad_input, "hello")

    def test_bad_warning(self):
        self.assertRaises(ValidationException, bad_warning, 250)

    def test_edge_good_warning(self):
        test = models.server.Server({
            "server": 123456,
            "daytime": "14:00",
            "nighttime": "06:00",
            "warning": 180
        })
        test.save()
        x = models.server.Server.find_one({"server": 123456})
        self.assertIsNotNone(x)
        test.remove()

    def test_default(self):
        test = models.server.Server({"server": 1234})
        test.save()
        x = models.server.Server.find_one({"server": 1234})
        self.assertIsNotNone(x)
        self.assertIsNotNone(x["daytime"])
        test.remove()

    def test_remove(self):
        test = models.server.Server({"server": 123})
        test.save()
        x = models.server.Server.find_one({"server": 123})
        self.assertIsNotNone(x)
        x.remove()
        x = models.server.Server.find_one({"server": 123})
        self.assertIsNone(x)


if __name__ == '__main__':
    unittest.main()
