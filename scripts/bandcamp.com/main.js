async function findAndClickAcceptButton() {
	updateStatus('Waiting 2 seconds before searching for the button...');
	await sleep(2000);

	updateStatus('Searching for button with text containing "accept all"...');

	const buttons = [...document.querySelectorAll('button')];
	const acceptButton = buttons.find(b => 
		b.textContent && b.textContent.toLowerCase().includes('accept all')
	);

	if (acceptButton) {
		updateStatus('Button found! Clicking it now...');
		acceptButton.click();
		updateStatus('Button clicked!');
	} else {
		updateStatus('Button not found.');
	}
}

function find_play_buttons_play_random_one() {
	var playButtons = document.getElementsByClassName("play_status");
	updateStatus(`Gefundene Play-Buttons: ${playButtons.length}`);

	if (playButtons.length === 0) {
		updateStatus("Keine Play-Buttons gefunden.");
	} else {
		var randomIndex = Math.floor(Math.random() * playButtons.length);
		updateStatus(`Wähle zufälligen Button #${randomIndex + 1} von ${playButtons.length}`);

		var chosenButton = playButtons[randomIndex];

		if (chosenButton.click) {
			chosenButton.click();
			updateStatus(`Button #${randomIndex + 1} wurde angeklickt.`);
		} else {
			updateStatus("Der Button unterstützt keinen Klick.");
		}
	}
}

async function accept_cookies_and_play_random() {
	await findAndClickAcceptButton();

	find_play_buttons_play_random_one();
}

accept_cookies_and_play_random();
