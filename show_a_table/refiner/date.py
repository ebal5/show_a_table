from importlib.resources import read_text
import toml

from .refiner import Refiner


class DateRefiner(Refiner):
    def __init__(self):
        self._data = toml.loads(read_text(__package__, "date.toml"))

    def refine(choice=""):
        return super().refine()


class DateRangeRefiner(Refiner):
    def __init__(self, data):
        self._data = data
        pass

    def refine(choice=""):
        return super().refine()


class JustOneDateRefiner(Refiner):
    def __init__(self, data, start=None):
        self._data = data
        self.year = ""
        self.month = ""
        self.day = ""
        self._last = ""

    def refine(self, choice=""):
        if not self.year:
            return self._year(choice)
        elif not self.month:
            return self._month(choice)
        elif not self.day:
            return self._day(choice)
        else:
            return [True, [f"{self.year}-{self.month}-{self.day}"]]

    def _year(self, choice):
        _yd = self._data["year"]
        _last = self._last
        self._last = choice
        if not _last:
            self._last = "MEANINGLESS VALUE"
            return (False, _yd["origin"])
        elif choice in _yd["origin"]:
            if choice == "SKIP":
                self._last = ""
                self.year = "*"
                return (False, self._data["month"]["origin"])
            elif choice == "BCE":
                return (False, _yd["bce"])
            else:
                idx = _yd["origin"].index(choice)
                return (False, _yd[f"y{idx - 1}"])
        elif choice in _yd["bce"]:
            # TODO: implementation of BCE refiner
            pass
        elif choice.startswith("-"):
            _y = int(choice[1:])
            lst = [str(y) for y in range(_y-25+1, _y+1, 1)]
            return (False, lst)
        else:
            self._last = ""
            self.year = choice
            return (False, self._data["month"]["origin"])

    def _month(self, choice):
        self.month = choice
        return (False, self._data["day"]["origin"])

    def _day(self, choice):
        _dd = self._data["day"]
        if "-" in choice:
            idx = _dd["origin"].index(choice)
            return (False, _dd[f"d{idx}"])
        else:
            self.day = choice
            return [True, [f"{self.year}-{self.month}-{self.day}"]]
