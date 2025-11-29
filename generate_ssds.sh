#!/bin/bash

# A script to generate HTML/CSS files for all processed SSD images and organize them.
# This script is idempotent and can be run multiple times.

# --- Configuration ---
BASE_DIR="SSDs"

# --- Main Logic ---

# Activate the python virtual environment
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "Warning: 'venv' directory not found. Assuming 'python3' and dependencies are in the system PATH."
    exit 1
fi

# Check if the base directory exists
if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Base directory '$BASE_DIR' not found. Have you run the extract_images.sh and rename_ssds.sh scripts yet?"
    exit 1
fi

echo "Starting SSD generation and organization process for directory: $BASE_DIR"

# Loop through each subdirectory in the base directory
for faction_dir in "$BASE_DIR"/*/; do
    if [ ! -d "$faction_dir" ]; then
        continue
    fi

    echo "---------------------------------"
    echo "Processing directory: $faction_dir"

    # --- Step 1: Organize PNGs ---
    # Create the 'images' and 'css' directories if they don't exist
    images_dir="${faction_dir}images"
    css_dir="${faction_dir}css"
    mkdir -p "$images_dir"
    mkdir -p "$css_dir"

    # Move any .png files from the faction root into the 'images' subdirectory
    # This consolidates images before processing.
    for png_file in "$faction_dir"*.png; do
        [ -f "$png_file" ] && mv "$png_file" "$images_dir/"
    done
    echo "  - Ensured all .png files are in $images_dir"

    # --- Step 2: Generate HTML and CSS files ---
    # Loop through the .png files in the 'images' subdirectory
    for file in "$images_dir"/*.png; do
        if [ -f "$file" ]; then
            echo "  - Generating files for '$file'..."
            # Run the python script. It will create .html and .css files
            # in the same directory as the input file (i.e., inside 'images/')
            cp "$file" "$file.white.png"
            magick "$file.white.png" -negate "$file"
            python3 full_ssd.py "$file"
            mv "$file.white.png" "$file"
        fi
    done
    echo "  - File generation complete for this faction."

    # --- Step 3: Organize generated files ---
    # Move .html files from 'images/' up to the faction directory
    for html_file in "$images_dir"/*.html; do
        [ -f "$html_file" ] && mv "$html_file" "$faction_dir"
    done
    echo "  - Moved .html files to $faction_dir"

    # Move .css files from 'images/' into the 'css' directory
    for css_file in "$images_dir"/*.css; do
        [ -f "$css_file" ] && mv "$css_file" "$css_dir/"
    done
    echo "  - Moved .css files to $css_dir"
done

echo "---------------------------------"
echo "SSD generation and organization complete."

# Deactivate the virtual environment
if [ -d "venv" ]; then
    deactivate
fi
