#!/usr/bin/env bash

# Create venv if doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install requirements
pip install -r requirements.txt

pip install git+https://github.com/rwalk/gsdmm.git
python download_models.py
