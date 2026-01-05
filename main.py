import pygame
import sys
import os
import pickle
from collections import deque

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

GAME_TITLE = "Maze Runner: Data Structures"

# 2. (Синя) Словники
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
    "speeds": {
        "cat": 300
    }
}

# Шляхи до файлів
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LEVEL_FILE = os.path.join(BASE_DIR, "level.txt")
SCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")
SAVE_FILE = os.path.join(BASE_DIR, "savegame.dat")

# --- Функції ---

def create_default_level_file():
    """Створює файл рівня"""
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
    
    if not os.path.exists(LEVEL_FILE) or os.path.getsize(LEVEL_FILE) == 0:
        with open(LEVEL_FILE, "w", encoding='utf-8') as f:
            f.write(default_map)

# 3. (Синя) Завантажити з файлу
def load_level_from_file():
    create_default_level_file()
    print("Loading level...")
    with open(LEVEL_FILE, "r", encoding='utf-8') as f:
        # 1. (Зелена) Зрізи
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines

# 6. (Зелена) Зберегти текст
def save_high_score(score):
    try:
        with open(SCORE_FILE, "w", encoding='utf-8') as f:
            f.write(f"Last Score: {score}")
    except Exception as e:
        print(f"Error: {e}")

# 7. (Зелена) Двійкові файли
def save_binary_state(player_pos, score):
    data = {"pos": player_pos, "score": score}
    try:
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(data, f)
        print("Game state saved (binary).")
    except Exception as e:
        print(f"Error: {e}")

def load_image(name, color_fallback):
    path = os.path.join(ASSETS_DIR, name)
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    except Exception:
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color_fallback)
        return surface

# 4. (Зелена) *args
def debug_log(prefix, *messages):
    print(f"[LOG] {prefix}:", end=" ")
    for m in messages:
        print(m, end=" ")
    print()

def draw_text(screen, text, size, x, y, color):
    font = pygame.font.Font(None, size)
    text_surface = font.render(str(text), True, color)
    rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, rect)

class GameObject:
    def __init__(self, x, y, type_obj):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = type_obj

# --- АЛГОРИТМ ПОШУКУ ШЛЯХУ (BFS) ---
def get_smart_cat_move(cat_rect, player_rect, walls):
    # Перетворюємо координати стін у множину для швидкого пошуку
    wall_set = set((w.rect.x, w.rect.y) for w in walls)
    
    start = (cat_rect.x, cat_rect.y)
    target = (player_rect.x, player_rect.y)
    
    # Черга для пошуку: (поточна_позиція, перший_крок_куди_йти)
    queue = deque([ (start, None) ])
    visited = set([start])
    
    while queue:
        current_pos, first_step = queue.popleft()
        cx, cy = current_pos
        
        # Якщо знайшли гравця
        if current_pos == target:
            return first_step # Повертаємо, куди треба зробити перший крок
        
        # Перевіряємо сусідів (Вгору, Вниз, Вліво, Вправо)
        for dx, dy in [(0, -TILE_SIZE), (0, TILE_SIZE), (-TILE_SIZE, 0), (TILE_SIZE, 0)]:
            nx, ny = cx + dx, cy + dy
            
            # Перевірка меж та стін
            if 0 <= nx < SCREEN_WIDTH and 0 <= ny < SCREEN_HEIGHT:
                if (nx, ny) not in wall_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    # Якщо це самий початок, запам'ятовуємо цей крок як "перший"
                    new_first_step = first_step if first_step else (dx, dy)
                    queue.append( ((nx, ny), new_first_step) )
    
    return None # Шлях не знайдено (неможливо дійти)

def setup_game():
    level_data = load_level_from_file()
    
    walls = []
    cheeses = []
    traps = []
    key = None
    door = None
    player_rect = None
    cat_rect = None
    
    for row_idx, row in enumerate(level_data):
        for col_idx in range(len(row)):
            char = row[col_idx]
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            
            if char == 'W': walls.append(GameObject(x, y, 'wall'))
            elif char == 'P': player_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            elif char == 'C': cheeses.append(GameObject(x, y, 'cheese'))
            elif char == 'K': key = GameObject(x, y, 'key')
            elif char == 'D': door = GameObject(x, y, 'door')
            elif char == 'T': traps.append(GameObject(x, y, 'trap'))
            elif char == 'E': cat_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    
    if player_rect is None:
        player_rect = pygame.Rect(40, 40, TILE_SIZE, TILE_SIZE)

    return walls, cheeses, key, door, traps, player_rect, cat_rect

