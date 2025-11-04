#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import time
import os
import random
import tldextract
import urllib3
import socket
import logging
import traceback

from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    JavascriptException,
    NoSuchElementException,
    MoveTargetOutOfBoundsException,
)

# ----------------------------
# Argument parsing
# ----------------------------
parser = argparse.ArgumentParser(description="Load URLs and execute JS with Selenium (robust edition).")
parser.add_argument("--url_list", required=True, help="Text file with URLs (one per line).")
parser.add_argument("--script_folder", required=True, help="Folder with per-domain main.js scripts.")
parser.add_argument("--sleep_seconds", type=int, default=300, help="Sleep time (seconds) spent on page for interaction.")
parser.add_argument("--loop", action="store_true", help="Loop through the URL list endlessly.")
parser.add_argument("--loop_sleep", type=int, default=60, help="Sleep between loops (only with --loop).")
parser.add_argument("--show_browser", action="store_true", help="Show browser window (disable headless mode).")
parser.add_argument("--url_shuffle", action="store_true", help="Activate URL shuffling.")
parser.add_argument("--max_visit_time", type=int, default=300, help="Max time to stay on a page in seconds.")
parser.add_argument("--mute", action="store_true", help="Mute browser audio.")
parser.add_argument("--scroll_chance", type=float, default=0.1, help="Chance (0 to 1) that scrolling happens randomly.")
parser.add_argument("--scroll_min_random_time", type=float, default=0.5, help="Min random time for random scrolling.")
parser.add_argument("--scroll_max_random_time", type=float, default=2, help="Max random time for random scrolling.")
parser.add_argument("--max_retries", type=int, default=2, help="Max retries per URL before skipping.")
parser.add_argument("--retry_backoff", type=float, default=3.0, help="Seconds to wait before retrying after a failure.")
parser.add_argument("--log_file", default="website_visitor.log", help="Path to log file.")

args = parser.parse_args()

# ----------------------------
# Logging setup
# ----------------------------
logger = logging.getLogger("website_visitor")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

# console
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# file
fh = logging.FileHandler(args.log_file)
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# ----------------------------
# Utility functions
# ----------------------------
def read_urls_from_file():
    if not os.path.isfile(args.url_list):
        logger.error("URL list file does not exist: %s", args.url_list)
        return []
    with open(args.url_list, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    logger.debug("Loaded %d URLs from %s", len(lines), args.url_list)
    return lines

def get_root_domain(url):
    ext = tldextract.extract(url)
    if not ext.suffix:
        # fallback to hostname parser
        parsed = urlparse(url if "://" in url else "https://" + url)
        hostname = parsed.hostname or ""
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname
    return f"{ext.domain}.{ext.suffix}"

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
        logger.warning("Script not found for %s: %s", hostname, script_path)
        return None
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            contents = f.read()
    except Exception as e:
        logger.exception("Failed to read script for %s: %s", hostname, e)
        return None

    # base UI + helpers injected before per-domain script
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
statusBox.style.textAlign = 'left';
statusBox.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.5)';
document.body.appendChild(statusBox);

var statusHeader = document.createElement('div');
statusHeader.style.display = 'flex';
statusHeader.style.justifyContent = 'space-between';
statusHeader.style.alignItems = 'center';

var statusText = document.createElement('span');
statusText.textContent = 'Initialisiere...';

var toggleButton = document.createElement('span');
toggleButton.textContent = '\\u25BC';
toggleButton.style.cursor = 'pointer';
toggleButton.style.marginLeft = '10px';
toggleButton.style.userSelect = 'none';

statusHeader.appendChild(statusText);
statusHeader.appendChild(toggleButton);
statusBox.appendChild(statusHeader);

var statusLog = document.createElement('div');
statusLog.style.display = 'none';
statusLog.style.marginTop = '10px';
statusLog.style.maxHeight = '150px';
statusLog.style.overflowY = 'auto';
statusLog.style.borderTop = '1px solid #555';
statusLog.style.paddingTop = '5px';
statusBox.appendChild(statusLog);

var isOpen = false;
toggleButton.onclick = function () {
    isOpen = !isOpen;
    statusLog.style.display = isOpen ? 'block' : 'none';
    toggleButton.textContent = isOpen ? '\\u25B2' : '\\u25BC';
};

function updateStatus(msg) {
    try {
        const time = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.textContent = '[' + time + '] ' + msg;
        statusLog.prepend(logEntry);
        statusText.textContent = msg;
    } catch (e) {
        // ignore errors in injected status UI
    }
}

