import pygame
import sys
import os

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

GAME_TITLE = "Maze Runner: Escape the Cat"

game_running = True

# Кольори
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Шляхи до файлів
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def load_image(name, color_fallback):
    """
    4d. Функції: вбудовані (try/except)
    """
    path = os.path.join(ASSETS_DIR, name)
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    except FileNotFoundError:
        print(f"ПОМИЛКА: Не знайдено {path}")
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill(color_fallback)
        return surface

# Ініціалізація
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()

# Ассети
img_wall = load_image("wall.png", BLACK)
img_mouse = load_image("mouse.png", BLUE)
img_cat = load_image("cat.png", RED)
img_cheese = load_image("cheese.png", YELLOW)
img_key = load_image("key.png", GREEN)
img_door = load_image("exit.png", (100, 50, 0))
img_trap = load_image("trap.png", (128, 0, 128))

# Карта рівня
level_map = [
    "WWWWWWWWWWWWWWWWWWWW",
    "W P       C        W",
    "W WWWWWW WWWWWW WW W",
    "W C      W      C  W",
    "WWWWWW W W WWWWWWWWW",
    "W T    W C   E     W",
    "W WWW WWWWWWWWWW W W",
    "W K   T          W W",
    "WWWWWWWWWWWWWWWW D W",
    "WWWWWWWWWWWWWWWWWWWW"
]

class GameObject:
    def __init__(self, x, y, type_obj):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = type_obj

def setup_game():
    walls = []
    cheeses = []
    traps = []
    key = None
    door = None
    player_rect = None
    cat_rect = None
    
    for row_idx, row in enumerate(level_map):
        for col_idx in range(len(row)):
            char = row[col_idx]
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            
            if char == 'W':
                walls.append(GameObject(x, y, 'wall'))
            elif char == 'P':
                player_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            elif char == 'C':
                cheeses.append(GameObject(x, y, 'cheese'))
            elif char == 'K':
                key = GameObject(x, y, 'key')
            elif char == 'D':
                door = GameObject(x, y, 'door')
            elif char == 'T':
                traps.append(GameObject(x, y, 'trap'))
            elif char == 'E':
                cat_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                
    return walls, cheeses, key, door, traps, player_rect, cat_rect

def draw_text(text, size, x, y, color=BLACK):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, rect)

def debug_log(prefix, *messages):
    print(f"[DEBUG] {prefix}:", end=" ")
    for m in messages:
        print(m, end=" ")
    print()

def main_game():
    walls, cheeses, key, door, traps, player, cat = setup_game()
    
    has_key = False
    score = 0

    add_score = lambda x: x + 10
    
    running = True
    
    # Таймери для кота
    CAT_MOVE_DELAY = 500
    last_cat_move_time = pygame.time.get_ticks()

    def check_game_over(reason):
        nonlocal running
        print(f"Game Over: {reason}")
        draw_text(reason, 50, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, RED)
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(WHITE)
        
        # --- 1. ОБРОБКА ПОДІЙ ---
        dx, dy = 0, 0
        player_moved = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            
            # Рух гравця (покроковий)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: dx = -TILE_SIZE
                elif event.key == pygame.K_RIGHT: dx = TILE_SIZE
                elif event.key == pygame.K_UP: dy = -TILE_SIZE
                elif event.key == pygame.K_DOWN: dy = TILE_SIZE
                player_moved = True

        # --- 2. ЛОГІКА ГРАВЦЯ ---
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

        # --- 3. ЛОГІКА КОТА (Таймер + Обхід) ---
        if cat and (current_time - last_cat_move_time > CAT_MOVE_DELAY):
            last_cat_move_time = current_time
            
            diff_x = player.x - cat.x
            diff_y = player.y - cat.y

            cat_dx, cat_dy = 0, 0
            tried_horizontal = False
            
            # Пріоритет руху
            if abs(diff_x) > abs(diff_y):
                cat_dx = TILE_SIZE if diff_x > 0 else -TILE_SIZE
                tried_horizontal = True
            else:
                cat_dy = TILE_SIZE if diff_y > 0 else -TILE_SIZE
                tried_horizontal = False

            # Перевірка основного шляху
            test_rect = cat.move(cat_dx, cat_dy)
            hit_wall = any(test_rect.colliderect(w.rect) for w in walls)

            if hit_wall:
                # Альтернативний шлях
                cat_dx, cat_dy = 0, 0
                if tried_horizontal:
                    if diff_y != 0: cat_dy = TILE_SIZE if diff_y > 0 else -TILE_SIZE
                else:
                    if diff_x != 0: cat_dx = TILE_SIZE if diff_x > 0 else -TILE_SIZE
                
                test_rect = cat.move(cat_dx, cat_dy)
                hit_wall = any(test_rect.colliderect(w.rect) for w in walls)

            if not hit_wall and (cat_dx != 0 or cat_dy != 0):
                cat = test_rect

        # --- 4. КОЛІЗІЇ ---
        # Сир
        for cheese in cheeses[:]: 
            if player.colliderect(cheese.rect):
                cheeses.remove(cheese)
                score = add_score(score)
                debug_log("GameInfo", "Ням-ням! Сир з'їдено.", "Рахунок:", score)
                continue

        # Пастки
        for trap in traps:
            if player.colliderect(trap.rect):
                check_game_over("Ви потрапили в пастку!")

        # Кіт спіймав
        if cat and player.colliderect(cat):
            check_game_over("Кіт наздогнав вас!")

        # Ключ
        if key and player.colliderect(key.rect):
            has_key = True
            key = None 
            debug_log("GameInfo", "Ключ знайдено! Тепер шукай двері.")

        # Вихід
        if door and player.colliderect(door.rect):
            if has_key and len(cheeses) == 0:
                draw_text("YOU WIN!", 100, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, GREEN)
                pygame.display.flip()
                pygame.time.wait(3000)
                running = False
            elif not has_key:
                 pass 

        # --- 5. МАЛЮВАННЯ ---
        for wall in walls: screen.blit(img_wall, wall.rect)
        for cheese in cheeses: screen.blit(img_cheese, cheese.rect)
        for trap in traps: screen.blit(img_trap, trap.rect)
        if key: screen.blit(img_key, key.rect)
        if door: screen.blit(img_door, door.rect)
        
        screen.blit(img_mouse, player)
        if cat: screen.blit(img_cat, cat)

        info_text = f"Score: {score} | Key: {'Yes' if has_key else 'No'}"
        draw_text(info_text, 30, SCREEN_WIDTH // 2, 20, BLACK)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main_game()