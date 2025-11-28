#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import time
import os
import re
import subprocess
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
    ElementClickInterceptedException
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
parser.add_argument("--scroll_min_random_time", type=float, default=0.3, help="Min random time for random scrolling.")
parser.add_argument("--scroll_max_random_time", type=float, default=5, help="Max random time for random scrolling.")
parser.add_argument("--max_retries", type=int, default=3, help="Max retries per URL before skipping.")
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
    if not os.path.exists(args.url_list):
        print(f"❌ Datei nicht gefunden: {args.url_list}")
        return []
    with open(args.url_list, 'r', encoding='utf-8') as f:
        # Filtert leere Zeilen und Kommentare, entfernt Whitespace
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('[source')]
    
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
    # Sucht die Haupt-main.js im domain-spezifischen Unterordner
    script_path = os.path.join(args.script_folder, hostname, "main.js")
    if not os.path.isfile(script_path):
        logger.warning("Script not found for %s: %s", hostname, script_path)
        return None
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            contents = f.read()
            return contents
    except Exception as e:
        logger.exception("Failed to read script for %s: %s", hostname, e)
        return None

# ----------------------------
# Browser creation and helpers
# ----------------------------
def create_browser_attempt(attempt=1, max_attempts=4):
    logger.info("Creating Chrome WebDriver (attempt %d/%d)...", attempt, max_attempts)
    
    options = Options()
    
    # 1. Entfernen des "Chrome wird von automatisierter Software gesteuert" Balkens
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    if not args.show_browser:
        options.add_argument("--headless=new") # Modernes Headless
    
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-certificate-errors-spki-list")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--log-level=3")

    options.add_argument("--autoplay-policy=no-user-gesture-required")

    if args.mute:
        options.add_argument("--mute-audio")

    # User Agent Spoofing (optional, macht es "menschlicher")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
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
        print("⚠️  Zeitüberschreitung beim Laden der Seite (document.readyState).")
    except WebDriverException as e:
        logger.debug("WebDriverException while waiting for page load: %s", e)

# Alias
wait_for_page_load_complete = wait_for_page_load 

# ----------------------------
# Kurze Pause Helper
# ----------------------------
def random_sleep(min_s=0.1, max_s=0.5):
    time.sleep(random.uniform(min_s, max_s))

# ----------------------------
# KORRIGIERTE FUNKTION: Ausführung der asynchronen main.js
# ----------------------------
def execute_async_js_script(driver, js_script, url):
    """
    Führt das asynchrone JS-Skript aus (window.automatePage()) und wartet auf den Status.
    
    Returns:
      action_string ('success', 'restart') oder None bei Fehler.
    """
    domain = get_root_domain(url)
    try:
        # 1. Injiziere den gesamten JS-Code, um window.automatePage zu definieren.
        driver.execute_script(js_script)
        
        # 2. Rufe die definierte Funktion asynchron auf und warte auf den Callback.
        # Wir wickeln den Aufruf in einen Wrapper, der den Selenium-Callback nutzt.
        async_wrapper = """
        var done = arguments[arguments.length - 1]; // Selenium Callback
        if (typeof window.automatePage === 'function') {
            window.automatePage()
                .then(function(res) { done(res); })
                .catch(function(err) { done('error: ' + err); });
        } else {
            done('error: automatePage not defined');
        }
        """
        
        # execute_async_script wartet, bis 'done()' im JS aufgerufen wird
        action = driver.execute_async_script(async_wrapper)
        
        # Sicherheitsprüfung für den Rückgabewert
        if not isinstance(action, str):
            logger.warning(f"[{domain}] JS-Skript gab keinen String zurück: {action}. Behandele als Fehler.")
            return None
        
        # Gib nur erlaubte Aktionen zurück
        action = action.lower()
        if 'error' in action:
             logger.warning(f"[{domain}] JS Fehler gemeldet: {action}")
             return None

        return action if action in ['success', 'restart'] else None
            
    except JavascriptException as e:
        logger.warning(f"[{domain}] JavaScript Fehler bei asynchroner Ausführung: {e}")
        return None
    except Exception as e:
        logger.warning(f"[{domain}] Unerwarteter Fehler bei asynchroner JS-Ausführung: {e}")
        return None

# ----------------------------
# Lange Pause Helper
# ----------------------------
def random_long_sleep(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))

