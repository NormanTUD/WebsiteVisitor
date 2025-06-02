// Alle passenden Links sammeln
var links = Array.from(document.querySelectorAll('a[href^="javascript:IRON.sonaar.player.setPlayerAndPlay"]'));

// Optional: Nur Links mit gültiger ID extrahieren (falls es andere geben könnte)
links = links.filter(function(link) {
    return /setPlayerAndPlay\(\s*\{\s*id\s*:\s*\d+\s*\}\s*\)/.test(link.getAttribute('href'));
});

// Zufällig eines auswählen und klicken
if (links.length > 0) {
    var randomIndex = Math.floor(Math.random() * links.length);
    links[randomIndex].click();
    links[randomIndex].click();

    // Nach 5 Sekunden das Play/Pause-Element suchen und klicken
    setTimeout(function() {
        var playButton = document.querySelector('div[aria-label="Play / Pause"].play.control--item.sricon-play');
        if (playButton) {
            playButton.click();
        } else {
            console.warn("Play/Pause-Button nicht gefunden.");
        }
    }, 5000);
} else {
    console.warn("Kein passender Link gefunden.");
}
