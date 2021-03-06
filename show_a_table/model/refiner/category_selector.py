import toml

from .date import DateRefiner
from .geo_refiner import GeoRefiner
from .refiner import Candidates, Categories
from .util import read_text


class CategorySelector:
    """
    カテゴリの選択や属性の選択，Refinerの生成を行う

    あるいみRootRefiner

    Refiner ではなくすることで種々の制限からはずす．
    """
    def __init__(self):
        self.cat = None
        self.attr = None
        self.queries = []
        self._data = toml.loads(read_text(__file__, "config.toml"))

    def categories(self):
        if self.cat:
            raise RuntimeError("既にカテゴリ選択は終了しています")
        return [c.value for c in Categories]

    def set_category(self, cat):
        """
        Parameters
        ----------
        cat : str
          確定したカテゴリ……？
        """
        self.cat = Categories.value_of(cat)

    def attributes(self):
        """"""
        return list(self._data["attributes"][self.cat.name].keys())

    def add_query(self, query):
        """
        Parameters
        ----------
        query : DQQuery
        """
        query.attr = self.attr
        self.queries.append(query)

    def refiners(self, attr):
        """
        Returns refiner based on attributes

        Parameters
        ----------
        attr : str

        Returns
        -------
        Refiner
          attr に基づいたRefiner
        """
        self.attr = attr
        key = self._data["attributes"][self.cat.name][attr]
        if key == "Geo":
            return GeoRefiner(attr)
        elif key == "Date":
            return DateRefiner(attr)
        elif key == "Free":
            # TODO FreeRefiner
            raise NotImplementedError("Not yet implemented")
            pass
        elif key == "Number":
            # TODO NumberRefiner
            raise NotImplementedError("Not yet implemented")
            pass
        elif key == "Data":
            # TODO DataSpecificRefiner
            raise NotImplementedError("Not yet implemented")
            pass
