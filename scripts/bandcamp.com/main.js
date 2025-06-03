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

