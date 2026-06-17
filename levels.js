(function () {
  "use strict";

  const App = window.CrystalRush = window.CrystalRush || {};

  App.DIRS = {
    none: { x: 0, y: 0, name: "none" },
    up: { x: 0, y: -1, name: "up" },
    down: { x: 0, y: 1, name: "down" },
    left: { x: -1, y: 0, name: "left" },
    right: { x: 1, y: 0, name: "right" }
  };

  App.DIR_LIST = [App.DIRS.up, App.DIRS.right, App.DIRS.down, App.DIRS.left];

  App.KEY_TO_DIR = {
    ArrowUp: "up",
    KeyW: "up",
    ArrowDown: "down",
    KeyS: "down",
    ArrowLeft: "left",
    KeyA: "left",
    ArrowRight: "right",
    KeyD: "right"
  };

  App.DIFFICULTY = {
    easy: {
      label: "Лёгкая",
      lives: 5,
      enemySpeed: 0.84,
      playerSpeed: 1.05,
      powerTime: 8.6,
      enemyDelay: 2.25,
      scoreBonus: 1
    },
    normal: {
      label: "Обычная",
      lives: 3,
      enemySpeed: 1,
      playerSpeed: 1,
      powerTime: 7,
      enemyDelay: 1.8,
      scoreBonus: 1
    },
    hard: {
      label: "Сложная",
      lives: 2,
      enemySpeed: 1.16,
      playerSpeed: 0.98,
      powerTime: 5.8,
      enemyDelay: 1.25,
      scoreBonus: 1.25
    }
  };

  App.oppositeDir = function oppositeDir(dir) {
    if (!dir || dir.name === "none") return App.DIRS.none;
    return App.DIR_LIST.find((candidate) => candidate.x === -dir.x && candidate.y === -dir.y) || App.DIRS.none;
  };

  App.sameDir = function sameDir(a, b) {
    return Boolean(a && b && a.x === b.x && a.y === b.y);
  };

  App.manhattan = function manhattan(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  };

  App.clamp = function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  };

  App.randInt = function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  };

  App.shuffle = function shuffle(items, rng) {
    const random = rng || Math.random;
    const copy = items.slice();
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(random() * (i + 1));
      const tmp = copy[i];
      copy[i] = copy[j];
      copy[j] = tmp;
    }
    return copy;
  };

  App.enemyTypeFromChar = function enemyTypeFromChar(char) {
    if (char === "R") return "random";
    if (char === "A") return "ambusher";
    return "chaser";
  };

  App.LEVELS = [
    {
      name: "Сад искр",
      enemySpeed: 2.95,
      playerSpeed: 5.9,
      bonusPoints: 2,
      layout: [
        "###################",
        "#P....#.....#...oX#",
        "#.##..#.###.#.##..#",
        "#......R#A#.......#",
        "###.#####.#####.###",
        "#...#.....o.....#.#",
        "#.#.#.###.###.#.#.#",
        "#.#.....#C#.....#.#",
        "#.#####.#.#.#####.#",
        "#.......#.#.......#",
        "#.###.###.###.###.#",
        "#o..#.........#...#",
        "#.##.#.##.##.#.##.#",
        "#.....#.....#.....#",
        "###################"
      ]
    },
    {
      name: "Лунная развязка",
      enemySpeed: 3.15,
      playerSpeed: 5.9,
      bonusPoints: 3,
      layout: [
        "###################",
        "#P..o....#....o..X#",
        "#.#####..#..#####.#",
        "#.....#..R..#.....#",
        "###.#.###.###.#.###",
        "#...#...#.#...#...#",
        "#.#####.#.#.#####.#",
        "#.....#C#A#C#.....#",
        "#.###.#.#.#.#.###.#",
        "#o..#.........#..o#",
        "###.#.###.###.#.###",
        "#...#...#.#...#...#",
        "#.#####.#.#.#####.#",
        "#.......#.........#",
        "###################"
      ]
    },
    {
      name: "Стеклянный узел",
      enemySpeed: 3.35,
      playerSpeed: 5.85,
      bonusPoints: 3,
      layout: [
        "###################",
        "#P....#..o..#....X#",
        "#.###.#.###.#.###.#",
        "#...#...#...#...#.#",
        "###.###.#.###.###.#",
        "#.....#R#A#.....#.#",
        "#.###.#.#.#.###.#.#",
        "#o#...#C#C#...#..o#",
        "#.#.###.#.###.#.###",
        "#.#.....#.....#...#",
        "#.#####.#.#####.#.#",
        "#...#...#...#...#.#",
        "###.#.#####.#.###.#",
        "#o............R...#",
        "###################"
      ]
    },
    {
      name: "Кварцевый шторм",
      enemySpeed: 3.55,
      playerSpeed: 5.82,
      bonusPoints: 4,
      layout: [
        "###################",
        "#P..#...o...#....X#",
        "#.#.#.#####.#.###.#",
        "#.#...#...#...#...#",
        "#.#####.#.#####.#.#",
        "#.....#R#A#.....#.#",
        "###.#.#.#.#.#.###.#",
        "#o#.#...C...#.#..o#",
        "#.#.###.#.###.#.###",
        "#.#.....#.....#...#",
        "#.#####.#.#####.#.#",
        "#...#...#...#...#.#",
        "#.#.#.#####.#.###.#",
        "#o..R....C....A..o#",
        "###################"
      ]
    },
    {
      name: "Сингулярный зал",
      enemySpeed: 3.78,
      playerSpeed: 5.78,
      bonusPoints: 4,
      layout: [
        "###################",
        "#P.o#.....#.....oX#",
        "#.#.#.###.#.###.#.#",
        "#.#...#...#...#.#.#",
        "#.#####.#####.#.#.#",
        "#...R...#...A...#.#",
        "###.###.#.#.###.#.#",
        "#o..#...C.C...#..o#",
        "#.###.#.###.#.###.#",
        "#.....#.....#.....#",
        "#.###.#####.#####.#",
        "#...#...R...#...#.#",
        "#.#.###.#.###.#.#.#",
        "#o....A.#.C....R.o#",
        "###################"
      ]
    }
  ];
})();
