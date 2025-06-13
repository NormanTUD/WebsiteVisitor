function click_random_play_button() {
	var buttons = document.querySelectorAll('[data-testid="audiocard-play-button"]');

	if (buttons.length === 0) {
		updateStatus('Keine Buttons gefunden.');
	} else {
		var index = Math.floor(Math.random() * buttons.length);
		var button = buttons[index];
		updateStatus('Wähle zufällig Button #' + (index + 1) + ' von ' + buttons.length);
		button.click();
	}
}

async function run_script() {
	await sleepRandomly(6000, 8000);
	click_random_play_button()
}

run_script();
