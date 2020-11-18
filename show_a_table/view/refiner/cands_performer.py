from enum import Enum, auto
from importlib.resources import read_text

import toml

from ...model.refiner import category_selector as CS
from ...model.refiner import refiner


class FinishState(Enum):
    COMPLETE = auto()
    ESCAPE = auto()


class CandsPerformer:
    """
    候補一覧の表示のための処理を担う

    50音による選択などはこれの仕事とする？

    Attributes
    ----------
    _cands : Candidates
      選択肢一覧
    _expects : Dict[str, None/Candidate/function]
      選択肢とそれに応じた行動の辞書
    _max_cands : int
      選択肢を表示する最大数
    _refiners : List[Refiner]
      スタックとして使い，peekして上から決定していく
    """

    def __init__(self):
        self._cands = None      # 候補一覧
        self._max_cands = toml.loads(read_text(__package__, "config.toml"))["max_cands"]
        self._refiner = None
        self._cat_sel = None
        self._expects = None
        self._cands = None
        self._attr = False       # as flg
        self._cat = False        # as flg

    def show(self, choice=""):
        """
        Viewの本体．これを呼ぶことで他のクラスはこの機能を使うことができる

        Parameters
        ----------
        choice : str
          self._expects に対応が存在することが期待される．
          空文字列が許されるのは起動直後の呼び出しのみ
          存在し，それが関数ならそれを実行する．
          存在し，それがCandidateならそれを親へ返す．
          存在しないならエラー

        Returns
        -------
        (str, List[str])
          タイトルと選択肢の表示値リスト．
        """
        # 何もない
        if not choice:
            self._cat_sel = CS.CategorySelector()
            lst = self._cat_sel.categories()
            self._expects = {c for c in lst}
            return ("カテゴリの選択", lst)
        # カテゴリ未選択 = `choice` はカテゴリ名
        if not self._cat:
            self._cat_sel.set_category(choice)
            self._cat = True
            attrs = self._cat_sel.attributes()
            return ("属性の選択", attrs)
        # `refiner`が無い = 属性未選択 = `choice` は属性名
        if not self._refiner:
            # TODO choice == "完了" の処理
            # => 実際の絞りこみ処理
            # => まだむり
            if choice == "完了":
                raise NotImplementedError("未実装")
            self._refiner = self._cat_sel.refiners(choice)
            self._cands = self._refiner.refine()
            return (self._cands.title, self._cands.cands())
        # `cands` がある = 選択途中 = choice は cands のなかみの一つ
        if self._cands:
            _cds = self._cands.select(self._max_cands, choice)
            if isinstance(_cds, refiner.Candidate):
                _cds = self._refiner.refine(_cds)
                if isinstance(_cds, refiner.DQQuery):
                    self._cat_sel.add_query(_cds)
                    self._refiner = None
                    attrs = self._cat_sel.attributes()
                    attrs.append("完了")
                    return ("属性の選択", attrs)
                else:
                    self._cands = _cds
                return (self._cands.title, self._cands.cands())
            else:
                return (self._cands.title, _cds)

    def complete(self):
        """
        完了処理 といっても戻り値のためにある
        """
        return FinishState.COMPLETE

    def escape(self):
        """
        離脱処理
        """
        return FinishState.ESCAPE
