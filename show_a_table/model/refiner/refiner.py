from collections import OrderedDict
import sys
import math
from enum import Enum

from .util import make_n_dict, AutoNumber


class RefinerState(AutoNumber):
    CONTINUE = ()
    FINISH = ()
    ERROR = ()


class Categories(Enum):
    COMPANY = "企業名"
    AIRPORT = "空港名"
    PERSON = "人名"
    CITY = "市区町村名"
    COMPOUND = "化合物名"

    @classmethod
    def value_of(cls, target_value):
        for e in cls:
            if e.value == target_value:
                return e
        return None


class Refiner:
    """
    Refinerの基底クラス．これを単体で用いることはないであろう
    """
    def __init__(self, attr_name=""):
        self.state = RefinerState.CONTINUE
        self.attr = attr_name

    def refine(self, choice=None):
        """
        Parameters
        ----------
        choice : Candidate
          直前の選択

        Returns
        -------
        Candidates or DQQuery
          途中ならばCandidatesだし，終わったならDQQueryを返す
        """
        return Candidates("PLACE HOLDER", ["SAMPLE", "CHOICE"], self)


class Candidate:
    """
    Refinerが返す候補の個別要素を示すクラス．
    典型的には表示値とRefinerに戻す値は同じだが，SPARQLを利用するなどでかわる可能性がある
    """
    def __init__(self, key, ref=None, **kwargs):
        """
        Parameters
        ----------
        key : str
          画面に表示される文字列
        ref : any
          Refinerが必要とする値．未セット時は`key`と等しい．
        """
        self.key = key
        self.ref = ref if ref else key
        self.obj = kwargs

    def __str__(self):
        return self.key


class Candidates:
    """
    Refinerが返す候補一覧を保持するクラス
    あとついでにそのRefinerの責任範囲が終了したことを示す信号も持つ．

    候補値に被りが無いことはこのクラスが保証する．
    まあ生成元が保証してくれるのがベストだけど，そうもいかないし．

    Attributes
    ----------
    title : str
      その絞りこみのタイトル
    cands : List[Candidate]
      候補一覧
    parent : Refiner
      発行元Refiner．結果の返し先
    """

    def __init__(self, title, cands, parent):
        """
        自身をcandsで初期化する

        Parameters
        ----------
        title : str
          絞り込みのタイトル

          候補値リスト．どちらかの型で統一される必要がある

        Raises
        ------
        ValueError
          cands の表示値に被りがある場合
        """
        if type(cands[0]) is str:
            cands = [Candidate(c) for c in cands]
        if not (len(cands) == len(set([c.key for c in cands]))):
            raise ValueError("候補値に被りがあります．")
        self._expects = {c.key: c for c in cands}
        self._lk = list(self._expects.keys())
        self.title = title
        self.parent = parent
        self._last_idx = None

    def cands(self, num_cands=30):
        """
        num_cands個以下の選択肢を返す．
        0ならば全てを返す．

        Parameters
        ----------
        num_cands : int

        Returns
        -------
        List[str]
          表示する候補のリスト
        """
        if len(self._lk) <= num_cands:
            return self._lk
        tmp = self._lk[:num_cands]
        tmp.append("NEXT")
        self._lk = self._lk[num_cands:]
        return tmp

    def select(self, num_cands, choice):
        """
        Parameters
        ----------
        num_cands : int
          choice で確定しなかった場合の動作で，最大の選択肢個数を示す
        choice : str
          直前の選択肢郡から選んだ文字列

        Returns
        -------
        Candidate or List[str]
          確定したならばCandidateを，そうでなければList[str]で候補を提示する

        Raises
        -------
        ValueError
          if choice not in proposal
        """
        if choice == "NEXT":
            return self.cands(num_cands)
        if choice not in self._expects:
            raise ValueError("{choice} is not in proposal".format(choice=choice))
        return self._expects[choice]

    def __str__(self):
        cands = ", ".join([str(c) for c in sorted(self._expects.keys())])
        return "title: {title}, cands: [{cands}]".format(title=self.title, cands=cands)


