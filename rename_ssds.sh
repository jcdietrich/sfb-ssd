#!/bin/bash

# A script to rename SSD image files based on the output of get_name.py
# It processes a directory of .png files, renames each file to the name
# extracted by the get_name.py script, replacing spaces with underscores
# and preserving the .png extension.

# --- Configuration ---
# Activate the python virtual environment if it exists in the current directory
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "Warning: 'venv' directory not found. Assuming 'python3' and dependencies are in the system PATH."
fi

# Check if a directory is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: ./rename_ssds.sh <directory_path>"
  echo "Example: ./rename_ssds.sh inverted_images"
  exit 1
fi

TARGET_DIR=$1
DICTIONARY_FILE="dictionary.txt"

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' not found."
    exit 1
fi

# --- Main Loop ---
echo "Starting renaming process for directory: $TARGET_DIR"

for file in "$TARGET_DIR"/*.png; do
  # Check if the file exists (to handle cases where no .png files are found)
  if [ ! -f "$file" ]; then
    continue
  fi

  echo "---------------------------------"
  echo "Processing '$file'..."

  # Build the command to run get_name.py
  GET_NAME_CMD="python3 get_name.py '$file'"
  if [ -f "$DICTIONARY_FILE" ]; then
      echo "  - Using default dictionary: $DICTIONARY_FILE"
      GET_NAME_CMD="$GET_NAME_CMD --dictionary '$DICTIONARY_FILE'"
  fi
  
  # Get the name from get_name.py and capture the output
  SHIP_NAME=$(eval $GET_NAME_CMD)

  # Check if get_name.py returned a valid name
  if [ -z "$SHIP_NAME" ]; then
    echo "  - No name found or an error occurred. Skipping."
    continue
  fi
  
  echo "  - Extracted name: '$SHIP_NAME'"

  # Format the new filename
  # 1. Replace spaces with underscores
  # 2. Remove any characters that are not alphanumeric, underscore, or hyphen
  NEW_NAME=$(echo "$SHIP_NAME" | tr ' ' '_' | sed 's/[^A-Za-z0-9_-]//g')
  EXTENSION="${file##*.}"
  
  # Check if a valid new name was generated
  if [ -z "$NEW_NAME" ]; then
      echo "  - Generated name is empty after formatting. Skipping."
      continue
  fi

  NEW_FILENAME="${TARGET_DIR}/${NEW_NAME}.${EXTENSION}"

  # Check if the new filename is different and does not already exist
  if [ "$file" != "$NEW_FILENAME" ]; then
      if [ ! -f "$NEW_FILENAME" ]; then
          echo "  - Renaming to '$NEW_FILENAME'"
          mv "$file" "$NEW_FILENAME"
      else
          echo "  - WARNING: Target file '$NEW_FILENAME' already exists. Skipping."
      fi
  else
      echo "  - No renaming needed."
  fi
done

echo "---------------------------------"
echo "Renaming process complete."

# Deactivate the virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi
