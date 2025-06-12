import sys
import argparse
import time
import selenium
import os
import random
import tldextract
import urllib3
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

parser = argparse.ArgumentParser(description="Load URLs and execute JS with Selenium.")
parser.add_argument("--url_list", required=True, help="Text file with URLs (one per line).")
parser.add_argument("--script_folder", required=True, help="Folder with per-domain main.js scripts.")
parser.add_argument("--sleep_seconds", type=int, default=300, help="Sleep time between pages.")
parser.add_argument("--loop", action="store_true", help="Loop through the URL list endlessly.")
parser.add_argument("--loop_sleep", type=int, default=60, help="Sleep between loops (only with --loop).")
parser.add_argument("--show_browser", action="store_true", help="Show browser window (disable headless mode).")
parser.add_argument("--url_shuffle", action="store_true", help="Activates URL shuffling.")
parser.add_argument("--max_visit_time", type=int, default=300, help="Max time to stay on a page in seconds.")
parser.add_argument("--mute", action="store_true", help="Mute browser audio.")
parser.add_argument("--scroll_chance", type=float, default=0.1, help="Chance (0 to 1) that scrolling happens randomly.")

args = parser.parse_args()

def realistic_user_interaction(driver, duration_seconds, scroll_chance=0.3):
    end_time = time.time() + duration_seconds
    actions = ActionChains(driver)
    
    while time.time() < end_time:
        # Zufällig Page Up oder Page Down drücken
        if random.random() < scroll_chance:
            key = random.choice([Keys.PAGE_DOWN, Keys.PAGE_UP])
            actions.send_keys(key).perform()
            print(f"Pressed {key}")
            time.sleep(random.uniform(0.5, 1.5))
        else:
            # Optional: Wartezeit ohne Aktion, um es realistischer zu machen
            time.sleep(random.uniform(0.5, 2))

def get_root_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

def read_urls_from_file():
    with open(args.url_list, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def get_hostname(url):
    parsed = urlparse(url if "://" in url else "https://" + url)
    hostname = parsed.hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname

def get_script_for_url(url):
    hostname = get_root_domain(url)
    script_path = os.path.join(args.script_folder, hostname, "main.js")
    if not os.path.isfile(script_path):
        print(f"⚠️  Script not found for {hostname}: {script_path}")
        return None
    with open(script_path, 'r') as f:
        contents = f.read()

        base_contents = """
var statusBox = document.createElement('div');
statusBox.style.position = 'fixed';
statusBox.style.top = '0';
statusBox.style.left = '0';
statusBox.style.right = '0';
statusBox.style.backgroundColor = '#333';
statusBox.style.color = '#fff';
statusBox.style.padding = '10px';
statusBox.style.fontFamily = 'sans-serif';
statusBox.style.fontSize = '14px';
statusBox.style.zIndex = '9999';
statusBox.style.textAlign = 'center';
statusBox.textContent = 'Initialisiere...';
document.body.appendChild(statusBox);

function updateStatus(msg) {
    statusBox.textContent = msg;
}

function sleep(ms) {
    updateStatus(`Warte ${ms} Millisekunden`);
    return new Promise(resolve => setTimeout(resolve, ms));
}
"""

        return base_contents + contents

def create_browser():
    options = Options()
    if not args.show_browser:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")

    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    if args.mute:
        options.add_argument("--mute-audio")

    return webdriver.Chrome(options=options)

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def process_url(driver, url):
    print(f"\n--- Loading URL: {url} ---")
    js_code = get_script_for_url(url)
    if js_code is None:
        print("Skipping (no JS found)...\n")
        return

    try:
        driver.get(url if url.startswith("http") else "https://" + url)

        wait_for_page_load(driver)

        print("Page loaded. Clicking somewhere to enable user input...")

        # Alternative: Klick in die Mitte des Viewports
        try:
            width = driver.execute_script("return window.innerWidth")
            height = driver.execute_script("return window.innerHeight")
            actions = ActionChains(driver)
            actions.move_by_offset(width // 2, height // 2).click().perform()
        except Exception as e:
            print(f"❌ Failed to click even at safe location: {e}")

        print("Clicked somewhere. Executing JavaScript...")
        result = driver.execute_script(js_code)

        print("Starting realistic user interaction")
        realistic_user_interaction(driver, duration_seconds=args.sleep_seconds)

        print("JS executed. Result:", result)
        print(f"Sleeping for {args.sleep_seconds} seconds...\n")
        time.sleep(min(args.sleep_seconds, args.max_visit_time))
    except selenium.common.exceptions.WebDriverException as e:
        print(f"⚠️  WebDriver error for {url}: {e}")

def main():
    if args.loop:
        print("🔁 Loop mode active. Press Ctrl+C to stop.")

    while True:
        urls = read_urls_from_file()
        if not urls:
            print("No URLs found. Exiting." if not args.loop else "No URLs found. Waiting before retry...")
            if not args.loop:
                break
            time.sleep(args.loop_sleep)
            continue

        driver = create_browser()

        try:
            if args.url_shuffle:
                random.shuffle(urls)

            for url in urls:
                try:
                    process_url(driver, url)
                except urllib3.exceptions.ProtocolError as e:
                    print(f"Error while trying to process URL {url}: {e}. Trying to restart browser...")
                    driver = create_browser()
        finally:
            driver.quit()
            print("Browser closed.")

        if not args.loop:
            break
        else:
            print(f"Loop complete. Sleeping for {args.loop_sleep} seconds before next round...\n")
            time.sleep(args.loop_sleep)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("You cancelled via CTRL-c")
        sys.exit(0)
