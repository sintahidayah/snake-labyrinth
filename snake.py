import pygame
import random
import heapq
import sys

# Konfigurasi awal
WIDTH, HEIGHT = 800, 600 # Lebar disesuaikan untuk info skor tambahan
GRID_SIZE = 30
CELL_SIZE = HEIGHT // GRID_SIZE # Ukuran sel berdasarkan tinggi
INFO_PANEL_WIDTH = 200

# Warna
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
BRIGHT_GREEN = (0, 250, 0)
BLUE_PLAYER = (0, 150, 255)
BRIGHT_BLUE_PLAYER = (100, 200, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GRID_GRAY = (40, 40, 40)
WALL_COLOR = (100, 100, 100)
CYAN_BRIGHT = (0, 255, 255)
MAGENTA_BRIGHT = (255, 0, 255)
YELLOW_BRIGHT = (255, 255, 0)
DARK_GRAY_BG = (20, 20, 20)
NEON_GREEN = (57, 255, 20)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = YELLOW_BRIGHT

# Inisialisasi Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake AI vs Player Labyrinth")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
rules_font_content = pygame.font.SysFont(None, 28)
title_font_rules = pygame.font.SysFont(None, 52)
prompt_font_rules = pygame.font.SysFont(None, 32)

MAZE_WALLS = set()
last_score_at_level_increase = 0

# ==============================================================================
# KELAS BARU UNTUK MENGELOLA ULAR
# ==============================================================================
class Snake:
    """Kelas untuk merepresentasikan seekor ular (AI atau Pemain)."""
    def __init__(self, start_pos, color, head_color, name):
        self.body = [start_pos]
        self.color = color
        self.head_color = head_color
        self.name = name
        self.score = 0
        self.direction = (1, 0) # Arah awal default

    def move(self, next_pos):
        """Memindahkan ular ke posisi berikutnya."""
        self.body.insert(0, next_pos)

    def grow(self):
        """Menumbuhkan ular dan menambah skor."""
        self.score += 1

    def shrink(self):
        """Memendekkan ular (menghapus ekor)."""
        self.body.pop()

    def check_self_collision(self):
        """Memeriksa apakah kepala menabrak tubuhnya sendiri."""
        return self.body[0] in self.body[1:]

    def draw(self, surface):
        """Menggambar ular di layar."""
        for i, segment in enumerate(self.body):
            color = self.head_color if i == 0 else self.color
            draw_cell(segment, color)

def initialize_maze_boundaries():
    MAZE_WALLS.clear()
    for i in range(GRID_SIZE):
        MAZE_WALLS.add((i, 0))
        MAZE_WALLS.add((i, GRID_SIZE - 1))
        MAZE_WALLS.add((0, i))
        MAZE_WALLS.add((GRID_SIZE - 1, i))

def add_labyrinth_walls(current_walls_set, player_snake, ai_snake, food_pos, num_walls_to_add=3):
    """Menambahkan dinding baru, menghindari kedua ular."""
    obstacles = set(player_snake.body) | set(ai_snake.body)
    added_count = 0
    for _ in range(num_walls_to_add * 50):
        if added_count >= num_walls_to_add: break
        rx, ry = random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2)
        new_wall = (rx, ry)
        if new_wall not in current_walls_set and new_wall not in obstacles and new_wall != food_pos:
            current_walls_set.add(new_wall)
            added_count += 1

def draw_grid_and_walls():
    for x in range(0, HEIGHT, CELL_SIZE): # Batas grid disamakan dengan tinggi
        pygame.draw.line(screen, GRID_GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_GRAY, (0, y), (HEIGHT, y)) # Lebar grid disamakan dengan tinggi
    for wall_pos in MAZE_WALLS:
        draw_cell(wall_pos, WALL_COLOR)

def draw_cell(pos, color):
    pygame.draw.rect(screen, color, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(pos):
    x, y = pos
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

# --- A* DIMODIFIKASI untuk menerima satu set rintangan ---
def a_star(start, goal, obstacles):
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        for neighbor in get_neighbors(current):
            if 0 <= neighbor[0] < GRID_SIZE and 0 <= neighbor[1] < GRID_SIZE:
                if neighbor in obstacles:
                    continue
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + heuristic(goal, neighbor)
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current
    return []

# --- Generate Food DIMODIFIKASI untuk menghindari kedua ular ---
def generate_food(player_snake, ai_snake, walls):
    max_attempts = GRID_SIZE * GRID_SIZE
    obstacles = set(player_snake.body) | set(ai_snake.body) | walls
    for _ in range(max_attempts):
        f = (random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2))
        if f not in obstacles:
            return f
    return None

