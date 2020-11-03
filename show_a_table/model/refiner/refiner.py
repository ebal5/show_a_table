from enum import Enum, auto
from typing import List, Tuple


class RefinerState(Enum):
    CONTINUE = auto()
    FINISH = auto()
    ERROR = auto()


class Refiner:
    """
    Refinerの基底クラス．これを単体で用いることはないであろう
    """
    def __init__(self):
        self.state = ""
        pass

    def refine(self, choice: str = ""):
        return Candidates("PLACE HOLDER", ["SAMPLE", "CHOICE"], self, False)


class CategoryRefiner:

    def __init__(self):
        self.categories = ["企業名", "空港名", "人名", "市区町村名", "化合物名"]

    def refine(self, choice=""):
        return Candidates()


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


class Candidates(list):
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
    is_finished : bool
      発行したRefinerの責任範囲が終了してるならばTrue．そうでなければFalse
    parent : Refiner
      発行元Refiner．結果の返し先
    """

    def __init__(self, title, cands, parent, is_finished=False):
        """
        自身をcandsで初期化する

        Parameters
        ----------
        title : str
          絞り込みのタイトル
        cands : List[Candidate/str]
          候補値リスト．どちらかの型で統一される必要がある
        is_finished : bool
          現在の属性について決定したならばTrue

        Raises
        ------
        ValueError
          cands の表示値に被りがある場合
        """
        if type(cands[0]) is str:
            cands = [Candidate(c) for c in cands]
        if not (len(cands) == len(set([c.key for c in cands]))):
            raise ValueError("候補値に被りがあります．")
        self.extend(cands)
        self.is_finished = is_finished
        self.title = title
        self.parent = parent

    def spend(self, num_cands):
        """
        num_cands 分の要素を既に提示したものとする

        Parameters
        ----------
        num_cands : int
          消費した数．

        Returns
        -------
        self : Candidates
        """
        del self[:num_cands]
        return self


class DQQuery:
    """
    DrQAに回すクエリを保持するクラス．

    これ自体は基底クラスとしての使用に留まり，実際は派生クラスが使われるはず
    """

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

    def make_query(self, target):
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

    def __init__(self, regex, gen_query):
        """
        Parameters
        ----------
        regex : re
          絞りのための正規表現オブジェクト．
          グループ化してもよいが，特別使用する方法は用意しない
        gen_query : str -> str
          質問生成のための関数
        """
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

    def __init__(self, refine, gen_query):
        """
        Parameters
        ----------
        refine : str -> bool
          絞りを実施する関数．bool値を返す
        gen_query : str -> str
          質問文を生成する関数
        """
        self.refine = refine
        self.gen = gen_query

    def exam(self, result):
        return self.refine(result)

    def get_query(self, target):
        return self.gen(target)
