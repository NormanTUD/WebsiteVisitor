/**
 * Universal Auto-Player & Cookie Accepter
 * Version: 2.2 (Fix: Missing Helper & Error Handling)
 */

(function() {
    'use strict';

    // --- KONFIGURATION & SELEKTOREN ---

    const CONFIG = {
        scanInterval: 2000,
        clickDelay: [3000, 6000],
        maxAttempts: 20,
        debug: true
    };

    const COOKIE_SELECTORS = [
        '#onetrust-accept-btn-handler',
        '#uc-btn-accept-banner',
        '.cc-btn.cc-accept',
        '[data-testid="cookie-policy-dialog-accept-button"]',
        '.borlabs-cookie-preference-accept',
        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        'button[data-testid="accept-cookie-button"]',
        'button[name="agree"]',
        'form[action*="consent"] button',
        '.js-accept-cookies',
        '.evidon-banner-acceptbutton',
        'button.cookie-banner__accept',
        '#sp-cc-accept',
        // Generische Klassen, oft genutzt
        '.cookie-accept',
        '.accept-cookies',
        'button[class*="agree"]',
        'button[class*="accept"]'
    ];

    const PLAY_SELECTORS = [
        '.play-button',
        '[data-testid="play-button"]',
        '.playControl',
        '.heroPlayButton',
        '.inline_player .playbutton',
        '.ytp-play-button',
        'button[aria-label="Play"]',
        'button[aria-label="Wiedergabe"]',
        '.player-controls__play',
        '.play-btn',
        '#play-button',
        'a.play',
        '.wp-audio-shortcode .mejs-playpause-button',
        // Generisch Play Icon Klassen
        '.fa-play',
        '.icon-play'
    ];

    const COOKIE_KEYWORDS = [
        "akzeptieren", "alle akzeptieren", "annehmen", "alle annehmen", "zulassen", "alle zulassen", 
        "einverstanden", "erlauben", "alle cookies erlauben", "accept", "accept all", "allow all", 
        "i agree", "okay", "cookies zulassen", "verstanden"
    ];

    // --- HELFER FUNKTIONEN (Hier fehlte sleepRandomly!) ---

    function updateStatus(msg) {
        if (CONFIG.debug) console.log(`[AutoBot] 🤖 ${msg}`);
    }

    function isVisible(elem) {
        if (!elem) return false;
        const style = window.getComputedStyle(elem);
        return style.width !== '0' &&
               style.height !== '0' &&
               style.opacity !== '0' &&
               style.display !== 'none' &&
               style.visibility !== 'hidden';
    }

    // WICHTIG: Diese Funktion fehlte vorher!
    function sleepRandomly(min, max) {
        const ms = Math.floor(Math.random() * (max - min + 1) + min);
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // --- LOGIK: COOKIES ---

    async function handleCookies() {
        updateStatus("Scanne nach Cookie-Bannern...");

        for (let selector of COOKIE_SELECTORS) {
            let btns = document.querySelectorAll(selector);
            for (let btn of btns) {
                 if (isVisible(btn)) {
                    updateStatus(`Cookie-Button gefunden via Selektor: ${selector}`);
                    btn.click();
                    return true;
                }
            }
        }

        const buttons = document.querySelectorAll('button, a, div[role="button"], input[type="submit"]');
        for (let btn of buttons) {
            const text = btn.innerText.toLowerCase().trim();
            if (COOKIE_KEYWORDS.some(keyword => text === keyword) && isVisible(btn)) {
                updateStatus(`Cookie-Button gefunden via Textanalyse: "${text}"`);
                btn.click();
                return true;
            }
        }
        return false;
    }

    // --- LOGIK: PLAYER ---

    async function handlePlay() {
        updateStatus("Suche nach Play-Button...");

        const mediaElements = document.querySelectorAll('video, audio');
        for (let media of mediaElements) {
            if (!media.paused && media.currentTime > 0) {
                updateStatus("Medien werden bereits abgespielt.");
                return true;
            }
        }

        for (let selector of PLAY_SELECTORS) {
            let btns = document.querySelectorAll(selector);
            for (let btn of btns) {
                if (isVisible(btn)) {
                    // YouTube Schutz
                    if( (selector.includes('ytp-play-button') && btn.getAttribute('title')?.includes('Pause')) ) {
                         updateStatus("YouTube läuft bereits.");
                         return true;
                    }

                    updateStatus(`Play-Button gefunden via Selektor: ${selector}`);
                    try {
                        btn.click();
                    } catch(e) {
                        btn.click(); // Retry without try/catch logic just raw
                    }
                    return true;
                }
            }
        }
        return false;
    }

    // --- HAUPTSTEUERUNG ---

    async function runOrchestrator() {
        // Wir wrappen alles in einen Try/Catch Block, damit Fehler nicht zum Timeout führen
        return new Promise(async (resolve) => {
            try {
                updateStatus("Starte Automatisierung für Domain: " + window.location.hostname);
                
                // Schritt 1: Warten
                await sleepRandomly(CONFIG.clickDelay[0], CONFIG.clickDelay[1]);

                // Schritt 2: Cookies
                await handleCookies();

                // Schritt 3: Pause nach Cookie
                await sleepRandomly(2000, 5000); // Zeit etwas reduziert für schnelleren Test

                // Schritt 4: Play Versuch 1
                let played = await handlePlay();

                if (played) {
                    updateStatus("Erfolg: Play geklickt oder Musik läuft.");
                    return resolve('success');
                }

                // Schritt 5: Observer (Warten auf dynamische Inhalte)
                updateStatus("Aktiviere Observer...");
                
                let timeoutTriggered = false;

                const observer = new MutationObserver(async (mutations, obs) => {
                    if (timeoutTriggered) return; // Wenn Timeout schon war, nichts tun

                    // Wir prüfen nicht bei jeder Mutation sofort (Performance), sondern entkoppelt? 
                    // Nein, direkt prüfen ist okay, aber handlePlay ist async.
                    // Einfacher Check:
                    const success = await handlePlay();
                    if (success) {
                        updateStatus("Play-Button dynamisch gefunden!");
                        obs.disconnect();
                        clearTimeout(timeoutId);
                        return resolve('success');
                    }
                });

                observer.observe(document.body, { childList: true, subtree: true });

                // Timeout für den Observer (Max 30s warten)
                const timeoutId = setTimeout(() => {
                    timeoutTriggered = true;
                    observer.disconnect();
                    updateStatus("Timeout im JS Observer: Kein Play-Button gefunden.");
                    // Wir geben 'success' zurück, damit Python NICHT restartet, sondern einfach auf der Seite bleibt (Interaktion)
                    // Oder 'restart', wenn du willst, dass er die Seite neu lädt. 
                    // Hier: restart, da ohne Musik der Besuch sinnlos ist?
                    resolve('success'); 
                }, 30000);

            } catch (error) {
                console.error("[AutoBot] Kritischer Fehler:", error);
                // WICHTIG: Promise auflösen, damit Selenium nicht timeoutet!
                resolve('error: ' + error.message);
            }
        });
    }

    window.automatePage = runOrchestrator;
})();