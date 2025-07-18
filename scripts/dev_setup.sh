#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[server] pre-commit
pre-commit install
