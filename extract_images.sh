#!/bin/bash

# A script to extract images from a PDF, filter them by size, process them,
# and save the final images into a directory named 'ssds'.

# --- Usage ---
if [ -z "$1" ]; then
  echo "Usage: ./extract_images.sh <path_to_pdf_file>"
  echo "Example: ./extract_images.sh 'Star_Fleet_Battles_Basic_Set_SSD_Book_2011_(B&W).pdf'"
  exit 1
fi

# --- Configuration ---
PDF_FILE=$1
OUTPUT_DIR="ssds"
TEMP_DIR="temp_extracted_pngs_$(date +%s)" # Use a unique temp dir name

# --- Pre-flight Checks ---
# Check if the PDF file exists
if [ ! -f "$PDF_FILE" ]; then
    echo "Error: PDF file '$PDF_FILE' not found."
    exit 1
fi

# Check if 'pdfimages' and 'magick' commands are available
if ! command -v pdfimages &> /dev/null; then
    echo "Error: 'pdfimages' command not found. Please install 'poppler' (e.g., 'brew install poppler' or 'sudo apt-get install poppler-utils')."
    exit 1
fi

if ! command -v magick &> /dev/null; then
    echo "Error: 'magick' command not found. Please install 'ImageMagick' (e.g., 'brew install imagemagick' or 'sudo apt-get install imagemagick')."
    exit 1
fi


# --- Main Steps ---
echo "Starting image extraction and processing..."

# 1. Create temporary and output directories
echo "Creating temporary directory '$TEMP_DIR' and output directory '$OUTPUT_DIR'..."
mkdir -p "$TEMP_DIR"
mkdir -p "$OUTPUT_DIR"

# 2. Extract images from PDF as PNGs into the temporary directory
echo "Extracting images from '$PDF_FILE'..."
pdfimages -png "$PDF_FILE" "$TEMP_DIR/ssd"
if [ $? -ne 0 ]; then
    echo "Error: pdfimages failed."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 3. Filter extracted images by size
echo "Filtering extracted images by size..."
# Delete files smaller than 1k
find "$TEMP_DIR" -type f -name "*.png" -size -1k -print -delete
# Delete files larger than 1M
find "$TEMP_DIR" -type f -name "*.png" -size +1M -print -delete


# 4. Process each remaining extracted image
echo "Processing remaining images (resize, invert)..."
IMAGE_COUNT=$(ls -1 "$TEMP_DIR"/*.png 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "Warning: No images remaining after size filtering."
else
    for file in "$TEMP_DIR"/*.png; do
      if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "  - Processing '$filename'..."
        
        # Use ImageMagick to resize, and invert colors
        magick "$file"  -resize 1500x -negate "${OUTPUT_DIR}/${filename}"
      fi
    done
fi

# 5. Clean up temporary directory
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "---------------------------------"
echo "Image extraction and processing complete."
echo "Final images are in the '$OUTPUT_DIR' directory."
