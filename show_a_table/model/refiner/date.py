import datetime

import toml
from dateutil.parser import parse as datetime_parser
from dateutil.parser._parser import ParserError

from .refiner import Candidate, Candidates, FunQuery, Refiner, RegQuery
from .util import read_text


def _preprocess_date(result):
    """
    Parameters
    ----------
    result : str
      実行結果．日付けらしいことを求める

    Returns
    -------
    date
      result を datetime の date として表現したもの
    """
    try:
        return datetime_parser(result).date()
    except ParserError as e:
        # TODO あきらめのモックアップを削除
        print(e)
        return datetime.date.today()


class DateRefiner(Refiner):
    def __init__(self, attr_name):
        super().__init__(attr_name)
        self._data = toml.loads(read_text(__file__, "date.toml"))
        self._refiner = None

    def refine(self, choice=None):
        if type(choice) is Candidate:
            choice = choice.key
        if not choice:
            cands = ["範囲", "日付指定"]
            return Candidates("日付の選択/方法の選択", cands, self)
        elif choice == "範囲":
            self._refiner = DateRangeRefiner(self.attr, self._data)
        elif choice == "日付指定":
            self._refiner = JustOneDateRefiner(self.attr, self._data)
        return self._refiner.refine(choice)


class DateRangeRefiner(Refiner):
    def __init__(self, attr_name, data):
        super().__init__(attr_name)
        self._data = data

    def refine(self, choice):
        # TODO 実装
        return super().refine()


class JustOneDateRefiner(Refiner):
    def __init__(self, attr_name, data, solo=True, start=None):
        """
        Parameters
        ----------
        attr_name : str
          属性名．クエリ生成に用いる
        data : Dict
          設定データ
        solo : bool
          独立して日付けを指定するか否か
          FalseならばRangeの一部と判断
        start : XXX
          Rangeの一部の場合に用いる．この日付けよりも後であることを明示する
        """
        super().__init__(attr_name)
        # TODO start を考慮する
        self._data = data
        self.year = ""
        self.month = ""
        self.day = ""
        self._last = ""
        self._solo = True

    def _solo_exam(self):
        def exam(result):
            res_date = _preprocess_date(result)
            if all([self.year != "*",
                    self.month != "*",
                    self.day != "*"]):
                pick_date = datetime.date(int(self.year),
                                          int(self.month),
                                          int(self.day))
                return res_date == pick_date
            else:
                return all([self.year == "*" or res_date.year == int(self.year),
                           self.month == "*" or res_date.month == int(self.month),
                           self.day == "*" or res_date.day == int(self.day)])
        return exam

    def refine(self, choice):
        if type(choice) is Candidate:
            choice = choice.key
        if not self.year:
            return self._year(choice)
        elif not self.month:
            return self._month(choice)
        elif not self.day:
            return self._day(choice)
        elif self._solo:
            # ここらへん，unreachableじゃね？
            return FunQuery(self._solo_exam(), lambda tgt: f"{tgt}の{self.attr}は?")
        else:
            # TODO Rangeの一部として動く場合
            pass

    def _year(self, choice):
        _yd = self._data["year"]
        _last = self._last
        self._last = choice
        if not _last:
            self._last = "MEANINGLESS VALUE"
            return Candidates("日付の選択/年の選択", _yd["origin"], self)
        elif choice in _yd["origin"]:
            if choice == "SKIP":
                self._last = ""
                self.year = "*"
                return Candidates("日付けの選択/月の選択", self._data["month"]["origin"], self)
            elif choice == "BCE":
                return Candidates("日付けの選択/年の選択/紀元前", _yd["bce"])
            else:
                idx = _yd["origin"].index(choice)
                return Candidates("日付けの選択/年の選択", _yd[f"y{idx - 1}"], self)
        elif choice in _yd["bce"]:
            # TODO: implementation of BCE refiner
            pass
        elif choice.startswith("-"):
            _y = int(choice[1:])
            lst = [str(y) for y in range(_y-25+1, _y+1, 1)]
            return Candidates("日付の選択/年の選択", lst)
        else:
            self._last = ""
            self.year = choice
            return Candidates("日付けの選択/月の選択", self._data["month"]["origin"], self)

    def _month(self, choice):
        if choice == "SKIP":
            self.month = "*"
        else:
            self.month = choice
        return Candidates("日付けの選択/月の選択", self._data["day"]["origin"], self)

    def _day(self, choice):
        # TODO 日付けのSKIPも対応するように
        _dd = self._data["day"]
        if "-" in choice:
            idx = _dd["origin"].index(choice)
            return Candidates("日付けの選択/日にちの選択", _dd[f"d{idx}"], self)
        else:
            self.day = choice
            return FunQuery(self._solo_exam(), lambda tgt: f"{tgt}の{self.attr}は?")
