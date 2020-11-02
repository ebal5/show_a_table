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
    def __init__(self, key, ref=None):
        self.key = key
        self.ref = ref if ref else key


class Candidates:
    """
    Refinerが返す候補一覧を保持するクラス
    あとついでにそのRefinerの責任範囲が終了したことを示す信号も持つ．
    """
    def __init__(self, cands, is_finished=False):
        self.cands = cands
        self.is_finished = is_finished