import concurrent.futures
import json
import logging
import multiprocessing
import sys
import threading
import time
import traceback
from abc import ABC, abstractclassmethod
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from itertools import islice

import matplotlib.pyplot as plt
import networkx as nx
from networkx.readwrite import json_graph
from requests.exceptions import ConnectionError

from .cache import Cache
from .preprocess import flatten, preprocess2
from .topic_extraction import TopicExtractor, filter_low
from .utils import hash_text

logger = logging.getLogger("topiclib")
SEARCH_LIMIT = 5


class IDocumentProvider(ABC):
    """Interface for content providers"""

    @abstractclassmethod
    def search(self, query: str) -> [str]:
        """Must take a search string and return a list of possible topics as strings that reference pages"""
        pass

    @abstractclassmethod
    def content(self, page: str) -> str:
        """Takes in a string returned by search and returns a corpus body"""
        pass

    @abstractclassmethod
    def categories(self, page: str) -> [str]:
        """Takes in a string returned by search and returns a list of unique categories the corresponding content is part of"""
        pass


@dataclass
class Provider:
    """Class for storing a provider and its basic info"""

    name: str
    provider: IDocumentProvider


providers_map = {}


def provider(name):
    """Decorator for adding more providers classes"""

    def wrapper(cls):
        assert issubclass(cls, IDocumentProvider)
        providers_map[name] = Provider(name=name, provider=cls())
        cls.name = name
        return cls

    return wrapper


def process_page(provider, page_name, topic_names) -> (Counter, list):
    """This function will run in a thread. page_name must be a valid page for the provider.
    It retuns the counter of topics for the page and the edges from the topic corresponding to page_name
    connecting to other other topics that are in topic_names: edges = [(this_topic, other_topic, n_references)]
    """
    topic = flatten(preprocess2(page_name))
    if topic not in topic_names:
        return None, None

    # Fetch from provider
    attempts = 0
    while True:
        if attempts > 3:
            print(f"Could not fetch content for {page_name}")
            return None, None
        try:
            content = provider.content(page_name)
            break
        except ConnectionError:
            time.sleep(1)
            attempts += 1

    model = TopicExtractor(content)
    counter = model.count()

    edges = []
    for ngram, _ in counter.items():
        if ngram not in topic_names or ngram == topic:
            continue
        edges.append((topic, ngram, counter[ngram]))
    return counter, edges


def process_categories(provider, page_name) -> Counter:
    """Will process a list of categories similarly to process_page"""
    categories = provider.categories(page_name)
    categories = [preprocess2(cat) for cat in categories]
    return sum((Counter(cat.split()) for cat in categories), Counter())


