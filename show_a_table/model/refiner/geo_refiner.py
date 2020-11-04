from importlib.resources import read_text
from os import environ

import toml
from SPARQLWrapper import JSON, SPARQLWrapper

import util

from .refiner import Refiner


class GeoRefiner(Refiner):
    def __init__(self):
        self._endpoint = environ.get("SPARQL_ENDPOINT", None) or \
            "http://localhost:3030/yago4/query"
        # "https://yago-knowledge.org/sparql/query"
        self._data = toml.loads(read_text(__package__, "geo.toml"))
        self._place = []
        self._sparql = SPARQLWrapper(self._endpoint)
        self._sparql.setReturnFormat(JSON)
        self._buf = None

    def refine(self, choice):
        # TODO 実装
        return super().refine(choice)

    def _country(self, choice):
        """
        国レベルの絞り込みを行う．

        Parameters
        ----------
        choice: `str` 直前の選択

        Returns
        -------
        Tuple[bool, List[Tuple[str, str]]]
        """
        self._sparql.setQuery(self._data["countries"])
        results = self._sparql.query().convert()
        bindings = results["results"]["bindings"]
        _list = [(row["s"]["value"], row["l"]["value"]) for row in bindings]
        cands = util.make_n_dict(_list)
