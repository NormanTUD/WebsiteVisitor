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
} else {
	updateStatus('Kein passender Link gefunden.');
	console.warn("Kein passender Link gefunden.");
}
