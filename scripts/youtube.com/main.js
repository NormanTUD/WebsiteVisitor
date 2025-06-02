const intervalId = setInterval(() => {
  // Suche den Button anhand der Klasse und des Texts "Accept all"
  const buttons = document.querySelectorAll('button.yt-spec-button-shape-next');
  for (let btn of buttons) {
    // Sicherstellen, dass es der richtige Button mit Text "Accept all" ist
    if (btn.textContent.trim() === 'Accept all') {
      btn.click();
      clearInterval(intervalId); // Intervall stoppen, wenn Button geklickt
      break;
    }
  }
}, 500);
