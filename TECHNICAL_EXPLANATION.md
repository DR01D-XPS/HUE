# Pygame в проекте Hue Maze

Этот файл объясняет функции, классы, методы и константы `pygame`, которые используются в игре.

## 1. `pygame.init()`

Запускает и подготавливает все основные модули pygame: окно, события, клавиатуру, мышь, шрифты и т.д.

В проекте вызывается один раз при создании игры:

```python
pygame.init()
```

Без этой строки многие части pygame могут не работать корректно.

## 2. `pygame.quit()`

Корректно завершает работу pygame.

В проекте используется перед закрытием игры:

```python
pygame.quit()
sys.exit()
```

Это нужно, чтобы закрыть окно и освободить ресурсы.

## 3. `pygame.display.set_caption()`

Задает заголовок окна.

В проекте:

```python
pygame.display.set_caption("Hue Maze - головоломка")
```

Этот текст виден сверху в рамке окна.

## 4. `pygame.display.set_mode()`

Создает окно игры и возвращает поверхность экрана.

В проекте:

```python
self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
```

Первый аргумент - размер окна.

Второй аргумент - флаги окна.

Используемые флаги:

```python
pygame.RESIZABLE
pygame.FULLSCREEN
```

`pygame.RESIZABLE` позволяет растягивать окно мышкой.

`pygame.FULLSCREEN` включает полноэкранный режим.

## 5. `pygame.display.flip()`

Показывает на экране все, что было нарисовано за текущий кадр.

В проекте:

```python
pygame.display.flip()
```

Обычно вызывается в конце метода `draw()`.

Логика такая:

1. Очистить экран.
2. Нарисовать уровень, игрока, интерфейс.
3. Вызвать `pygame.display.flip()`.
4. Готовый кадр появляется на экране.

## 6. `pygame.time.Clock()`

Создает объект часов, который помогает управлять FPS.

В проекте:

```python
self.clock = pygame.time.Clock()
```

Сам объект часов используется в игровом цикле.

## 7. `Clock.tick()`

Ограничивает частоту кадров и возвращает время с прошлого кадра.

В проекте:

```python
real_delta_time = self.clock.tick(FPS) / 1000
```

`FPS` равен `60`, поэтому игра старается работать примерно в 60 кадров в секунду.

`tick()` возвращает миллисекунды, поэтому делим на `1000`, чтобы получить секунды.

Это нужно для плавного движения и замедления времени.

## 8. `pygame.event.get()`

Возвращает список событий pygame.

В проекте:

```python
for event in pygame.event.get():
```

Через события игра узнает:

- закрыли ли окно;
- нажали ли клавишу;
- отпустили ли клавишу;
- подвинули ли мышь;
- нажали ли кнопку мыши;
- изменили ли размер окна.

## 9. Событие `pygame.QUIT`

Срабатывает, когда пользователь закрывает окно.

В проекте:

```python
if event.type == pygame.QUIT:
    self.quit_game()
```

## 10. Событие `pygame.VIDEORESIZE`

Срабатывает, когда пользователь изменяет размер окна.

В проекте:

```python
if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
    self.resize_window(event.w, event.h)
```

`event.w` и `event.h` - новая ширина и высота окна.

## 11. Событие `pygame.KEYDOWN`

Срабатывает в момент нажатия клавиши.

В проекте используется для:

- выбора пункта меню;
- выхода в меню;
- рестарта уровня;
- открытия колеса цвета;
- включения полного экрана.

Пример:

```python
if event.type == pygame.KEYDOWN:
```

## 12. Событие `pygame.KEYUP`

Срабатывает в момент отпускания клавиши.

В проекте используется для выбора цвета после отпускания `SPACE`:

```python
if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
    self.close_color_wheel(apply_selection=True)
```

## 13. Событие `pygame.MOUSEMOTION`

Срабатывает, когда мышь двигается.

В меню используется для подсветки пункта под курсором:

```python
if event.type == pygame.MOUSEMOTION:
```

## 14. Событие `pygame.MOUSEBUTTONDOWN`

Срабатывает при нажатии кнопки мыши.

В меню используется для выбора пункта:

```python
if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
```

`event.button == 1` означает левую кнопку мыши.

## 15. Клавиатурные константы `pygame.K_*`

