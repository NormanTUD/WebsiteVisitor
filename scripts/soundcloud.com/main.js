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
	await sleepRandomly(1000, 2000);

	updateStatus("Warte auf den Consent-Button")
	const consentBtn = await waitForElement("#onetrust-accept-btn-handler", "Cookie-Zustimmung");

	if (consentBtn && typeof consentBtn.click === "function") {
		updateStatus("Klicke auf 'Cookie-Zustimmung'");
		try {
			consentBtn.click();
			updateStatus("Cookie-Zustimmung geklickt.");
		} catch (e) {
			alert(`Fehler beim Klicken des Consent-Buttons: ${e}`);
			updateStatus(`Fehler beim Klicken des Consent-Buttons: ${e}`);
			return;
		}
	} else {
		updateStatus("Consent-Button nicht klickbar gefunden.");
		return;
	}

	await sleepRandomly(1000, 2000);

	updateStatus("Prüfe, ob Popup vorhanden ist...");

	updateStatus("Popup close button selector (alle Klassen in einem String, getrennt durch Punkte, für querySelector)")
	let popupSelector = ".modal__closeButton.sc-button.sc-button-secondary.sc-button-large.sc-button-icon";
	let popupCloseBtn = document.querySelector(popupSelector);

	if (popupCloseBtn && popupCloseBtn.offsetParent !== null) {
		updateStatus("Popup gefunden, klicke es weg.");
		try {
			popupCloseBtn.click();
			updateStatus("Popup geschlossen.");
			updateStatus("Warte kurz, dass das Popup komplett weg ist")
			await sleepRandomly(1000, 2000);
		} catch (e) {
			updateStatus("Fehler beim Klicken des Popup-Schließbuttons: " + e);
		}
	} else {
		updateStatus("Kein Popup gefunden, fahre fort.");
	}

	updateStatus("Suche den großen Playbutton");

	updateStatus("Warte auf den Play-Button")
	const playBtn = await waitForElement(".sc-button-xxlarge", "großer Playbutton");

	if (playBtn && typeof playBtn.click === "function") {
		updateStatus("Prüfen, ob der Button schon die Klasse 'sc-button-pause' hat")
		if (playBtn.classList.contains("sc-button-pause")) {
			updateStatus("Playbutton ist bereits im Pause-Zustand (spielt schon). Klicke nicht.");
		} else {
			updateStatus("Klicke den großen Playbutton an");
			playBtn.click();
			updateStatus("Playbutton geklickt.");
		}
	} else {
		updateStatus("Playbutton nicht klickbar gefunden.");
	}
}

waitForConsentAndClickNext();
