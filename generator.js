(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};
  const WALL = "#";
  const SPACE = " ";
  const COLLECTIBLES = new Set([".", "o"]);
  const WALKABLE = new Set([" ", ".", "o", "P", "C", "R", "A", "X"]);

  function createRng(seed) {
    let state = seed >>> 0;
    return function rng() {
      state = (state * 1664525 + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }

  function inBounds(layout, x, y) {
    return y >= 0 && y < layout.length && x >= 0 && x < layout[0].length;
  }

  function isWalkableChar(char) {
    return WALKABLE.has(char);
  }

  function isWalkable(layout, x, y) {
    return inBounds(layout, x, y) && isWalkableChar(layout[y][x]);
  }

  function toRows(grid) {
    return grid.map((row) => row.join(""));
  }

  function getNeighbors(layout, cell) {
    const result = [];
    for (const dir of App.DIR_LIST) {
      const nx = cell.x + dir.x;
      const ny = cell.y + dir.y;
      if (isWalkable(layout, nx, ny)) {
        result.push({ x: nx, y: ny });
      }
    }
    return result;
  }

  function bfs(layout, start) {
    const height = layout.length;
    const width = layout[0].length;
    const visited = Array.from({ length: height }, () => Array(width).fill(false));
    const distance = Array.from({ length: height }, () => Array(width).fill(Infinity));
    const queue = [start];
    let head = 0;
    visited[start.y][start.x] = true;
    distance[start.y][start.x] = 0;

    while (head < queue.length) {
      const current = queue[head];
      head += 1;
      for (const next of getNeighbors(layout, current)) {
        if (!visited[next.y][next.x]) {
          visited[next.y][next.x] = true;
          distance[next.y][next.x] = distance[current.y][current.x] + 1;
          queue.push(next);
        }
      }
    }

    return { visited, distance, cells: queue };
  }

  function findChars(layout, chars) {
    const wanted = new Set(chars);
    const found = [];
    for (let y = 0; y < layout.length; y += 1) {
      for (let x = 0; x < layout[y].length; x += 1) {
        if (wanted.has(layout[y][x])) {
          found.push({ x, y, char: layout[y][x] });
        }
      }
    }
    return found;
  }

  function validateLayout(layout) {
    if (!Array.isArray(layout) || layout.length < 5) {
      return { ok: false, reason: "layout is too small" };
    }

    const width = layout[0].length;
    if (width < 5 || layout.some((row) => typeof row !== "string" || row.length !== width)) {
      return { ok: false, reason: "layout is not rectangular" };
    }

    const player = findChars(layout, ["P"])[0];
    const portal = findChars(layout, ["X"])[0];
    const enemies = findChars(layout, ["C", "R", "A"]);
    const dots = findChars(layout, [".", "o"]);

    if (!player) return { ok: false, reason: "missing player start" };
    if (!portal) return { ok: false, reason: "missing portal" };
    if (enemies.length === 0) return { ok: false, reason: "missing enemies" };
    if (dots.length === 0) return { ok: false, reason: "missing collectibles" };

    const reach = bfs(layout, player);
    const unreachableDot = dots.find((dot) => !reach.visited[dot.y][dot.x]);
    if (unreachableDot) {
      return { ok: false, reason: "collectible is unreachable", cell: unreachableDot };
    }

    const unreachableEnemy = enemies.find((enemy) => !reach.visited[enemy.y][enemy.x]);
    if (unreachableEnemy) {
      return { ok: false, reason: "enemy start is unreachable", cell: unreachableEnemy };
    }

    if (!reach.visited[portal.y][portal.x]) {
      return { ok: false, reason: "portal is unreachable" };
    }

    const openCells = reach.cells.length;
    const totalCells = width * layout.length;
    if (openCells < totalCells * 0.25) {
      return { ok: false, reason: "not enough open space" };
    }

    return {
      ok: true,
      stats: {
        width,
        height: layout.length,
        openCells,
        dots: dots.length,
        enemies: enemies.length
      }
    };
  }

  function carveMaze(width, height, rng) {
    const grid = Array.from({ length: height }, () => Array(width).fill(WALL));
    const start = { x: 1, y: 1 };
    const stack = [start];
    grid[start.y][start.x] = SPACE;

    // DFS/backtracking carves a perfect maze first; later we punch a few extra links
    // to create readable loops without breaking connectivity.
    while (stack.length > 0) {
      const current = stack[stack.length - 1];
      const options = App.shuffle(App.DIR_LIST, rng)
        .map((dir) => ({
          between: { x: current.x + dir.x, y: current.y + dir.y },
          target: { x: current.x + dir.x * 2, y: current.y + dir.y * 2 }
        }))
        .filter((option) => (
          option.target.x > 0 &&
          option.target.x < width - 1 &&
          option.target.y > 0 &&
          option.target.y < height - 1 &&
          grid[option.target.y][option.target.x] === WALL
        ));

      if (options.length === 0) {
        stack.pop();
      } else {
        const next = options[Math.floor(rng() * options.length)];
        grid[next.between.y][next.between.x] = SPACE;
        grid[next.target.y][next.target.x] = SPACE;
        stack.push(next.target);
      }
    }

    return grid;
  }

  function addLoops(grid, rng, levelNumber, difficultyKey) {
    const height = grid.length;
    const width = grid[0].length;
    const diffBoost = difficultyKey === "hard" ? 0.02 : difficultyKey === "easy" ? -0.02 : 0;
    const loopChance = App.clamp(0.08 + (levelNumber - App.LEVELS.length) * 0.008 + diffBoost, 0.06, 0.24);

    for (let y = 2; y < height - 2; y += 1) {
      for (let x = 2; x < width - 2; x += 1) {
        if (grid[y][x] !== WALL || rng() > loopChance) continue;

        const horizontal = grid[y][x - 1] === SPACE && grid[y][x + 1] === SPACE;
        const vertical = grid[y - 1][x] === SPACE && grid[y + 1][x] === SPACE;
        if (horizontal || vertical) {
          grid[y][x] = SPACE;
        }
      }
    }
  }

  function degree(layout, cell) {
    return App.DIR_LIST.reduce((sum, dir) => sum + (isWalkable(layout, cell.x + dir.x, cell.y + dir.y) ? 1 : 0), 0);
  }

  function farthestCells(layout, from) {
    const reach = bfs(layout, from);
    return reach.cells
      .map((cell) => ({ ...cell, distance: reach.distance[cell.y][cell.x], degree: degree(layout, cell) }))
      .sort((a, b) => b.distance - a.distance || b.degree - a.degree);
  }

  function chooseSeparated(candidates, taken, minDistance) {
    return candidates.find((cell) => taken.every((other) => App.manhattan(cell, other) >= minDistance));
  }

  function stampGeneratedContent(grid, rng, levelNumber, difficultyKey) {
    let layout = toRows(grid);
    const open = findChars(layout, [SPACE]);
    const player = open.find((cell) => cell.x === 1 && cell.y === 1) || open[0];
    const reachFromPlayer = bfs(layout, player);
    const candidates = farthestCells(layout, player);
    const portal = candidates[0];
    const diffExtra = difficultyKey === "hard" ? 1 : difficultyKey === "easy" ? -1 : 0;
    const enemyCount = App.clamp(3 + Math.floor((levelNumber - 5) / 2) + diffExtra, 3, 8);
    const enemyChars = ["C", "R", "A", "C", "R", "A", "C", "R"];
    const taken = [player, portal];
    const enemies = [];

    for (let i = 0; i < enemyCount; i += 1) {
      const minDistance = App.clamp(9 - Math.floor(levelNumber / 5), 5, 9);
      const enemy = chooseSeparated(candidates.slice(2 + i), taken, minDistance) ||
        candidates.find((cell) => App.manhattan(cell, player) > 5 && !taken.some((other) => other.x === cell.x && other.y === cell.y));
      if (enemy) {
        enemies.push({ ...enemy, char: enemyChars[i % enemyChars.length] });
        taken.push(enemy);
      }
    }

    const powerCount = App.clamp(3 + Math.floor((levelNumber - 6) / 6), 3, 6);
    const powers = [];
    for (const candidate of candidates) {
      if (powers.length >= powerCount) break;
      if (taken.some((cell) => cell.x === candidate.x && cell.y === candidate.y)) continue;
      if (App.manhattan(candidate, player) < 6) continue;
      if (powers.every((cell) => App.manhattan(cell, candidate) >= 7)) {
        powers.push(candidate);
        taken.push(candidate);
      }
    }
    for (const candidate of candidates) {
      if (powers.length >= powerCount) break;
      if (taken.some((cell) => cell.x === candidate.x && cell.y === candidate.y)) continue;
      if (App.manhattan(candidate, player) < 4) continue;
      powers.push(candidate);
      taken.push(candidate);
    }

    const rows = grid.map((row) => row.slice());
    for (const cell of reachFromPlayer.cells) {
      if (App.manhattan(cell, player) <= 2) {
        rows[cell.y][cell.x] = SPACE;
      } else {
        rows[cell.y][cell.x] = ".";
      }
    }

    rows[player.y][player.x] = "P";
    rows[portal.y][portal.x] = "X";
    powers.forEach((cell) => {
      rows[cell.y][cell.x] = "o";
    });
    enemies.forEach((enemy) => {
      rows[enemy.y][enemy.x] = enemy.char;
    });

    return toRows(rows);
  }

  function generateLevel(levelNumber, difficultyKey) {
    const difficulty = difficultyKey || "normal";
    const index = Math.max(0, levelNumber - App.LEVELS.length - 1);
    const width = 19 + Math.min(10, Math.floor(index / 2) * 2);
    const height = 15 + Math.min(8, Math.floor(index / 3) * 2);
    const seedBase = 9719 + levelNumber * 811 + difficulty.length * 97 + Math.floor(Math.random() * 100000);

    for (let attempt = 0; attempt < 30; attempt += 1) {
      const rng = createRng(seedBase + attempt * 1013);
      const grid = carveMaze(width | 1, height | 1, rng);
      addLoops(grid, rng, levelNumber, difficulty);
      const layout = stampGeneratedContent(grid, rng, levelNumber, difficulty);
      const check = validateLayout(layout);
      if (check.ok) {
        return {
          name: `Случайный лабиринт ${levelNumber}`,
          generated: true,
          enemySpeed: App.clamp(3.08 + levelNumber * 0.085, 3.1, 5.15),
          playerSpeed: 5.82,
          bonusPoints: 4,
          layout
        };
      }
    }

    throw new Error("Не удалось создать проходимый лабиринт");
  }

  App.Generator = {
    generateLevel,
    validateLayout,
    bfs,
    isWalkableChar,
    createRng
  };
})();
