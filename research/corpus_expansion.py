import matplotlib.pyplot as plt
import networkx as nx
from mediawiki import MediaWiki, exceptions

from lda import lda
from collections import Counter
from preprocess import preprocess2, text_to_ngrams, flatten, get_ngrams

from abc import ABC, abstractclassmethod

W = 0
W_MIN = 1


class ICorpus(ABC):
    """Interface for content providers"""
    @abstractclassmethod
    def search(self, query: str) -> [str]:
        """Must take a search string and return a list of possible topics as strings that reference pages"""
        pass

    @abstractclassmethod
    def content(self, page: str) -> str:
        """Takes in a string returned by search and returns a corpus body"""
        pass

class WikiCorpus(ICorpus):
    def __init__(self):
        self.wikipedia = self._gen_wiki()

    def content(self, page: str) -> str:
        return self.wikipedia.page(page).content

    def _gen_wiki(self):
        return MediaWiki()

    def _wikisearch(self, query: str) -> [str]:
        return self.wikipedia.search(query)

    def _wikipage(self, title: str) -> str:
        return self.wikipedia.page(title)

    def search(self, search: str) -> str:
        pages = self._wikisearch(search)
        i = 0
        while i < len(pages):
            try:
                title = pages[i]
                break
            except exceptions.DisambiguationError:
                i += 1
        return title

wiki = WikiCorpus()

# TODO wiki pages might not be found
# 'number close', 'associative property', 'number example', 'number rational', 'property respect', 'communicative associative', 'close addition']
topics = ['number', 'natural number',
          'rational number', 'number real', 'number rational']
print("loading pages...")
page_names = [wiki.search(topic) for topic in topics]
topic_names = set([flatten(preprocess2(name)) for name in page_names])
print(f"{topic_names=}")
# pages = {page_name: (page_name) for page_name in page_names}
print("Pages loaded!")

graph = nx.DiGraph()
graph.add_nodes_from(topic_names)
print("Initialized graph")


def add_arrow(start, end, weight=1):
    """Add edge if weight 'weight' if not exists, else increase the 'weight' by 1"""
    # If contrary edge exists subtract from it
    if graph.has_edge(end, start):
        w = graph[end][start]['weight']
        graph[end][start]['weight'] -= weight

        if graph[end][start]['weight'] <= 0:
            graph.remove_edge(end, start)
            graph.add_edge(start, end, weight=weight - w)

    # If edge exists add to it
    elif graph.has_edge(start, end):
        graph[start][end]['weight'] += weight
    else:
        graph.add_edge(start, end, weight=weight)


# Loop over each topic and populated edges between topics
for page_name in page_names:
    topic = flatten(preprocess2(page_name))
    print(f"Processing topic: {topic}")
    if topic not in topic_names:
        continue
    # page = pages[page_name]
    # content = page.content
    # backlinks = set(page.backlinks)
    # links = set(page.links)
    content = wiki.content(page_name)

    if W > 0:
        for other_page in page_names:
            other_topic = flatten(preprocess2(other_page))
            if other_page == page_name:
                continue
            # if other_page in backlinks:
            #     add_arrow(other_topic, topic, W)
            #     print(f"  link --> {other_page} -> {page_name}")
            # if other_page in links:
            #     add_arrow(topic, other_topic, W)
            #     print(f"  backlink --> {page_name} -> {other_page}")

    # Loop over content and add edges each time a topic is found
    tokens = preprocess2(content)
    # TODO check if not ngram first
    for word in tokens:
        if word in topic_names and word != topic:
            add_arrow(topic, word, 1)
            print(f"   ref {topic} -> {word}")

    # Do the same for bigrams
    bigrams = Counter(get_ngrams(" ".join(tokens), 2)).most_common()
    for bigram in bigrams:
        if bigram[0] in topic_names and bigram[0] != topic:
            add_arrow(topic, bigram[0], bigram[1])
            print(f"   ref {topic} -> {bigram[0]} ({bigram[1]})")
            break


# Remove edges with weight smaller than W_MIN
edge_weights = nx.get_edge_attributes(graph, 'weight')
graph.remove_edges_from((e for e, w in edge_weights.items() if w < W_MIN))

# PLOT
# pos = nx.spring_layout(graph)
pos = nx.nx_agraph.graphviz_layout(graph)
nx.draw_networkx(graph, pos)
labels = nx.get_edge_attributes(graph, 'weight')
nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
plt.show()