# ----------------------------
# Cookie und Play Button Handling
# ----------------------------
def attempt_cleanup_actions(driver):
    """
    Versucht nacheinander, Pop-ups oder Banner zu schließen/akzeptieren.
    """
    # KONSOLIDIERTER XPATH für Schließen/Ablehnen
    # (Syntaktisch korrigiert, damit das Skript ausführbar ist)
    try:
        close_xpath_combined = (
            "//button[.='x' or .='X' or @aria-label='Close' or @title='Close' or @aria-label='Anmelden' or @title='Anmelden' or @aria-label='Cookie Hinweis' or @title='Cookie Hinweis']"
            + "| //*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'schlie') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abbrechen') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'spaeter') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not now') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'later')]"
            + "| //*[contains(@class, 'modal-close') or contains(@class, 'close-button') or contains(@class, 'dismiss') or contains(@class, 'fancybox-close') or contains(@class, 'lightbox-close')]"
        )
        # Hier könnte Logik stehen, um diesen XPath zu klicken, aber im Original fehlte der Codeblock.
        # Wir lassen es als Platzhalter stehen, falls später Logik ergänzt wird.
        pass
    except Exception:
        pass

def click_element_safely(driver, element, name="Element"):
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)
        # Versuch 1: Normaler Klick
        element.click()
        print(f"✅ Klick auf '{name}' erfolgreich.")
        return True
    except (ElementClickInterceptedException, Exception):
        try:
            # Versuch 2: JS Klick (erzwungen)
            driver.execute_script("arguments[0].click();", element)
            print(f"✅ Klick auf '{name}' per JS erzwungen.")
            return True
        except Exception as e:
            print(f"❌ Konnte '{name}' nicht klicken: {e}")
    return False

def handle_cookies(driver):
    """
    Sucht nach Cookie-Bannern basierend auf Text-Keywords.
    """
    print("🍪 [Fallback] Prüfe auf Cookie-Banner...")
    
    # Liste der Suchbegriffe (Case-Insensitive Logik via XPath)
    keywords = [
        "akzeptieren", "alle akzeptieren", "annehmen", "alle annehmen", "zulassen", "alle zulassen", "einverstanden", "erlauben", "alle cookies erlauben", "accept", "accept all", "allow all", "i agree"
    ]
    
    found = False
    for keyword in keywords:
        if found: break
        try:
            xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')] | " \
                    f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')] | " \
                    f"//div[@role='button' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
            
            elements = driver.find_elements(By.XPATH, xpath)
            
            for elem in elements:
                if elem.is_displayed():
                    print(f"   -> Möglicher Cookie-Button gefunden: '{elem.text.strip()}'")
                    if click_element_safely(driver, elem, f"Cookie: {keyword}"):
                        found = True
                        break
        except Exception:
            continue
    
    if not found:
        print("   -> Kein offensichtlicher Cookie-Banner gefunden (oder bereits akzeptiert).")

def handle_play_buttons(driver):
    """
    Sucht nach Play-Buttons basierend auf Text und gängigen Klassen.
    """
    print("▶️  [Fallback] Suche nach Play/Hörprobe/Shuffle Buttons...")
    
    # 1. Textbasierte Suche
    text_keywords = ["Hoerprobe", "Abspielen", "Play", "Shuffle", "Listen"]
    clicked = False
    
    for keyword in text_keywords:
        if clicked: break
        try:
            xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]"
            elements = driver.find_elements(By.XPATH, xpath)
            for elem in elements:
                if elem.is_displayed() and elem.tag_name in ['button', 'a', 'span', 'div']:
                    if click_element_safely(driver, elem, f"Play-Text: {keyword}"):
                        clicked = True
                        break
        except Exception:
            pass

    # 2. Suche nach Symbolen/Klassen
    if not clicked:
        css_selectors = [
            ".playbutton", ".play-button", ".playControl", # Bandcamp / Soundcloud
            "button[aria-label*='Play']", "button[title*='Play']",
            ".ytp-play-button", # Youtube
            ".audio-player-play"
        ]
        
        for selector in css_selectors:
            if clicked: break
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        if click_element_safely(driver, elem, f"Play-Icon: {selector}"):
                            clicked = True
                            break
            except Exception:
                pass
    
    if not clicked:
        print("   -> Keinen Play-Button gefunden.")
        
# ----------------------------
# Realistic interaction (resilient)
# ----------------------------
def realistic_user_interaction(driver, duration_seconds, scroll_chance=None):
    if scroll_chance is None:
        scroll_chance = args.scroll_chance
    end_time = time.time() + duration_seconds
    
    print(f"⏱️  Verweile auf der Seite für ca. {duration_seconds} Sekunden...")

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

# Alias
run_interaction = realistic_user_interaction