def expand_corpus(
    topics: [str], provider: str, full: bool = False, use_cache=True
) -> nx.DiGraph:
    """Expands a corpus by adding pages from a provider and returns a graph"""

    topic_hash = hash_text(",".join([t for t, _ in topics]))
    cache = Cache.instance() if use_cache else {}

    if isinstance(provider, str):
        assert provider in providers_map
        provider: IDocumentProvider = providers_map[provider].provider

    n_cores = multiprocessing.cpu_count()

    logger.debug(topics)
    logger.info("loading pages...")

    cache_key = "search_" + repr((provider.name, topic_hash))
    if cache_key not in cache:
        page_names = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_cores) as executor:
            future_to_page = {
                executor.submit(provider.search, topic): topic for topic, _ in topics
            }
            for future in concurrent.futures.as_completed(future_to_page):
                page_names.append(next(future.result()))

        topic_names = [flatten(preprocess2(name)) for name in page_names]
        cache[cache_key] = json.dumps((page_names, topic_names))
    else:
        page_names, topic_names = json.loads(cache[cache_key])
    logger.debug(f"{topic_names=}")

    graph = nx.DiGraph()
    graph.add_nodes_from(topic_names)
    logger.debug("Initialized graph")

    def add_arrow(start, end, weight=1):
        """Add edge if weight 'weight' if not exists, else increase the 'weight' by 1"""
        s = start
        e = end

        # If contrary edge exists subtract from it
        if graph.has_edge(end, start):
            w = graph[end][start]["weight"]
            graph[end][start]["weight"] -= weight

            # Direction flip
            if graph[end][start]["weight"] <= 0:
                weight_total = graph[end][start]["weight_total"]
                graph.remove_edge(end, start)
                graph.add_edge(start, end, weight=weight - w, weight_total=weight_total)
            else:
                s = end
                e = start

        # If edge exists add to it
        elif graph.has_edge(start, end):
            graph[start][end]["weight"] += weight
        else:
            graph.add_edge(start, end, weight=weight, weight_total=0)

        # Add to overall weight property for that edge
        graph[s][e]["weight_total"] += weight

        return graph[s][e]["weight_total"]

    def filter_topics_from_cache(page_name):
        # Read from cache
        cache_key = "provider_" + repr((provider.name, page_name))
        if cache_key in cache:
            logger.debug(f"{page_name} found in cache")
            _, edges = json.loads(cache[cache_key])
            return edges
        else:
            logger.debug(f"{cache_key} not found in cache, computing...")
            return False

    def add_edges(edges):
        if edges is None:
            return
        for edge in edges:
            topic, ngram, weight = edge
            weight_total = add_arrow(topic, ngram, weight)
            logger.debug(f"Added arrow: '{topic}' -> '{ngram}'   weight: {weight}")
            logger.debug(f"    weight_total: {weight_total}")

    # remove topics that are cached from page_names and add them to the graph already
    non_cached_names = []
    cached_edges = {}
    for name in page_names:
        cached = filter_topics_from_cache(name)
        if cached is False:
            non_cached_names.append(name)
            continue

        # is in cache
        cached_edges[name] = cached

    # Loop over each topic and populated edges between topics
    logger.debug(f"{non_cached_names=}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_cores) as executor:
        logger.info("Submitting tasks")
        future_to_page = {
            executor.submit(process_page, provider, name, topic_names): name
            for name in non_cached_names
        }
        logger.debug("Processing pages")
        for future in concurrent.futures.as_completed(future_to_page):
            page_name = future_to_page[future]
            logger.debug(f"Finished for {page_name}")
            try:
                counter, edges = future.result()
                if counter is None:
                    logger.debug(
                        f"{page_name} is being skipped because it is not in topic_names or provider request failed"
                    )
                    continue

                add_edges(edges)

                # Store in cache
                cache_key = "provider_" + repr((provider.name, page_name))
                cache[cache_key] = json.dumps((counter, edges))
                logger.debug(f"{page_name} stored in cache")

            except Exception as e:
                print("%r generated an exception: %s" % (page_name, e))
                print(
                    "".join(traceback.format_exception(type(e), e, e.__traceback__)),
                    file=sys.stderr,
                    flush=True,
                )

    # Add cached edges
    for name, edges in cached_edges.items():
        add_edges(edges)

    if not full:
        # Remove edges with weight smaller than W_MIN
        logger.debug("Removing edges with weight smaller than W_MIN")
        weight_totals = nx.get_edge_attributes(graph, "weight_total")
        logger.debug(f"{weight_totals.values()=}")
        w_min = filter_low(list(weight_totals.values()))[1][0]
        full_graph = graph.copy()
        graph.remove_edges_from((e for e, w in weight_totals.items() if w < w_min))

        # Remove nodes with no edges
        graph.remove_nodes_from(list(nx.isolates(graph)))

        # Restore edges with weight smaller than W_MIN for remaining nodes
        for node in full_graph.nodes():
            if node not in graph.nodes():
                continue
            for edge in full_graph.edges(node):
                if (
                    edge not in graph.edges()
                    and edge[0] in graph.nodes()
                    and edge[1] in graph.nodes()
                ):
                    graph.add_edge(
                        edge[0],
                        edge[1],
                        weight=full_graph[edge[0]][edge[1]]["weight"],
                        weight_total=full_graph[edge[0]][edge[1]]["weight_total"],
                    )

    return graph


def plot_graph(graph: nx.DiGraph, width: int, height: int, style=0) -> bytes:
    """Returns a plot of the graph"""

    # Set layout
    if style == 0:
        pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    elif style == 1:
        # Ortogonal
        pos = nx.nx_agraph.pygraphviz_layout(
            graph, prog="patchwork", args="-Goverlap=scale "
        )

    # Compute plotting data
    weight_totals = nx.get_edge_attributes(graph, "weight_total")
    labels = nx.get_edge_attributes(graph, "weight")
    thickness = list(weight_totals.values())
    thickness = [(w + 1) / max(thickness) for w in thickness]

    # Resize image
    dpi = 128
    plt.gcf().set_size_inches(width / dpi, height / dpi)
    plt.axis("off")

    # PLOT
    nx.draw_networkx(graph, pos, width=thickness)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=weight_totals)

    # Convert to bytes[]
    b = BytesIO()
    plt.savefig(b, format="png", dpi=dpi)
    b.seek(0)
    return b.read()
