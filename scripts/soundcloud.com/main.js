function waitForElement(selector, description, callback) {
    updateStatus("Warte auf '" + selector + "' (" + description + ")...");
    let interval = setInterval(() => {
        let el = document.querySelector(selector);
        if (el && el.offsetParent !== null) {
            updateStatus("Gefunden: '" + selector + "', " + description + "...");
            clearInterval(interval);
            callback(el);
        }
    }, 500);
}

function waitForConsentAndClickNext() {
    waitForElement("#onetrust-accept-btn-handler", "Cookie-Zustimmung", (consentBtn) => {
        consentBtn.click();
        updateStatus("Cookie-Zustimmung geklickt.");

        waitForElement(".sc-button-xxlarge", "großer Playbutton", (playBtn) => {
            playBtn.click();
            updateStatus("Playbutton geklickt.");
        });
    });
}

async function start_handling_website() {
	waitForConsentAndClickNext();

	await sleep(1000);

	updateStatus("Suche den grossen Playbutton");
	let playbutton = document.getElementsByClassName("sc-button-xxlarge")[0];

	updateStatus("Klicke den grossen Playbutton an")
	playbutton.click()
}
