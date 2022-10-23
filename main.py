import json
import logging
import multiprocessing
import os
import pathlib
from collections import Counter
from enum import auto
from typing import Union
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi_utils.enums import StrEnum
from networkx.readwrite import json_graph

from config import (AUTH_HEADER, BLACKLISTED_IPS, CACHE_PATH, HOST, LOGLEVEL,
                    PORT, PROXY_IP, TMP_PATH, WHITELISTED_IPS)
from topiclib import (Cache, SqliteCache, TopicExtractor, expand_corpus, gsd,
                      hash_text, plot_graph, providers_map, wordcloud)
from topiclib.parser import get_text

app = FastAPI(
    title="Topic API",
    description="Extracts topics and their correlation hierarchy from audio transcriptions",
    version="0.0.1",
)

logger = logging.getLogger("topiclib")
logger.setLevel(LOGLEVEL)
command_line_handler = logging.StreamHandler()
command_line_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s- api - %(asctime)s - %(message)s")
command_line_handler.setFormatter(formatter)
logger.addHandler(command_line_handler)

commands = {}
pathlib.Path(TMP_PATH).mkdir(parents=True, exist_ok=True)

Cache.set_cache(SqliteCache(CACHE_PATH))


@app.middleware("http")
async def validate_ip_and_auth_header(request: Request, call_next):
    # Check for header if set in config
    if AUTH_HEADER:
        if request.headers.get("Authorization") != AUTH_HEADER:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid Authorization header"},
            )

    ip = str(request.client.host)
    if ip == PROXY_IP:
        headers = request.headers
        key = "X-Forwarded-For"
        if key in headers:
            ip = headers[key]

    if (
        len(WHITELISTED_IPS) > 0 and ip not in WHITELISTED_IPS
    ) or ip in BLACKLISTED_IPS:
        data = {
            "message": f"Sorry, this ip {ip} is not allowed to access this resource."
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=data)
    return await call_next(request)


def error_resp(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"message": message}
    )


# Api test


@app.get("/")
async def root():
    return {"message": "Hi. You seeing this message means the api is running!"}


async def get_json(request: Request) -> dict:
    try:
        return await request.json()
    except json.decoder.JSONDecodeError:
        return {}


class TopicExtractionMethod(StrEnum):
    gsdmm = auto()
    ngram = auto()
    anygram = auto()


def get_topics(
    text: str, method: TopicExtractionMethod, ngram_size: int = 1
) -> Union[dict, Counter]:
    cache = Cache.instance()
    cache_key = f"body_{method}_{ngram_size}" + repr(hash_text(text))
    if cache_key in cache:
        logger.debug(f"Cache hit for {cache_key}")
        return Counter(json.loads(cache[cache_key]))

    if method == TopicExtractionMethod.gsdmm:
        counter = gsd(text)
    elif method == TopicExtractionMethod.ngram:
        counter = TopicExtractor(text, ngram_range=(ngram_size,)).count_vectorizer(
            ngram_size=ngram_size
        )
    elif method == TopicExtractionMethod.anygram:
        counter = TopicExtractor(text).count()

    # Store in cache
    cache[cache_key] = json.dumps(counter)

    return counter


@app.post(
    "/image/wordcloud",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
async def wordcloud_image(
    request: Request,
    width: int = 600,
    height: int = 600,
    method: TopicExtractionMethod = TopicExtractionMethod.gsdmm,
    ngram_size: int = 1,
    limit: int = 100,
):
    """Wordcloud png image from json.

    - **with**: width of resulting image
    - **height**: height of resulting image
    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: size of ngrams to use (only for ngram method)
    - **limit**: Max of topics to display. Defaults to 100
    """
    body = await get_json(request)
    if "Items" not in body:
        return error_resp("Missing Items key in body")

    text = get_text(body)
    d = get_topics(text, method, ngram_size)
    image_bytes: bytes = wordcloud(d, width, height, limit)
    return Response(content=image_bytes, media_type="image/png")


ProviderStr = StrEnum("ProviderStr", {k: auto() for k in providers_map})

# Simple List


@app.post("/topics")
async def topics(
    request: Request,
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
    ngram_size: int = 1,
    limit: int = 10,
    provider: ProviderStr = list(providers_map.keys())[0],
):
    """
    Returns a list of topics using multiple methods.
    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: max ngram size to use starting from 2 (only for ngram method)
    - **limit**: Max of topics to return. Defaults to 10
    """
    body = await get_json(request)
    if "Items" not in body:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "No Items found"},
        )

    # Get the text from the request
    text = get_text(body)
    d = get_topics(text, method, ngram_size).most_common(limit)
    return d


