#!/bin/bash
for file in basic_ssds/*.png; do
  filename=$(basename "$file")
  magick "$file" -negate "inverted_images/$filename"
done
