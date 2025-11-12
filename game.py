import pygame
import cv2
import mediapipe as mp
import math
import random

# ==================================
# KONFIGURASI GAME (FIXED VERSION)
# ==================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
PLAYER_START_LEVEL = 2
PLAYER_BASE_SIZE = 60  # Ukuran awal player (Lvl 2)
PLAYER_GROWTH_FACTOR = 1.15 # Player membesar 15% setiap naik level

# Skor level up
SCORE_TO_LEVEL_UP = [
    10,  # Lvl 2 -> 3 (Total 10)
    30,  # Lvl 3 -> 4 (Total 40)
    70,  # Lvl 4 -> 5 (Total 110)
    130, # Lvl 5 -> 6 (Total 240)
    200, # Lvl 6 -> 7 (Total 440)
    300, # Lvl 7 -> 8 (Total 740)
    450, # Lvl 8 -> 9 (Total 1190)
    600, # Lvl 9 -> 10 (Total 1790)
    800, # Lvl 10 -> 11 (Total 2590)
    1000,# Lvl 11 -> 12 (Total 3590)
    1250,# Lvl 12 -> 13 (Total 4840)
    1500,# Lvl 13 -> 14 (Total 6340)
    2000 # Lvl 14 -> 15 (Total 8340)
]
MAX_LEVEL = 15
TOTAL_SCORE_TO_WIN = sum(SCORE_TO_LEVEL_UP)

# Database ukuran ikan
FISH_BASE_SIZES = {
    1: 30, 2: 60, 3: 50, 4: 55, 5: 80,
    6: 65, 7: 60, 8: 75, 9: 70, 10: 90,
    11: 85, 12: 80, 13: 100, 14: 120, 15: 250
}

# Asset paths
FISH_ASSET_PATHS = {
    1:  {"closed": "assets/Basic Fish 2.png",     "open": "assets/Basic Fish 1.png"},
    2:  {"closed": "assets/Anglar Fish 2.png",    "open": "assets/Anglar Fish 1.png"},
    3:  {"closed": "assets/Clownfish 2.png",      "open": "assets/Clownfish 1.png"},
    4:  {"closed": "assets/White Fish 2.png",     "open": "assets/White Fish 1.png"},
    5:  {"closed": "assets/Jellyfish 2.png",      "open": "assets/Jellyfish 1.png"},
    6:  {"closed": "assets/Surgeon Fish 2.png",   "open": "assets/Surgeon Fish 1.png"},
    7:  {"closed": "assets/Purple Fish 2.png",    "open": "assets/Purple Fish 1.png"},
    8:  {"closed": "assets/Flounder 2.png",       "open": "assets/Flounder 1.png"},
    9:  {"closed": "assets/Pattern Fish 2.png",   "open": "assets/Pattern Fish 1.png"},
    10: {"closed": "assets/Puffer Fish 2.png",    "open": "assets/Puffer Fish 1.png"},
    11: {"closed": "assets/Dapper Fish 2.png",    "open": "assets/Dapper Fish 1.png"},
    12: {"closed": "assets/Ninja Fish 2.png",     "open": "assets/Ninja Fish 1.png"},
    13: {"closed": "assets/Broadhammer Fish 2.png","open": "assets/Broadhammer Fish 1.png"},
    14: {"closed": "assets/Swordfish 2.png",      "open": "assets/Swordfish 1.png"},
    15: {"closed": "assets/Whale 2.png",          "open": "assets/Whale 1.png"}
}

# Spawn config
MAX_TOTAL_BOTS = 30
SPAWN_INTERVAL_GENERAL = 600 # ms
PREDATOR_THREAT_ZONE = 250
MOUTH_OPEN_THRESHOLD = 0.03

# Konfigurasi Safe Zone Tracking
TRACKING_X_MIN = 0.2
TRACKING_X_MAX = 0.8
TRACKING_Y_MIN = 0.25
TRACKING_Y_MAX = 0.75

# =====================
# Pygame init + assets
# =====================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Feeding Frenzy: Evolution (With Level Indicators)")
clock = pygame.time.Clock()

score_font = pygame.font.Font(None, 50)
level_font = pygame.font.Font(None, 50)
game_over_font = pygame.font.Font(None, 100)
win_font = pygame.font.Font(None, 100)
# Font untuk level indicator
indicator_font = pygame.font.Font(None, 36)
indicator_font_bold = pygame.font.Font(None, 42)

