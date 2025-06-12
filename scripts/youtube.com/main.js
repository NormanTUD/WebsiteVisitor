const intervalId = setInterval(() => {
  const buttons = document.querySelectorAll('button.yt-spec-button-shape-next');
  for (let btn of buttons) {
    if (btn.textContent.trim() === 'Accept all') {
      btn.click();
      clearInterval(intervalId);
      break;
    }
  }
}, 1500);
