import datetime

from dateutil.parser import parse as datetime_parser
from dateutil.parser._parser import ParserError

from .refiner import Candidate, Candidates, FunQuery, Refiner, NumCandidates, DQQuery


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
        self._refiner = None

    def refine(self, choice=None):
        if not choice:
            cands = ["範囲", "日付指定"]
            return Candidates("日付の選択/方法の選択", cands, self)
        elif choice.key == "範囲":
            self._refiner = DateRangeRefiner(self.attr)
        elif choice.key == "日付指定":
            self._refiner = JustOneDateRefiner(self.attr, solo=True, start=None)
        return self._refiner.refine(choice)


class DateRangeRefiner(Refiner):
    def __init__(self, attr_name):
        super().__init__(attr_name)
        self._start = None
        self._sref = None
        self._end = None
        self._eref = None

    def refine(self, choice):
        if not self._sref:
            self._sref = JustOneDateRefiner(self.attr, solo=False)
            ret = self._sref.refine("日付指定")
            ret.title = "開始" + ret.title
            return ret
        elif not self._start:
            ret = self._sref.refine(choice)
            if isinstance(ret, DQQuery):
                self._start = self._sref.expression()
                self._eref = JustOneDateRefiner(self.attr, solo=False, start=self._start)
                ret = self._eref.refine("日付指定")
                ret.title = "終了" + ret.title
                return ret
            else:
                ret.title = "開始" + ret.title
                return ret
        else:
            ret = self._eref.refine(choice)
            if isinstance(ret, DQQuery):
                self._end = self._eref.expression()
                return FunQuery(self._mk_exam(),
                                lambda tgt: "{tgt}の{attr}は?".format(tgt=tgt, attr=self.attr))
            else:
                ret.title = "終了" + ret.title
                return ret

    def _mk_exam(self):
        # 天文学などで使われる単位に変換
        if self._start.startswith("BCE"):
            start = self._start = [int(c) if c.isdigit() else None for c in self._start.split("-")]
            start[0] = -(start[0]-1)
        else:
            start = self._start = [int(c) if c.isdigit() else None for c in self._start.split("-")]
        if self._end.startswith("BCE"):
            end = self._start = [int(c) if c.isdigit() else None for c in self._end.split("-")]
            end[0] = -(end[0]-1)
        else:
            end = self._start = [int(c) if c.isdigit() else None for c in self._end.split("-")]
        _s = start
        _e = end

        def both(idx):
            return _s[idx] and _e[idx]

        def flgs(idx, item):
            # item, is in range, equal to start, queal to end, greater than start, smaller than end
            if not both(idx):
                return (item, False, False, False, False, False)
            else:
                return (item, _s[idx] < item < _e[idx], _s[idx] == item, _e[idx] == item,
                        _s[idx] <= item, _e[idx] >= item)

        def exam(result):
            res_date = _preprocess_date(result)
            y = flgs(0, res_date.year)
            m = flgs(1, res_date.month)
            d = flgs(2, res_date.day)
            return any([
                # Year-Month-Day
                both(0) and any([y[1],
                                 y[2] and y[5] and any([m[4],
                                                        m[2] and m[3] and d[1],
                                                        m[2] and m[5] and d[4]]),
                                 y[4] and y[3] and any([m[5],
                                                        m[2] and m[3] and d[1],
                                                        m[4] and m[3] and d[5]]),
                                 y[2] and y[3] and any([m[1],
                                                        m[2] and m[5] and d[4],
                                                        m[2] and m[3] and d[1],
                                                        m[4] and m[3] and d[5]])]),
                # Month-Day
                both(1) and any([m[1],
                                 m[2] and m[5] and d[4],
                                 m[2] and m[3] and d[1],
                                 m[4] and m[3] and d[5]]),
                # Day
                both(2) and d[1]
            ])

        return exam


class JustOneDateRefiner(Refiner):
    """
    Attributes
    ----------
    bce : bool
      日付けが紀元前か否かを示す
    """
    def __init__(self, attr_name, solo=True, start=None):
        """
        Parameters
        ----------
        attr_name : str
          属性名．クエリ生成に用いる
        solo : bool
          独立して日付けを指定するか否か
          FalseならばRangeの一部と判断
        start : str ((yyyy|\\*)-(mm|\\*)-(dd|\\*))
          Rangeの一部の場合に用いる．この日付けよりも後であることを明示する
        """
        super().__init__(attr_name)
        if start:
            if start.startswith("BCE"):
                self._canbce = True
                self._start = [int(c) if c.isdigit() else None for c in start[3:].split("-")]
            else:
                self._canbce = False
                self._start = [int(c) if c.isdigit() else None for c in start.split("-")]
        else:
            self._start = None
        self.year = ""
        self.month = ""
        self.day = ""
        self._last = ""
        self._solo = True
        self.bce = False

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
        """"""
        if type(choice) is str:
            choice = Candidate(choice)
        if choice.key == "SKIP":
            choice = Candidate("SKIP", ref="*")
        if not self.year:
            return self._year(choice)
        elif not self.month:
            return self._month(choice)
        elif not self.day:
            return self._day(choice)

    def _year(self, choice):
        if choice.key == "日付指定" and (not self._start or self._canbce):
            return Candidates("日付の選択/紀元前・後の選択", ["紀元前（BCE）", "紀元後（CE）", "SKIP"], self)
        elif choice.key == "紀元前（BCE）":
            self.bce = True
            if self._start and self._start[0]:
                return NumCandidates("日付の選択/年の選択", 1, self._start[0], self, skippable=False)
            else:
                return NumCandidates("日付の選択/年の選択", 1, 4713, self, skippable=False)
        elif choice.key == "紀元後（CE）" or (choice.key == "日付指定" and not self._canbce):
            self.bce = False
            if self._start and self._start[0]:
                return NumCandidates("日付の選択/年の選択", self._start[0], 2030, self, skippable=False)
            else:
                return NumCandidates("日付の選択/年の選択", 1, 2030, self, skippable=False)
        else:
            self.year = choice.ref
            if self._start and self._start[1] and \
               (self.year == str(self._start[0]) or not self._start[0]):
                return NumCandidates("日付の選択/月の選択", self._start[1], 12, self, skippable=True)
            else:
                return NumCandidates("日付の選択/月の選択", 1, 12, self, skippable=True)

    def _month(self, choice):
        self.month = choice.ref
        if self._start and self._start[2] and (not self._start[1] or self.month == self._start[1]):
            return NumCandidates("日付けの選択/日にちの選択", self._start[2], 31, self, skippable=True)
        else:
            return NumCandidates("日付けの選択/日にちの選択", 1, 31, self, skippable=True)

    def _day(self, choice):
        self.day = choice.ref
        if self._solo:
            return FunQuery(self._solo_exam(),
                            lambda tgt: "{tgt}の{attr}は?".format(tgt=tgt, attr=self.attr))
        else:
            # メッセージとして返す
            return DQQuery()

    def expression(self):
        return "{b}{y}-{m}-{d}".format(
            b="BCE" if self.bce else "", y=self.year, m=self.month, d=self.day)
