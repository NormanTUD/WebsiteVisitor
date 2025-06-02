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

// Statusbox ist schon definiert in deinem Code

// Schritt 1: Alle Play-Buttons holen
var playButtons = document.getElementsByClassName("play_status");
updateStatus(`Gefundene Play-Buttons: ${playButtons.length}`);

if (playButtons.length === 0) {
  updateStatus("Keine Play-Buttons gefunden.");
} else {
  // Schritt 2: Zufälligen Button auswählen
  var randomIndex = Math.floor(Math.random() * playButtons.length);
  updateStatus(`Wähle zufälligen Button #${randomIndex + 1} von ${playButtons.length}`);

  // Schritt 3: Button klicken
  var chosenButton = playButtons[randomIndex];
  
  if (chosenButton.click) {
    chosenButton.click();
    updateStatus(`Button #${randomIndex + 1} wurde angeklickt.`);
  } else {
    updateStatus("Der Button unterstützt keinen Klick.");
  }
}

