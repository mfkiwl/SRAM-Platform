#!/usr/bin/env zsh

src_path="$(dirname $0)/../src"
reorder-python-imports $src_path/**/*.py
black $src_path/**/*.py
