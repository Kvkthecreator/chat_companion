#!/bin/bash

echo "⚙️ Cleaning and reinstalling dependencies from scratch..."
pip install --upgrade pip setuptools
pip install -r src/requirements.txt --force-reinstall --no-cache-dir

