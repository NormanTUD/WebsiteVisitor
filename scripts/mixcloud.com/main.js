function isVisible(el) {
        updateStatus("Check if element and all parents are visible");

        while (el) {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        return false;
                }
                el = el.parentElement;
        }
        return true;
}

function click_random_play_button() {
        var buttons = document.querySelectorAll('[data-testid="audiocard-play-button"]');

        if (buttons.length === 0) {
                updateStatus('Keine kleinen Buttons gefunden, versuche, grosse Buttons zu finden.');

                buttons = Array.from(document.getElementsByClassName("play-button-rings-svg"));
                buttons = buttons.filter(isVisible);

		buttons = buttons
			.filter(isVisible)
			.map(el => {
				while (el && el.tagName !== "BUTTON") {
					el = el.parentElement;
				}
				return el;
			})
			.filter(Boolean);
        }

        if(buttons.length) {
                var index = Math.floor(Math.random() * buttons.length);
                var button = buttons[index];
                updateStatus('Wähle zufällig Button #' + (index + 1) + ' von ' + buttons.length);
                button.click();
        } else {
                updateStatus("Keine Buttons gefunden");
        }
}

async function run_script() {
        await sleepRandomly(6000, 8000);
        click_random_play_button()
}

run_script();
