(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  class GridMover {
    constructor(x, y, speed) {
      this.x = x;
      this.y = y;
      this.speed = speed;
      this.dir = App.DIRS.none;
      this.desiredDir = App.DIRS.none;
    }

    isAtCenter(epsilon) {
      const eps = epsilon || 0.035;
      return Math.abs(this.x - Math.round(this.x)) < eps && Math.abs(this.y - Math.round(this.y)) < eps;
    }

    snapToCenter() {
      this.x = Math.round(this.x);
      this.y = Math.round(this.y);
    }

    tile() {
      return { x: Math.round(this.x), y: Math.round(this.y) };
    }

    setDirection(name) {
      this.desiredDir = App.DIRS[name] || App.DIRS.none;
    }

    nextCenter() {
      if (this.dir.x > 0) return { x: Math.floor(this.x + 0.0001) + 1, y: this.y };
      if (this.dir.x < 0) return { x: Math.ceil(this.x - 0.0001) - 1, y: this.y };
      if (this.dir.y > 0) return { x: this.x, y: Math.floor(this.y + 0.0001) + 1 };
      if (this.dir.y < 0) return { x: this.x, y: Math.ceil(this.y - 0.0001) - 1 };
      return { x: this.x, y: this.y };
    }

    advance(dt, canMove, chooseDirection) {
      let remaining = this.speed * dt;
      let guard = 0;

      while (remaining > 0.0001 && guard < 8) {
        guard += 1;

        if (this.isAtCenter()) {
          this.snapToCenter();
          if (chooseDirection) chooseDirection(this);
          if (this.dir.name === "none" || !canMove(this.tile().x, this.tile().y, this.dir)) {
            this.dir = App.DIRS.none;
            break;
          }
        }

        if (this.dir.name === "none") break;

        const target = this.nextCenter();
        const dx = target.x - this.x;
        const dy = target.y - this.y;
        const distanceToTarget = Math.hypot(dx, dy);

        if (distanceToTarget < 0.0001) {
          this.x = target.x;
          this.y = target.y;
          continue;
        }

        const step = Math.min(remaining, distanceToTarget);
        this.x += this.dir.x * step;
        this.y += this.dir.y * step;
        remaining -= step;

        if (step >= distanceToTarget - 0.0001) {
          this.x = target.x;
          this.y = target.y;
        }
      }
    }
  }

  class Player extends GridMover {
    constructor(start, speed) {
      super(start.x, start.y, speed);
      this.spawn = { ...start };
      this.invulnerableTimer = 0;
      this.motionTime = 0;
    }

    reset(start, speed) {
      this.spawn = { ...start };
      this.x = start.x;
      this.y = start.y;
      this.speed = speed;
      this.dir = App.DIRS.none;
      this.desiredDir = App.DIRS.none;
      this.invulnerableTimer = 1.4;
      this.motionTime = 0;
    }

    update(dt, game) {
      this.motionTime += dt;
      this.invulnerableTimer = Math.max(0, this.invulnerableTimer - dt);
      this.advance(dt, (x, y, dir) => game.canMoveFrom(x, y, dir), () => {
        if (this.desiredDir.name !== "none" && game.canMoveFrom(this.tile().x, this.tile().y, this.desiredDir)) {
          this.dir = this.desiredDir;
        } else if (this.dir.name !== "none" && !game.canMoveFrom(this.tile().x, this.tile().y, this.dir)) {
          this.dir = App.DIRS.none;
        }
      });
    }
  }

  App.GridMover = GridMover;
  App.Player = Player;
})();
