#!/usr/bin/env bash
# Downloads the data on first run (kept in ./data when mounted), then runs every step in order.
set -euo pipefail
mkdir -p data results
DATA=data/criteo-uplift-v2.1.csv.gz
if [ ! -f "$DATA" ]; then
  echo "Downloading the Criteo uplift dataset (about 300 MB, first run only)..."
  curl -L --fail -o "$DATA" \
    "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz"
fi
for step in analysis/0*.py; do
  echo
  echo "=== $step ==="
  python "$step"
done
echo
echo "Done. Results are in ./results"
