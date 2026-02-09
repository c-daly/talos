#!/bin/bash
set -e
poetry install --with dev
poetry run pip install -e ../logos
echo "Local dev setup complete. Verify: poetry run pip show logos-foundry"
