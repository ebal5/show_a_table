from importlib.resources import read_text

import toml
from show_a_table.refiner.model import Candidates


class CandsPerformer:
    """
    候補一覧の表示のための処理を担う

    50音による選択などはこれの仕事とする？
    """
    def __init__(self):
        self._cands = None      # 候補一覧
        self._expects = None    # 戻り値のための辞書
        self._max_cands = toml.loads(read_text(__package__, "config.toml"))["max_cands"]
        self._queries = None

    def set_cands(self, cands):
        """
        候補一覧をセットする

        Parameters
        ----------
        cands : candidates.Candidates
          候補一覧をセット済みのもの

        Returns
        -------
        None
        """
        self._cands = cands

    def get_cands(self):
        """
        候補一覧から適切な数を返す．

        Parameters
        ----------

        Returns
        -------
        List[str]
          候補値の表示値リスト．内部値は異なる可能性がある

        Raises
        -------
        ValueError
          候補がセットされていないときに呼びだされた場合
        """
        if not self._cands:
            raise ValueError("候補がセットされていません")
        if len(self._cands.cands) > self._max_cands:
            head = self._cands.cands[:self._max_cands]
            self._cands.cands = self._cands.cands[self._max_cands:]
            ret = [c.key for c in head]
            self._expects = {c.key: c for c in head}
        else:
            ret = [c.key for c in self._cands.cands]
            self._expects = {c.key: c for c in self._cands.cands}
        # TODO # 共通処理を追加する
        ret.append("終了")
        # TODO 終了の処理を考える
        self._expects["終了"] = None
        if self._cands.
        return ret
