#!/usr/bin/env python3
from api import app
from api import toml_config
from waitress import serve

if __name__ == "__main__":
    host = toml_config["station"]["host"]
    port = toml_config["station"]["port"]
    print(f"Serving station at {host}:{port}")
    serve(app, host=host, port=port)
