"""
GoGetter AutoBot v2 — Real USB Mouse, Keyboard + OCR
Takes over actual USB hardware, reads screen, finds jobs.

Capabilities:
- Screenshot and map screen elements
- Click by coordinates (real USB mouse)
- Type text (real USB keyboard)
- OCR — read text from screenshots
- Find jobs on social media
- Navigate and interact with websites

Usage:
    python autobot.py screenshot
    python autobot.py click 500 300
    python autobot.py type "Hello world"
    python autobot.py ocr
    python autobot.py find-text "jobs"
    python autobot.py facebook-jobs
    python autobot.py scan-screen
"""

import pyautogui
import time
import sys
import os
import json
import easyocr
from datetime import datetime

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

class GoGetterAutoBot:
    def __init__(self):
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "Desktop", "gogetter-digital", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.action_log = []
        self.reader = None
        
    def get_reader(self):
        if self.reader is None:
            print("Loading OCR model (first time takes a moment)...")
            self.reader = easyocr.Reader(['en'], gpu=False)
        return self.reader
    
    def log(self, action, details=""):
        entry = {"time": datetime.now().isoformat(), "action": action, "details": details}
        self.action_log.append(entry)
        print(f"[{entry['time'][11:19]}] {action}: {details}")
    
    def screenshot(self, name=None):
        if not name:
            name = f"screen_{datetime.now().strftime('%H%M%S')}"
        path = os.path.join(self.screenshot_dir, f"{name}.png")
        pyautogui.screenshot(path)
        self.log("screenshot", path)
        return path
    
    def click(self, x, y, clicks=1):
        pyautogui.click(x, y, clicks=clicks)
        self.log("click", f"({x}, {y})")
        time.sleep(0.5)
    
    def double_click(self, x, y):
        pyautogui.doubleClick(x, y)
        self.log("double_click", f"({x}, {y})")
        time.sleep(0.5)
    
    def type_text(self, text, interval=0.05):
        pyautogui.typewrite(text, interval=interval)
        self.log("type", text[:50])
        time.sleep(0.3)
    
    def press_key(self, key):
        pyautogui.press(key)
        self.log("press_key", key)
        time.sleep(0.2)
    
    def hotkey(self, *keys):
        pyautogui.hotkey(*keys)
        self.log("hotkey", "+".join(keys))
        time.sleep(0.3)
    
    def scroll(self, direction, amount=3):
        if direction == "down":
            pyautogui.scroll(-amount)
        else:
            pyautogui.scroll(amount)
        self.log("scroll", f"{direction} {amount}")
        time.sleep(0.3)

    def wait(self, seconds):
        """Wait for specified seconds"""
        time.sleep(seconds)
        self.log("wait", f"{seconds}s")
    
    def navigate(self, url):
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.5)
        pyautogui.typewrite(url, interval=0.02)
        pyautogui.press("enter")
        self.log("navigate", url)
        time.sleep(3)
    
    def ocr_screen(self, path=None):
        """Read all text from screen using OCR"""
        if path is None:
            path = self.screenshot("ocr_temp")
        
        reader = self.get_reader()
        results = reader.readtext(path)
        
        texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                texts.append({
                    "text": text,
                    "confidence": round(confidence, 2),
                    "x": center_x,
                    "y": center_y,
                    "bbox": [[int(p[0]), int(p[1])] for p in bbox]
                })
        
        self.log("ocr", f"Found {len(texts)} text elements")
        return texts
    
    def find_text(self, target):
        """Find specific text on screen and return coordinates"""
        texts = self.ocr_screen()
        matches = []
        for item in texts:
            if target.lower() in item["text"].lower():
                matches.append(item)
                self.log("found_text", f"'{item['text']}' at ({item['x']}, {item['y']})")
        return matches
    
    def click_text(self, target):
        """Find text on screen and click it"""
        matches = self.find_text(target)
        if matches:
            self.click(matches[0]["x"], matches[0]["y"])
            return True
        self.log("text_not_found", target)
        return False
    
    def scan_screen(self):
        """Take screenshot and read all text"""
        path = self.screenshot("scan")
        texts = self.ocr_screen(path)
        
        print("\n=== SCREEN CONTENT ===")
        for item in texts:
            print(f"  [{item['confidence']}] {item['text']} @ ({item['x']}, {item['y']})")
        print(f"\nTotal: {len(texts)} text elements found")
        
        return texts
    
    def find_job_listings(self):
        """Scan screen for job-related text"""
        texts = self.ocr_screen()
        job_keywords = ["job", "hire", "freelance", "project", "budget", "bid", "proposal", 
                       "work", "remote", "apply", "description", "skills", "experience"]
        
        jobs = []
        for item in texts:
            for keyword in job_keywords:
                if keyword.lower() in item["text"].lower():
                    jobs.append(item)
                    break
        
        if jobs:
            print(f"\n=== JOB-RELATED TEXT FOUND ({len(jobs)}) ===")
            for job in jobs:
                print(f"  {job['text']} @ ({job['x']}, {job['y']})")
        
        return jobs
    
    def facebook_job_search(self):
        """Navigate to Facebook jobs and scan"""
        self.navigate("https://www.facebook.com/marketplace/category/jobs")
        time.sleep(5)
        
        texts = self.scan_screen()
        jobs = self.find_job_listings()
        
        return {"texts": texts, "jobs": jobs}
    
    def save_log(self):
        log_path = os.path.join(self.screenshot_dir, "action_log.json")
        with open(log_path, "w") as f:
            json.dump(self.action_log, f, indent=2)
        self.log("log_saved", log_path)
        return log_path

