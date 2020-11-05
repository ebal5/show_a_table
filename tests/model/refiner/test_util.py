import unittest

from show_a_table.model.refiner import util
from SPARQLWrapper import JSON, SPARQLWrapper


class TestUtil(unittest.TestCase):
    def setUp(self):
        q = """
        PREFIX schema: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?s ?l WHERE {
        ?s rdf:type schema:Country .
        ?s rdfs:label ?l ;
        FILTER(LANG(?l) = 'ja') .
        FILTER NOT EXISTS {
        ?s schema:dissolutionDate ?d
        }
        }"""
        self.sparql = SPARQLWrapper("http://localhost:3030/yago4/query")
        self.sparql.setReturnFormat(JSON)
        self.sparql.setQuery(q)
        results = self.sparql.query().convert()
        self.countries = [(d["s"]["value"], d["l"]["value"]) for d in results["results"]["bindings"]]

    def test_make_n_dict(self):
        dic = util.make_n_dict(self.countries)
        print(dic)


if __name__ == "__main__":
    unittest.main()
