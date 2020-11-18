from os import environ

import toml
from SPARQLWrapper import JSON, SPARQLWrapper

from .refiner import Candidate, FunQuery, KanaCandidates, Refiner
from .util import read_text


class GeoRefiner(Refiner):
    def __init__(self, attr_name=""):
        super().__init__(attr_name)
        self._endpoint = environ.get("SPARQL_ENDPOINT", None) or \
            "http://localhost:3030/yago4/query"
            # "https://yago-knowledge.org/sparql/query"
        self._data = toml.loads(read_text(__file__, "geo.toml"))
        self._place = []
        self._sparql = SPARQLWrapper(self._endpoint)
        self._sparql.setReturnFormat(JSON)
        self._buf = None

    def refine(self, choice=None):
        """
        Parameters
        ----------
        choice : Candidate
        """
        if choice is None:
            return self._country()
        if choice.key != "完了":
            self._place.append(choice.key)
            return self._other_place(choice)
        else:
            # TODO Queryの実装
            fq = FunQuery(self._make_exam(), lambda tgt: f"{tgt}の{self.attr}は?")
            print(self._place)
            return fq

    def _make_exam(self):
        # 国名を除き全部が含まれていれば合格……でいいか
        def exam(result):
            if len(self._place) == 1:
                # TODO 国名のみの選択の場合
                pass
            else:
                needs = self._place[1:]
                return all([place in result for place in needs])
        return exam

    def _country(self):
        """
        国レベルの絞り込みを行う．

        Parameters
        ----------
        choice: `str` 直前の選択

        Returns
        -------
        Candidates
        """
        self._sparql.setQuery(self._data["countries"])
        results = self._sparql.query().convert()
        bindings = results["results"]["bindings"]
        _list = [(row["s"]["value"], row["l"]["value"]) for row in bindings]
        country_cands = [Candidate(key=l, ref=s) for (s, l) in _list]
        return KanaCandidates(title="地名の選択/国の選択", cands=country_cands, parent=self)

    def _other_place(self, place):
        """
        `place` に含まれる地域の一覧を候補とする．

        ここでは途中で完了も可能
        候補が存在しない場合（最小単位の場合）は完了のみが表示？

        Parameters
        ----------
        place : Candidate
        """
        uri = place.ref
        query = self._data["other_place"].format(uri)
        self._sparql.setQuery(query)
        results = self._sparql.query().convert()
        bindings = results["results"]["bindings"]
        _list = [(row["s"]["value"], row["l"]["value"]) for row in bindings]
        _cands = [Candidate(key=l, ref=s) for (s, l) in _list]
        _cands.append(Candidate(key="完了"))
        return KanaCandidates(title="地名の選択/国以下の選択", cands=_cands, parent=self)
