let cookieClicked = false;
let cookieIntervalId = null;
const startTime = Date.now();

function tryClickCookieButton() {
  const buttons = document.querySelectorAll(
    '.yt-spec-button-shape-next.yt-spec-button-shape-next--filled.yt-spec-button-shape-next--mono.yt-spec-button-shape-next--size-m.yt-spec-button-shape-next--enable-backdrop-filter-experiment'
  );

  let cookieButton = null;
  buttons.forEach(button => {
    let parent = button.closest('.eom-buttons.style-scope.ytd-consent-bump-v2-lightbox');
    if (parent) cookieButton = button;
  });

  if (cookieButton) {
    // Random wait 1-5s before click
    const randomDelay = 1000 + Math.random() * 4000;
    setTimeout(() => {
      if (!cookieClicked) {
        cookieButton.click();
        cookieClicked = true;
        clearInterval(cookieIntervalId);
        console.log('Cookie button clicked');
      }
    }, randomDelay);
    return true;
  }
  return false;
}

cookieIntervalId = setInterval(() => {
  if (cookieClicked) {
    clearInterval(cookieIntervalId);
    return;
  }

  const elapsed = Date.now() - startTime;
  if (elapsed > 60000) {
    // Fallback nach 1 Minute
    console.log('Fallback: Trying to click "Accept all" button');
    const buttons = document.querySelectorAll('button.yt-spec-button-shape-next');
    for (let btn of buttons) {
      if (btn.textContent.trim() === 'Accept all') {
        btn.click();
        cookieClicked = true;
        clearInterval(cookieIntervalId);
        console.log('"Accept all" button clicked');
        break;
      }
    }
    if (!cookieClicked) {
      console.log('No cookie button found after 1 minute');
      clearInterval(cookieIntervalId);
    }
  } else {
    tryClickCookieButton();
  }
}, 2000);