Pygame обозначает клавиши специальными константами.

В проекте используются:

```python
pygame.K_UP
pygame.K_DOWN
pygame.K_LEFT
pygame.K_RIGHT
pygame.K_w
pygame.K_a
pygame.K_s
pygame.K_d
pygame.K_RETURN
pygame.K_ESCAPE
pygame.K_SPACE
pygame.K_r
pygame.K_F11
```

Пример:

```python
if event.key == pygame.K_SPACE:
    self.open_color_wheel()
```

## 16. `pygame.KMOD_ALT`

Константа для проверки, удерживается ли `Alt`.

В проекте нужна для комбинации `Alt+Enter`:

```python
alt_enter = event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
```

Если нажаты `Alt` и `Enter`, игра переключает полноэкранный режим.

## 17. `pygame.key.get_pressed()`

Возвращает состояние всех клавиш в текущий момент.

В проекте используется для движения игрока:

```python
keys = pygame.key.get_pressed()
```

Потом проверяется, какая клавиша удерживается:

```python
if keys[pygame.K_a] or keys[pygame.K_LEFT]:
    return (0, -1)
```

В отличие от `KEYDOWN`, эта функция удобна для движения, потому что показывает, удерживается ли клавиша прямо сейчас.

## 18. `pygame.mouse.get_pos()`

Возвращает текущую позицию мыши:

```python
mouse_x, mouse_y = pygame.mouse.get_pos()
```

В проекте используется для колеса цветов.

Игра сравнивает позицию мыши с центром колеса и понимает, в сторону какого цвета игрок ведет курсор.

## 19. `pygame.font.SysFont()`

Создает шрифт из системных шрифтов Windows.

В проекте:

```python
self.title_font = pygame.font.SysFont("arial", 64, bold=True)
self.large_font = pygame.font.SysFont("arial", 38)
self.font = pygame.font.SysFont("arial", 24)
self.small_font = pygame.font.SysFont("arial", 18)
```

Используется именно `Arial`, потому что он нормально отображает русские буквы.

## 20. `Font.render()`

Создает картинку с текстом.

Пример:

```python
level_text = self.font.render(f"Уровень {self.level_index + 1}: {self.level_name}", True, TEXT_COLOR)
```

Аргументы:

- текст;
- сглаживание `True`;
- цвет текста.

После `render()` текст нужно вывести на экран через `blit()`.

## 21. `Surface.blit()`

Рисует одну поверхность на другой.

В проекте чаще всего используется для вывода текста:

```python
self.screen.blit(level_text, (20, 10))
```

Также используется для прозрачных поверхностей:

```python
self.screen.blit(surface, rect.topleft)
```

## 22. `Surface.fill()`

Заливает поверхность цветом.

В проекте очищает экран перед новым кадром:

```python
self.screen.fill(self.get_background_color())
```

Также используется для прозрачных поверхностей:

```python
surface.fill(color)
```

## 23. `Surface.get_size()`

Возвращает размер поверхности.

В проекте используется для получения текущего размера окна:

```python
self.window_width, self.window_height = self.screen.get_size()
```

Это важно при изменении размера окна и включении полного экрана.

## 24. `pygame.Surface()`

Создает новую поверхность.

В проекте используется для полупрозрачных эффектов:

```python
surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
```

Еще пример:

```python
overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
```

Так создается затемнение поверх экрана при открытом колесе цветов.

## 25. `pygame.SRCALPHA`

Флаг, который разрешает прозрачность на поверхности.

Используется так:

```python
pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
```

Без `SRCALPHA` прозрачные цвета с альфа-каналом работали бы неправильно.

## 26. `pygame.Rect()`

Создает прямоугольник.

В проекте `Rect` используется для:

- игрока;
- ящиков;
- клеток карты;
- кнопок меню;
- игрового поля;
- областей текста.

Пример:

```python
self.player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
```

Другой пример:

```python
rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
```

Формат:

```python
pygame.Rect(x, y, width, height)
```

## 27. Свойство `Rect.center`

Задает или возвращает центр прямоугольника.

В проекте используется для размещения игрока и ящиков в центре клетки:

```python
self.player_rect.center = self.cell_center(cell)
```

Для ящика:

