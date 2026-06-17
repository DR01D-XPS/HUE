(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  const TYPE_COLORS = {
    chaser: "#ff4f6d",
    random: "#b76dff",
    ambusher: "#67ff9a"
  };

  class Enemy extends App.GridMover {
    constructor(type, start, speed, index) {
      super(start.x, start.y, speed);
      this.type = type;
      this.spawn = { ...start };
      this.baseSpeed = speed;
      this.index = index;
      this.color = TYPE_COLORS[type] || "#ff4f6d";
      this.pathTimer = 0;
      this.respawnTimer = 0;
      this.wobble = Math.random() * Math.PI * 2;
    }

    reset(speed) {
      this.x = this.spawn.x;
      this.y = this.spawn.y;
      this.speed = speed || this.baseSpeed;
      this.baseSpeed = this.speed;
      this.dir = App.DIRS.none;
      this.desiredDir = App.DIRS.none;
      this.pathTimer = 0;
      this.respawnTimer = 0;
    }

    sendHome(delay) {
      this.x = this.spawn.x;
      this.y = this.spawn.y;
      this.dir = App.DIRS.none;
      this.desiredDir = App.DIRS.none;
      this.pathTimer = 0;
      this.respawnTimer = delay || 1.15;
    }

    isActive() {
      return this.respawnTimer <= 0;
    }

    legalDirs(game, avoidReverse) {
      const tile = this.tile();
      let options = App.DIR_LIST.filter((dir) => game.canMoveFrom(tile.x, tile.y, dir));
      if (avoidReverse && this.dir.name !== "none" && options.length > 1) {
        const reverse = App.oppositeDir(this.dir);
        const withoutReverse = options.filter((dir) => !App.sameDir(dir, reverse));
        if (withoutReverse.length > 0) options = withoutReverse;
      }
      return options;
    }

    chooseRandomDirection(game) {
      const options = this.legalDirs(game, true);
      if (options.length === 0) return App.DIRS.none;

      const currentWorks = this.dir.name !== "none" && options.some((dir) => App.sameDir(dir, this.dir));
      const atJunction = options.length >= 3 || !currentWorks;
      if (!atJunction && currentWorks && Math.random() > 0.08) {
        return this.dir;
      }

      return options[Math.floor(Math.random() * options.length)];
    }

    chooseFleeDirection(game) {
      const options = this.legalDirs(game, true);
      if (options.length === 0) return App.DIRS.none;
      const tile = this.tile();
      let best = options[0];
      let bestScore = -Infinity;

      for (const dir of options) {
        const next = { x: tile.x + dir.x, y: tile.y + dir.y };
        const score = game.getDistanceFromPlayer(next) + Math.random() * 0.35;
        if (score > bestScore) {
          bestScore = score;
          best = dir;
        }
      }

      return best;
    }

    chooseHunterDirection(game) {
      const tile = this.tile();
      let target = game.player.tile();
      if (this.type === "ambusher") {
        target = game.getAmbushTarget(4);
      }

      const pathDir = game.findPathDirection(tile, target, this.dir);
      if (pathDir && pathDir.name !== "none") return pathDir;
      return this.chooseRandomDirection(game);
    }

    chooseDirection(game) {
      if (game.enemyHoldTimer > 0) return App.DIRS.none;
      if (game.frightenedTimer > 0) return this.chooseFleeDirection(game);
      if (this.type === "random") return this.chooseRandomDirection(game);
      return this.chooseHunterDirection(game);
    }

    update(dt, game) {
      this.wobble += dt * 5;

      if (this.respawnTimer > 0) {
        this.respawnTimer = Math.max(0, this.respawnTimer - dt);
        return;
      }

      const frightened = game.frightenedTimer > 0;
      this.speed = this.baseSpeed * (frightened ? 0.86 : 1);
      this.pathTimer -= dt;

      this.advance(dt, (x, y, dir) => game.canMoveFrom(x, y, dir), () => {
        const needsNewPath = this.pathTimer <= 0 || this.dir.name === "none" || !game.canMoveFrom(this.tile().x, this.tile().y, this.dir);
        if (needsNewPath) {
          this.desiredDir = this.chooseDirection(game);
          this.pathTimer = frightened ? 0.34 : this.type === "random" ? 0.22 : 0.42;
        }
        if (this.desiredDir.name !== "none" && game.canMoveFrom(this.tile().x, this.tile().y, this.desiredDir)) {
          this.dir = this.desiredDir;
        } else if (this.dir.name !== "none" && !game.canMoveFrom(this.tile().x, this.tile().y, this.dir)) {
          this.dir = this.chooseRandomDirection(game);
        }
      });
    }
  }

  App.Enemy = Enemy;
})();
