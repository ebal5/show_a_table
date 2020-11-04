import unittest

from show_a_table.model.refiner import date


class TestDateRefiner(unittest.TestCase):
    def setUp(self):
        self.dr = date.DateRefiner("誕生日")

    def test_range(self):
        pass

    def test_point(self):
        pass


class TestJO(unittest.TestCase):
    def setUp(self):
        self.data = date.DateRefiner("")._data

    def test_jo_day_no_wildcard(self):
        jo = date.JustOneDateRefiner("誕生日", self.data)
        jo.year = "2020"
        jo.month = "9"
        cds = jo.refine("1-10")
        cds = jo.refine("1")
        self.assertEqual(cds.exam("2020-09-01"), True)

    def test_jo_day_wildcard(self):
        jo = date.JustOneDateRefiner("誕生日", self.data)
        jo.year = "*"
        jo.month = "9"
        cds = jo.refine("1-10")
        cds = jo.refine("1")
        self.assertEqual(cds.exam("2020-09-01"), True)

    def test_get_query(self):
        jo = date.JustOneDateRefiner("誕生日", self.data)
        jo.year = "*"
        jo.month = "9"
        cds = jo.refine("1-10")
        cds = jo.refine("1")
        q = "猫の誕生日は?"
        self.assertEqual(cds.get_query("猫"), q)


if __name__ == "__main__":
    unittest.main()
