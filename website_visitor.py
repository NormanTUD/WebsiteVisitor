import argparse
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Load URLs and execute JS with Selenium.")
    parser.add_argument("--url_list", required=True, help="Path to text file with URLs (one per line).")
    parser.add_argument("--js_script", required=True, help="Path to JavaScript file to execute.")
    parser.add_argument("--sleep_seconds", type=int, default=300, help="Sleep time between pages in seconds. Default: 300 (5 minutes).")
    return parser.parse_args()

def read_urls_from_file(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def read_js_script(path):
    with open(path, 'r') as f:
        return f.read()

def create_browser():
    options = Options()
    options.add_argument("--headless")  # remove if you want to see the browser
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    return driver

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def execute_js(driver, script):
    return driver.execute_script(script)

def process_url(driver, url, js_code, sleep_seconds):
    print(f"\n--- Loading URL: {url} ---")
    driver.get(url)
    wait_for_page_load(driver)
    print("Page loaded. Executing JavaScript...")
    result = execute_js(driver, js_code)
    print("JS executed. Result:", result)
    print(f"Sleeping for {sleep_seconds} seconds...\n")
    time.sleep(sleep_seconds)

def main():
    args = parse_arguments()
    urls = read_urls_from_file(args.url_list)
    js_code = read_js_script(args.js_script)

    driver = create_browser()

    try:
        for url in urls:
            process_url(driver, url, js_code, args.sleep_seconds)
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
