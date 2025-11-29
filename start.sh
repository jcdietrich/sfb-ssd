#!/usr/bin/env bash
PDF_FILE="$1"

source venv/bin/activate
./extract_images.sh "$PDF_FILE"
./rename_ssds.sh SSDs
./generate_ssds.sh


