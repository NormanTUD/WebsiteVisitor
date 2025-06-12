function waitForElement(selector, description = "") {
	updateStatus("Warte auf '" + selector + "' (" + description + ")...");
	return new Promise(resolve => {
		let interval = setInterval(() => {
			let el = document.querySelector(selector);
			if (el && el.offsetParent !== null) {
				updateStatus("Gefunden: '" + selector + "', " + description + "...");
				clearInterval(interval);
				resolve(el);
			}
		}, 500);
	});
}

async function waitForConsentAndClickNext() {
	await sleep(1000);

	// Warte auf den Consent-Button
	const consentBtn = await waitForElement("#onetrust-accept-btn-handler", "Cookie-Zustimmung");

	if (consentBtn && typeof consentBtn.click === "function") {
		updateStatus("Klicke auf 'Cookie-Zustimmung'");
		try {
			consentBtn.click();
			updateStatus("Cookie-Zustimmung geklickt.");
		} catch (e) {
			alert(`Fehler beim Klicken des Consent-Buttons: ${e}`);
			updateStatus(`Fehler beim Klicken des Consent-Buttons: ${e}`);
		}
	} else {
		updateStatus("Consent-Button nicht klickbar gefunden.");
		return; // Abbrechen, wenn Button nicht da oder nicht klickbar
	}

	await sleep(2000);

	updateStatus("Suche den großen Playbutton");

	// Warte auf den Play-Button
	const playBtn = await waitForElement(".sc-button-xxlarge", "großer Playbutton");

	if (playBtn && typeof playBtn.click === "function") {
		updateStatus("Klicke den großen Playbutton an");
		playBtn.click();
		updateStatus("Playbutton geklickt.");
	} else {
		updateStatus("Playbutton nicht klickbar gefunden.");
	}
}

waitForConsentAndClickNext();