def main_game():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()

    colors = GAME_CONFIG["colors"]
    
    img_wall = load_image("wall.png", colors["BLACK"])
    img_mouse = load_image("mouse.png", colors["BLUE"])
    img_cat = load_image("cat.png", colors["RED"])
    img_cheese = load_image("cheese.png", colors["YELLOW"])
    img_key = load_image("key.png", colors["GREEN"])
    img_door = load_image("exit.png", colors["BROWN"])
    img_trap = load_image("trap.png", (128, 0, 128))

    walls, cheeses, key, door, traps, player, cat = setup_game()
    
    # 2. (Зелена) Спискові включення
    wall_positions = [(w.rect.x, w.rect.y) for w in walls]
    
    # 5. (Зелена) Множини
    visited_cells = set()
    
    has_key = False
    score = 0
    add_score = lambda x: x + 10
    running = True
    
    CAT_MOVE_DELAY = GAME_CONFIG["speeds"]["cat"]
    last_cat_move_time = pygame.time.get_ticks()

    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(colors["WHITE"])
        
        dx, dy = 0, 0
        player_moved = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: dx = -TILE_SIZE
                elif event.key == pygame.K_RIGHT: dx = TILE_SIZE
                elif event.key == pygame.K_UP: dy = -TILE_SIZE
                elif event.key == pygame.K_DOWN: dy = TILE_SIZE
                
                if event.key == pygame.K_s:
                    save_binary_state((player.x, player.y), score)
                    debug_log("System", "Game Saved!")
                
                player_moved = True

        if player_moved:
            new_rect = player.move(dx, dy)
            hit_wall = False
            for wall in walls:
                if new_rect.colliderect(wall.rect):
                    hit_wall = True
                    break 
            else:
                if 0 <= new_rect.x < SCREEN_WIDTH and 0 <= new_rect.y < SCREEN_HEIGHT:
                    player = new_rect
                    visited_cells.add((player.x, player.y))

        # --- ЛОГІКА КОТА (РОЗУМНИЙ ПОШУК ШЛЯХУ) ---
        if cat and (current_time - last_cat_move_time > CAT_MOVE_DELAY):
            last_cat_move_time = current_time
            
            # Викликаємо функцію пошуку шляху
            next_step = get_smart_cat_move(cat, player, walls)
            
            if next_step:
                move_x, move_y = next_step
                cat = cat.move(move_x, move_y)

        # Колізії
        for cheese in cheeses[:]: 
            if player.colliderect(cheese.rect):
                cheeses.remove(cheese)
                score = add_score(score)
                debug_log("Game", "Yummy!", "Score:", score)
                continue

        for trap in traps:
            if player.colliderect(trap.rect):
                print("Game Over: Trap")
                running = False

        if cat and player.colliderect(cat):
            print("Game Over: Cat")
            running = False

        if key and player.colliderect(key.rect):
            has_key = True
            key = None 
            debug_log("Info", "Key found!")

        if door and player.colliderect(door.rect):
            if has_key and len(cheeses) == 0:
                draw_text(screen, "YOU WIN!", 100, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, colors["GREEN"])
                pygame.display.flip()
                save_high_score(score)
                pygame.time.wait(2000)
                running = False

        # Малювання
        for wall in walls: screen.blit(img_wall, wall.rect)
        for cheese in cheeses: screen.blit(img_cheese, cheese.rect)
        for trap in traps: screen.blit(img_trap, trap.rect)
        if key: screen.blit(img_key, key.rect)
        if door: screen.blit(img_door, door.rect)
        
        screen.blit(img_mouse, player)
        if cat: screen.blit(img_cat, cat)

        info_text = f"Score: {score} | Key: {has_key} | Visited: {len(visited_cells)}"
        draw_text(screen, info_text, 30, SCREEN_WIDTH // 2, 20, colors["BLACK"])

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main_game()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Error detected. Press Enter to exit...")