```python
rect.center = self.cell_center(crate_cell)
```

## 28. Свойство `Rect.topleft`

Возвращает левый верхний угол прямоугольника.

В проекте:

```python
self.screen.blit(surface, rect.topleft)
```

Так прозрачная поверхность рисуется точно поверх нужной клетки.

## 29. `Rect.inflate()`

Создает новый прямоугольник больше или меньше исходного.

В проекте:

```python
inner_rect = rect.inflate(-10, -10)
```

Отрицательные значения уменьшают прямоугольник.

Так рисуется внутренняя часть финиша или декоративные полосы на ящиках.

## 30. `Rect.inflate_ip()`

Меняет размер прямоугольника прямо на месте.

В проекте:

```python
rect.inflate_ip(-inset * 2, -inset * 2)
```

`ip` означает `in place`, то есть без создания нового объекта.

## 31. `Surface.get_rect()`

Возвращает прямоугольник поверхности.

Чаще всего используется для удобного центрирования текста:

```python
title_rect = title_surface.get_rect(center=(self.window_width // 2, self.window_height // 2 - 140))
```

Также используется для выравнивания справа сверху:

```python
plate_rect = plate_text.get_rect(topright=(self.window_width - 20, 14))
```

## 32. `pygame.draw.rect()`

Рисует прямоугольник.

В проекте используется постоянно:

```python
pygame.draw.rect(self.screen, PLAYER_COLOR, self.player_rect)
```

Если передать четвертый аргумент, рисуется только контур:

```python
pygame.draw.rect(self.screen, PLAYER_OUTLINE, self.player_rect, 2)
```

Используется для:

- игрока;
- стен;
- пола;
- ящиков;
- плит;
- дверей;
- кнопок меню;
- цветных плашек.

## 33. `pygame.draw.line()`

Рисует одну линию.

В проекте используется для сетки уровня:

```python
pygame.draw.line(self.screen, GRID_COLOR, (x, self.level_rect.top), (x, self.level_rect.bottom))
```

Вертикальные и горизонтальные линии создают клеточную сетку.

## 34. `pygame.draw.polygon()`

Рисует многоугольник.

В проекте используется для цветных секторов колеса:

```python
pygame.draw.polygon(self.screen, color, points)
```

`points` - список точек многоугольника.

## 35. `pygame.draw.lines()`

Рисует ломаную линию по списку точек.

В проекте используется для обводки сектора колеса:

```python
pygame.draw.lines(self.screen, TEXT_COLOR, True, points[1:], outline_width)
```

Аргумент `True` означает, что линия замкнутая.

## 36. `pygame.draw.circle()`

Рисует круг.

В проекте используется для центра колеса цветов:

```python
pygame.draw.circle(self.screen, BACKGROUND_COLOR, center, inner_radius)
```

И для обводки круга:

```python
pygame.draw.circle(self.screen, TEXT_COLOR, center, inner_radius, 2)
```

Если передать последний аргумент `2`, рисуется только контур толщиной 2 пикселя.

## 37. `pygame.RESIZABLE`

Флаг окна, который позволяет изменять размер окна.

Используется так:

```python
pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
```

## 38. `pygame.FULLSCREEN`

Флаг окна для полноэкранного режима.

В проекте:

```python
self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
```

Размер `(0, 0)` означает: взять текущее разрешение экрана.

## Как pygame работает в игровом цикле

Главная схема такая:

```python
while True:
    real_delta_time = self.clock.tick(FPS) / 1000
    self.handle_events()
    self.update(real_delta_time)
    self.draw()
```

Pygame здесь отвечает за четыре основные вещи:

1. окно игры;
2. ввод с клавиатуры и мыши;
3. время между кадрами;
4. рисование на экране.

## Самое важное для понимания

В игре почти все визуальные объекты - это прямоугольники `pygame.Rect`.

Почти все, что видно на экране, рисуется через:

```python
pygame.draw.rect()
pygame.draw.line()
pygame.draw.polygon()
pygame.draw.circle()
screen.blit()
```

А все управление приходит через:

```python
pygame.event.get()
pygame.key.get_pressed()
pygame.mouse.get_pos()
```

Поэтому pygame в этом проекте выполняет роль простого набора инструментов для окна, ввода, времени и рисования.
