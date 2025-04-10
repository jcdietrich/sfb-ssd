#!/usr/bin/env python3
import cv2
import numpy as np
import os
import argparse # Import argparse

# --- Parameters to Tune ---
# Thresholding
THRESH_BLOCK_SIZE = 15
THRESH_C = 5

# Contour Filtering
MIN_AREA = 100
MAX_AREA = 250
ASPECT_RATIO_TOL = 0.25
APPROX_POLY_EPSILON = 0.04

# De-duplication
MIN_DIST_SQ_DEDUP = (10**2)

# Detected Box Size (for CSS)
BOX_SIZE_PX = 16
# --- End Parameters ---

# --- These will be set based on input arg ---
BG_IMG_FILENAME = None 
IMG_NO_EXT = None
CSS_OUTPUT_FILENAME = None
HTML_OUTPUT_FILENAME = None
VIZ_OUTPUT_FILENAME = None

def get_basename_no_extension(filepath):
  """Gets the filename without the directory path or the extension."""
  # 1. Get the filename part (removes directory)
  basename_with_ext = os.path.basename(filepath)
  # 2. Split the filename from its extension
  #    splitext splits on the LAST dot, handling cases like .tar.gz correctly
  basename_no_ext, extension = os.path.splitext(basename_with_ext)
  return basename_no_ext

def generate_files_relative(bg_img_filename, final_boxes, img_width, img_height): # Pass background filename
    """Generates the HTML and CSS files with one master group using px."""
    global CSS_OUTPUT_FILENAME, HTML_OUTPUT_FILENAME, IMG_NO_EXT

    if not final_boxes:
        print("No boxes found, cannot generate files.")
        return

    min_x = min(b[0] for b in final_boxes)
    min_y = min(b[1] for b in final_boxes)
    print(f"Master group top-left determined at: x={min_x}px, y={min_y}px")

    # --- Generate HTML ---
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{IMG_NO_EXT}</title>
    <link rel="stylesheet" href="{CSS_OUTPUT_FILENAME}">
</head>
<body>
<div id="ship-diagram">
    <div id="checkbox-master-group">
"""
    for i, (x, y, w, h) in enumerate(final_boxes):
        box_id = f"box{i+1}"
        html_content += f'        <input type="checkbox" id="{box_id}" title="{box_id}: x={x}px, y={y}px">\n'
    html_content += """    </div> </div> </body>
</html>
"""
    # --- Generate CSS ---
    css_content = f"""/* Auto-generated CSS - Relative Group (px units) */
