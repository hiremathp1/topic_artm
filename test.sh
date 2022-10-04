#!/usr/bin/env bash

# Create venv and install dependencies if doesn't exist
if [ ! -d "venv" ]; then
    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

source venv/bin/activate
# Check if pytest is installed, if not install test_requirements.txt
if ! command -v pytest &> /dev/null; then
    pip install -r test_requirements.txt
fi

# Run all tests
python -m pytest tests/ -vv