class KanaCandidates:
    """
    受け取ったcandsをカナによって事前振り分けした上でcandsから1つ選択する

    Attributes
    ----------
    title : str
    parent : Refiner
    _cands : List[Candidate]
    _last : List[str]

    Examples
    --------
    国名の場合，国名をカナで書いたときの先頭N文字（1で足りる？）がまず選択肢となる．
    カナを選択したのちに，そのカナから始まる国名一覧によって国名が選択可能となる．
    """

    def __init__(self, title, cands, parent):
        """
        Parameters
        ----------
        title : str
        cands : List[Candidate] or List[str]
        parent : Refiner

        Raises
        ------
        ValueError
          cands の表示値に被りがある場合
        """
        if type(cands[0]) is str:
            cands = [Candidate(c) for c in cands]
            # TODO 国名の被りを考える
        # if not (len(cands) == len(set([c.key for c in cands]))):
        #     raise ValueError("候補値に被りがあります．")
        self.title = title
        self.parent = parent
        self._cands = cands
        self._last = []
        self._kana = ""
        self._proposal = []
        self._cands_dict = None

    def cands(self, num_cands=30):
        """
        num_cands個以下の選択肢を返す．
        0ならば全てを返す．

        Parameters
        ----------
        num_cands : int

        Returns
        -------
        List[str]
          表示する候補のリスト
        """
        # 辞書がないなら作る
        if self._cands_dict is None:
            pl = [(c.ref, c.key) for c in self._cands]
            self._cands_dict = {
                kana: [Candidate(key=l, ref=s, kana=k) for (s, l, k) in val]
                for kana, val in make_n_dict(pl, num_cands).items()
            }
        if self._last:
            tmpl = self._last[:num_cands]
            self._last = self._last[num_cands:]
            if len(self._last) > 0:
                tmpl.append("NEXT")
            self._proposal = tmpl
            return tmpl
        elif len(self._cands_dict.keys()) <= num_cands:
            self._proposal = list(sorted(self._cands_dict.keys()))
            return self._proposal
        else:
            tmpl = list(sorted(self._cands_dict.keys()))
            self._last = tmpl[num_cands:]
            tmpl = tmpl[:num_cands]
            tmpl.append("NEXT")
            if "完了" in self._cands_dict.keys() and "完了" not in tmpl:
                tmpl.append("完了")
            self._proposal = tmpl
            return tmpl

    def select(self, num_cands, choice):
        """
        Parameters
        ----------
        num_cands : int
          choice で確定しなかった場合の動作で，最大の選択肢個数を示す
        choice : str
          直前の選択肢郡から選んだ文字列

        Returns
        -------
        Candidate or List[str]
          確定したならばCandidateを，そうでなければList[str]で候補を提示する

        Raises
        -------
        ValueError
          if choice not in proposal
        """
        if choice == "NEXT":
            return self.cands(num_cands)
        if choice not in self._proposal:
            raise ValueError("not in proposal")
        if choice == "完了":
            return Candidate("完了")
        if self._kana == "":
            self._kana = choice
            self._proposal = OrderedDict([(c.key, c) for c in self._cands_dict[choice]])
            return list(self._proposal.keys())
        else:
            return self._proposal[choice]

    def __str__(self):
        return super().__str__()


