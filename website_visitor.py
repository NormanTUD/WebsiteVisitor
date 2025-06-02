import sys
import argparse
import time
import selenium
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def parse_arguments():
    parser = argparse.ArgumentParser(description="Load URLs and execute JS with Selenium.")
    parser.add_argument("--url_list", required=True, help="Text file with URLs (one per line).")
    parser.add_argument("--script_folder", required=True, help="Folder with per-domain main.js scripts.")
    parser.add_argument("--sleep_seconds", type=int, default=300, help="Sleep time between pages.")
    parser.add_argument("--loop", action="store_true", help="Loop through the URL list endlessly.")
    parser.add_argument("--loop_sleep", type=int, default=60, help="Sleep between loops (only with --loop).")
    parser.add_argument("--show_browser", action="store_true", help="Show browser window (disable headless mode).")
    parser.add_argument("--max_visit_time", type=int, default=300, help="Max time to stay on a page in seconds.")

    return parser.parse_args()

def read_urls_from_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def get_hostname(url):
    parsed = urlparse(url if "://" in url else "https://" + url)
    hostname = parsed.hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname

def get_script_for_url(script_folder, url):
    hostname = get_hostname(url)
    script_path = os.path.join(script_folder, hostname, "main.js")
    if not os.path.isfile(script_path):
        print(f"⚠️  Script not found for {hostname}: {script_path}")
        return None
    with open(script_path, 'r') as f:
        return f.read()

def create_browser(show_browser):
    options = Options()
    if not show_browser:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def process_url(driver, url, script_folder, sleep_seconds, max_visit_time):
    print(f"\n--- Loading URL: {url} ---")
    js_code = get_script_for_url(script_folder, url)
    if js_code is None:
        print("Skipping (no JS found)...\n")
        return

    try:
        driver.get(url if url.startswith("http") else "https://" + url)


        wait_for_page_load(driver)


        print("Page loaded. Clicking somewhere to enable user input...")
        ActionChains(driver).move_by_offset(10, 10).click().perform()

        print("Clicked somewhere. Executing JavaScript...")
        result = driver.execute_script(js_code)
        print("JS executed. Result:", result)
        print(f"Sleeping for {sleep_seconds} seconds...\n")
        time.sleep(min(sleep_seconds, max_visit_time))
    except selenium.common.exceptions.WebDriverException as e:
        print(f"⚠️  WebDriver error for {url}: {e}")

def main():
    args = parse_arguments()

    if args.loop:
        print("🔁 Loop mode active. Press Ctrl+C to stop.")

    while True:
        urls = read_urls_from_file(args.url_list)
        if not urls:
            print("No URLs found. Exiting." if not args.loop else "No URLs found. Waiting before retry...")
            if not args.loop:
                break
            time.sleep(args.loop_sleep)
            continue

        driver = create_browser(args.show_browser)
        try:
            for url in urls:
                process_url(driver, url, args.script_folder, args.sleep_seconds, args.max_visit_time)
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
