#!/usr/bin/env python3
import cv2
import numpy as np
import os
import argparse

# --- Parameters to Tune ---
THRESH_BLOCK_SIZE = 15
THRESH_C = 5
MIN_AREA = 100
MAX_AREA = 250
ASPECT_RATIO_TOL = 0.25
APPROX_POLY_EPSILON = 0.04
MIN_DIST_SQ_DEDUP = (10**2)
BOX_SIZE_PX = 16
# --- End Parameters ---

def generate_files_relative(html_path, css_path, css_filename, bg_filename, final_boxes, img_width, img_height, title):
    """Generates the HTML and CSS files with one master group using px."""
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
    <title>{title}</title>
    <link rel="stylesheet" href="css/{css_filename}">
</head>
<body>
<div id="ship-diagram">
    <div id="checkbox-master-group">
"""
    for i, (x, y, w, h) in enumerate(final_boxes):
        box_id = f"box{i+1}"
        html_content += f'        <input type="checkbox" id="{box_id}" title="{box_id}: x={x}px, y={y}px">\n'
    html_content += "    </div> </div> </body></html>"
    # --- Generate CSS ---
    css_content = f"""/* Auto-generated CSS - Relative Group (px units) */
body {{ font-family: sans-serif; }}
#ship-diagram {{
    position: relative; width: {img_width}px; height: {img_height}px; margin: 20px;
    background-image: url('../images/{bg_filename}');
    background-repeat: no-repeat; background-size: contain;
    border: 1px solid #ccc; /* Optional */
}}
 #checkbox-master-group input[type="checkbox"] {{
     position: absolute; width: {BOX_SIZE_PX}px; height: {BOX_SIZE_PX}px;
     margin: 0; padding: 0; cursor: pointer; box-sizing: border-box;
    appearance: none; -webkit-appearance: none;
    border: 1px solid rgba(128, 128, 128, 0.5);
    }}
 #checkbox-master-group input[type="checkbox"]:not(:checked) {{
    appearance: none; -webkit-appearance: none;
    border: 1px solid rgba(0, 255, 0, .5); background-color: transparent; opacity: 1;
 }}
 #checkbox-master-group input[type="checkbox"]:checked {{
   background-color: rgba(255, 0, 0, 0.5); /* Translucent red */
   border: 1px solid rgba(255, 0, 0, 1); /* Solid red border */
 }}

#checkbox-master-group {{
    position: absolute; top: {min_y}px; left: {min_x}px; position: relative;
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
        with open(html_path, "w") as f_html: f_html.write(html_content)
        print(f"Successfully generated '{html_path}'")
        with open(css_path, "w") as f_css: f_css.write(css_content)
        print(f"Successfully generated '{css_path}'")
    except IOError as e:
        print(f"Error writing output files: {e}")

# === Main Script Execution ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Detect checkbox locations in an image and generate HTML/CSS overlay.')
    parser.add_argument('image_filename', help='Path to the input image file (e.g., SSDs/FEDERATION/ship.png)')
    args = parser.parse_args()

    IMAGE_PATH = args.image_filename

    try:
        print(f"----------['{IMAGE_PATH}']----------")
        
        # 1. Define paths and filenames
        base_path_no_ext, _ = os.path.splitext(IMAGE_PATH)
        
        html_output_path = base_path_no_ext + ".html"
        css_output_path = base_path_no_ext + ".css"
        
        # Basenames for use inside the files
        bg_img_filename_for_css = os.path.basename(IMAGE_PATH)
        css_filename_for_html = os.path.basename(css_output_path)
        title = os.path.basename(base_path_no_ext)

        # 2. Load Image
        img = cv2.imread(IMAGE_PATH)
        if img is None:
            raise FileNotFoundError(f"Image not found at {IMAGE_PATH}")
        height, width = img.shape[:2]
        print(f"Loaded image '{IMAGE_PATH}' ({width}px x {height}px)")

        # 3. Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, THRESH_BLOCK_SIZE, THRESH_C)

        # 4. Find and Filter Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        detected_boxes = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, APPROX_POLY_EPSILON * perimeter, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                area = cv2.contourArea(contour)
                aspect_ratio = float(w) / h if h != 0 else 0
                if MIN_AREA <= area <= MAX_AREA and abs(aspect_ratio - 1.0) <= ASPECT_RATIO_TOL and cv2.isContourConvex(approx):
                    detected_boxes.append((x, y, w, h))

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
                        if not used[j] and np.sum((points[i] - points[j])**2) < MIN_DIST_SQ_DEDUP:
                            used[j] = True
            final_boxes = [detected_boxes[i] for i in unique_boxes_indices]
            final_boxes.sort(key=lambda b: (b[1], b[0]))
        else:
            final_boxes = []

        # 6. Output Info & Generate Files
        print(f"Found {len(final_boxes)} potential boxes after filtering and de-duplication.")
        generate_files_relative(
            html_path=html_output_path,
            css_path=css_output_path,
            css_filename=css_filename_for_html,
            bg_filename=bg_img_filename_for_css,
            final_boxes=final_boxes,
            img_width=width,
            img_height=height,
            title=title
        )
        if final_boxes:
            print("Boxes found and saved to CSS/HTML files.")
        else:
            # No need to write debug_threshold.png if no boxes are found in production
            print("\nNo boxes found. No files generated.")

        print(f"")
    except ImportError:
        print("Error: OpenCV or NumPy not found. Please run 'pip install opencv-python numpy'")
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
