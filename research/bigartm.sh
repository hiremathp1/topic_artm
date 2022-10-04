#!/bin/bash

# Step 1. Update and install dependencies
# If apt-get is a command, then we are on a Debian-based system.
if hash apt-get 2>/dev/null; then
  sudo apt-get --yes update
  sudo apt-get --yes install git make cmake build-essential libboost-all-dev
  sudo apt-get --yes install python-numpy python-pandas python-scipy
fi

mkdir -p vendor
cd vendor
source ../venv/bin/activate
pip install protobuf tqdm wheel

# Step 2. Clone repository and build
git clone --depth=1 --branch=master https://github.com/bigartm/bigartm.git
cd bigartm
mkdir build && cd build
cmake ..
make

# Step 3. Install BigARTM
make install
export ARTM_SHARED_LIBRARY=/usr/local/lib/libartm.so

pip install python/bigartm*.whl
