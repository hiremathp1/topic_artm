import logging
from collections import Counter
from functools import wraps
from pathlib import Path

import click
from networkx.readwrite import json_graph

from .corpus_expansion import expand_corpus, plot_graph
from .parser import parsefile
from .topic_extraction import TopicExtractor
from .wordprocess import gsd
from .wordprocess import wordcloud as wc

logger = logging.getLogger("topiclib")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


def get_topics(text: str, method: str, ngram_size: int = 2):
    if method == "gdsm":
        counter = gsd(text)
    elif method == "ngram":
        counter = TopicExtractor(text, ngram_range=(ngram_size,)).count_vectorizer(
            ngram_size=ngram_size
        )
    elif method == "anygram":
        counter = TopicExtractor(text).count()

    return Counter(counter)


def checkinput_file(func):
    """
    Decorator to check if input file exists
    """

    @wraps(func)
    def wrapper(input: str, *args, **kwargs):
        if not Path(input).is_file():
            raise click.ClickException(f"Input file {input} does not exist")
        return func(input, *args, **kwargs)

    return wrapper


@click.group()
def cli():
    pass


@cli.command(help="Parses json and returns text to stdout")
@click.option("-i", "--input", help="Input file path")
def text(input):
    # Check if input exists and is a file
    if not Path(input).is_file():
        raise click.ClickException(f"Input file {input} does not exist")
    text = parsefile(input)
    print(text)


@cli.command(help="Wordcloud png image from json transcript.")
@click.option("-i", "--input", help="Input file path")
@click.option("-w", "--width", default=600, help="Width of the image.")
@click.option("-h", "--height", default=600, help="Height of the image.")
@click.option(
    "-m",
    "--method",
    default="gdsm",
    type=click.Choice(["gdsm", "ngram", "anygram"]),
    help="method to use for topic generation",
)
@click.option(
    "-n",
    "--ngram_size",
    default=2,
    help="size of ngrams to use (only for ngram method)",
)
@click.option("-l", "--limit", default=10, help="limit the number of topics to display")
@click.option("-o", "--output", default=None, help="Output path")
@checkinput_file
def wordcloud(
    input,
    width: int = 600,
    height: int = 600,
    method: str = "gsdm",
    ngram_size: int = 2,
    limit: int = 10,
    output: str = None,
):
    text = parsefile(input)
    d = get_topics(text, method, ngram_size)
    image_bytes: bytes = wc(d, width, height, limit)

    # Save to output
    output = output if output else input + ".png"
    print(f"Saving resulting png to {output}")
    with open(output, "wb") as f:
        f.write(image_bytes)


@cli.command(help="Return topic counter from json transcript")
@click.option("-i", "--input", help="Input file path")
@click.option(
    "-m",
    "--method",
    default="anygram",
    type=click.Choice(["gdsm", "ngram", "anygram"]),
    help="method to use for topic generation",
)
@click.option(
    "-n",
    "--ngram_size",
    default=2,
    help="size of ngrams to use (only for ngram method)",
)
@click.option("-l", "--limit", default=10, help="limit the number of topics to display")
@checkinput_file
def topics(input, method: str = "anygram", ngram_size: int = 2, limit: int = 20):
    # Check if input exists and is a file
    if not Path(input).is_file():
        raise click.ClickException(f"Input file {input} does not exist")

    # Get the text from the request
    text = parsefile(input)
    d = get_topics(text, method, ngram_size).most_common(limit)
    print(d)


@cli.command(help="Graph png image from json transcript.")
@click.option("-i", "--input", help="Input file path")
@click.option("-w", "--width", default=600, help="Width of the image.")
@click.option("-h", "--height", default=600, help="Height of the image.")
@click.option(
    "-m",
    "--method",
    default="anygram",
    type=click.Choice(["gdsm", "ngram", "anygram"]),
    help="method to use for topic generation",
)
@click.option(
    "-n",
    "--ngram_size",
    default=2,
    help="size of ngrams to use (only for ngram method)",
)
@click.option("-l", "--limit", default=10, help="limit the number of topics to display")
@click.option("-o", "--output", default=None, help="Output path")
@click.option(
    "-p", "--provider", default=None, help="provider to use for topic expansion"
)
@click.option(
    "-g",
    "--graph_type",
    default="tree",
    type=click.Choice(["network", "tree"]),
    help="type of graph to use",
)
@checkinput_file
def graphimg(
    input,
    width: int = 600,
    height: int = 600,
    method: str = "anygram",
    ngram_size: int = 2,
    limit: int = 10,
    output: str = None,
    provider: str = None,
    graph_type: str = None,
):
    text = parsefile(input)
    d = get_topics(text, method, ngram_size).most_common(limit)
    print(f"Got topics: {limit=} {d}")
    graph = expand_corpus(d, provider, use_cache=False)

    if graph_type == "network":
        image_bytes: bytes = plot_graph(graph, width, height)
    elif graph_type == "tree":
        image_bytes: bytes = plot_graph(graph, width, height, 1)

    # Save to output
    output = output if output else input + ".png"
    print(f"Saving resulting png to {output}")
    with open(output, "wb") as f:
        f.write(image_bytes)


@cli.command(help="Graph json from json transcript.")
@click.option("-i", "--input", help="Input file path")
@click.option(
    "-m",
    "--method",
    default="anygram",
    type=click.Choice(["gdsm", "ngram", "anygram"]),
    help="method to use for topic generation",
)
@click.option(
    "-n",
    "--ngram_size",
    default=2,
    help="size of ngrams to use (only for ngram method)",
)
@click.option("-l", "--limit", default=10, help="limit the number of topics to display")
@click.option(
    "-p", "--provider", default=None, help="provider to use for topic expansion"
)
@click.option(
    "-g",
    "--graph_type",
    default="tree",
    type=click.Choice(["network", "tree"]),
    help="type of graph to use",
)
@checkinput_file
def graph(
    input,
    method: str = "anygram",
    ngram_size: int = 2,
    limit: int = 10,
    provider: str = None,
    graph_type: str = None,
):
    text = parsefile(input)
    d = get_topics(text, method, ngram_size).most_common(limit)
    graph = expand_corpus(d, provider, use_cache=False)

    print(json_graph.node_link_data(graph))


if __name__ == "__main__":
    cli()