def main():
    bot = GoGetterAutoBot()
    
    if len(sys.argv) < 2:
        print("GoGetter AutoBot v2 — USB Mouse + Keyboard + OCR")
        print("")
        print("Commands:")
        print("  screenshot              — Take screenshot")
        print("  click X Y               — Click at coordinates")
        print("  type TEXT               — Type text")
        print("  key KEY                 — Press key")
        print("  hotkey KEY1 KEY2        — Key combo")
        print("  scroll DOWN/UP N       — Scroll")
        print("  navigate URL            — Open URL")
        print("  ocr                     — Read all text on screen")
        print("  find-text TEXT          — Find text and get coordinates")
        print("  click-text TEXT         — Find text and click it")
        print("  scan-screen             — Screenshot + OCR everything")
        print("  find-jobs               — Scan for job-related text")
        print("  facebook-jobs           — Search Facebook jobs")
        print("  save-log                — Save action log")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "screenshot":
        bot.screenshot()
    elif cmd == "click" and len(sys.argv) >= 4:
        bot.click(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "type" and len(sys.argv) >= 3:
        bot.type_text(" ".join(sys.argv[2:]))
    elif cmd == "key" and len(sys.argv) >= 3:
        bot.press_key(sys.argv[2])
    elif cmd == "hotkey" and len(sys.argv) >= 3:
        bot.hotkey(*sys.argv[2:])
    elif cmd == "scroll" and len(sys.argv) >= 4:
        bot.scroll(sys.argv[2].lower(), int(sys.argv[3]))
    elif cmd == "navigate" and len(sys.argv) >= 3:
        bot.navigate(sys.argv[2])
    elif cmd == "ocr":
        texts = bot.ocr_screen()
        for t in texts:
            print(f"  [{t['confidence']}] {t['text']} @ ({t['x']}, {t['y']})")
    elif cmd == "find-text" and len(sys.argv) >= 3:
        target = " ".join(sys.argv[2:])
        matches = bot.find_text(target)
        for m in matches:
            print(f"  Found: {m['text']} @ ({m['x']}, {m['y']})")
    elif cmd == "click-text" and len(sys.argv) >= 3:
        target = " ".join(sys.argv[2:])
        bot.click_text(target)
    elif cmd == "scan-screen":
        bot.scan_screen()
    elif cmd == "find-jobs":
        bot.find_job_listings()
    elif cmd == "facebook-jobs":
        bot.facebook_job_search()
    elif cmd == "save-log":
        bot.save_log()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
