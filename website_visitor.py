import argparse
import time
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Load URLs and execute JS with Selenium.")
    parser.add_argument("--url_list", required=True, help="Path to text file with URLs (one per line).")
    parser.add_argument("--js_script", required=True, help="Path to JavaScript file to execute.")
    parser.add_argument("--sleep_seconds", type=int, default=300, help="Sleep time between pages. Default: 300s.")
    parser.add_argument("--loop", action="store_true", help="Loop through the URL list endlessly.")
    parser.add_argument("--loop_sleep", type=int, default=60, help="Sleep time between loops (only with --loop). Default: 60s.")
    parser.add_argument("--show_browser", action="store_true", help="Show the browser window (disable headless mode).")
    return parser.parse_args()

def read_urls_from_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def read_js_script(path):
    with open(path, 'r') as f:
        return f.read()

def normalize_url(url):
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url

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

def execute_js(driver, script):
    return driver.execute_script(script)

def process_url(driver, url, js_code, sleep_seconds):
    normalized_url = normalize_url(url)
    print(f"\n--- Loading URL: {normalized_url} ---")
    try:
        driver.get(normalized_url)
        wait_for_page_load(driver)
        print("Page loaded. Executing JavaScript...")
        result = execute_js(driver, js_code)
        print("JS executed. Result:", result)
        print(f"Sleeping for {sleep_seconds} seconds...\n")
        time.sleep(sleep_seconds)
    except selenium.common.exceptions.InvalidArgumentException as e:
        print(f"Error: {e}. This can happen for wrong URLs in the --url_list file")

def main():
    args = parse_arguments()
    js_code = read_js_script(args.js_script)

    if args.loop:
        print("Running in loop mode. Press Ctrl+C to stop.")
    
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
                process_url(driver, url, js_code, args.sleep_seconds)
        finally:
            driver.quit()
            print("Browser closed.")

        if not args.loop:
            break
        else:
            print(f"Loop complete. Sleeping for {args.loop_sleep} seconds before next round...\n")
            time.sleep(args.loop_sleep)

if __name__ == "__main__":
    main()
