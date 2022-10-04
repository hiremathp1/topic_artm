# Questions

## 1). Please make sure the output is in JSON format. Header info is not required. Also, the format should be as mentioned in the following document, https://docs.google.com/presentation/d/1DcEPO9NyeVuGx6885HwxjomraijQ_7TxHDD3DXFLnpA/edit#slide=id.g11d1c1556db_0_292

A. That url is protected, I've requests access and didn't get accepted yet. Anyway see my answer bellow reguarding the format.


## 2). There is a number which appears in the output. What does it represent? Does that represent a score?

A. I will also answer to this altogether bellow.


## 3) There is no relationship between the topics and heirarchy. At least the relationship is not shown in the output

A. The output format is a JSON in the node-link format for networkx. In this case it is a directed graph where children topics point to their possible parents.
Relevant urls:
https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.json_graph.node_link_data.html
https://networkx.org/documentation/stable/reference/readwrite/json_graph.html
https://stackoverflow.com/questions/3162909/method-to-save-networkx-graph-to-json-graph
https://bl.ocks.org/mbostock/4062045

This is a universal format for gaphs. The weight of the links means how many connects a topic has to another overall (in the direction of that connection, children->parent where parent is the topic that contains the children), while "weight_total" is an overall measure of how many connections these topics have. By connection I mean how many times they are referenced by each other.

Changing this format would be beyond what we initially agreeed so is not something i am willing to include on this milestone at least. I believe that I have already overworked myself on this and if any format change is really needed it can be done from the client side or by editing main.py (which is the api path definitions and general processing steps for each endpoint).

Output Example:

```json
{
  "directed": true,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {
      "id": "square root"
    },
    {
      "id": "number"
    },
    {
      "id": "complex number"
    },
    {
      "id": "imaginary number"
    },
    {
      "id": "real number"
    },
    {
      "id": "number line"
    }
  ],
  "links": [
    {
      "weight": 33,
      "weight_total": 49,
      "source": "square root",
      "target": "number"
    },
    {
      "weight": 1,
      "weight_total": 17,
      "source": "square root",
      "target": "real number"
    },
    {
      "weight": 31,
      "weight_total": 39,
      "source": "complex number",
      "target": "real number"
    },
    {
      "weight": 84,
      "weight_total": 128,
      "source": "complex number",
      "target": "number"
    },
    {
      "weight": 2,
      "weight_total": 12,
      "source": "complex number",
      "target": "square root"
    },
    {
      "weight": 23,
      "weight_total": 29,
      "source": "imaginary number",
      "target": "number"
    },
    {
      "weight": 4,
      "weight_total": 4,
      "source": "imaginary number",
      "target": "real number"
    },
    {
      "weight": 6,
      "weight_total": 10,
      "source": "imaginary number",
      "target": "complex number"
    },
    {
      "weight": 59,
      "weight_total": 113,
      "source": "real number",
      "target": "number"
    },
    {
      "weight": 29,
      "weight_total": 29,
      "source": "number line",
      "target": "number"
    },
    {
      "weight": 9,
      "weight_total": 9,
      "source": "number line",
      "target": "real number"
    },
    {
      "weight": 2,
      "weight_total": 2,
      "source": "number line",
      "target": "complex number"
    }
  ]
}
// POST http://127.0.0.1:8000/graph
// HTTP/1.1 200 OK
// date: Thu, 29 Sep 2022 02:24:01 GMT
// server: uvicorn
// content-length: 1130
// content-type: application/json
// Request duration: 19.280262s
```


4. How do we run this app in the background? (uvicorn)

start.sh now will run a decent guinicorn version of the service. The uvicorn development server is now commented.

```
# Starts uvicorn debug dev server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "venv*" --log-level "debug"

# Starts gunicor deployment server
./venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --log-level "debug" --graceful-timeout 4800 --timeout 7200
```

Notice that requesting directly to the "/graph" or "/image/graph" endpoints can be take long and most html clients will timeout. For this reason I've also implemented the /command endpoint that works similarly but returns command id's that you can check the progress with and when it is done directly request the final result, without making your http client block or wait for too long:

