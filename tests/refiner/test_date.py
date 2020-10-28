import unittest
from show_a_table.refiner import date


class TestJO(unittest.TestCase):
    def setUp(self):
        self.data = date.DateRefiner()._data

    def test_jo_day(self):
        jo = date.JustOneDateRefiner(self.data)
        jo.year = "2020"
        jo.month = "9"
        (b, v) = jo.refine("1-10")
        self.assertEqual(b, False)
        self.assertEqual(v, self.data["day"]["d0"])
        (b, v) = jo.refine("1")
        self.assertEqual(b, True)
        self.assertEqual(v, ["2020-9-1"])


if __name__ == "__main__":
    unittest.main()
