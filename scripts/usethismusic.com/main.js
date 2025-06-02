// Nachrichtenelement erstellen und einfügen
var statusBox = document.createElement('div');
statusBox.style.position = 'fixed';
statusBox.style.top = '0';
statusBox.style.left = '0';
statusBox.style.right = '0';
statusBox.style.backgroundColor = '#333';
statusBox.style.color = '#fff';
statusBox.style.padding = '10px';
statusBox.style.fontFamily = 'sans-serif';
statusBox.style.fontSize = '14px';
statusBox.style.zIndex = '9999';
statusBox.style.textAlign = 'center';
statusBox.textContent = 'Initialisiere...';
document.body.appendChild(statusBox);

// Funktion zum Aktualisieren der Statusmeldung
function updateStatus(msg) {
	statusBox.textContent = msg;
}

// Alle passenden Links sammeln
updateStatus('Suche passende Links...');
var links = Array.from(document.querySelectorAll('a[href^="javascript:IRON.sonaar.player.setPlayerAndPlay"]'));

// Optional: Nur Links mit gültiger ID extrahieren (falls es andere geben könnte)
links = links.filter(function(link) {
	return /setPlayerAndPlay\(\s*\{\s*id\s*:\s*\d+\s*\}\s*\)/.test(link.getAttribute('href'));
});

// Zufällig eines auswählen und klicken
if (links.length > 0) {
	var randomIndex = Math.floor(Math.random() * links.length);
	updateStatus('Klicke zufälligen Link...');
	links[randomIndex].click();
	links[randomIndex].click();

	updateStatus('Warte 5 Sekunden, dann klicke Play...');
	setTimeout(function() {
		var playButton = document.querySelector('div[aria-label="Play / Pause"].play.control--item.sricon-play');
		if (playButton) {
			updateStatus('Klicke Play/Pause-Button...');
			playButton.click();
			updateStatus('Play/Pause-Button geklickt.');
		} else {
			updateStatus('Play/Pause-Button nicht gefunden.');
			console.warn("Play/Pause-Button nicht gefunden.");
		}
	}, 5000);
} else {
	updateStatus('Kein passender Link gefunden.');
	console.warn("Kein passender Link gefunden.");
}
