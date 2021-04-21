#!/usr/bin/env python3
from waitress import serve

from api import app
from api import toml_config

if __name__ == "__main__":
    host = toml_config["station"]["host"]
    port = toml_config["station"]["port"]
    print(f"Serving station at {host}:{port}")
    serve(app, host=host, port=port)
