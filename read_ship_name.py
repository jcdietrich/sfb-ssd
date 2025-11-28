import pytesseract
from PIL import Image
import cv2
import numpy as np

def ocr_image_region_processed(image_path, crop_box):
    """
    Performs OCR on a specific region of an image after pre-processing and returns the extracted text.
    """
    try:
        img = cv2.imread(image_path)
        
        # Crop the image
        cropped_img = img[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]

        # Pre-processing
        gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Find contours and filter by area
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create a mask to draw the filtered contours
        mask = np.zeros(cropped_img.shape[:2], dtype="uint8")

        # Define a minimum area threshold
        min_area = 20 # This value might need tuning

        for c in contours:
            if cv2.contourArea(c) > min_area:
                cv2.drawContours(mask, [c], -1, (255), -1)

        # Invert the mask back to black text on white background
        mask = 255 - mask

        # Convert back to PIL image for pytesseract
        pil_img = Image.fromarray(mask)

        # OCR with custom configuration
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(pil_img, config=custom_config)
        
        return text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    image_path = "inverted_images/ssd-003.png"
    # Crop box for the top-right quadrant (left, top, right, bottom)
    crop_box = (499, 0, 998, 274)
    extracted_text = ocr_image_region_processed(image_path, crop_box)
    print(f"Extracted text from the top-right of '{image_path}' (processed):\n---\n{extracted_text}\n---")
