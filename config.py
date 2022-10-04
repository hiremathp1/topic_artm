import os
import logging

# 	test.py
# Host and port of the api
HOST = "0.0.0.0"
PORT = 8000

LOGLEVEL = logging.DEBUG

CACHE_PATH = "cache.db"
TMP_PATH = "/tmp/topicapi/"


# ##############################################################################################
# Authorization header: If not set anyone can access the API (Except by IP whitelist/blacklisting bellow)
# If set the client must send this same authorization header. This is basically a simple plaintext password.
AUTH_HEADER = ""
# Example:
# AUTH_HEADER = "1dedf8842d7586c7a35fa56f06dc7c8b8e15bf1373363ffffffd65"

# ##############################################################################################
# To use the whitelist or blacklist remember to pass the real ip from the proxy to the backend
# On nginx:
#          proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;

# Not needed if not using a reverse proxy
PROXY_IP = "127.0.0.1"

# If the whitelist is empty then all IP's will be allowed
# If the whitelist is set then only the ips in the list will be accepted
WHITELISTED_IPS = []

# If you have an empty whitelist but still wish to block some ip addresses you can
# use the ip blacklist
BLACKLISTED_IPS = []

# Make it so all those values are overwritten by Environment variables
for key, value in os.environ.items():
    if key in globals() and key.isupper():
        if isinstance(globals()[key], str):
            globals()[key] = value
        if isinstance(globals()[key], int):
            globals()[key] = value
        if isinstance(globals()[key], list):
            globals()[key] = value.split(",")
