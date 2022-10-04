from parser import parsefile
from networkx.readwrite import json_graph
from topiclib import TopicExtractor, expand_corpus
import providers
from pprint import pp
import logging

# logging.getLogger("topiclib").setLevel(logging.DEBUG)


def test_expansion():
    file = "samples/number_system.json"
    text = parsefile(file)
    d = TopicExtractor(text).count().most_common(4)
    graph = expand_corpus(d, "wikipedia", True, False)
    obj = json_graph.node_link_data(graph)
    assert obj == {'directed': True,
                   'multigraph': False,
                   'graph': {},
                   'nodes': [{'id': 'number'}, {'id': 'natural number'}],
                   'links': [{'weight': 226,
                              'weight_total': 254,
                              'source': 'natural number',
                              'target': 'number'}]}
