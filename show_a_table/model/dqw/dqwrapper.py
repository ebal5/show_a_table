import json
import sys
from collections import OrderedDict, defaultdict
from os import environ, path
import copy

import time
import torch
from drqa.reader import Predictor
from tqdm import tqdm

_datadir = environ.get("DRQA_DATA_DIR", None) or "/drqa_shinra/data"

_datasets = {
    "AIRPORT": path.join(_datadir, "work/train-multipleanswer/squad_Airport.json"),
    "CITY": path.join(_datadir, "work/train-multipleanswer/squad_City.json"),
    "COMPANY": path.join(_datadir, "work/train-multipleanswer/squad_Company.json"),
    "COMPOUND": path.join(_datadir, "work/train-multipleanswer/squad_Compound.json"),
    "PERSON": path.join(_datadir, "work/train-multipleanswer/squad_Person.json"),
}
_model = path.join(_datadir, "drqa-models/train-multipleanswer/20190730-9760b184.mdl")
_embedding_file = path.join(_datadir, 'embeddings/cc.ja.300.vec')
_tokenizer = 'mecab'
_num_workers = 10


_predictor = Predictor(
    model=_model,
    tokenizer=_tokenizer,
    embedding_file=_embedding_file,
    num_workers=_num_workers,
)
_predictor.cuda()


def _make_questions(ds, query, ids=None, titles=None):
    """
    Parameters
    ----------
    ds : str
      path of dataset. maybe, listed above
    query : DQQuery

    Returns
    -------
    exs : [(str, str, str, str)]
      context, query, title, wiki_id
    """
    with open(ds) as f:
        data = json.load(f)['data']
    exs = []
    for art in data:
        title = art['title']
        wiki_id = art['WikipediaID']
        if ids and wiki_id not in ids:
            continue
        if titles and title not in titles:
            continue
        for prh in art['paragraphs']:
            ctx = prh['context']
            q = query.get_query(title)
            exs.append((ctx, q, title, wiki_id))
    return exs


def _update(store, qg, ds, batch_size=6):
    """
    Parameters
    ----------
    store : {str: {"title": str, "attrs": {str: [str]}}}
    qg : DQQuery
    batch_size : int

    Returns
    -------
    store : {str: {"title": str, "attrs": {str: [str]}}}
    """
    questions = _make_questions(ds, qg, ids=set(store))
    batches = [questions[idx:idx+batch_size] for idx in range(0, len(questions), batch_size)]
    for batch in batches:
        results = _predictor.predict_batch([b[:2] for b in batch], top_n=1)
        for i in range(len(results)):
            if not len(results[i]):
                continue
            res_text = results[i][0][0]['text']
            if not qg.exam(res_text):
                continue
            wid = batch[i][3]
            wobj = store.get(wid, {})
            if not wobj:
                wobj["title"] = batch[i][2]
                wobj["attrs"] = {
                    qg.attr: [res_text]
                }
                store[wid] = wobj
            else:
                _l = wobj["attrs"].get(qg.attr, [])
                _l.append(res_text)
                wobj["attrs"][qg.attr] = _l
    excludes = [wid for wid, wobj in store.items() if not wobj["attrs"].get(qg.attr, False)]
    for ex in excludes:
        store.pop(ex)
    return store


def run(cs, full=True):
    """
    Parameters
    ----------
    cs : CategorySelector
      Query設定済みのもの．
    full : bool = True
      戻り値の型を決定する．Falseならば結果を[str]で返す
    """
    ds = _datasets[cs.cat.name]
    store = {}
    for qg in cs.queries:
        store = _update(store, qg, ds)
    if full:
        return store
    else:
        return [v["title"] for _, v in store.items()]
