from importlib.resources import read_text
from itertools import groupby

import pykakasi
import toml


def _gbh(lst, key=0, idx=0):
    """
    `lst` を`key`番目要素の`idx`文字目によって分割し辞書を返す

    Parameters
    ----------
    lst: `List[Tuple[str, str, str]]` 分割対象のリスト
    key: `int` Tupleのインデックス．
    idx: `int` idx文字目の文字によって分割を行う

    Returns
    -------
    `Dict[str, List[Tuple[str, str, str]]]`: 文字をキーとした辞書
    """
    return {k: list(v) for (k, v) in groupby(sorted(lst, key=lambda row: row[key][idx]),
                                             key=lambda row: row[key][idx])}


def _merge_dict(base, additional, key):
    """
    `base`に `additional` を加算し返却する

    Parameters
    ----------
    base: `Dict[str, List[Tuple[str, str, str]]]` この辞書に `additional` を加算する
    additional: `Dict[str, List[Tuple[str, str, str]]]` これを`base` に加算する
    key: `str` key of base

    Returns
    -------
    Dict[str, List[Tuple[str, str, str]]]: base にadditional を加算したもの
    """
    base.pop(key)
    base.update(additional)
    return base


def make_n_dict(_list, max_cands=0):
    """
    リストを受けとり，`max_cands`数を下回るグループになるまで，先頭仮名文字で分割する

    例えば， `{"あ": [...], "いあ": [...]}` のように，最大が20になるまで削りつづける．

    Parameters
    ----------
    _list : List[Tuple[str, str]]
      subject, label のペアのリスト．表示されるのはlabelにする
    max_cands : int
      最大候補数．辞書1要素あたりの最大候補数

    Returns
    -------
    Dict[str, List[Tuple[str, str, str]] :
      カナをキーとした，(主語，ラベル，カナ)のリスト
    """
    if max_cands == 0:
        max_cands = toml.loads(read_text(__package__, "config.toml"))["max_cands"]
    kks = pykakasi.kakasi()
    lst = [(s, l, "".join([d["kana"] for d in kks.convert(l)])) for s, l in _list]
    dic = _gbh(lst, 2, 0)
    # TODO 2文字目以降を使う方法を考える（StringOutOfIndexで中断中）
    # checked = [k for k, v in dic.items() if len(v) > max_cands]
    # idx = 0
    # while checked:
    #     for k in checked:
    #         dic = _merge_dict(dic, {f"{k}{_k}": v for _k, v in _gbh(dic[k], key=2, idx=idx).items()}, k)
    #     checked = [k for k, v in dic.items() if len(v) > max_cands]
    #     idx += 1
    return dic