```
# Request
POST http://127.0.0.1:8000/command/image/graph

will return a :command_id = a4deb283-2876-4f63-a401-7b4353af5319

# Check progress (replace with actual command_id from last request)
GET http://127.0.0.1:8000/command/progress?command_id=:command_id

# Get result
GET http://127.0.0.1:8000/command/result?command_id=:command_id
```

For backgrounding the api in general in a VPS environment i would recommend pm2: https://pm2.keymetrics.io/docs/usage/quick-start/


If this is planned to be more dynamically requests or requested directly by end users instead of batches that only run eventually I highly recommend investing more on dockernizing and developing a separated worker that could temporarily spawn on a high cpu AWS computing instance using cloud technology like kubernets. For that case the "/command" implementation is already a starting point.


## 5) curl -i -H "Authorization: 1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65" -H "Content-type: application/json" -X POST -d @samples/number_system.json "http://prodpy.lumoslearning.com:8000/image/wordcloud? width=300&height=400&method=anygram&limit=20" -O img.png Some process runs but does not give the output or create an image file. What should be the appropriate value for "O" flag? curl: (6) Could not resolve host: img.png

A. Readme Updated, the parameter is "--output" to download a file. Refer to `$ man curl` for more info: https://linux.die.net/man/1/curl

These image endpoints are meant to easy the visualisation but they are not able to provide a frontend ready image. 

For further questions about curl refer to `$ man curl`: https://linux.die.net/man/1/curl


## 6) Can we set a threshold for quality of the topics we get? 

A. You can set the number of topics but not limit the quality, if you mean something that will change the performance, make it run faster, no thats currently not even posssible for the current design.


## 7) Same issue with "/image/graph" as row no. 5 curl: (6) Could not resolve host: img.png

A. --output not -O (-o is also ok). No need to rely on the curl commands though. This is a REST http API, the sweager documentation is under the `/docs` endpoints when you run it. Useful link: https://curlconverter.com/


## 8) Some topics appear to duplicated with the addition of a word. For example, in the number system, "number natural number", "natural number natural", "number rational number", etc. Can this be avoided? 

A. Yes the `graph` endpoints provide a `ngram_size` and different methods. Please check http://127.0.0.1:8000/docs while running the api or the docstrings in main.py. For the "anygram" method, the default is trigrams

This is because the algorithm will find out each n grams repeat more (after pre-processing). The default is for ngrams of size 3 (trigrams). You can limit the number of topics and the maximum size of the ngrams with extra parameters on the api or CLI:


```sh
python -m topiclib graphimg -i samples/Basic\ Math\ -\ Lesson\ 1\ -\ Complex\ Numbers.json -p "wikipedia" -l 5 -n 2
```

In the api that would be:

```
POST http://127.0.0.1:8000/image/graph?limit=5&ngram_size=2
```

Please refer to the api documentation at: http://127.0.0.1:8000/docs


# More info

Don't be afraid to look in the code, it is pretty clean and commented, with docstrings, type hints and a decent tree structure.

## Providers

I made it so because I believe there can be still improvements on the core idea. One important thing is that it currently uses wikipedia as a provider but this is an interface that could be reimplemented to use other sources, which could improve the results, so check `toopiclib/providers.py` to learn how to create your own.


## Cache

The file `cache.db` holds all cache for provider pages, and processing. While it is not possible to remove results from the api (and might be not necessary) you can remove the entire cache.db or back it up and topiclib will restore it if necessary, recomputing what is needed. It is a simple sqlite3 file.

It is possible to implement the cache as it is also an interface similar to the provider. Check out `topiclib/cache.py` and main.py for the usage. In case you want to use redis or another db thats the way to go.


## Performance

This is currently a CPU intensive and network intensive (because of the default provider that is scrapping wikipedia). There is no much of a way around this, multithreading is already implemented. This is a direct method for computing the correlation (just as LDA).


