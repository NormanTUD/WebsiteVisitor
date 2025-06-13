async function acceptCookiesIfPresent() {
	updateStatus("Suche Cookie-Bestätigungsbutton...");
	var btn = document.getElementById("onetrust-accept-btn-handler");

	if (btn) {
		updateStatus("Cookie-Bestätigungsbutton gefunden, klicke...");
		btn.click();
	} else {
		updateStatus("Kein Cookie-Bestätigungsbutton gefunden.");
	}
}

function start_play() {
	updateStatus("Alle passenden Buttons holen");
	var buttons = document.querySelectorAll('button[data-testid="play-button"]');

	updateStatus("Prüfen, ob welche gefunden wurden");
	if (buttons.length > 0) {
		updateStatus("Ersten Index wählen");
		var index = 0;

		updateStatus("Ersten Button anklicken");
		buttons[index].click();
	} else {
		updateStatus("Keine Buttons gefunden.");
	}
}

async function accept_cookies_and_play() {
	await sleepRandomly(3000, 6000);

	await acceptCookiesIfPresent();

	await sleepRandomly(3000, 6000);

	start_play();
}

accept_cookies_and_play();
