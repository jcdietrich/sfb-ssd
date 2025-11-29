#!/usr/bin/env python3
import pytesseract
from PIL import Image
import cv2
import numpy as np
import argparse
import os

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def correct_word(word_to_correct, allowed_dict, forbidden_dict, direct_substitutions, max_distance_ratio=0.4):
    if not word_to_correct:
        return ""
    if word_to_correct.upper() in direct_substitutions:
        return direct_substitutions[word_to_correct.upper()]
    for forbidden_word in forbidden_dict:
        distance = levenshtein_distance(word_to_correct.upper(), forbidden_word.upper())
        if distance <= len(word_to_correct) * max_distance_ratio:
            return ""
    if not allowed_dict:
        return word_to_correct
    best_match = None
    min_distance = float('inf')
    for word in allowed_dict:
        distance = levenshtein_distance(word_to_correct.upper(), word.upper())
        if distance < min_distance:
            min_distance = distance
            best_match = word
    if best_match and min_distance <= len(word_to_correct) * max_distance_ratio:
        return best_match
    else:
        return word_to_correct

def ocr_image_region_processed(image_path, min_area, direct_substitutions):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return f"Error: Image not found at {image_path}", ""
        height, width, _ = img.shape
        crop_box = (int(width * 0.5), 0, width, int(height * 0.4))
        cropped_img = img[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
        gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask = np.zeros(cropped_img.shape[:2], dtype="uint8")
        for c in contours:
            if cv2.contourArea(c) > min_area:
                cv2.drawContours(mask, [c], -1, 255, -1)
        mask = 255 - mask
        pil_img = Image.fromarray(mask)
        custom_config = r'--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(pil_img, config=custom_config)
        
        all_lines = raw_text.split('\n')
        non_empty_lines = [line.strip() for line in all_lines if line.strip()]
        lines_to_process = non_empty_lines[:4]
        
        processed_words_from_lines = []
        for line in lines_to_process:
            words_in_line = line.split()
            for word in words_in_line:
                if word.upper() in direct_substitutions:
                    processed_words_from_lines.extend(direct_substitutions[word.upper()].split())
                    continue
                if any(c.islower() for c in word):
                    continue
                filtered_word = "".join(char for char in word if char.isupper() or char.isdigit() or char == '-')
                if filtered_word:
                    if not filtered_word.isdigit():
                        processed_words_from_lines.append(filtered_word)
        processed_text = " ".join(processed_words_from_lines)
        return raw_text, processed_text
    except Exception as e:
        return str(e), ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract and spellcheck ship names from images.')
    parser.add_argument('input_path', type=str, help='Path to the input image file or directory.')
    parser.add_argument('--min_area', type=int, default=3, help='Minimum contour area for OCR (default: 3).')
    parser.add_argument('--debug', '-d', '-v', action='store_true', help='Enable debug output.')
    parser.add_argument('--vv', action='store_true', help='Enable very verbose output (shows raw OCR text and implies debug).')
    parser.add_argument('--dictionary', '--dict', type=str, default='dictionary.txt', help='Path to a ship name dictionary file for spellchecking (default: dictionary.txt).')
    parser.add_argument('--max_distance_ratio', type=float, default=0.4, help='Maximum Levenshtein distance ratio for a match (default: 0.4).')
    args = parser.parse_args()

    if args.vv:
        args.debug = True

    allowed_words = set()
    forbidden_words = set()
    stop_words = set()
    direct_substitutions = {}
    if args.dictionary:
        try:
            with open(args.dictionary, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('='):
                        parts = line[1:].split('|', 1)
                        if len(parts) == 2:
                            wrong_word, correct_word_sub = parts[0].strip().upper(), parts[1].strip()
                            direct_substitutions[wrong_word] = correct_word_sub
                        else:
                            print(f"Warning: Malformed direct substitution entry in dictionary: {line}")
                    elif line.startswith('!'):
                        forbidden_words.add(line[1:].upper())
                    elif line.startswith('$'):
                        stop_word = line[1:].upper()
                        stop_words.add(stop_word)
                        allowed_words.add(stop_word)
                    else:
                        allowed_words.add(line.upper())
        except FileNotFoundError:
            print(f"Error: Dictionary file not found at {args.dictionary}")
            args.dictionary = None
            print("Running without dictionary features.")

    def get_final_output(original_ocr_text, args):
        if not args.dictionary or not original_ocr_text:
            return original_ocr_text

        original_words = original_ocr_text.split()
        
        if args.dictionary:
            corrected_words = [correct_word(word, allowed_words, forbidden_words, direct_substitutions, args.max_distance_ratio) for word in original_words]
            corrected_words = [word for word in corrected_words if word]
        else:
            corrected_words = original_words

        final_words = []
        for word in corrected_words:
            final_words.append(word)
            if word.upper() in stop_words:
                break
        
        final_corrected_text = " ".join(final_words)
        
        is_corrected = final_corrected_text.upper() != original_ocr_text.upper()
        
        if is_corrected and args.debug:
            return f"{final_corrected_text} (original: {original_ocr_text})"
        else:
            return final_corrected_text

    def process_file(file_path):
        raw_text, extracted_text = ocr_image_region_processed(file_path, args.min_area, direct_substitutions)
        final_output = get_final_output(extracted_text, args)
        if args.vv:
            print(f"--- Raw OCR for {os.path.basename(file_path)} ---\n{raw_text}\n--------------------")
        if os.path.isdir(args.input_path):
            if args.debug:
                print(f"{os.path.basename(file_path)}: {final_output}")
            else:
                print(final_output)
        elif args.debug:
            print(f"Result from '{file_path}' (min_area={args.min_area}):\n---\n{final_output}\n---")
        else:
            print(final_output)

    if os.path.isdir(args.input_path):
        image_files = sorted([f for f in os.listdir(args.input_path) if f.lower().endswith('.png')])
        for filename in image_files:
            file_path = os.path.join(args.input_path, filename)
            process_file(file_path)
    else:
        process_file(args.input_path)
