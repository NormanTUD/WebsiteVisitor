async function findAndClickAcceptButton() {
	updateStatus('Waiting 2 seconds before searching for the button...');
	await new Promise(resolve => setTimeout(resolve, 2000)); // sleep 2s

	updateStatus('Searching for button with text containing "accept all"...');

	function isAcceptAllButton(button) {
		if (!button.textContent) return false;
		var text = button.textContent.trim().toLowerCase();
		return text === 'accept all';
	}

	function findAllShadowRoots(root = document) {
		let results = [];
		let elements = root.querySelectorAll('*');
		elements.forEach(el => {
			if (el.shadowRoot) {
				results.push(el.shadowRoot);
				results = results.concat(findAllShadowRoots(el.shadowRoot));
			}
		});
		return results;
	}

	let acceptButton = null;

	let buttons = [...document.querySelectorAll('button')];
	acceptButton = buttons.find(b => b.textContent && b.textContent.toLowerCase().includes('accept all'));

	if (!acceptButton) {
		let shadowRoots = findAllShadowRoots();
		for (let sr of shadowRoots) {
			let shadowButtons = [...sr.querySelectorAll('button')];
			acceptButton = shadowButtons.find(isAcceptAllButton);
			if (acceptButton) {
				updateStatus('Found Accept all button in shadowRoot!');
				break;
			}
		}
	}

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

	await sleep(2456);

	find_play_buttons_play_random_one();
}

accept_cookies_and_play_random();
