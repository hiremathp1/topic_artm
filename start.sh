#!/usr/bin/env bash

# Create venv and install dependencies if doesn't exist
if [ ! -d "venv" ]; then
    if [ -n "$(uname -a | grep Ubuntu)" ]; then
      sudo apt-get -y install libpython3.8-dev python3-dev python3-venv graphviz graphviz-dev
    else
      echo "You are not on Ubuntu, please install graphviz and graphviz-dev manually for graph images generation"
    fi

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

source venv/bin/activate

# Starts uvicorn debug dev server
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "venv*" --log-level "debug"

# Starts gunicor deployment server
./venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --log-level "debug" --graceful-timeout 4800 --timeout 7200
