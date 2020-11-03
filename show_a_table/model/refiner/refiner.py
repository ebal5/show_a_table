from typing import List, Tuple


class Refiner:

    def __init__(self):
        pass

    def refine(choice: str = "") -> Tuple[bool, List[str]]:
        return (False, [])


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
        cands : List[Candidate]
        is_finished : bool

        Raises
        ------
        ValueError
          cands の表示値に被りがある場合
        """
        if not (len(cands) == len(set([c.key for c in cands]))):
            raise ValueError("候補値に被りがあります．")
        self.extend(cands)
        self.is_finished = is_finished
        self.title = title
        self.parent = parent