class NumCandidates:
    """
    数値に関する候補を提示して絞り込みの補助を行う
    """
    def __init__(self, title, start, end, parent, skippable=False):
        """
        Parameters
        ----------
        title : str
        start : int
          開始点．含まれる
        end : int
          終点．含まれる
        parent : Refiner
        skippable : bool = False
          Trueなら選択肢にSKIPが追加され，その選択をSKIPできる
        """
        self.title = title
        self.parent = parent
        self._start = start
        self._end = end
        self._skippable = skippable
        self._num = ""
        self._n_cands = 0
        self._last = None

    def _mk_range(self, ncands):
        self._cands = [i for i in range(self._start, self._end+1)]
        width = math.ceil(len(self._cands) / ncands)
        if self._skippable:
            width -= 1
        self._proposal = OrderedDict(
            [("{s}-{e}".format(s=self._cands[idx], e=self._cands[idx:idx+width][-1]),
              self._cands[idx:idx+width])
             for idx in range(0, len(self._cands), width)]
        )
        if self._skippable:
            self._proposal["SKIP"] = Candidate("SKIP", ref="*")
            self._proposal.move_to_end("SKIP")

    def _mk_next(self, ncands):
        self._cands = [i for i in range(self._start, self._end+1)]
        if self._last:
            self._proposal = self._last
        else:
            tps = [(str(c), c) for c in self._cands]
            if self._skippable:
                tps.append(("SKIP", Candidate("SKIP", ref="*")))
            if len(tps) > ncands:
                tps.insert(ncands-1, ("NEXT", "NEXT"))
            self._last = OrderedDict(tps[ncands:])
            self._proposal = OrderedDict(tps[:ncands])

    def cands(self, num_cands=30):
        """
        num_cands個以下の選択肢を返す．
        0ならば全てを返す．

        Parameters
        ----------
        num_cands : int

        Returns
        -------
        List[str]
          表示する候補のリスト
        """
        if (self._end - self._start) > 2*num_cands:
            self._mk_range(num_cands)
        else:
            self._mk_next(num_cands)
        retl = list(self._proposal.keys())
        return retl

    def select(self, num_cands, choice):
        """
        Parameters
        ----------
        num_cands : int
          choice で確定しなかった場合の動作で，最大の選択肢個数を示す
        choice : str
          直前の選択肢郡から選んだ文字列

        Returns
        -------
        Candidate or List[str]
          確定したならばCandidateを，そうでなければList[str]で候補を提示する

        Raises
        -------
        ValueError
          if choice not in proposal
        """
        if choice not in self._proposal:
            raise ValueError("{c} is not in proposal".format(c=choice))
        ret = self._proposal[choice]
        if isinstance(ret, Candidate):
            return ret
        elif type(ret) is list:
            self._start = ret[0]
            self._end = ret[-1]
            return self.cands(num_cands)
        elif choice == "NEXT":
            return self.cands(num_cands)
        elif type(ret) == int:
            return Candidate(choice)
        else:
            print(type(ret), ret, file=sys.stderr)
            raise RuntimeError("UNREACHABLE BLOCK")


class Priority(AutoNumber):
    """
    クエリの優先度．HIGHESTならば真先に実行するべきだし，LOWESTならば最後で良い．
    """
    HIGHEST = ()
    HIGHER = ()
    HIGH = ()
    MIDDLE = ()
    LOW = ()
    LOWER = ()
    LOWEST = ()


class DQQuery:
    """
    DrQAに回すクエリを保持するクラス．

    これ自体は基底クラスとしての使用に留まり，実際は派生クラスが使われるはず

    Attributes
    ----------
    priori : Priority
    """

    def __init__(self, priori=None):
        if priori and priori in Priority:
            self.priori = priori
        else:
            self.priori = Priority.MIDDLE

    def exam(self, result):
        """
        Parameters
        ----------
        result : str
          QAシステムの戻り値．SGMLタグを含まないテキストを期待する

        Returns
        -------
        is_passed
          `result` がこの試験を通過可能か示すブール値
        """
        return False

    def get_query(self, target):
        """
        Parameters
        ----------
        target : str
          Wikipedia 記事タイトルになることが多いかと
          QAシステムに投げる質問文を生成する

        Returns
        -------
        str
          生成された質問文
        """
        return ""


class RegQuery(DQQuery):
    """
    正規表現による絞りを実施するクラス

    Attributes
    ----------
    reg : re
      絞りのための正規表現オブジェクト
    """

    def __init__(self, regex, gen_query, priori=None):
        """
        Parameters
        ----------
        regex : re
          絞りのための正規表現オブジェクト．
          グループ化してもよいが，特別使用する方法は用意しない
        gen_query : str -> str
          質問生成のための関数
        """
        super().__init__(priori)
        self.reg = regex
        self.gen = gen_query

    def exam(self, result):
        return True if self.reg.match(result) else False

    def get_query(self, target):
        return self.gen(target)


class FunQuery(DQQuery):
    """
    独自実装の関数による絞りを実施するクラス

    Attributes
    ----------
    refine : str -> bool
    gen : str -> str
    """

    def __init__(self, refine, gen_query, priori=None):
        """
        Parameters
        ----------
        refine : str -> bool
          絞りを実施する関数．bool値を返す
        gen_query : str -> str
          質問文を生成する関数
        """
        super().__init__(priori)
        self.refine = refine
        self.gen = gen_query

    def exam(self, result):
        return self.refine(result)

    def get_query(self, target):
        return self.gen(target)
