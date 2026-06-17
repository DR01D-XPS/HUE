(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  class SoundEngine {
    constructor() {
      this.enabled = localStorage.getItem("ncm.sound") !== "off";
      this.context = null;
      this.master = null;
    }

    ensureContext() {
      if (!this.context) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return null;
        this.context = new AudioContext();
        this.master = this.context.createGain();
        this.master.gain.value = 0.18;
        this.master.connect(this.context.destination);
      }
      if (this.context.state === "suspended") {
        this.context.resume();
      }
      return this.context;
    }

    setEnabled(enabled) {
      this.enabled = Boolean(enabled);
      localStorage.setItem("ncm.sound", this.enabled ? "on" : "off");
      if (this.enabled) this.ensureContext();
    }

    toggle() {
      this.setEnabled(!this.enabled);
      return this.enabled;
    }

    tone(freq, start, duration, type, volume, endFreq) {
      const ctx = this.ensureContext();
      if (!ctx || !this.enabled) return;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type || "sine";
      osc.frequency.setValueAtTime(freq, start);
      if (endFreq) {
        osc.frequency.exponentialRampToValueAtTime(Math.max(20, endFreq), start + duration);
      }
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(volume || 0.42, start + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
      osc.connect(gain);
      gain.connect(this.master);
      osc.start(start);
      osc.stop(start + duration + 0.02);
    }

    play(name) {
      if (!this.enabled) return;
      const ctx = this.ensureContext();
      if (!ctx) return;
      const now = ctx.currentTime;

      if (name === "dot") {
        this.tone(720, now, 0.055, "triangle", 0.24, 940);
      } else if (name === "bonus") {
        [420, 630, 880, 1180].forEach((freq, i) => {
          this.tone(freq, now + i * 0.055, 0.12, "sine", 0.34);
        });
      } else if (name === "enemy") {
        this.tone(520, now, 0.12, "square", 0.24, 240);
        this.tone(1040, now + 0.02, 0.12, "triangle", 0.16, 440);
      } else if (name === "life") {
        this.tone(360, now, 0.26, "sawtooth", 0.32, 90);
      } else if (name === "win") {
        [523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
          this.tone(freq, now + i * 0.08, 0.26, "triangle", 0.32);
        });
      } else if (name === "gameover") {
        [220, 164.81, 123.47].forEach((freq, i) => {
          this.tone(freq, now + i * 0.13, 0.36, "sawtooth", 0.28, freq * 0.72);
        });
      } else if (name === "portal") {
        this.tone(360, now, 0.18, "sine", 0.26, 720);
        this.tone(540, now + 0.06, 0.2, "triangle", 0.22, 1080);
      }
    }
  }

  App.SoundEngine = SoundEngine;
})();