class GraphType(StrEnum):
    network = auto()
    tree = auto()


@app.post(
    "/image/graph",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
async def graph_image(
    request: Request,
    width: int = 600,
    height: int = 600,
    ngram_size: int = 2,
    limit: int = 10,
    graph_type: GraphType = GraphType.network,
    full: bool = False,
    provider: ProviderStr = list(providers_map.keys())[0],
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
):
    """Graph png image representing the network of topic hierarchy.

    - **with**: width of resulting image
    - **height**: height of resulting image
    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: size of ngrams to use (only for ngram method)
    - **limit**: Max of topics to display. Defaults to 10
    - **graph_type**: Type of graph to display
        - **network**: Network graph. Default
        - **tree**: Tree graph

    - **full**: If true, will return the full graph without supressing unlikely (low ammount of connections) topics
    - **provider**: The document provider atlas for corpus expansion.
    """
    body = await get_json(request)
    if "Items" not in body:
        return error_resp("Missing Items key in body")

    text = get_text(body)
    d = get_topics(text, method, ngram_size).most_common(limit)
    graph = expand_corpus(d, provider, full)

    if graph_type == GraphType.network:
        image_bytes: bytes = plot_graph(graph, width, height)
        return Response(content=image_bytes, media_type="image/png")
    elif graph_type == GraphType.tree:
        image_bytes: bytes = plot_graph(graph, width, height, 1)
        return Response(content=image_bytes, media_type="image/png")


# Topic Structure
@app.post("/graph")
async def graph(
    request: Request,
    ngram_size: int = 2,
    limit: int = 10,
    full: bool = False,
    provider: ProviderStr = list(providers_map.keys())[0],
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
):
    """Graph json representing the network of topic hierarchy.

    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: size of ngrams to use (only for ngram method)
    - **limit**: Max of topics to display. Defaults to 10
    - **full**: If true, will return the full graph without supressing unlikely (low ammount of connections) topics
    - **provider**: The document provider atlas for corpus expansion.
    """
    body = await get_json(request)
    if "Items" not in body:
        return error_resp("Missing Items key in body")

    text = get_text(body)
    d = get_topics(text, method, ngram_size).most_common(limit)
    graph = expand_corpus(d, provider, full)
    return json_graph.node_link_data(graph)


# File system based command backgrounding and chaching system


def write_placeholder(path: str):
    """Write a placeholder file to path."""
    pathlib.Path(path).touch()


def is_empty_file(path: str):
    """Check if a file is empty."""
    return os.path.exists(path) and os.stat(path).st_size == 0


def generate_graph_image(
    body: dict,
    width: int = 600,
    height: int = 600,
    ngram_size: int = 2,
    limit: int = 10,
    graph_type: GraphType = GraphType.network,
    full: bool = False,
    provider: ProviderStr = list(providers_map.keys())[0],
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
    path: str = None,
):
    """Generate a graph from a request body and writes to a temporary file"""
    write_placeholder(path)

    text = get_text(body)
    d = get_topics(text, method, ngram_size).most_common(limit)
    graph = expand_corpus(d, provider, full)

    if graph_type == GraphType.network:
        image_bytes: bytes = plot_graph(graph, width, height)
    elif graph_type == GraphType.tree:
        image_bytes: bytes = plot_graph(graph, width, height, 1)

    # Write image to file
    with open(path, "wb") as f:
        f.write(image_bytes)


def generate_graph(
    body: dict,
    provider: str,
    full: bool = False,
    limit: int = 10,
    ngram_size: int = 2,
    method: str = "anygram",
    path: str = "0",
):
    """Generate a graph from a request body and writes to a temporary file"""
    write_placeholder(path)

    text = get_text(body)
    d = get_topics(text, method, ngram_size).most_common(limit)
    graph = expand_corpus(d, provider, full)
    jgraph = json_graph.node_link_data(graph)
    with open(path, "w") as f:
        json.dump(jgraph, f)


@app.post("/command/image/graph")
async def command_graph_image(
    request: Request,
    width: int = 600,
    height: int = 600,
    ngram_size: int = 2,
    limit: int = 10,
    graph_type: GraphType = GraphType.network,
    full: bool = False,
    provider: ProviderStr = list(providers_map.keys())[0],
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
):
    """Graph png image representing the network of topic hierarchy. This endpoint will spawn the computation in background and return a command id that you can use to check the progress.

    - **with**: width of resulting image
    - **height**: height of resulting image
    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: size of ngrams to use (only for ngram method)
    - **limit**: Max of topics to display. Defaults to 10
    - **graph_type**: Type of graph to display
        - **network**: Network graph. Default
        - **tree**: Tree graph

    - **full**: If true, will return the full graph without supressing unlikely (low ammount of connections) topics
    - **provider**: The document provider atlas for corpus expansion.
    """
    global commands
    body = await get_json(request)
    if "Items" not in body:
        return error_resp("Missing Items key in body")

    command_id = str(uuid4())
    path = f"{TMP_PATH}/{command_id}.png"
    commands[command_id] = {
        "path": path,
        "type": "png",
    }
    multiprocessing.Process(
        target=generate_graph_image,
        args=(
            body,
            width,
            height,
            ngram_size,
            limit,
            graph_type,
            full,
            provider,
            method,
            path,
        ),
        daemon=True,
    ).start()

    return {"command_id": command_id}


@app.post("/command/graph")
async def command_graph(
    request: Request,
    ngram_size: int = 2,
    limit: int = 10,
    full: bool = False,
    provider: ProviderStr = list(providers_map.keys())[0],
    method: TopicExtractionMethod = TopicExtractionMethod.anygram,
):
    """Graph json representing the network of topic hierarchy. This endpoint will spawn the computation in background and return a command id that you can use to check the progress.

    - **method**: method to use for topic generation
        - **gsdmm**: Single word topics https://github.com/rwalk/gsdmm
        - **ngram**: N-gram topics
        - **anygram**: Any size ngram topics mixed

    - **ngram_size**: size of ngrams to use (only for ngram method)
    - **limit**: Max of topics to display. Defaults to 10
    - **full**: If true, will return the full graph without supressing unlikely (low ammount of connections) topics
    - **provider**: The document provider atlas for corpus expansion.
    """
    global commands
    body = await get_json(request)
    if "Items" not in body:
        return error_resp("Missing Items key in body")

    command_id = str(uuid4())
    path = f"{TMP_PATH}/{command_id}.json"
    commands[command_id] = {
        "path": path,
        "type": "json",
    }
    multiprocessing.Process(
        target=generate_graph,
        args=(body, provider, full, limit, ngram_size, method, path),
        daemon=True,
    ).start()

    return {"command_id": command_id}


@app.get("/command/progress")
async def command_progress(command_id: str):
    """Get the progress of a command. The command id is returned by the command endpoints."""
    global commands

    if command_id not in commands:
        return error_resp("Command not found")

    path = commands[command_id]["path"]
    if is_empty_file(path):
        return {"progress": "running", "type": commands[command_id]["type"]}

    return {"progress": "done", "type": commands[command_id]["type"]}


@app.get("/command/result")
async def command_result(command_id: str):
    """Get the result of a command. The command id is returned by the command endpoints. Can return a png image or a json depending on the command"""
    if command_id not in commands:
        return error_resp("Command not found")

    path = commands[command_id]["path"]
    if is_empty_file(path):
        return error_resp("Command not finished or failed")

    # Read file and return
    if commands[command_id]["type"] == "png":
        return FileResponse(path, media_type="image/png")

    elif commands[command_id]["type"] == "json":
        with open(path, "r") as f:
            return json.load(f)

    else:
        return error_resp("Uninplemented command type")




if __name__ == "__main__":
    from topiclib.parser import parsefile

    def test(file: str):
        print(f"\n\n{file}:")
        t = TopicExtractor(parsefile(file))
        p = t.count().most_common(10)
        expand_corpus(p, "wikipedia")

    test("research/samples/number_system.json")
    # test('samples/Basic Math - Lesson 1 - Complex Numbers.json')