body {{ font-family: sans-serif; }}
#ship-diagram {{
    position: relative; width: {img_width}px; height: {img_height}px; margin: 20px;
    background-image: url('{bg_img_filename}'); /* Use passed filename */
    background-repeat: no-repeat; background-size: contain;
    border: 1px solid #ccc; /* Optional */
}}
#checkbox-master-group {{
    position: absolute; top: {min_y}px; left: {min_x}px; position: relative;
    /* border: 1px dashed red; */ /* Optional */
}}
#checkbox-master-group input[type="checkbox"] {{
    position: absolute; width: {BOX_SIZE_PX}px; height: {BOX_SIZE_PX}px;
    margin: 0; padding: 0; cursor: pointer; box-sizing: border-box;
}}
#checkbox-master-group input[type="checkbox"]:not(:checked) {{
    appearance: none; -webkit-appearance: none;
    border: 1px solid rgba(0, 255, 0, .5); background-color: transparent; opacity: 1;
}}
#checkbox-master-group input[type="checkbox"]:checked {{
   background-color: rgba(0, 255, 0, 0.5);
}}
/* --- Individual Box Positions (Relative to Master Group - px units) --- */
"""
    for i, (x, y, w, h) in enumerate(final_boxes):
        box_id = f"box{i+1}"
        rel_x = x - min_x
        rel_y = y - min_y
        css_content += f"#{box_id} {{ top: {rel_y}px; left: {rel_x}px; }}\n"
    # Write files
    try:
        with open(HTML_OUTPUT_FILENAME, "w") as f_html: f_html.write(html_content)
        print(f"Successfully generated '{HTML_OUTPUT_FILENAME}'")
        with open(CSS_OUTPUT_FILENAME, "w") as f_css: f_css.write(css_content)
        print(f"Successfully generated '{CSS_OUTPUT_FILENAME}'")
    except IOError as e: print(f"Error writing output files: {e}")

# === Main Script Execution ===
if __name__ == "__main__":
    # --- Argument Parsing Setup ---
    parser = argparse.ArgumentParser(description='Detect checkbox locations in an image and generate HTML/CSS overlay.')
    parser.add_argument('image_filename', help='Path to the input image file (e.g., rom-star-eagle.png)')
    args = parser.parse_args()

    # --- Use parsed filename ---
    IMAGE_PATH = args.image_filename
    BG_IMG_FILENAME = os.path.basename(IMAGE_PATH) # Get just filename for CSS
    IMG_NO_EXT = get_basename_no_extension(IMAGE_PATH)
    CSS_OUTPUT_FILENAME = IMG_NO_EXT + ".css"
    HTML_OUTPUT_FILENAME = IMG_NO_EXT + ".html"
    VIZ_OUTPUT_FILENAME = IMG_NO_EXT + "_viz.png"

    try:
        print(f"----------['{IMAGE_PATH}']----------")
        # 1. Load Image
        img = cv2.imread(IMAGE_PATH)
        if img is None: raise FileNotFoundError(f"Image not found at {IMAGE_PATH}")
        height, width = img.shape[:2]
        print(f"Loaded image '{IMAGE_PATH}' ({width}px x {height}px)")

        # 2. Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, THRESH_BLOCK_SIZE, THRESH_C)

        # 3. Find Contours & 4. Filter Contours (Combined loop)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        detected_boxes = []
        output_img = img.copy()
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, APPROX_POLY_EPSILON * perimeter, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                area = cv2.contourArea(contour)
                aspect_ratio = float(w) / h if h != 0 else 0
                if MIN_AREA <= area <= MAX_AREA and \
                   abs(aspect_ratio - 1.0) <= ASPECT_RATIO_TOL and \
                   cv2.isContourConvex(approx):
                    detected_boxes.append((x, y, w, h))
                    cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 1)

        # 5. Refine / Deduplicate
        if detected_boxes:
            points = np.array([(b[0] + b[2]//2, b[1] + b[3]//2) for b in detected_boxes])
            unique_boxes_indices = []
            used = np.zeros(len(points), dtype=bool)
            for i in range(len(points)):
                if not used[i]:
                    unique_boxes_indices.append(i)
                    used[i] = True
                    for j in range(i + 1, len(points)):
                        if not used[j]:
                            dist_sq = np.sum((points[i] - points[j])**2)
                            if dist_sq < MIN_DIST_SQ_DEDUP: used[j] = True
            final_boxes = [detected_boxes[i] for i in unique_boxes_indices]
            final_boxes.sort(key=lambda b: (b[1], b[0]))
        else: final_boxes = []

        # 6. Output Info & Generate Files
        print(f"Found {len(final_boxes)} potential boxes after filtering and de-duplication.")
        generate_files_relative(BG_IMG_FILENAME, final_boxes, width, height) # Pass necessary info
        if final_boxes:
            cv2.imwrite(VIZ_OUTPUT_FILENAME, output_img)
            print(f"\nVisualization saved to '{VIZ_OUTPUT_FILENAME}'")
        else:
            cv2.imwrite("debug_threshold.png", thresh)
            print("\nNo boxes found. Saved thresholded image to 'debug_threshold.png'.")

        print(f"")
    except ImportError: print("Error: OpenCV or NumPy not found. pip install opencv-python numpy")
    except FileNotFoundError as e: print(e)
    except Exception as e: print(f"An error occurred: {e}")
