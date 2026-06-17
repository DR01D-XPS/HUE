(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  const TILE_WALL = "wall";
  const TILE_EMPTY = "empty";
  const TILE_DOT = "dot";
  const TILE_POWER = "power";

  class Game {
    constructor(elements) {
      this.elements = elements;
      this.canvas = elements.canvas;
      this.ctx = this.canvas.getContext("2d");
      this.sound = new App.SoundEngine();

      this.state = "menu";
      this.score = 0;
      this.lives = 3;
      this.levelNumber = 1;
      this.highScore = Number(localStorage.getItem("ncm.highScore") || 0);
      this.difficultyKey = localStorage.getItem("ncm.difficulty") || "normal";
      this.difficulty = App.DIFFICULTY[this.difficultyKey] || App.DIFFICULTY.normal;

      this.map = [];
      this.cols = 19;
      this.rows = 15;
      this.tile = 32;
      this.offsetX = 0;
      this.offsetY = 0;
      this.player = null;
      this.enemies = [];
      this.enemyStarts = [];
      this.playerStart = { x: 1, y: 1 };
      this.portal = { x: 1, y: 1 };
      this.portalActive = false;
      this.dotsRemaining = 0;
      this.frightenedTimer = 0;
      this.enemyHoldTimer = 0;
      this.lifePauseTimer = 0;
      this.transitionTimer = 0;
      this.particles = [];
      this.playerDistance = [];
      this.distanceTimer = 0;
      this.lastPlayerDistanceTile = null;
      this.lastTime = 0;
      this.animationTime = 0;
      this.running = false;

      this.resizeCanvas();
      this.updateHud();
      this.updateSoundButton();
      window.addEventListener("resize", () => this.resizeCanvas());
    }

    startLoop() {
      if (this.running) return;
      this.running = true;
      this.lastTime = performance.now();
      requestAnimationFrame((time) => this.loop(time));
    }

    loop(time) {
      const dt = Math.min(0.05, (time - this.lastTime) / 1000 || 0);
      this.lastTime = time;
      this.animationTime += dt;
      this.update(dt);
      this.render();
      requestAnimationFrame((next) => this.loop(next));
    }

    setDifficulty(key) {
      this.difficultyKey = App.DIFFICULTY[key] ? key : "normal";
      this.difficulty = App.DIFFICULTY[this.difficultyKey];
      localStorage.setItem("ncm.difficulty", this.difficultyKey);
    }

    setSound(enabled) {
      this.sound.setEnabled(enabled);
      this.updateSoundButton();
    }

    toggleSound() {
      this.sound.toggle();
      this.updateSoundButton();
    }

    resetHighScore() {
      this.highScore = 0;
      localStorage.setItem("ncm.highScore", "0");
      this.updateHud();
    }

    showOverlay(name) {
      const overlays = [
        this.elements.menuOverlay,
        this.elements.settingsOverlay,
        this.elements.pauseOverlay,
        this.elements.levelOverlay,
        this.elements.gameOverOverlay
      ];
      overlays.forEach((overlay) => overlay.classList.remove("active"));
      if (name && this.elements[name]) {
        this.elements[name].classList.add("active");
      }
    }

    openMenu() {
      this.state = "menu";
      this.showOverlay("menuOverlay");
      this.updateCountdown("");
    }

    openSettings() {
      this.state = this.state === "playing" ? "paused" : this.state;
      this.showOverlay("settingsOverlay");
    }

    closeSettings() {
      if (this.state === "paused") {
        this.showOverlay("pauseOverlay");
      } else {
        this.state = "menu";
        this.showOverlay("menuOverlay");
      }
    }

    startCampaign() {
      this.score = 0;
      this.lives = this.difficulty.lives;
      this.levelNumber = 1;
      this.loadLevel(this.levelNumber);
    }

    startRandomLevel() {
      this.score = 0;
      this.lives = this.difficulty.lives;
      this.levelNumber = App.LEVELS.length + App.randInt(1, 6);
      this.loadLevel(this.levelNumber);
    }

    nextLevel() {
      this.levelNumber += 1;
      this.loadLevel(this.levelNumber);
    }

    loadLevel(levelNumber) {
      const source = levelNumber <= App.LEVELS.length
        ? App.LEVELS[levelNumber - 1]
        : App.Generator.generateLevel(levelNumber, this.difficultyKey);

      const validation = App.Generator.validateLayout(source.layout);
      if (!validation.ok) {
        console.warn("Level validation warning:", validation.reason, source.name);
      }

      this.currentLevel = source;
      this.parseLevel(source);
      this.portalActive = false;
      this.frightenedTimer = 0;
      this.enemyHoldTimer = this.difficulty.enemyDelay;
      this.lifePauseTimer = 0;
      this.transitionTimer = 0.75;
      this.particles = [];
      this.state = "playing";
      this.showOverlay(null);
      this.resizeCanvas();
      this.rebuildPlayerDistances(true);
      this.updateHud();
      if (this.sound.enabled) this.sound.ensureContext();
      this.updateCountdown("Старт");
      window.setTimeout(() => {
        if (this.state === "playing" && this.enemyHoldTimer <= this.difficulty.enemyDelay) {
          this.updateCountdown("");
        }
      }, 650);
    }

    parseLevel(source) {
      const layout = source.layout;
      this.rows = layout.length;
      this.cols = layout[0].length;
      this.map = Array.from({ length: this.rows }, () => Array(this.cols).fill(TILE_EMPTY));
      this.enemyStarts = [];
      this.dotsRemaining = 0;

      for (let y = 0; y < this.rows; y += 1) {
        for (let x = 0; x < this.cols; x += 1) {
          const char = layout[y][x];
          if (char === "#") {
            this.map[y][x] = TILE_WALL;
          } else if (char === ".") {
            this.map[y][x] = TILE_DOT;
            this.dotsRemaining += 1;
          } else if (char === "o") {
            this.map[y][x] = TILE_POWER;
            this.dotsRemaining += 1;
          } else {
            this.map[y][x] = TILE_EMPTY;
          }

          if (char === "P") {
            this.playerStart = { x, y };
          } else if (char === "X") {
            this.portal = { x, y };
          } else if (char === "C" || char === "R" || char === "A") {
            this.enemyStarts.push({ x, y, type: App.enemyTypeFromChar(char) });
          }
        }
      }

      const playerSpeed = (source.playerSpeed || 5.85) * this.difficulty.playerSpeed;
      if (!this.player) {
        this.player = new App.Player(this.playerStart, playerSpeed);
      }
      this.player.reset(this.playerStart, playerSpeed);

      const enemySpeed = (source.enemySpeed || 3.2) * this.difficulty.enemySpeed;
      this.enemies = this.enemyStarts.map((start, index) => {
        const typeMultiplier = start.type === "random" ? 0.95 : start.type === "ambusher" ? 1.03 : 1;
        return new App.Enemy(start.type, start, enemySpeed * typeMultiplier, index);
      });
    }

    pause() {
      if (this.state !== "playing") return;
      this.state = "paused";
      this.showOverlay("pauseOverlay");
      this.updateCountdown("");
    }

    resume() {
      if (this.state !== "paused") return;
      this.state = "playing";
      this.showOverlay(null);
    }

    togglePause() {
      if (this.state === "playing") this.pause();
      else if (this.state === "paused") this.resume();
    }

    handleDirection(name) {
      if (!this.player) return;
      if (this.state === "menu") return;
      this.player.setDirection(name);
      this.sound.ensureContext();
    }

    update(dt) {
      this.updateParticles(dt);

      if (this.state !== "playing") {
        this.updateHud();
        return;
      }

      this.transitionTimer = Math.max(0, this.transitionTimer - dt);
      this.enemyHoldTimer = Math.max(0, this.enemyHoldTimer - dt);
      this.frightenedTimer = Math.max(0, this.frightenedTimer - dt);

      if (this.lifePauseTimer > 0) {
        this.lifePauseTimer = Math.max(0, this.lifePauseTimer - dt);
        this.updateCountdown(Math.ceil(this.lifePauseTimer).toString());
        if (this.lifePauseTimer === 0) this.updateCountdown("");
        this.updateHud();
        return;
      }

      this.player.update(dt, this);
      this.collectAtPlayer();
      this.rebuildPlayerDistances(false);

      for (const enemy of this.enemies) {
        enemy.update(dt, this);
      }

      this.checkCollisions();
      this.checkPortal();
      this.updateHud();
    }

    updateHud() {
      this.elements.scoreValue.textContent = Math.floor(this.score).toString();
      this.elements.livesValue.textContent = this.lives.toString();
      this.elements.levelValue.textContent = this.levelNumber.toString();
      this.elements.highScoreValue.textContent = this.highScore.toString();
      this.elements.bonusValue.textContent = this.frightenedTimer > 0 ? this.frightenedTimer.toFixed(1) : "0.0";
      this.elements.bonusMeter.classList.toggle("active", this.frightenedTimer > 0);
    }

    updateSoundButton() {
      const enabled = this.sound.enabled;
      this.elements.soundToggle.classList.toggle("muted", !enabled);
      this.elements.soundToggle.textContent = enabled ? "♪" : "×";
      this.elements.soundToggle.setAttribute("aria-label", enabled ? "Звук включён" : "Звук выключен");
      if (this.elements.soundSetting) {
        this.elements.soundSetting.checked = enabled;
      }
    }

    updateCountdown(text) {
      const label = this.elements.countdownLabel;
      label.textContent = text || "";
      label.classList.toggle("show", Boolean(text));
    }

    canMoveFrom(x, y, dir) {
      if (!dir || dir.name === "none") return false;
      const nx = Math.round(x) + dir.x;
      const ny = Math.round(y) + dir.y;
      return this.isWalkable(nx, ny);
    }

    isWalkable(x, y) {
      return y >= 0 && y < this.rows && x >= 0 && x < this.cols && this.map[y][x] !== TILE_WALL;
    }

    legalDirs(tile) {
      return App.DIR_LIST.filter((dir) => this.canMoveFrom(tile.x, tile.y, dir));
    }

    collectAtPlayer() {
      const tile = this.player.tile();
      if (!this.isWalkable(tile.x, tile.y)) return;
      const current = this.map[tile.y][tile.x];
      if (current !== TILE_DOT && current !== TILE_POWER) return;

      this.map[tile.y][tile.x] = TILE_EMPTY;
      this.dotsRemaining -= 1;

      if (current === TILE_POWER) {
        this.score += 50 * this.difficulty.scoreBonus;
        this.frightenedTimer = this.difficulty.powerTime;
        this.enemies.forEach((enemy) => {
          enemy.pathTimer = 0;
        });
        this.spawnBurst(tile.x, tile.y, "#ffd166", 34, 1.45);
        this.sound.play("bonus");
      } else {
        this.score += 10 * this.difficulty.scoreBonus;
        this.spawnBurst(tile.x, tile.y, "#7df9ff", 8, 0.7);
        this.sound.play("dot");
      }

      if (this.dotsRemaining <= 0 && !this.portalActive) {
        this.portalActive = true;
        this.spawnBurst(this.portal.x, this.portal.y, "#8bffb0", 46, 1.7);
        this.sound.play("portal");
      }

      this.saveHighScore();
    }

    checkPortal() {
      if (!this.portalActive) return;
      const tile = this.player.tile();
      if (tile.x === this.portal.x && tile.y === this.portal.y) {
        this.completeLevel();
      }
    }

    checkCollisions() {
      for (const enemy of this.enemies) {
        if (!enemy.isActive()) continue;
        const distance = Math.hypot(enemy.x - this.player.x, enemy.y - this.player.y);
        if (distance > 0.48) continue;

        if (this.frightenedTimer > 0) {
          this.score += 250 * this.difficulty.scoreBonus;
          enemy.sendHome(1.1);
          this.spawnBurst(enemy.x, enemy.y, "#b8ecff", 26, 1.2);
          this.sound.play("enemy");
          this.saveHighScore();
        } else if (this.player.invulnerableTimer <= 0) {
          this.loseLife();
          break;
        }
      }
    }

    loseLife() {
      this.lives -= 1;
      this.sound.play("life");
      this.spawnBurst(this.player.x, this.player.y, "#ff4f6d", 32, 1.35);

      if (this.lives <= 0) {
        this.gameOver();
        return;
      }

      const playerSpeed = (this.currentLevel.playerSpeed || 5.85) * this.difficulty.playerSpeed;
      this.player.reset(this.playerStart, playerSpeed);
      this.enemies.forEach((enemy) => enemy.reset());
      this.frightenedTimer = 0;
      this.enemyHoldTimer = this.difficulty.enemyDelay + 0.6;
      this.lifePauseTimer = 1.6;
      this.updateCountdown("2");
    }

    completeLevel() {
      if (this.state !== "playing") return;
      this.state = "levelComplete";
      this.score += Math.max(250, this.levelNumber * 80) * this.difficulty.scoreBonus;
      this.saveHighScore();
      this.spawnBurst(this.portal.x, this.portal.y, "#8bffb0", 80, 2.2);
      this.sound.play("win");

      const preparedDone = this.levelNumber === App.LEVELS.length;
      this.elements.levelResultEyebrow.textContent = preparedDone ? "режим генератора открыт" : "портал открыт";
      this.elements.levelResultTitle.textContent = preparedDone ? "Все готовые уровни пройдены" : "Уровень пройден";
      this.elements.levelResultText.textContent = preparedDone
        ? "Дальше игра будет создавать новые проходимые лабиринты автоматически."
        : `Лабиринт «${this.currentLevel.name}» очищен.`;
      this.elements.nextLevelButton.textContent = preparedDone ? "Создать лабиринт" : "Следующий уровень";
      this.showOverlay("levelOverlay");
      this.updateCountdown("");
      this.updateHud();
    }

    gameOver() {
      this.state = "gameOver";
      this.saveHighScore();
      this.elements.gameOverText.textContent = `Очки: ${Math.floor(this.score)}. Рекорд: ${this.highScore}.`;
      this.sound.play("gameover");
      this.showOverlay("gameOverOverlay");
      this.updateCountdown("");
      this.updateHud();
    }

    saveHighScore() {
      if (this.score > this.highScore) {
        this.highScore = Math.floor(this.score);
        localStorage.setItem("ncm.highScore", String(this.highScore));
      }
    }

    rebuildPlayerDistances(force) {
      this.distanceTimer -= 1 / 60;
      const tile = this.player.tile();
      const changedTile = !this.lastPlayerDistanceTile ||
        this.lastPlayerDistanceTile.x !== tile.x ||
        this.lastPlayerDistanceTile.y !== tile.y;

      if (!force && !changedTile && this.distanceTimer > 0) return;

      this.lastPlayerDistanceTile = tile;
      this.distanceTimer = 0.25;
      this.playerDistance = Array.from({ length: this.rows }, () => Array(this.cols).fill(Infinity));
      const queue = [tile];
      let head = 0;
      this.playerDistance[tile.y][tile.x] = 0;

      while (head < queue.length) {
        const current = queue[head];
        head += 1;
        for (const dir of App.DIR_LIST) {
          const next = { x: current.x + dir.x, y: current.y + dir.y };
          if (!this.isWalkable(next.x, next.y)) continue;
          if (this.playerDistance[next.y][next.x] !== Infinity) continue;
          this.playerDistance[next.y][next.x] = this.playerDistance[current.y][current.x] + 1;
          queue.push(next);
        }
      }
    }

    getDistanceFromPlayer(cell) {
      if (!this.playerDistance[cell.y] || this.playerDistance[cell.y][cell.x] === undefined) return 0;
      const distance = this.playerDistance[cell.y][cell.x];
      return distance === Infinity ? 0 : distance;
    }

    getAmbushTarget(stepsAhead) {
      const playerTile = this.player.tile();
      const dir = this.player.dir.name !== "none" ? this.player.dir : this.player.desiredDir;
      const ideal = {
        x: playerTile.x + dir.x * stepsAhead,
        y: playerTile.y + dir.y * stepsAhead
      };
      return this.findNearestWalkable(ideal);
    }

    findNearestWalkable(target) {
      let best = this.player.tile();
      let bestScore = Infinity;
      for (let y = 0; y < this.rows; y += 1) {
        for (let x = 0; x < this.cols; x += 1) {
          if (!this.isWalkable(x, y)) continue;
          const score = Math.abs(x - target.x) + Math.abs(y - target.y);
          if (score < bestScore) {
            bestScore = score;
            best = { x, y };
          }
        }
      }
      return best;
    }

    findPathDirection(start, target, currentDir) {
      if (!this.isWalkable(start.x, start.y)) return App.DIRS.none;
      const realTarget = this.isWalkable(target.x, target.y) ? target : this.findNearestWalkable(target);
      if (start.x === realTarget.x && start.y === realTarget.y) return App.DIRS.none;

      const visited = Array.from({ length: this.rows }, () => Array(this.cols).fill(false));
      const firstStep = Array.from({ length: this.rows }, () => Array(this.cols).fill(null));
      const queue = [start];
      let head = 0;
      visited[start.y][start.x] = true;

      const preferred = [];
      if (currentDir && currentDir.name !== "none") preferred.push(currentDir);
      for (const dir of App.DIR_LIST) {
        if (!preferred.some((candidate) => App.sameDir(candidate, dir))) preferred.push(dir);
      }

      while (head < queue.length) {
        const current = queue[head];
        head += 1;
        for (const dir of preferred) {
          const next = { x: current.x + dir.x, y: current.y + dir.y };
          if (!this.isWalkable(next.x, next.y) || visited[next.y][next.x]) continue;
          visited[next.y][next.x] = true;
          firstStep[next.y][next.x] = current.x === start.x && current.y === start.y ? dir : firstStep[current.y][current.x];
          if (next.x === realTarget.x && next.y === realTarget.y) {
            return firstStep[next.y][next.x] || App.DIRS.none;
          }
          queue.push(next);
        }
      }

      return App.DIRS.none;
    }

    spawnBurst(x, y, color, count, strength) {
      const amount = count || 12;
      const power = strength || 1;
      for (let i = 0; i < amount; i += 1) {
        const angle = Math.random() * Math.PI * 2;
        const speed = (0.7 + Math.random() * 2.2) * power;
        this.particles.push({
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 0.42 + Math.random() * 0.52,
          maxLife: 0.75,
          size: 0.05 + Math.random() * 0.09,
          color
        });
      }
    }

    updateParticles(dt) {
      for (const particle of this.particles) {
        particle.life -= dt;
        particle.x += particle.vx * dt;
        particle.y += particle.vy * dt;
        particle.vx *= 1 - dt * 1.8;
        particle.vy *= 1 - dt * 1.8;
      }
      this.particles = this.particles.filter((particle) => particle.life > 0);
    }

    resizeCanvas() {
      const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
      const wrap = this.elements.canvasWrap;
      const panelWidth = Math.max(320, wrap.clientWidth || window.innerWidth - 36);
      const hudHeight = this.elements.hud ? this.elements.hud.offsetHeight : 70;
      const touchSpace = window.matchMedia("(pointer: coarse)").matches || window.innerWidth < 760 ? 190 : 34;
      const availableHeight = Math.max(260, window.innerHeight - hudHeight - touchSpace - 42);
      const aspect = this.cols / this.rows;

      let cssWidth = Math.min(panelWidth - 18, availableHeight * aspect);
      let cssHeight = cssWidth / aspect;
      if (cssHeight > availableHeight) {
        cssHeight = availableHeight;
        cssWidth = cssHeight * aspect;
      }

      cssWidth = Math.max(280, Math.floor(cssWidth));
      cssHeight = Math.max(220, Math.floor(cssHeight));
      this.canvas.style.width = `${cssWidth}px`;
      this.canvas.style.height = `${cssHeight}px`;
      this.canvas.width = Math.floor(cssWidth * dpr);
      this.canvas.height = Math.floor(cssHeight * dpr);
      this.tile = Math.min(this.canvas.width / this.cols, this.canvas.height / this.rows);
      this.offsetX = (this.canvas.width - this.tile * this.cols) / 2;
      this.offsetY = (this.canvas.height - this.tile * this.rows) / 2;
    }

    cellCenter(x, y) {
      return {
        x: this.offsetX + (x + 0.5) * this.tile,
        y: this.offsetY + (y + 0.5) * this.tile
      };
    }

    render() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.drawBackdrop(ctx);

      if (this.map.length === 0) return;

      this.drawCollectibles(ctx);
      this.drawPortal(ctx);
      this.drawWalls(ctx);
      this.drawEnemies(ctx);
      this.drawPlayer(ctx);
      this.drawParticles(ctx);
      this.drawTransition(ctx);
    }

    drawBackdrop(ctx) {
      const gradient = ctx.createLinearGradient(0, 0, this.canvas.width, this.canvas.height);
      gradient.addColorStop(0, "#050713");
      gradient.addColorStop(0.52, "#101530");
      gradient.addColorStop(1, "#050711");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

      ctx.save();
      ctx.globalAlpha = 0.22;
      ctx.strokeStyle = "#1a3554";
      ctx.lineWidth = 1;
      const grid = Math.max(22, this.tile);
      for (let x = (this.animationTime * 9) % grid; x < this.canvas.width; x += grid) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, this.canvas.height);
        ctx.stroke();
      }
      for (let y = (this.animationTime * 6) % grid; y < this.canvas.height; y += grid) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(this.canvas.width, y);
        ctx.stroke();
      }
      ctx.restore();
    }

    roundedRect(ctx, x, y, w, h, radius) {
      const r = Math.min(radius, w / 2, h / 2);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    drawWalls(ctx) {
      const pad = this.tile * 0.045;
      const radius = this.tile * 0.18;

      ctx.save();
      for (let y = 0; y < this.rows; y += 1) {
        for (let x = 0; x < this.cols; x += 1) {
          if (this.map[y][x] !== TILE_WALL) continue;

          const px = this.offsetX + x * this.tile + pad;
          const py = this.offsetY + y * this.tile + pad;
          const size = this.tile - pad * 2;
          const glow = 0.55 + Math.sin(this.animationTime * 2 + x * 0.47 + y * 0.3) * 0.12;

          ctx.shadowColor = `rgba(53, 232, 255, ${0.34 * glow})`;
          ctx.shadowBlur = this.tile * 0.22;
          const fill = ctx.createLinearGradient(px, py, px + size, py + size);
          fill.addColorStop(0, "#173264");
          fill.addColorStop(0.45, "#16204b");
          fill.addColorStop(1, "#2b1760");
          ctx.fillStyle = fill;
          this.roundedRect(ctx, px, py, size, size, radius);
          ctx.fill();

          ctx.shadowBlur = 0;
          ctx.lineWidth = Math.max(1, this.tile * 0.035);
          ctx.strokeStyle = "rgba(126, 245, 255, 0.38)";
          ctx.stroke();
          ctx.strokeStyle = "rgba(255, 79, 184, 0.14)";
          ctx.strokeRect(px + size * 0.2, py + size * 0.2, size * 0.6, size * 0.6);
        }
      }
      ctx.restore();
    }

    drawCollectibles(ctx) {
      ctx.save();
      for (let y = 0; y < this.rows; y += 1) {
        for (let x = 0; x < this.cols; x += 1) {
          const type = this.map[y][x];
          if (type !== TILE_DOT && type !== TILE_POWER) continue;
          const center = this.cellCenter(x, y);
          const pulse = 0.82 + Math.sin(this.animationTime * 5.4 + x + y) * 0.18;

          if (type === TILE_POWER) {
            const radius = this.tile * (0.18 + pulse * 0.03);
            ctx.shadowColor = "rgba(255, 209, 102, 0.85)";
            ctx.shadowBlur = this.tile * 0.28;
            ctx.fillStyle = "#ffd166";
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.lineWidth = Math.max(1, this.tile * 0.035);
            ctx.strokeStyle = "rgba(255, 255, 255, 0.55)";
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius * 1.72, 0, Math.PI * 2);
            ctx.stroke();
          } else {
            const radius = this.tile * (0.075 + pulse * 0.008);
            ctx.shadowColor = "rgba(125, 249, 255, 0.72)";
            ctx.shadowBlur = this.tile * 0.15;
            ctx.fillStyle = "#d8fcff";
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
      ctx.restore();
    }

    drawPortal(ctx) {
      const center = this.cellCenter(this.portal.x, this.portal.y);
      const pulse = this.portalActive ? 1 : 0.36;
      const spin = this.animationTime * (this.portalActive ? 2.7 : 0.8);
      ctx.save();
      ctx.translate(center.x, center.y);
      ctx.globalAlpha = this.portalActive ? 1 : 0.42;
      ctx.shadowColor = this.portalActive ? "rgba(139, 255, 176, 0.85)" : "rgba(94, 124, 160, 0.45)";
      ctx.shadowBlur = this.tile * 0.35 * pulse;
      for (let i = 0; i < 3; i += 1) {
        ctx.rotate(spin * (i % 2 === 0 ? 1 : -1));
        ctx.lineWidth = Math.max(2, this.tile * (0.035 + i * 0.01));
        ctx.strokeStyle = i === 1 ? "#35e8ff" : this.portalActive ? "#8bffb0" : "#5e7ca0";
        ctx.beginPath();
        ctx.ellipse(0, 0, this.tile * (0.22 + i * 0.09), this.tile * (0.36 + i * 0.05), spin + i, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }

    drawPlayer(ctx) {
      if (!this.player) return;
      const center = this.cellCenter(this.player.x, this.player.y);
      const radius = this.tile * (0.36 + Math.sin(this.player.motionTime * 8) * 0.018);
      const dir = this.player.dir.name !== "none" ? this.player.dir : this.player.desiredDir;
      const blink = this.player.invulnerableTimer > 0 && Math.floor(this.animationTime * 16) % 2 === 0;

      ctx.save();
      ctx.globalAlpha = blink ? 0.48 : 1;
      ctx.shadowColor = "rgba(53, 232, 255, 0.85)";
      ctx.shadowBlur = this.tile * 0.35;
      const body = ctx.createRadialGradient(center.x - radius * 0.35, center.y - radius * 0.45, radius * 0.1, center.x, center.y, radius);
      body.addColorStop(0, "#ffffff");
      body.addColorStop(0.25, "#94fff1");
      body.addColorStop(0.76, "#35e8ff");
      body.addColorStop(1, "#3578ff");
      ctx.fillStyle = body;
      ctx.beginPath();
      ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
      ctx.fill();

      ctx.shadowBlur = 0;
      ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
      const eyeOffsetX = dir.x * radius * 0.18;
      const eyeOffsetY = dir.y * radius * 0.18;
      const eyeY = center.y - radius * 0.18 + eyeOffsetY;
      const leftEyeX = center.x - radius * 0.22 + eyeOffsetX;
      const rightEyeX = center.x + radius * 0.22 + eyeOffsetX;
      ctx.beginPath();
      ctx.arc(leftEyeX, eyeY, radius * 0.14, 0, Math.PI * 2);
      ctx.arc(rightEyeX, eyeY, radius * 0.14, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#071023";
      ctx.beginPath();
      ctx.arc(leftEyeX + dir.x * radius * 0.05, eyeY + dir.y * radius * 0.05, radius * 0.06, 0, Math.PI * 2);
      ctx.arc(rightEyeX + dir.x * radius * 0.05, eyeY + dir.y * radius * 0.05, radius * 0.06, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "rgba(255, 255, 255, 0.42)";
      ctx.lineWidth = Math.max(1, this.tile * 0.025);
      ctx.beginPath();
      ctx.arc(center.x, center.y, radius * 1.12, 0.2 + this.animationTime * 2, Math.PI * 1.35 + this.animationTime * 2);
      ctx.stroke();
      ctx.restore();
    }

    drawEnemies(ctx) {
      for (const enemy of this.enemies) {
        const center = this.cellCenter(enemy.x, enemy.y);
        const frightened = this.frightenedTimer > 0;
        const flashing = frightened && this.frightenedTimer < 2 && Math.floor(this.animationTime * 8) % 2 === 0;
        const color = frightened ? (flashing ? "#ffffff" : "#8fd7ff") : enemy.color;
        const radius = this.tile * (0.32 + Math.sin(enemy.wobble) * 0.018);
        const inactive = enemy.respawnTimer > 0;

        ctx.save();
        ctx.globalAlpha = inactive ? 0.36 : 1;
        ctx.translate(center.x, center.y);
        ctx.rotate(Math.sin(enemy.wobble * 0.8) * 0.1);
        ctx.shadowColor = color;
        ctx.shadowBlur = this.tile * 0.28;
        ctx.fillStyle = color;
        ctx.beginPath();
        if (enemy.type === "ambusher") {
          ctx.moveTo(0, -radius * 1.1);
          ctx.lineTo(radius * 0.95, 0);
          ctx.lineTo(0, radius * 1.1);
          ctx.lineTo(-radius * 0.95, 0);
          ctx.closePath();
        } else if (enemy.type === "random") {
          for (let i = 0; i < 6; i += 1) {
            const a = -Math.PI / 2 + i * Math.PI / 3;
            const r = i % 2 === 0 ? radius * 1.02 : radius * 0.78;
            const px = Math.cos(a) * r;
            const py = Math.sin(a) * r;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
        } else {
          ctx.arc(0, 0, radius, 0, Math.PI * 2);
        }
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
        ctx.beginPath();
        ctx.arc(-radius * 0.22, -radius * 0.14, radius * 0.13, 0, Math.PI * 2);
        ctx.arc(radius * 0.22, -radius * 0.14, radius * 0.13, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#080b16";
        const look = frightened ? App.oppositeDir(enemy.dir) : enemy.dir;
        ctx.beginPath();
        ctx.arc(-radius * 0.22 + look.x * radius * 0.05, -radius * 0.14 + look.y * radius * 0.05, radius * 0.055, 0, Math.PI * 2);
        ctx.arc(radius * 0.22 + look.x * radius * 0.05, -radius * 0.14 + look.y * radius * 0.05, radius * 0.055, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    drawParticles(ctx) {
      ctx.save();
      for (const particle of this.particles) {
        const center = this.cellCenter(particle.x, particle.y);
        const alpha = App.clamp(particle.life / particle.maxLife, 0, 1);
        ctx.globalAlpha = alpha;
        ctx.shadowColor = particle.color;
        ctx.shadowBlur = this.tile * 0.18;
        ctx.fillStyle = particle.color;
        ctx.beginPath();
        ctx.arc(center.x, center.y, particle.size * this.tile, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }

    drawTransition(ctx) {
      if (this.transitionTimer <= 0) return;
      const alpha = App.clamp(this.transitionTimer / 0.75, 0, 1);
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = "#02040c";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = "#edf7ff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = `${Math.max(18, this.tile * 0.48)}px Inter, sans-serif`;
      ctx.fillText(this.currentLevel ? this.currentLevel.name : "", this.canvas.width / 2, this.canvas.height / 2);
      ctx.restore();
    }
  }

  App.Game = Game;
})();
