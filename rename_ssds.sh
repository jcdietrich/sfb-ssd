#!/bin/bash

# A script to rename SSD image files and sort them into faction-specific directories.
# It processes a directory of .png files, renames each file to the name
# extracted by the get_name.py script, and then moves it into a subdirectory
# based on the first word of the extracted name.

# --- Configuration ---
FACTION_KEYWORDS="FEDERATION GORN KLINGON KZNINTI ROMULAN THOLIAN ORION"

# Activate the python virtual environment if it exists
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
echo "Starting renaming and sorting process for directory: $TARGET_DIR"

for file in "$TARGET_DIR"/*.png; do
  if [ ! -f "$file" ]; then
    continue
  fi

  echo "---------------------------------"
  echo "Processing '$file'..."

  GET_NAME_CMD="python3 get_name.py '$file'"
  if [ -f "$DICTIONARY_FILE" ]; then
      echo "  - Using default dictionary: $DICTIONARY_FILE"
      GET_NAME_CMD="$GET_NAME_CMD --dictionary '$DICTIONARY_FILE'"
  fi
  
  SHIP_NAME=$(eval $GET_NAME_CMD)

  if [ -z "$SHIP_NAME" ]; then
    echo "  - No name found or an error occurred. Skipping."
    continue
  fi
  
  echo "  - Extracted name: '$SHIP_NAME'"

  # Determine target subdirectory
  FIRST_WORD=$(echo "$SHIP_NAME" | cut -d' ' -f1)
  TARGET_SUBDIR="MISC" # Default directory
  for KEYWORD in $FACTION_KEYWORDS; do
    if [ "$FIRST_WORD" == "$KEYWORD" ]; then
      TARGET_SUBDIR=$KEYWORD
      break
    fi
  done
  
  echo "  - Determined faction/subdirectory: $TARGET_SUBDIR"
  
  # Create subdirectory if it doesn't exist
  mkdir -p "${TARGET_DIR}/${TARGET_SUBDIR}"

  # Format the new filename
  NEW_NAME=$(echo "$SHIP_NAME" | tr ' ' '_' | sed 's/[^A-Za-z0-9_-]//g')
  EXTENSION="${file##*.}"
  
  if [ -z "$NEW_NAME" ]; then
      echo "  - Generated name is empty after formatting. Skipping."
      continue
  fi

  # Include the subdirectory in the new path
  NEW_FILENAME="${TARGET_DIR}/${TARGET_SUBDIR}/${NEW_NAME}.${EXTENSION}"

  # Check if the new filename is different and does not already exist
  if [ "$file" != "$NEW_FILENAME" ]; then
      if [ ! -f "$NEW_FILENAME" ]; then
          echo "  - Moving and renaming to '$NEW_FILENAME'"
          mv "$file" "$NEW_FILENAME"
      else
          echo "  - WARNING: Target file '$NEW_FILENAME' already exists. Skipping."
      fi
  else
      echo "  - No renaming needed."
  fi
done

echo "---------------------------------"
echo "Renaming and sorting process complete."

if [ -d "venv" ]; then
    deactivate
fi