# --- Game Over DIMODIFIKASI untuk menampilkan pemenang ---
def show_game_over(message, player_score, ai_score):
    screen.fill(BLACK)
    
    final_message_render = font.render(message, True, RED)
    screen.blit(final_message_render, (WIDTH // 2 - final_message_render.get_width() // 2, HEIGHT // 2 - 80))
    
    score_text = f"Skor Akhir -> Pemain: {player_score} | AI: {ai_score}"
    score_render = font.render(score_text, True, WHITE)
    screen.blit(score_render, (WIDTH // 2 - score_render.get_width() // 2, HEIGHT // 2 - 40))

    restart_text = font.render("Tekan tombol apa saja untuk memulai ulang", True, WHITE)
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
    
    quit_text = font.render("Tekan ESC untuk keluar", True, WHITE)
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 60))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                global last_score_at_level_increase
                last_score_at_level_increase = 0
                main()
                waiting = False

def draw_text_custom(surface, text, font, color, center_x, y_pos):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(centerx=center_x, top=y_pos)
    surface.blit(text_surface, text_rect)
    return text_rect.bottom

# --- Aturan DIMODIFIKASI untuk gameplay baru ---
def show_rules():
    screen.fill(DARK_GRAY_BG)
    current_y = HEIGHT // 12

    draw_text_custom(screen, "SNAKE: Player vs AI", title_font_rules, NEON_GREEN, WIDTH // 2, current_y)
    current_y += title_font_rules.get_height() + 25

    rules_sections = {
        "Tujuan Game:": [
            "Bertahan hidup lebih lama dari Ular AI.",
            "Kumpulkan makanan (merah) untuk tumbuh & mendapat skor."
        ],
        "Kontrol Pemain (Biru):": [
            "- Gunakan Tombol Panah (Arrow Keys) untuk bergerak.",
            "- Jangan menabrak dinding, dirimu, atau Ular AI!"
        ],
        "Tantangan:": [
            "- Ular AI (Hijau) juga berburu makanan yang sama.",
            "- Setiap 5 poin skor (total), labirin makin SULIT!",
            "- Kecepatan akan meningkat seiring total skor."
        ],
        "Game Over Jika:": [
            "- Anda menabrak sesuatu -> AI Menang.",
            "- AI menabrak sesuatu -> Anda Menang!"
        ]
    }
    content_start_x = WIDTH // 6
    for title, lines in rules_sections.items():
        current_y = draw_text_custom(screen, title, rules_font_content, HIGHLIGHT_COLOR, WIDTH // 2, current_y) + 10
        for line in lines:
            line_surface = rules_font_content.render(line, True, TEXT_COLOR)
            line_rect = line_surface.get_rect(left=content_start_x, top=current_y)
            screen.blit(line_surface, line_rect)
            current_y += line_rect.height + 8
        current_y += 15

    prompt_surface = prompt_font_rules.render("Tekan [SPASI] untuk Mulai!", True, WHITE)
    prompt_rect = prompt_surface.get_rect(centerx=WIDTH // 2, top=current_y + 20)
    screen.blit(prompt_surface, prompt_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: waiting = False
                elif event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

def get_valid_start_position(walls, other_pos=None):
    while True:
        pos = (random.randint(1, GRID_SIZE - 2), random.randint(1, GRID_SIZE - 2))
        if pos not in walls and pos != other_pos:
            return pos

# ==============================================================================
# FUNGSI UTAMA (MAIN) YANG DIROMBAK TOTAL
# ==============================================================================
def main():
    global MAZE_WALLS, last_score_at_level_increase

    initialize_maze_boundaries()
    if last_score_at_level_increase == 0:
        show_rules()

    # Inisialisasi kedua ular
    player_start_pos = get_valid_start_position(MAZE_WALLS)
    player = Snake(player_start_pos, BLUE_PLAYER, BRIGHT_BLUE_PLAYER, "Player")
    
    ai_start_pos = get_valid_start_position(MAZE_WALLS, player_start_pos)
    ai = Snake(ai_start_pos, GREEN, BRIGHT_GREEN, "AI")

    food = generate_food(player, ai, MAZE_WALLS)
    if food is None:
        show_game_over("Labirin terlalu padat!", 0, 0)
        return

    running = True
    while running:
        total_score = player.score + ai.score
        clock.tick(8 + total_score // 2)

        # --- Handle Input Pemain ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                if event.key == pygame.K_UP and player.direction != (0, 1):
                    player.direction = (0, -1)
                elif event.key == pygame.K_DOWN and player.direction != (0, -1):
                    player.direction = (0, 1)
                elif event.key == pygame.K_LEFT and player.direction != (1, 0):
                    player.direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and player.direction != (-1, 0):
                    player.direction = (1, 0)

        # --- Logika AI ---
        ai_obstacles = MAZE_WALLS | set(ai.body) | set(player.body)
        path = []
        if food:
            path = a_star(ai.body[0], food, ai_obstacles)
        
        if not path:
             show_game_over("Pemain Menang! AI tidak menemukan jalan.", player.score, ai.score)
             return

        # --- Tentukan langkah berikutnya untuk kedua ular ---
        player_head = player.body[0]
        player_next_pos = (player_head[0] + player.direction[0], player_head[1] + player.direction[1])

        ai_next_pos = path[0]

        # --- Deteksi Tabrakan ---
        # Pemain menabrak
        if player_next_pos in MAZE_WALLS or player_next_pos in player.body or player_next_pos in ai.body:
            show_game_over("AI Menang! Pemain menabrak.", player.score, ai.score)
            return
        # AI menabrak
        if ai_next_pos in MAZE_WALLS or ai_next_pos in ai.body:
            show_game_over("Pemain Menang! AI menabrak.", player.score, ai.score)
            return
        # AI menabrak pemain
        if ai_next_pos in player.body or ai_next_pos == player_next_pos: # Termasuk tabrakan kepala
            show_game_over("Pemain Menang! AI menabrak Anda.", player.score, ai.score)
            return

        # --- Pindahkan Kedua Ular ---
        player.move(player_next_pos)
        ai.move(ai_next_pos)

        # --- Cek Makan & Pertumbuhan ---
        ate_food = False
        # Cek pemain makan
        if player.body[0] == food:
            player.grow()
            ate_food = True
        else:
            player.shrink()
        
        # Cek AI makan
        if ai.body[0] == food:
            ai.grow()
            ate_food = True
        else:
            ai.shrink()
        
        # Jika ada yang makan, buat makanan baru
        if ate_food:
            food = generate_food(player, ai, MAZE_WALLS)
            if food is None:
                show_game_over("Papan Penuh! Tidak ada tempat makanan.", player.score, ai.score)
                return

        # --- Tingkatkan Kesulitan Labirin ---
        current_level_trigger = total_score // 5
        last_level_trigger = (last_score_at_level_increase // 5) if last_score_at_level_increase > 0 else -1
        if total_score > 0 and total_score % 5 == 0 and current_level_trigger > last_level_trigger:
            add_labyrinth_walls(MAZE_WALLS, player, ai, food, num_walls_to_add=2)
            last_score_at_level_increase = total_score

        # --- Menggambar Semua Elemen ---
        screen.fill(BLACK)
        # Area Game
        game_surface = screen.subsurface(pygame.Rect(0, 0, HEIGHT, HEIGHT))
        game_surface.fill(BLACK)
        draw_grid_and_walls()
        if food: draw_cell(food, RED)
        player.draw(game_surface)
        ai.draw(game_surface)

        # Panel Info di Kanan
        info_panel = screen.subsurface(pygame.Rect(HEIGHT, 0, INFO_PANEL_WIDTH, HEIGHT))
        info_panel.fill(DARK_GRAY_BG)
        
        draw_text_custom(info_panel, "SKOR", font, YELLOW_BRIGHT, INFO_PANEL_WIDTH // 2, 50)
        draw_text_custom(info_panel, f"Pemain: {player.score}", font, BRIGHT_BLUE_PLAYER, INFO_PANEL_WIDTH // 2, 100)
        draw_text_custom(info_panel, f"AI: {ai.score}", font, BRIGHT_GREEN, INFO_PANEL_WIDTH // 2, 140)
        draw_text_custom(info_panel, f"Total: {total_score}", font, WHITE, INFO_PANEL_WIDTH // 2, 180)

        pygame.display.flip()

if __name__ == "__main__":
    main()