# ----------------------------
# Process single URL with retries and safe failure modes
# ----------------------------
def process_url(driver, url):
    """
    Returns:
      None -> success (visit complete)
      "restart" -> caller should restart the browser (driver has been quit)
      "skip" -> skip this URL (non-recoverable or file missing)
    """
    logger.info("Loading URL: %s", url)

    print(f"\n{'='*60}")
    print(f"🌍 Lade URL: {url}")
    print(f"{'='*60}")

    try:
        # 1. Seite laden
        if not url.startswith("http"):
            url = "https://" + url
        
        driver.get(url)

        # 2. Warten bis vollständig geladen
        wait_for_page_load_complete(driver)
        print("✅ Seite geladen.")

        # 3. Kurze Pause
        print("⏳ Kurze Pause (Init)...")
        random_long_sleep(1, 3)
        
        # 4. JavaScript aus Ordner laden (falls vorhanden)
        hostname = get_root_domain(url)
        script_path = os.path.join(args.script_folder, hostname, "main.js")
        
        # Flag um zu speichern, ob JS erfolgreich war
        js_was_successful = False

        # HIER WIRD DIE LOGIK FÜR DIE ASYNCHRONE main.js INTEGRIERT
        if os.path.isfile(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                    print(f"📜 Führe benutzerdefiniertes ASYNCHRONES JS für {hostname} aus...")
                    
                    # Führt die neue main.js aus und wartet auf das Ergebnis
                    action = execute_async_js_script(driver, js_content, url)
                    
                    if action == 'success':
                        print(f"✅ ASYNCHRONES JS erfolgreich (Play gedrückt oder läuft bereits).")
                        # WICHTIG: KEIN Return hier! Wir wollen auf der Seite bleiben.
                        js_was_successful = True 
                    elif action == 'restart':
                        print(f"♻️ ASYNCHRONES JS fordert Browser-Neustart an (Timeout).")
                        return "restart" 
                    else:
                        print(f"⚠️ ASYNCHRONES JS beendet ohne 'success'. Nutze Python-Fallbacks.")
            except Exception as e:
                print(f"⚠️  Fehler beim Laden/Ausführen des benutzerdefinierten JS: {e}")
        
        # 5. Längere Pause
        random_long_sleep(3, 5)
        
        # 6., 7., 8. Fallbacks nur ausführen, wenn JS NICHT erfolgreich war
        if not js_was_successful:
            handle_cookies(driver)
            print("⏳ Kurze Pause (Post-Cookie)...")
            random_long_sleep(1, 3)
            handle_play_buttons(driver)
        else:
            print("⏭️  Überspringe Python-Fallbacks (Cookies/Play), da JS erfolgreich war.")

        # 9. Interaktion / Verweildauer
        # Das wird jetzt IMMER erreicht, auch wenn JS erfolgreich war.
        run_interaction(driver, args.sleep_seconds)

        # (Alter Block zur Sicherheit, falls run_interaction oben abstürzt, aber wir haben es sichergestellt)
        # visit_time = min(args.sleep_seconds, args.max_visit_time)
        # realistic_user_interaction(driver, duration_seconds=visit_time, scroll_chance=args.scroll_chance)

        logger.info("Finished visit for %s", url)
        return None 

    except (TimeoutException, urllib3.exceptions.ReadTimeoutError, socket.timeout) as e:
        logger.warning("Timeout-like exception for %s: %s", url, e)
        try:
            driver.quit()
        except Exception:
            pass
        return "restart"

    except (WebDriverException, urllib3.exceptions.ProtocolError) as e:
        logger.warning("WebDriver/Protocol error for %s: %s", url, e)
        try:
            driver.quit()
        except Exception:
            pass
        return "restart"

    except Exception as e:
        logger.exception("Unexpected error while processing %s: %s", url, e)
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
            print("mj🎲 Mische URLs...")
            random.shuffle(urls)

        # create initial browser
        try:
            driver = create_browser_attempt()
            # WICHTIG: Setze Timeout für asynchrone Skripte (damit execute_async_script nicht unendlich wartet)
            driver.set_script_timeout(120) 
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
                        # success -> move to next URL
                        break
                    if action == "skip":
                        logger.info("Skipping URL after unrecoverable error: %s", url)
                        break
                    if action == "restart":
                        logger.info("Restart requested for URL %s (attempt %d of %d).", url, attempt, args.max_retries + 1)
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        time.sleep(args.retry_backoff)
                        try:
                            driver = create_browser_attempt()
                            driver.set_script_timeout(120) # Reset timeout nach Neustart
                        except Exception as e:
                            logger.exception("Failed to recreate WebDriver while retrying URL %s: %s", url, e)
                            time.sleep(args.retry_backoff)
                            if attempt > args.max_retries:
                                break
                            continue
                        if attempt > args.max_retries:
                            break
                        else:
                            continue
                    else:
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
            time.sleep(0.2)
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error in main: %s", e)
        sys.exit(1)