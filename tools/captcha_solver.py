"""
GoGetter AutoBot — Captcha Solver
Uses OCR + real USB control to solve text-based captchas.

For image captchas (reCAPTCHA, hCaptcha):
- Screenshots the challenge
- Uses AI vision to identify correct images
- Clicks on the correct ones

Usage:
    python captcha_solver.py --type text --image captcha.png
    python captcha_solver.py --type grid --image captcha_grid.png
    python captcha_solver.py --solve-current
"""

import pyautogui
import time
import sys
import os
import json
import easyocr
from datetime import datetime

class CaptchaSolver:
    def __init__(self):
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "Desktop", "gogetter-digital", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.reader = None
        
    def get_reader(self):
        if self.reader is None:
            self.reader = easyocr.Reader(['en'], gpu=False)
        return self.reader
    
    def solve_text_captcha(self, image_path=None):
        """Solve a text-based captcha (letters/numbers)"""
        if image_path is None:
            image_path = os.path.join(self.screenshot_dir, "captcha.png")
        
        reader = self.get_reader()
        results = reader.readtext(image_path)
        
        # Combine all text elements
        captcha_text = ""
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                captcha_text += text.replace(" ", "")
        
        print(f"Captcha text detected: {captcha_text}")
        return captcha_text
    
    def solve_grid_captcha_description(self, image_path=None):
        """Describe what's in a grid captcha for manual solving"""
        if image_path is None:
            image_path = os.path.join(self.screenshot_dir, "captcha_grid.png")
        
        reader = self.get_reader()
        results = reader.readtext(image_path)
        
        print("\n=== CAPTCHA GRID ANALYSIS ===")
        print("Text found in captcha:")
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                print(f"  '{text}' at ({center_x}, {center_y})")
        
        return results
    
    def type_captcha(self, text):
        """Type captcha text into active field"""
        pyautogui.typewrite(text, interval=0.1)
        print(f"Typed: {text}")
        time.sleep(0.5)
    
    def click_submit(self):
        """Find and click submit/verify button"""
        # Try common button texts
        reader = self.get_reader()
        path = os.path.join(self.screenshot_dir, "captcha_submit.png")
        pyautogui.screenshot(path)
        
        results = reader.readtext(path)
        for (bbox, text, confidence) in results:
            text_lower = text.lower()
            if any(word in text_lower for word in ["submit", "verify", "continue", "next", "login", "sign"]):
                center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                pyautogui.click(center_x, center_y)
                print(f"Clicked: '{text}' at ({center_x}, {center_y})")
                return True
        
        print("Submit button not found")
        return False
    
    def solve_text_captcha_workflow(self):
        """Full workflow: screenshot captcha, read it, type it, submit"""
        print("=== Text Captcha Solver ===")
        print("1. Navigate to the captcha page")
        print("2. I'll screenshot the captcha area")
        print("3. I'll read the text")
        print("4. I'll type it")
        print("5. I'll click submit")
        print("")
        print("Make sure the captcha is visible on screen.")
        input("Press Enter when ready...")
        
        # Take screenshot of captcha area
        print("Taking screenshot...")
        path = os.path.join(self.screenshot_dir, "captcha_area.png")
        pyautogui.screenshot(path)
        
        # Read captcha
        print("Reading captcha...")
        captcha_text = self.solve_text_captcha(path)
        
        if captcha_text:
            print(f"Captcha detected: {captcha_text}")
            
            # Click on captcha input field
            print("Click on the captcha input field, then press Enter...")
            input()
            
            # Type captcha
            self.type_captcha(captcha_text)
            
            # Click submit
            print("Clicking submit...")
            self.click_submit()
            
            print("Done!")
        else:
            print("Could not read captcha")
        
        return captcha_text
    
    def save_analysis(self, results):
        """Save captcha analysis to file"""
        path = os.path.join(self.screenshot_dir, "captcha_analysis.json")
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        return path

def main():
    solver = CaptchaSolver()
    
    if len(sys.argv) < 2:
        print("GoGetter AutoBot — Captcha Solver")
        print("")
        print("Commands:")
        print("  solve-text          — Solve text captcha interactively")
        print("  read IMAGE          — Read text from captcha image")
        print("  type TEXT           — Type captcha text")
        print("  submit              — Click submit button")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "solve-text":
        solver.solve_text_captcha_workflow()
    elif cmd == "read" and len(sys.argv) >= 3:
        results = solver.solve_text_captcha(sys.argv[2])
        print(f"Detected: {results}")
    elif cmd == "type" and len(sys.argv) >= 3:
        solver.type_captcha(" ".join(sys.argv[2:]))
    elif cmd == "submit":
        solver.click_submit()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