# Preload images
FISH_IMAGES = {}
try:
    for level, paths in FISH_ASSET_PATHS.items():
        FISH_IMAGES[level] = {
            "closed": pygame.image.load(paths["closed"]).convert_alpha(),
            "open": pygame.image.load(paths["open"]).convert_alpha()
        }
except FileNotFoundError as e:
    print(f"Error: Gagal load aset! File tidak ditemukan: {e.filename}")
    exit()

player_closed_base = FISH_IMAGES[PLAYER_START_LEVEL]["closed"]
player_open_base = FISH_IMAGES[PLAYER_START_LEVEL]["open"]

# =====================
# Helper function untuk draw level indicator
# =====================
def draw_level_indicator(surface, level, x, y, is_player=False, player_level=None):
    """
    Menggambar level indicator di atas ikan
    - Hijau: Bisa dimakan (level lebih rendah dari player)
    - Kuning: Sama level dengan player
    - Merah: Bahaya! (predator, level lebih tinggi)
    - Biru: Player sendiri
    """
    if is_player:
        # Player indicator (biru cyan)
        color = (0, 255, 255)
        text = indicator_font_bold.render(f"LV.{level}", True, (0, 0, 0))
        bg_text = indicator_font_bold.render(f"LV.{level}", True, color)
    else:
        # Bot fish indicator dengan color coding
        if player_level is not None:
            if level < player_level:
                color = (0, 255, 0)  # Hijau - Aman dimakan
            elif level == player_level:
                color = (255, 255, 0)  # Kuning - Sama level
            else:
                color = (255, 0, 0)  # Merah - Bahaya!
        else:
            color = (255, 255, 255)  # Default putih
        
        text = indicator_font.render(f"{level}", True, (0, 0, 0))
        bg_text = indicator_font.render(f"{level}", True, color)
    
    # Shadow/outline effect untuk readability
    text_rect = text.get_rect(center=(x, y - 35))
    
    # Draw shadow
    for offset_x in [-2, 0, 2]:
        for offset_y in [-2, 0, 2]:
            if offset_x != 0 or offset_y != 0:
                shadow_rect = text_rect.copy()
                shadow_rect.x += offset_x
                shadow_rect.y += offset_y
                surface.blit(text, shadow_rect)
    
    # Draw main text
    surface.blit(bg_text, text_rect)

# =====================
# Classes
# =====================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.level = PLAYER_START_LEVEL
        self.score = 0
        self.score_to_next = SCORE_TO_LEVEL_UP[0]
        self.current_size = FISH_BASE_SIZES[PLAYER_START_LEVEL]
        self.is_eating = False

        # create rect placeholder before load images
        self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.load_and_scale_images()

    def load_and_scale_images(self):
        size = (int(self.current_size), int(self.current_size))
        self.closed_mouth_image = pygame.transform.scale(player_closed_base, size)
        self.open_mouth_image = pygame.transform.scale(player_open_base, size)

        # Pastikan tampilan sesuai state is_eating: True -> open mouth
        self.image = self.open_mouth_image if self.is_eating else self.closed_mouth_image
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)

    def update(self, x, y, eating):
        target_pos = (x, y)
        current_pos = self.rect.center
        self.rect.center = (
            current_pos[0] + (target_pos[0] - current_pos[0]) * 0.2,
            current_pos[1] + (target_pos[1] - current_pos[1]) * 0.2
        )

        # update eating state and image
        if eating != self.is_eating:
            self.is_eating = eating
            new_image = self.open_mouth_image if self.is_eating else self.closed_mouth_image
            self.image = new_image
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)

    def add_score(self, points):
        self.score += points
        if self.level < MAX_LEVEL:
            current_level_index = self.level - PLAYER_START_LEVEL
            total_score_needed = sum(SCORE_TO_LEVEL_UP[:current_level_index + 1])
            if self.score >= total_score_needed:
                self.level_up()

    def level_up(self):
        self.level += 1
        self.current_size *= PLAYER_GROWTH_FACTOR
        self.load_and_scale_images()
        print(f"LEVEL UP! Kamu sekarang Level {self.level}")
        if self.level < MAX_LEVEL:
            next_level_index = self.level - PLAYER_START_LEVEL
            self.score_to_next = sum(SCORE_TO_LEVEL_UP[:next_level_index + 1])
        else:
            print("KAMU ADALAH PREDATOR PUNCAK!")
    
    def draw_indicator(self, surface):
        """Draw level indicator untuk player"""
        draw_level_indicator(surface, self.level, self.rect.centerx, self.rect.centery, 
                           is_player=True)


