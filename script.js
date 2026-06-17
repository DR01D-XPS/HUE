(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  function byId(id) {
    return document.getElementById(id);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const elements = {
      canvas: byId("gameCanvas"),
      canvasWrap: byId("canvasWrap"),
      hud: document.querySelector(".hud"),
      scoreValue: byId("scoreValue"),
      livesValue: byId("livesValue"),
      levelValue: byId("levelValue"),
      highScoreValue: byId("highScoreValue"),
      bonusMeter: byId("bonusMeter"),
      bonusValue: byId("bonusValue"),
      soundToggle: byId("soundToggle"),
      soundSetting: byId("soundSetting"),
      countdownLabel: byId("countdownLabel"),
      menuOverlay: byId("menuOverlay"),
      settingsOverlay: byId("settingsOverlay"),
      pauseOverlay: byId("pauseOverlay"),
      levelOverlay: byId("levelOverlay"),
      gameOverOverlay: byId("gameOverOverlay"),
      levelResultEyebrow: byId("levelResultEyebrow"),
      levelResultTitle: byId("levelResultTitle"),
      levelResultText: byId("levelResultText"),
      nextLevelButton: byId("nextLevelButton"),
      gameOverText: byId("gameOverText")
    };

    const game = new App.Game(elements);
    window.neonCrystalMaze = game;

    const difficultyRadios = Array.from(document.querySelectorAll("input[name='difficulty']"));
    difficultyRadios.forEach((radio) => {
      radio.checked = radio.value === game.difficultyKey;
      radio.addEventListener("change", () => {
        if (radio.checked) game.setDifficulty(radio.value);
      });
    });

    elements.soundSetting.checked = game.sound.enabled;
    elements.soundSetting.addEventListener("change", () => {
      game.setSound(elements.soundSetting.checked);
    });

    byId("playButton").addEventListener("click", () => game.startCampaign());
    byId("randomButton").addEventListener("click", () => game.startRandomLevel());
    byId("settingsButton").addEventListener("click", () => game.openSettings());
    byId("settingsBackButton").addEventListener("click", () => game.closeSettings());
    byId("resetHighScoreButton").addEventListener("click", () => game.resetHighScore());
    byId("resumeButton").addEventListener("click", () => game.resume());
    byId("pauseMenuButton").addEventListener("click", () => game.openMenu());
    byId("nextLevelButton").addEventListener("click", () => game.nextLevel());
    byId("levelMenuButton").addEventListener("click", () => game.openMenu());
    byId("restartButton").addEventListener("click", () => game.startCampaign());
    byId("gameOverMenuButton").addEventListener("click", () => game.openMenu());
    elements.soundToggle.addEventListener("click", () => game.toggleSound());

    window.addEventListener("keydown", (event) => {
      const direction = App.KEY_TO_DIR[event.code];
      if (direction) {
        event.preventDefault();
        game.handleDirection(direction);
        return;
      }

      if (event.code === "Escape") {
        event.preventDefault();
        if (elements.settingsOverlay.classList.contains("active")) {
          game.closeSettings();
        } else {
          game.togglePause();
        }
      } else if (event.code === "KeyP") {
        event.preventDefault();
        game.togglePause();
      }
    });

    document.querySelectorAll(".pad-btn").forEach((button) => {
      const direction = button.dataset.dir;
      const sendDirection = (event) => {
        event.preventDefault();
        game.handleDirection(direction);
      };
      button.addEventListener("pointerdown", sendDirection);
      button.addEventListener("click", sendDirection);
    });

    let touchStart = null;
    elements.canvas.addEventListener("touchstart", (event) => {
      const touch = event.changedTouches[0];
      touchStart = { x: touch.clientX, y: touch.clientY };
    }, { passive: true });

    elements.canvas.addEventListener("touchend", (event) => {
      if (!touchStart) return;
      const touch = event.changedTouches[0];
      const dx = touch.clientX - touchStart.x;
      const dy = touch.clientY - touchStart.y;
      touchStart = null;
      if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return;
      if (Math.abs(dx) > Math.abs(dy)) {
        game.handleDirection(dx > 0 ? "right" : "left");
      } else {
        game.handleDirection(dy > 0 ? "down" : "up");
      }
    }, { passive: true });

    document.addEventListener("visibilitychange", () => {
      if (document.hidden && game.state === "playing") {
        game.pause();
      }
    });

    game.startLoop();
  });
})();
