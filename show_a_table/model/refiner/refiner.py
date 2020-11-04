from enum import Enum, auto


class RefinerState(Enum):
    CONTINUE = auto()
    FINISH = auto()
    ERROR = auto()


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


class CategoryRefiner:
    """
    カテゴリ選択に関するRefiner
    同時にルートRefinerとして各属性に関するQueryも保持する


    Attributes
    ----------
    selected : Categories
      選択されたカテゴリ
    queries : DQQuery
      実行するべきクエリのリスト
    """

    def __init__(self):
        self.selected = None
        self.queries = []

    def refine(self, choice=""):
        if choice:
            cat = Categories.value_of(choice)
            if cat:
                self.selected = cat
            else:
                raise ValueError(f"{choice} は正しいカテゴリではありません")
        else:
            return Candidates("カテゴリの選択", self.categories, self, False)


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
        cands : List[Candidate/str]
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
        self.extend(cands)
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

    def __str__(self):
        cands = ", ".join([str(c) for c in self])
        return f"title: {self.title}, cands: [{cands}]"


class Priority(Enum):
    """
    クエリの優先度．HIGHESTならば真先に実行するべきだし，LOWESTならば最後で良い．
    """
    HIGHEST = auto()
    HIGHER = auto()
    HIGH = auto()
    MIDDLE = auto()
    LOW = auto()
    LOWER = auto()
    LOWEST = auto()


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