class BotFish(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level

        # Ambil base image
        closed_base = FISH_IMAGES[level]["closed"]
        open_base = FISH_IMAGES[level]["open"]

        base_scale = FISH_BASE_SIZES[level]
        scale = base_scale * random.uniform(0.9, 1.1)
        size = (int(scale), int(scale))

        # scale first
        self.closed_image = pygame.transform.scale(closed_base, size)
        self.open_image = pygame.transform.scale(open_base, size)

        # tentukan arah gerak dulu
        self.direction = random.choice([-1, 1])
        if self.direction == 1:
            start_x = -size[0]
        else:
            start_x = SCREEN_WIDTH + size[0]
            # jika spawn di kanan dan bergerak ke kiri, flip agar menghadap kiri
            self.closed_image = pygame.transform.flip(self.closed_image, True, False)
            self.open_image = pygame.transform.flip(self.open_image, True, False)

        # Setelah flip/scale, set image ke closed (default)
        self.image = self.closed_image

        start_y = random.randint(int(size[1] / 2), SCREEN_HEIGHT - int(size[1] / 2))
        self.rect = self.image.get_rect(center=(start_x, start_y))

        self.speed = random.randint(1, 3) + (self.level / 3)

        # Animasi
        self.animation_timer = pygame.time.get_ticks()
        self.animation_interval = random.randint(500, 2000)

    def update(self, player_level, player_rect):
        # Gerakan horizontal
        self.rect.x += self.speed * self.direction

        # Predator behavior
        if self.level > player_level:
            distance = math.hypot(self.rect.centerx - player_rect.centerx, self.rect.centery - player_rect.centery)
            if distance < PREDATOR_THREAT_ZONE:
                if self.rect.centery < player_rect.centery:
                    self.rect.y += 1
                elif self.rect.centery > player_rect.centery:
                    self.rect.y -= 1

        # Animasi mulut
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer > self.animation_interval:
            self.animation_timer = current_time
            center = self.rect.center
            # toggle antara closed dan open
            if self.image == self.closed_image:
                self.image = self.open_image
            else:
                self.image = self.closed_image
            self.rect = self.image.get_rect(center=center)

        # Despawn ketika keluar layar
        if (self.direction == 1 and self.rect.left > SCREEN_WIDTH + 50) or \
           (self.direction == -1 and self.rect.right < -50):
            self.kill()
    
    def draw_indicator(self, surface, player_level):
        """Draw level indicator untuk bot fish"""
        draw_level_indicator(surface, self.level, self.rect.centerx, self.rect.centery, 
                           is_player=False, player_level=player_level)

# =====================
# Helper functions
# =====================

def get_random_spawn_level(player_level):
    possible_levels = list(range(1, MAX_LEVEL + 1))
    weights = [0.0] * MAX_LEVEL

    # Simplified but robust probabilities
    if player_level <= 5:
        weights[0] = 0.7
        if player_level > 1:
            for lvl in range(1, player_level):
                weights[lvl] = 0.2 / (player_level - 1)
        if player_level + 1 <= MAX_LEVEL: weights[player_level] = 0.07
        if player_level + 2 <= MAX_LEVEL: weights[player_level + 1] = 0.03
    elif player_level <= 10:
        weights[0] = 0.4
        prey_levels = list(range(1, player_level))
        if prey_levels:
            for lvl in prey_levels: weights[lvl] = 0.3 / len(prey_levels)
        predator_levels = list(range(player_level, MAX_LEVEL))
        if predator_levels:
            for lvl in predator_levels: weights[lvl] = 0.3 / len(predator_levels)
    else:
        weights[0] = 0.3
        prey_levels = list(range(1, player_level))
        if prey_levels:
            for lvl in prey_levels: weights[lvl] = 0.5 / len(prey_levels)
        predator_levels = list(range(player_level, MAX_LEVEL))
        if predator_levels:
            for lvl in predator_levels: weights[lvl] = 0.2 / len(predator_levels)

    # jangan spawn selevel dengan player
    weights[player_level - 1] = 0.0

    # normalize fallback
    if sum(weights) == 0:
        return 1

    chosen_level = random.choices(possible_levels, weights=weights, k=1)[0]
    return chosen_level

# =====================
# Setup Mediapipe
# =====================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Tidak bisa membuka kamera.")
    exit()

# =====================
# Game init
# =====================
all_sprites = pygame.sprite.Group()
bot_fish_group = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

last_spawn_time = pygame.time.get_ticks()

running = True
game_over = False
win = False

# =====================
# Main loop
# =====================
while running:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        running = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if (game_over or win) and event.key == pygame.K_r:
                game_over = False
                win = False
                all_sprites.empty()
                bot_fish_group.empty()
                player = Player()
                all_sprites.add(player)
                last_spawn_time = pygame.time.get_ticks()

    success, image = cap.read()
    if not success: continue

    image = cv2.flip(image, 1)
    debug_image = image.copy()
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)

    player_x, player_y = player.rect.centerx, player.rect.centery
    is_eating = False

    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0].landmark
        nose_tip = face_landmarks[1]
        
        # Logika Mapping Safe Zone
        percent_x = (nose_tip.x - TRACKING_X_MIN) / (TRACKING_X_MAX - TRACKING_X_MIN)
        percent_y = (nose_tip.y - TRACKING_Y_MIN) / (TRACKING_Y_MAX - TRACKING_Y_MIN)

        percent_x = max(0.0, min(1.0, percent_x))
        percent_y = max(0.0, min(1.0, percent_y))

        player_x = int(percent_x * SCREEN_WIDTH)
        player_y = int(percent_y * SCREEN_HEIGHT)

        # Deteksi mulut terbuka
        lip_top = face_landmarks[13]
        lip_bottom = face_landmarks[14]
        lip_distance = abs(lip_top.y - lip_bottom.y)
        if lip_distance > MOUTH_OPEN_THRESHOLD:
            is_eating = True

        mp.solutions.drawing_utils.draw_landmarks(
            image=debug_image,
            landmark_list=results.multi_face_landmarks[0],
            connections=mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style()
        )

    cv2.imshow("CV Tracking Feed (Tekan 'q' untuk Keluar)", debug_image)

    if not game_over and not win:
        player.update(player_x, player_y, is_eating)
        bot_fish_group.update(player.level, player.rect)

    # Spawning
    if not game_over and not win and len(bot_fish_group) < MAX_TOTAL_BOTS:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time > SPAWN_INTERVAL_GENERAL:
            num_to_spawn = random.randint(1, 3)
            for _ in range(num_to_spawn):
                spawn_level = get_random_spawn_level(player.level)
                bot = BotFish(level=spawn_level)
                all_sprites.add(bot)
                bot_fish_group.add(bot)
            last_spawn_time = current_time

    # Collision
    if not game_over and not win:
        collisions = pygame.sprite.spritecollide(player, bot_fish_group, False)
        for fish in collisions:
            if player.is_eating and player.level >= fish.level:
                player.add_score(fish.level)
                fish.kill()
            elif player.level < fish.level:
                game_over = True

    if player.score >= TOTAL_SCORE_TO_WIN and not win:
        win = True
        player.level = MAX_LEVEL

    # ===== RENDER =====
    screen.fill((0, 105, 148))
    
    # Draw all sprites (ikan)
    all_sprites.draw(screen)
    
    # Draw level indicators di atas semua ikan
    player.draw_indicator(screen)
    for bot in bot_fish_group:
        bot.draw_indicator(screen, player.level)

    # UI Score & Level
    score_next = player.score_to_next if player.level < MAX_LEVEL else TOTAL_SCORE_TO_WIN
    score_text = score_font.render(f'Score: {player.score} / {score_next}', True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    level_text = level_font.render(f'Level: {player.level}', True, (255, 255, 255))
    screen.blit(level_text, (10, 50))
    
    # Legend indicator (pojok kanan atas)
    legend_y = 10
    legend_x = SCREEN_WIDTH - 250
    legend_title = indicator_font.render("Legend:", True, (255, 255, 255))
    screen.blit(legend_title, (legend_x, legend_y))
    legend_y += 35
    
    # Hijau = Aman
    green_text = indicator_font.render("🟢 = Safe to Eat", True, (0, 255, 0))
    screen.blit(green_text, (legend_x, legend_y))
    legend_y += 30
    
    # Merah = Bahaya
    red_text = indicator_font.render("🔴 = DANGER!", True, (255, 0, 0))
    screen.blit(red_text, (legend_x, legend_y))

    if game_over:
        text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
        prompt_text = score_font.render("Tekan 'R' untuk Mulai Lagi", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        screen.blit(prompt_text, prompt_rect)

    if win:
        text = win_font.render("YOU WIN!", True, (255, 215, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
        prompt_text = score_font.render("Tekan 'R' untuk Main Lagi", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        screen.blit(prompt_text, prompt_rect)

    pygame.display.flip()
    clock.tick(30)

# Cleanup
cap.release()
cv2.destroyAllWindows()
pygame.quit()