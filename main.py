import pygame
import sys
import os
import pickle
import unittest # 5. Тестування
from collections import deque
from typing import List, Tuple, Optional, Any # 4. Анотації типів

# --- 2. Модулі (Імпорт власного модуля) ---
from utils import debug_trace, make_score_adder, id_generator

# --- Глобальні константи ---
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
TILE_SIZE: int = 40
FPS: int = 60
GAME_TITLE: str = "Maze Runner: Advanced Python"

# --- 1. Винятки (Власний клас помилки) ---
class GameError(Exception):
    """Базовий клас для помилок гри."""
    pass

class LevelLoadError(GameError):
    """Помилка завантаження рівня."""
    pass

# Конфігурація через словник
GAME_CONFIG = {
    "colors": {
        "WHITE": (255, 255, 255),
        "BLACK": (0, 0, 0),
        "RED": (255, 0, 0),
        "GREEN": (0, 255, 0),
        "BLUE": (0, 0, 255),
        "YELLOW": (255, 255, 0),
        "BROWN": (100, 50, 0)
    },
    "speeds": {"cat": 300}
}

# Шляхи
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LEVEL_FILE = os.path.join(BASE_DIR, "level.txt")
SAVE_FILE = os.path.join(BASE_DIR, "savegame.dat")

# Генератор ID
gen_id = id_generator(1)

# --- 1. Послідовності (Власний клас-контейнер) ---
class GameMap:
    """Клас, що поводиться як послідовність (sequence) рядків."""
    def __init__(self, data: List[str]):
        self._data = data

    def __getitem__(self, index: int) -> str:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self):
        return iter(self._data)

# --- Функції ---
def load_image(name: str, color_fallback: Tuple[int, int, int]) -> pygame.Surface:
    path = os.path.join(ASSETS_DIR, name)
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    except Exception:
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color_fallback)
        return surface

def create_default_level_file():
    if not os.path.exists(LEVEL_FILE) or os.path.getsize(LEVEL_FILE) == 0:
        default_map = """WWWWWWWWWWWWWWWWWWWW
W P       C        W
W WWWWWW WWWWWW WW W
W C      W      C  W
WWWWWW W W WWWWWWWWW
W T    W C   E     W
W WWW WWWWWWWWWW W W
W K      T       W W
WWWWWWWWWWWWWWWW D W
WWWWWWWWWWWWWWWWWWWW"""
        with open(LEVEL_FILE, "w", encoding='utf-8') as f:
            f.write(default_map)