function sleep(ms) {
    updateStatus('Warte ' + ms + ' Millisekunden');
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function sleepRandomly(minMs, maxMs) {
    const randomMs = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
    await sleep(randomMs);
}
"""
    return base_contents + contents

# ----------------------------
# Browser creation and helpers
# ----------------------------
def create_browser_attempt(attempt=1, max_attempts=3):
    logger.info("Creating Chrome WebDriver (attempt %d/%d)...", attempt, max_attempts)
    options = Options()
    if not args.show_browser:
        # headless newer Chrome requires --headless=new in some versions, but keep generic
        options.add_argument("--headless=new")  # try new headless; if unsupported, fallback below
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-certificate-errors-spki-list")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--log-level=3")
    # optional mute
    if args.mute:
        options.add_argument("--mute-audio")

    # try to create driver
    try:
        driver = webdriver.Chrome(options=options)
        # configure timeouts
        try:
            driver.set_page_load_timeout(args.max_visit_time)
        except Exception:
            # older/newer selenium might raise; ignore if not supported
            pass
        try:
            driver.set_script_timeout(args.max_visit_time)
        except Exception:
            pass
        logger.info("WebDriver created successfully.")
        return driver
    except Exception as e:
        logger.exception("Failed to create WebDriver on attempt %d: %s", attempt, e)
        # small backoff before reattempting
        if attempt < max_attempts:
            wait = 1 + attempt * 2
            logger.info("Waiting %s seconds before retrying WebDriver creation...", wait)
            time.sleep(wait)
            return create_browser_attempt(attempt + 1, max_attempts)
        raise

# ----------------------------
# Wait for page load helper (resilient)
# ----------------------------
def wait_for_page_load(driver, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        logger.debug("Document.readyState not 'complete' after %d seconds (continuing).", timeout)
    except WebDriverException as e:
        logger.debug("WebDriverException while waiting for page load: %s", e)

# ----------------------------
# Realistic interaction (resilient)
# ----------------------------
def realistic_user_interaction(driver, duration_seconds, scroll_chance=None):
    if scroll_chance is None:
        scroll_chance = args.scroll_chance
    end_time = time.time() + duration_seconds
    try:
        actions = ActionChains(driver)
        # get body element for safe move_to_element_with_offset
        try:
            body = driver.find_element(By.TAG_NAME, "body")
        except Exception:
            body = None

        while time.time() < end_time:
            if random.random() < scroll_chance:
                try:
                    key = random.choice([Keys.PAGE_DOWN, Keys.PAGE_UP])
                    # use actions on body if available, else send_keys directly
                    if body is not None:
                        actions.move_to_element_with_offset(body, 1, 1).send_keys(key).perform()
                    else:
                        actions.send_keys(key).perform()
                    logger.debug("Pressed %s during interaction", "PAGE_DOWN" if key == Keys.PAGE_DOWN else "PAGE_UP")
                except MoveTargetOutOfBoundsException:
                    try:
                        actions = ActionChains(driver)  # reset and try direct send
                        actions.send_keys(key).perform()
                        logger.debug("Fallback: direct send_keys after MoveTargetOutOfBoundsException")
                    except Exception as e:
                        logger.debug("Failed to send key during realistic interaction: %s", e)
            # random short sleep
            try:
                time.sleep(random.uniform(args.scroll_min_random_time, args.scroll_max_random_time))
            except Exception:
                # guard against weird interruptions
                time.sleep(0.5)
    except Exception as e:
        # don't crash the main flow if interactions fail
        logger.debug("realistic_user_interaction error: %s", e)

# ----------------------------
# Process single URL with retries and safe failure modes
# ----------------------------
def process_url(driver, url):
    """
    Returns:
      None -> success (or skipped due to missing script)
      "restart" -> caller should restart the browser (driver has been quit)
      "skip" -> skip this URL (non-recoverable or file missing)
    """
    logger.info("Loading URL: %s", url)
    js_code = get_script_for_url(url)
    if js_code is None:
        logger.info("No JS for %s -> skipping.", url)
        return None

    try:
        # ensure scheme
        full_url = url if url.startswith("http://") or url.startswith("https://") else "https://" + url
        logger.debug("Navigating to %s", full_url)
        try:
            driver.get(full_url)
        except Exception as e:
            # log and re-raise to be handled below
            logger.warning("driver.get raised: %s", e)
            raise

        wait_for_page_load(driver, timeout=min(30, args.max_visit_time))

        logger.info("Page loaded for %s. Attempting safe click to enable input.", url)
        try:
            width = driver.execute_script("return window.innerWidth") or 800
            height = driver.execute_script("return window.innerHeight") or 600
            body = None
            try:
                body = driver.find_element(By.TAG_NAME, "body")
            except Exception:
                body = None
            actions = ActionChains(driver)
            if body is not None:
                # center-ish click relative to body
                try:
                    actions.move_to_element_with_offset(body, int(width / 2) - 1, int(height / 2) - 1).click().perform()
                except Exception:
                    # fallback: send a SPACE key to focus
                    actions.send_keys(Keys.SPACE).perform()
            else:
                actions.move_by_offset(int(width / 2), int(height / 2)).click().perform()
        except Exception as e:
            logger.debug("Safe click failed: %s", e)

        logger.info("Executing injected JavaScript on %s", url)
        try:
            result = driver.execute_script(js_code)
            logger.debug("Script execution returned: %s", result)
        except JavascriptException as e:
            logger.warning("JavascriptException while executing script on %s: %s", url, e)
        except Exception as e:
            logger.warning("Exception while executing script on %s: %s", url, e)

        # run interaction for configured sleep_seconds but never exceed max_visit_time
        visit_time = min(args.sleep_seconds, args.max_visit_time)
        logger.info("Starting realistic user interaction for ~%d seconds", visit_time)
        realistic_user_interaction(driver, duration_seconds=visit_time, scroll_chance=args.scroll_chance)

        # final sleep guard to make sure we respect max_visit_time
        extra_sleep = max(0, args.sleep_seconds - visit_time)
        if extra_sleep > 0:
            logger.debug("Extra sleep for %d seconds (capped by max_visit_time)", extra_sleep)
            time.sleep(extra_sleep)

        logger.info("Finished visit for %s", url)
        return None

    except (TimeoutException, urllib3.exceptions.ReadTimeoutError, socket.timeout) as e:
        logger.warning("Timeout-like exception for %s: %s", url, e)
        # try to recover by quitting driver and signalling restart
        try:
            driver.quit()
        except Exception:
            pass
        logger.info("Driver quit after timeout; requesting restart.")
        return "restart"

    except (WebDriverException, urllib3.exceptions.ProtocolError) as e:
        logger.warning("WebDriver/Protocol error for %s: %s", url, e)
        # restart driver
        try:
            driver.quit()
        except Exception:
            pass
        logger.info("Driver quit after WebDriver/Protocol error; requesting restart.")
        return "restart"

    except Exception as e:
        # catch-all for other exceptions: log and skip this URL
        logger.exception("Unexpected error while processing %s: %s", url, e)
        # you might want to restart on specific fatal errors, but to be conservative, skip
        return "skip"

# ----------------------------
# Main loop
# ----------------------------
def main():
    if args.loop:
        logger.info("Loop mode active. Press Ctrl+C to stop.")

    while True:
        urls = read_urls_from_file()
        if not urls:
            if not args.loop:
                logger.info("No URLs found. Exiting.")
                return
            logger.info("No URLs found. Waiting before retry...")
            time.sleep(args.loop_sleep)
            continue

        if args.url_shuffle:
            random.shuffle(urls)

        # create initial browser
        try:
            driver = create_browser_attempt()
        except Exception as e:
            logger.exception("Could not create WebDriver, exiting: %s", e)
            return

        try:
            for url in urls:
                attempt = 0
                while attempt <= args.max_retries:
                    attempt += 1
                    logger.info("Processing URL [%d/%d] attempt %d: %s", urls.index(url) + 1, len(urls), attempt, url)
                    action = None
                    try:
                        action = process_url(driver, url)
                    except Exception as e:
                        logger.exception("process_url raised an unexpected exception: %s", e)
                        action = "restart"

                    if action is None:
                        # success or skipped because no script -> move to next URL
                        break
                    if action == "skip":
                        logger.info("Skipping URL after unrecoverable error: %s", url)
                        break
                    if action == "restart":
                        # try to restart driver then retry URL (if attempts remain)
                        logger.info("Restart requested for URL %s (attempt %d of %d).", url, attempt, args.max_retries + 1)
                        # try to ensure driver is quit
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        time.sleep(args.retry_backoff)
                        try:
                            driver = create_browser_attempt()
                        except Exception as e:
                            logger.exception("Failed to recreate WebDriver while retrying URL %s: %s", url, e)
                            # wait a bit before another try or abort if out of attempts
                            time.sleep(args.retry_backoff)
                            if attempt > args.max_retries:
                                logger.error("Out of retries for URL %s. Moving on.", url)
                                break
                            continue
                        # after restart, loop will retry the same URL
                        if attempt > args.max_retries:
                            logger.error("Reached max retries for %s. Skipping.", url)
                            break
                        else:
                            continue
                    else:
                        # unknown action -> skip
                        logger.warning("Unknown action from process_url: %s. Skipping URL.", action)
                        break

        finally:
            try:
                driver.quit()
            except Exception:
                pass
            logger.info("Browser closed.")

        if not args.loop:
            logger.info("Completed single run; exiting.")
            return

        logger.info("Loop complete. Sleeping for %d seconds before next round...", args.loop_sleep)
        time.sleep(args.loop_sleep)

# ----------------------------
# Entrypoint
# ----------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("You cancelled via CTRL-C.")
        try:
            # do a brief grace period for cleanups
            time.sleep(0.2)
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error in main: %s", e)
        sys.exit(1)
