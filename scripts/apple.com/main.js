async function start_play() {
	updateStatus("Hole Button");

	var button = document.querySelector('button[data-testid="click-action"]');

	if (button) {
		updateStatus("Schlafe randomly zwischen 2 und 4 Sekunden, dann klicke den Start-Button");
		sleepRandomly(2000, 4000).then(() => {
			updateStatus("Klicke den Start-Button");
			button.click();
			updateStatus("Start-Button geklickt");
		});
	} else {
		updateStatus('Button mit data-testid="click-action" nicht gefunden.');
	}
}

start_play();