def load_level_data() -> GameMap:
    create_default_level_file()
    try:
        with open(LEVEL_FILE, "r", encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            return GameMap(lines) # Повертаємо нашу "Послідовність"
    except FileNotFoundError:
        # 1. Винятки (підняття помилки)
        raise LevelLoadError("Файл рівня не знайдено!")

# --- Mixin ---
class MovableMixin:
    def move_simulated(self, dx: int, dy: int) -> pygame.Rect:
        # Тут self.rect підсвічується, бо IDE не знає про нього в Mixin, але це ок
        return self.rect.move(dx, dy) # type: ignore

# --- Класи ---
class GameObject:
    def __init__(self, x: int, y: int, image: pygame.Surface, type_obj: str):
        self.id = next(gen_id) # Використання генератора
        self._x = x
        self._y = y
        self.image = image
        self.type = type_obj
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    @property
    def x(self) -> int: return self._x
    
    @x.setter
    def x(self, value: int):
        self._x = value
        self.rect.x = value

    @property
    def y(self) -> int: return self._y
    
    @y.setter
    def y(self, value: int):
        self._y = value
        self.rect.y = value

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

class Wall(GameObject):
    def __init__(self, x: int, y: int, image: pygame.Surface):
        super().__init__(x, y, image, 'wall')

class Item(GameObject):
    def __init__(self, x: int, y: int, image: pygame.Surface, item_type: str):
        super().__init__(x, y, image, item_type)

class Character(GameObject, MovableMixin):
    def __init__(self, x: int, y: int, image: pygame.Surface, char_type: str):
        super().__init__(x, y, image, char_type)
        
class Player(Character):
    def __init__(self, x: int, y: int, image: pygame.Surface):
        super().__init__(x, y, image, 'player')
    
    # 4. Декоратори (застосування)
    @debug_trace
    def handle_move(self, dx: int, dy: int, walls: List[Wall]) -> bool:
        new_rect = self.move_simulated(dx, dy)
        if not (0 <= new_rect.x < SCREEN_WIDTH and 0 <= new_rect.y < SCREEN_HEIGHT):
            return False
        for wall in walls:
            if new_rect.colliderect(wall.rect):
                return False
        self.x = new_rect.x
        self.y = new_rect.y
        return True

class Enemy(Character):
    def __init__(self, x: int, y: int, image: pygame.Surface):
        super().__init__(x, y, image, 'enemy')
        self.move_delay = GAME_CONFIG["speeds"]["cat"]
        self.last_move_time = pygame.time.get_ticks()

    def get_bfs_path(self, target_rect: pygame.Rect, walls: List[Wall]) -> Optional[Tuple[int, int]]:
        wall_set = set((w.rect.x, w.rect.y) for w in walls)
        start = (self.x, self.y)
        target = (target_rect.x, target_rect.y)
        queue = deque([(start, None)])
        visited = set([start])
        
        while queue:
            current_pos, first_step = queue.popleft()
            if current_pos == target: return first_step # type: ignore
            
            cx, cy = current_pos
            for dx, dy in [(0, -TILE_SIZE), (0, TILE_SIZE), (-TILE_SIZE, 0), (TILE_SIZE, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < SCREEN_WIDTH and 0 <= ny < SCREEN_HEIGHT:
                    if (nx, ny) not in wall_set and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_first = first_step if first_step else (dx, dy)
                        queue.append(((nx, ny), new_first))
        return None

    def update(self, current_time: int, player: Player, walls: List[Wall]):
        if current_time - self.last_move_time > self.move_delay:
            self.last_move_time = current_time
            step = self.get_bfs_path(player.rect, walls)
            if step:
                dx, dy = step
                self.x += dx
                self.y += dy

class GameManager:
    def __init__(self):
        self.score = 0
        self.has_key = False
        self.running = True
        self.visited_cells = set()
        
        # 3. Лексичне замикання (створюємо функцію для додавання очок)
        self.score_adder = make_score_adder(10)
        
        self.load_assets()
        try:
            self.create_level()
        except LevelLoadError as e:
            print(f"CRITICAL ERROR: {e}")
            self.running = False

    def load_assets(self):
        c = GAME_CONFIG["colors"]
        self.imgs = {
            'wall': load_image("wall.png", c["BLACK"]),
            'mouse': load_image("mouse.png", c["BLUE"]),
            'cat': load_image("cat.png", c["RED"]),
            'cheese': load_image("cheese.png", c["YELLOW"]),
            'key': load_image("key.png", c["GREEN"]),
            'door': load_image("exit.png", c["BROWN"]),
            'trap': load_image("trap.png", (128, 0, 128))
        }

    def create_level(self):
        level_data = load_level_data()
        self.walls: List[Wall] = []
        self.cheeses: List[Item] = []
        self.traps: List[Item] = []
        self.key: Optional[Item] = None
        self.door: Optional[Item] = None
        self.player: Optional[Player] = None
        self.cat: Optional[Enemy] = None

        # Використовуємо наш клас-послідовність GameMap
        for r, row in enumerate(level_data):
            for c, char in enumerate(row):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if char == 'W': self.walls.append(Wall(x, y, self.imgs['wall']))
                elif char == 'P': self.player = Player(x, y, self.imgs['mouse'])
                elif char == 'E': self.cat = Enemy(x, y, self.imgs['cat'])
                elif char == 'C': self.cheeses.append(Item(x, y, self.imgs['cheese'], 'cheese'))
                elif char == 'K': self.key = Item(x, y, self.imgs['key'], 'key')
                elif char == 'D': self.door = Item(x, y, self.imgs['door'], 'door')
                elif char == 'T': self.traps.append(Item(x, y, self.imgs['trap'], 'trap'))

        if not self.player:
             self.player = Player(40, 40, self.imgs['mouse'])

    def save_state(self):
        if self.player:
            data = {"pos": (self.player.x, self.player.y), "score": self.score}
            try:
                with open(SAVE_FILE, "wb") as f: pickle.dump(data, f)
                print("State Saved")
            except Exception as e: print(e)

    def draw(self, screen: pygame.Surface):
        screen.fill(GAME_CONFIG["colors"]["WHITE"])
        for w in self.walls: w.draw(screen)
        for c in self.cheeses: c.draw(screen)
        for t in self.traps: t.draw(screen)
        if self.key: self.key.draw(screen)
        if self.door: self.door.draw(screen)
        
        if self.player: self.player.draw(screen)
        if self.cat: self.cat.draw(screen)

def draw_text(screen, text, size, x, y, color):
    font = pygame.font.Font(None, size)
    text_surface = font.render(str(text), True, color)
    rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, rect)

# --- 5. Тестування (Unit Tests) ---
class TestGameMechanics(unittest.TestCase):
    def test_score_adder(self):
        """Тест замикання для очок"""
        adder = make_score_adder(10)
        self.assertEqual(adder(0), 10)
        self.assertEqual(adder(50), 60)

    def test_map_sequence(self):
        """Тест послідовності карти"""
        m = GameMap(["ABC", "DEF"])
        self.assertEqual(len(m), 2)
        self.assertEqual(m[0], "ABC")

def main():
    # Запуск тестів, якщо передано аргумент 'test'
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()
    
    game = GameManager()

    while game.running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: game.running = False
            
            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_LEFT: dx = -TILE_SIZE
                elif event.key == pygame.K_RIGHT: dx = TILE_SIZE
                elif event.key == pygame.K_UP: dy = -TILE_SIZE
                elif event.key == pygame.K_DOWN: dy = TILE_SIZE
                elif event.key == pygame.K_s: game.save_state()

                if (dx != 0 or dy != 0) and game.player:
                    if game.player.handle_move(dx, dy, game.walls):
                        game.visited_cells.add((game.player.x, game.player.y))

        if game.cat and game.player:
            game.cat.update(current_time, game.player, game.walls)
            if game.player.rect.colliderect(game.cat.rect):
                print("Cat caught you!")
                game.running = False

        if game.player:
            for cheese in game.cheeses[:]:
                if game.player.rect.colliderect(cheese.rect):
                    game.cheeses.remove(cheese)
                    # Використання замикання
                    game.score = game.score_adder(game.score)
                    print(f"Yummy! Score: {game.score}")

            for trap in game.traps:
                if game.player.rect.colliderect(trap.rect):
                    print("Trap hit!")
                    game.running = False

            if game.key and game.player.rect.colliderect(game.key.rect):
                game.has_key = True
                game.key = None
                print("Key taken")

            if game.door and game.player.rect.colliderect(game.door.rect):
                if game.has_key and len(game.cheeses) == 0:
                    print("WIN!")
                    game.running = False

        game.draw(screen)
        
        info = f"Score: {game.score} | Key: {game.has_key} | Visited: {len(game.visited_cells)}"
        draw_text(screen, info, 30, SCREEN_WIDTH // 2, 20, (0,0,0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()