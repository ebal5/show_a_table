from enum import Enum, auto
from importlib.resources import read_text

import toml
from show_a_table.refiner.model import Candidates


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
        self._expects = None
        self._max_cands = toml.loads(read_text(__package__, "config.toml"))["max_cands"]
        # TODO category refiner の実装
        self._refiners = []
        self.set_cands(self._refiner[0].refine())

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
        if not choice:
            return self.get_cands()
        res = self._expects.get(choice, None)
        if res is None:
            raise ValueError(f"{choice} は選択肢として正しくありません")
        elif callable(res):
            return res()
        elif type(res) is str:
            self.set_cands(self._refiners.refine(res))
            return self.get_cands()

    def set_cands(self, cands):
        """
        候補一覧をセットする

        Parameters
        ----------
        cands : candidates.Candidates
          候補一覧をセット済みのもの
        """
        self._cands = cands

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

    def enter(self):
        """
        現在の属性に関する入力を決定し次の属性に入る
        """
        # TODO 決定処理の実装
        self._refiners[-1].add_query()

    def get_cands(self):
        """
        候補一覧から適切な数を返す．

        Returns
        -------
        Tuple[str, List[str]]
          タイトルと選択肢の表示値リスト．

        Raises
        -------
        ValueError
          候補がセットされていないときに呼びだされた場合
        """
        if not self._cands:
            raise ValueError("候補がセットされていません")
        if len(self._cands) > self._max_cands:
            head = self._cands[:self._max_cands]
            self._cands.spend(self._max_cands)
            ret = [c.key for c in head]
            self._expects = {c.key: c for c in head}
            ret.append("次の選択肢")
            self._expects["次の選択肢"] = self.get_cands
        else:
            # 選択肢の数が少ない場合
            ret = [c.key for c in self._cands.cands]
            self._expects = {c.key: c for c in self._cands.cands}
        ret.append("終了")
        self._expects["終了"] = self.escape
        ret.append("キャンセル")
        self._expects["キャンセル"] = self.cancel
        if self._cands.is_finished:
            ret.append("完了")
            self._expects["完了"] = self.complete
            ret.append("決定")
            self._expects["決定"] = self.enter
        return (self._cands.title, ret)
