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

async function waitForConsentAndClickNext() {
	await sleep(1000);
	let consentBtn = await waitForElement("#onetrust-accept-btn-handler", "Cookie-Zustimmung");
	await sleep(1000);
	consentBtn.click();
	updateStatus("Cookie-Zustimmung geklickt.");

	await sleep(2000);

	updateStatus("Suche den grossen Playbutton");

	let playBtn = await waitForElement(".sc-button-xxlarge", "großer Playbutton");
	updateStatus("Klicke den grossen Playbutton an");
	playBtn.click();
	updateStatus("Playbutton geklickt.");
}

waitForConsentAndClickNext();
