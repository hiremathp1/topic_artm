# Topic API

Run `./start.sh` to create the env, install dependencies and start the uvicorn api in debug mode.

Check swagger docs at `http://127.0.0.1:8000/docs`

Topiclib can also be used as a simple library.

To deploy in production use something like:

```bash
./venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8080
```

And you can use a process manager like pm2 to keep it in background: https://pm2.keymetrics.io/docs/usage/quick-start/ 


## Endpoints

#### POST /image/wordcloud

```bash
curl -i -H "Authorization: 1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65" -H "Content-type: application/json" -X POST -d @samples/number_system.json "http://127.0.0.1:8000/image/wordcloud?width=300&height=400&method=anygram&limit=20" --output img.png
```


#### POST /topics

```bash
curl -i -H "Authorization: 1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65" -H "Content-type: application/json" -X POST -d @samples/number_system.json "http://127.0.0.1:8000/topics"
```


#### POST /image/graph

```bash
curl -i -H "Authorization: 1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65" -H "Content-type: application/json" -X POST -d @samples/number_system.json "http://127.0.0.1:8000/image/graph" --output img.png
```


#### POST /graph

```bash
curl -i -H "Authorization: 1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65" -H "Content-type: application/json" -X POST -d @samples/number_system.json "http://127.0.0.1:8000/graph"
```

Can be read in python with:

```python
from networkx.readwrite import json_graph;
DG = json_graph.node_link_graph(data)
```

Which will be a directed graph. Each node is a topic and the `weight` of the topics represent how much dependent a topic is of another (which means chances are it is a children of it) and the attribute `weight_total` means how much correlated the topics are in general. Nodes that receive a lot are more likely to be parents while nodes that only have exiting topcis are childrens.

https://networkx.org/documentation/stable/reference/readwrite/json_graph.html


You can print this graph as an image with:

```python
from topiclib.corpus_expansion import plot_graph
png_bytes = plot_graph(DG, 600, 600)
with open("graph.png", "wb") as f:
  f.write(png_bytes)
```

Notice that it is a directed graph. The subtopics point to the topic that is most likely to be in a upper level, a parent topic.


## Scheduling api

Calling directly on the endpoints `/graph`  or  `/image/graph` might result in a http timeout because the client can't wait for that long. For this reason I've implemented the scheduling endpoints:

### POST /command/image/graph

Same as `image/graph` but it will return a command id and launch the process in background in the server.

Example response:

```json
{
  "command_id": "b96dee06-b7f0-4957-95a6-cbf983d23c4d"
}
```


### POST /command/graph

Same as /command/image/graph but only for the json graph, like with `/graph` endpoint


### GET /command/progress?command_id=:command_id

This is a GET endpoint where `:command_id` should be replaced with the actual value returned by the command POST endpoints.

Example return values:

```json
{
  "message": "Command not found"
}
```


```json
{
  "progress": "running",
  "type": "json"
}
```

```json
{
  "progress": "done",
  "type": "png"
}
```

### GET /command/result?command_id=:command_id

Gets the actual result of the command. Will only work if the progress is done.


## Caching

The current caching implementation uses sqlite3. You can define your own cache by implementing the abstract class `ICache` at `topiclib/cache.py`. Maybe something like redis if there are many repeated calls is more suitable. Then it is a matter of calling `Cache.set_cache(NewClass())` like in `main.py`.

The default created file `cache.db` can be removed without worries (except that the cache is lost and topics will be recomputed).


## Corpus Expansion

Currently only en.wikipedia.com (English Wikipedia) is used for document lookups. If you wish to implement and use more implement the class `IDocumentProvider` from `topiclib` and decorate it with `provider("newname")`. Then you can obtain a graph using it with: `expand_corpus(counter, "newname", full)`

## CLI

A simple command line interface using `click` was implemented at `topiclib/__main__.py`. An example usage would be:

```sh
python -m topiclib graphimg -i samples/number_system.json -p "wikipedia"
```

from within an activated venv.

Most of the endpoints are available from this CLI but there is no caching.

Help menus are available:

```
$ python -m topiclib --help
Usage: python -m topiclib [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  graph      Graph json from json transcript.
  graphimg   Graph png image from json transcript.
  text       Parses json and returns text to stdout
  topics     Return topic counter from json transcript
  wordcloud  Wordcloud png image from json transcript.


-------------------------------------------------------------------
$ python -m topiclib wordcloud --help
Usage: python -m topiclib wordcloud [OPTIONS]

  Wordcloud png image from json transcript.

Options:
  -i, --input TEXT                Input file path
  -w, --width INTEGER             Width of the image.
  -h, --height INTEGER            Height of the image.
  -m, --method [gdsm|ngram|anygram]
                                  method to use for topic generation
  -n, --ngram_size INTEGER        size of ngrams to use (only for ngram
                                  method)
  -l, --limit TEXT                limit the number of topics to display
  -o, --output TEXT               Output path
  --help                          Show this message and exit.

-------------------------------------------------------------------
$ python -m topiclib graph --help
Usage: python -m topiclib graph [OPTIONS]

  Graph json from json transcript.

Options:
  -i, --input TEXT                Input file path
  -m, --method [gdsm|ngram|anygram]
                                  method to use for topic generation
  -n, --ngram_size INTEGER        size of ngrams to use (only for ngram
                                  method)
  -l, --limit TEXT                limit the number of topics to display
  -p, --provider TEXT             provider to use for topic expansion
  -g, --graph_type [network|tree]
                                  type of graph to use
  --help                          Show this message and exit.
```

### Example usage

Limit to 5 topics only, and with 2 words at most (bigrams).

```sh
python -m topiclib graphimg -i samples/Basic\ Math\ -\ Lesson\ 1\ -\ Complex\ Numbers.json -p "wikipedia" -l 5 -n 2
```

In the api that would be:

```
POST http://127.0.0.1:8000/image/graph?limit=5&ngram_size=2
```
