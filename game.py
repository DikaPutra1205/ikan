import pygame
import cv2
import mediapipe as mp
import math
import random
import json
import os
import numpy as np


# ==================================
# KONFIGURASI GAME (ENHANCED VERSION)
# ==================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
PLAYER_START_LEVEL = 2
PLAYER_BASE_SIZE = 60
PLAYER_GROWTH_FACTOR = 1.15

# Skor level up
SCORE_TO_LEVEL_UP = [
    10, 30, 70, 130, 200, 300, 450, 600, 800, 1000, 1250, 1500, 2000
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
MAX_TOTAL_BOTS = 15  # Dikurangi dari 30 ke 15
SPAWN_INTERVAL_GENERAL = 2000  # Ditambah dari 600ms ke 2 detik
PREDATOR_THREAT_ZONE = 250
MOUTH_OPEN_THRESHOLD = 0.03

# Tracking config
TRACKING_X_MIN = 0.2
TRACKING_X_MAX = 0.8
TRACKING_Y_MIN = 0.25
TRACKING_Y_MAX = 0.75

# Health & Power-up config
MAX_HEALTH = 3
INVINCIBILITY_DURATION = 2000  # ms
POWER_UP_SPAWN_CHANCE = 0.02   # 2% per frame
POWER_UP_DURATION = {
    'speed': 5000,
    'shield': 8000,
    'magnet': 10000,
    'double_xp': 10000,
    'freeze': 5000,
    'size_boost': 7000
}

# Ultimate config
ULTIMATE_CHARGE_MAX = 100
ULTIMATE_DURATION = 5000

# Combo config
COMBO_TIMEOUT = 3000  # 3 detik
COMBO_MULTIPLIERS = {1: 1.0, 3: 1.5, 5: 2.0, 10: 3.0}

# =====================
# AUDIO FILE PATHS (Placeholder)
# =====================
# Buat folder "assets/sounds/" dan taruh file audio di sana
# Format yang didukung: .wav, .ogg, .mp3

AUDIO_FILES = {
    # === SOUND EFFECTS (SFX) ===
    'eat': 'assets/sounds/eat.mp3',              # Suara makan ikan (seperti "gulp" atau "nom")
    'level_up': 'assets/sounds/level-up.mp3',    # Fanfare/ding saat level naik
    'power_up_collect': 'assets/sounds/power-up-collect.mp3',  # "Bling!" saat ambil power-up
    'ultimate_ready': 'assets/sounds/powerup-ready.mp3',     # "Charged!" saat ultimate siap
    'ultimate_activate': 'assets/sounds/ultimate_activate.mp3', # Epic sound saat ultimate dipakai
    'hit': 'assets/sounds/hit.mp3',              # "Oof!" saat terkena predator
    'game_over': 'assets/sounds/game-over.mp3',  # Sad trombone/dramatic death sound
    'victory': 'assets/sounds/win.mp3',      # Triumphant fanfare saat menang
    
    # === BACKGROUND MUSIC (BGM) ===
    'bgm_gameplay': 'assets/sounds/bgm-gameplay.mp3',  # Upbeat underwater theme (looping)
    'bgm_menu': 'assets/sounds/ibgm-menu.mp3',          # Chill ocean ambience (optional)
}

# Rekomendasi sumber audio gratis:
# - freesound.org (SFX)
# - incompetech.com (BGM)
# - opengameart.org (Game audio)
# - zapsplat.com (SFX & music)

# =====================
# Pygame init + assets
# =====================
pygame.init()
pygame.mixer.init()  # Init audio mixer
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Feeding Frenzy: Evolution (Enhanced)")
clock = pygame.time.Clock()

# Fonts
score_font = pygame.font.Font(None, 50)
level_font = pygame.font.Font(None, 50)
game_over_font = pygame.font.Font(None, 100)
win_font = pygame.font.Font(None, 100)
indicator_font = pygame.font.Font(None, 36)
indicator_font_bold = pygame.font.Font(None, 42)
notification_font = pygame.font.Font(None, 60)
combo_font = pygame.font.Font(None, 70)
ui_font = pygame.font.Font(None, 32)

# Load images
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

# Load audio (with error handling)
SOUNDS = {}
def load_audio():
    """Load semua file audio, skip jika tidak ada"""
    for key, path in AUDIO_FILES.items():
        try:
            if os.path.exists(path):
                if 'bgm' in key:
                    SOUNDS[key] = pygame.mixer.Sound(path)
                else:
                    SOUNDS[key] = pygame.mixer.Sound(path)
                print(f"✓ Audio loaded: {key}")
            else:
                SOUNDS[key] = None
                print(f"⚠ Audio not found: {path}")
        except Exception as e:
            SOUNDS[key] = None
            print(f"⚠ Error loading {key}: {e}")

load_audio()

def play_sound(sound_key, volume=1.0):
    """Helper untuk play sound dengan error handling"""
    if sound_key in SOUNDS and SOUNDS[sound_key] is not None:
        SOUNDS[sound_key].set_volume(volume)
        SOUNDS[sound_key].play()

def play_bgm(sound_key, volume=0.5, loops=-1):
    """Helper untuk play background music (looping)"""
    if sound_key in SOUNDS and SOUNDS[sound_key] is not None:
        SOUNDS[sound_key].set_volume(volume)
        SOUNDS[sound_key].play(loops=loops)

# =====================
# Particle System
# =====================
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, velocity, lifetime=1000, size=5, particle_type='circle'):
        super().__init__()
        self.x = x
        self.y = y
        self.vx, self.vy = velocity
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.particle_type = particle_type
        
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = pygame.time.get_ticks()
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.spawn_time
        
        if elapsed >= self.lifetime:
            self.kill()
            return
        
        # Fade out
        alpha = int(255 * (1 - elapsed / self.lifetime))
        self.image.fill((0, 0, 0, 0))
        
        if self.particle_type == 'circle':
            pygame.draw.circle(self.image, (*self.color, alpha), (self.size, self.size), self.size)
        elif self.particle_type == 'star':
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                points.append((self.size + math.cos(angle) * self.size, 
                             self.size + math.sin(angle) * self.size))
            if len(points) >= 3:
                pygame.draw.polygon(self.image, (*self.color, alpha), points)
        
        self.rect.center = (int(self.x), int(self.y))

def create_eat_particles(x, y, particle_group):
    """Buat particle saat makan ikan"""
    for _ in range(8):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        color = random.choice([(255, 255, 100), (255, 200, 50), (255, 150, 0)])
        particle = Particle(x, y, color, velocity, lifetime=500, size=4, particle_type='circle')
        particle_group.add(particle)

def create_level_up_particles(x, y, particle_group):
    """Buat particle saat level up"""
    for _ in range(20):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 8)
        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        color = random.choice([(255, 215, 0), (255, 255, 100), (255, 200, 255)])
        particle = Particle(x, y, color, velocity, lifetime=1000, size=6, particle_type='star')
        particle_group.add(particle)

def create_hit_particles(x, y, particle_group):
    """Buat particle saat terkena hit"""
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 6)
        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        color = (255, 0, 0)
        particle = Particle(x, y, color, velocity, lifetime=700, size=5, particle_type='circle')
        particle_group.add(particle)

# =====================
# Background System
# =====================
class BackgroundLayer:
    def __init__(self, y_offset, speed, color, element_type='bubble'):
        self.y_offset = y_offset
        self.speed = speed
        self.color = color
        self.element_type = element_type
        self.elements = []
        
        # Generate random elements
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(5, 15)
            self.elements.append({'x': x, 'y': y, 'size': size})
    
    def update(self):
        for elem in self.elements:
            elem['x'] -= self.speed
            if elem['x'] < -elem['size']:
                elem['x'] = SCREEN_WIDTH + elem['size']
                elem['y'] = random.randint(0, SCREEN_HEIGHT)
    
    def draw(self, surface):
        for elem in self.elements:
            if self.element_type == 'bubble':
                pygame.draw.circle(surface, self.color, (int(elem['x']), int(elem['y'])), elem['size'], 2)
            elif self.element_type == 'seaweed':
                pygame.draw.line(surface, self.color, 
                               (int(elem['x']), SCREEN_HEIGHT),
                               (int(elem['x']), SCREEN_HEIGHT - elem['size'] * 4), 3)

# =====================
# Power-up System
# =====================
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.power_type = power_type
        self.size = 30
        
        # Warna power-up
        colors = {
            'speed': (0, 255, 255),      # Cyan
            'shield': (255, 215, 0),     # Gold
            'magnet': (255, 0, 255),     # Magenta
            'double_xp': (0, 255, 0),    # Green
            'freeze': (100, 200, 255),   # Light blue
            'size_boost': (255, 100, 0)  # Orange
        }
        
        self.color = colors.get(power_type, (255, 255, 255))
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.size // 2, self.size // 2), self.size // 2)
        pygame.draw.circle(self.image, (255, 255, 255), (self.size // 2, self.size // 2), self.size // 2 - 3, 2)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.float_offset = random.uniform(0, math.pi * 2)
        self.spawn_time = pygame.time.get_ticks()
        
    def update(self):
        # Floating animation
        time = pygame.time.get_ticks() / 1000.0
        self.rect.y += math.sin(time * 3 + self.float_offset) * 0.5
        
        # Despawn after 10 seconds
        if pygame.time.get_ticks() - self.spawn_time > 10000:
            self.kill()

# =====================
# Notification System
# =====================
class Notification:
    def __init__(self, text, color=(255, 255, 255), duration=2000, size='normal'):
        self.text = text
        self.color = color
        self.duration = duration
        self.spawn_time = pygame.time.get_ticks()
        self.font = combo_font if size == 'large' else notification_font
        self.alpha = 255
        
    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.duration:
            return False
        
        # Fade out di akhir
        if elapsed > self.duration - 500:
            self.alpha = int(255 * (1 - (elapsed - (self.duration - 500)) / 500))
        
        return True
    
    def draw(self, surface):
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        surface.blit(text_surface, text_rect)

# =====================
# Helper functions
# =====================
def draw_level_indicator(surface, level, x, y, is_player=False, player_level=None):
    if is_player:
        color = (0, 255, 255)
        text = indicator_font_bold.render(f"LV.{level}", True, (0, 0, 0))
        bg_text = indicator_font_bold.render(f"LV.{level}", True, color)
    else:
        if player_level is not None:
            if level < player_level:
                color = (0, 255, 0)
            elif level == player_level:
                color = (255, 255, 0)
            else:
                color = (255, 0, 0)
        else:
            color = (255, 255, 255)
        
        text = indicator_font.render(f"{level}", True, (0, 0, 0))
        bg_text = indicator_font.render(f"{level}", True, color)
    
    text_rect = text.get_rect(center=(x, y - 35))
    
    for offset_x in [-2, 0, 2]:
        for offset_y in [-2, 0, 2]:
            if offset_x != 0 or offset_y != 0:
                shadow_rect = text_rect.copy()
                shadow_rect.x += offset_x
                shadow_rect.y += offset_y
                surface.blit(text, shadow_rect)
    
    surface.blit(bg_text, text_rect)

def get_random_spawn_level(player_level):
    possible_levels = list(range(1, MAX_LEVEL + 1))
    weights = [0.0] * MAX_LEVEL

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

    weights[player_level - 1] = 0.0

    if sum(weights) == 0:
        return 1

    chosen_level = random.choices(possible_levels, weights=weights, k=1)[0]
    return chosen_level

def apply_screen_shake(intensity=10):
    """Return random offset untuk screen shake"""
    return (random.randint(-intensity, intensity), random.randint(-intensity, intensity))

def draw_progress_bar(surface, x, y, width, height, progress, bg_color=(50, 50, 50), fill_color=(0, 255, 0)):
    """Draw progress bar"""
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    fill_width = int(width * progress)
    if fill_width > 0:
        pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)

# =====================
# Save System
# =====================
class SaveData:
    def __init__(self):
        self.filename = 'savegame.json'
        self.data = self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return self.default_data()
        return self.default_data()
    
    def default_data(self):
        return {
            'high_score': 0,
            'total_fish_eaten': 0,
            'total_playtime': 0,
            'games_played': 0,
            'max_level_reached': 2,
            'max_combo': 0
        }
    
    def save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving: {e}")
    
    def update_stats(self, score, fish_eaten, level, combo):
        self.data['high_score'] = max(self.data['high_score'], score)
        self.data['total_fish_eaten'] += fish_eaten
        self.data['games_played'] += 1
        self.data['max_level_reached'] = max(self.data['max_level_reached'], level)
        self.data['max_combo'] = max(self.data['max_combo'], combo)
        self.save()

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
        
        # Health system
        self.health = MAX_HEALTH
        self.max_health = MAX_HEALTH
        self.invincible = False
        self.invincible_timer = 0
        
        # Power-ups
        self.active_powerups = {}
        self.base_speed = 1.0
        self.current_speed = 1.0
        self.magnet_radius = 0
        self.double_xp = False
        self.frozen_enemies = False
        self.size_multiplier = 1.0
        
        # Ultimate
        self.ultimate_charge = 0
        self.ultimate_active = False
        self.ultimate_timer = 0
        
        # Combo
        self.combo_count = 0
        self.combo_timer = 0
        self.max_combo = 0
        
        # Stats
        self.fish_eaten = 0

        self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.load_and_scale_images()

    def load_and_scale_images(self):
        size = int(self.current_size * self.size_multiplier)
        self.closed_mouth_image = pygame.transform.scale(player_closed_base, (size, size))
        self.open_mouth_image = pygame.transform.scale(player_open_base, (size, size))
        self.image = self.open_mouth_image if self.is_eating else self.closed_mouth_image
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)

    def update(self, x, y, eating):
        # Movement with speed multiplier
        target_pos = (x, y)
        current_pos = self.rect.center
        speed = 0.2 * self.current_speed
        self.rect.center = (
            current_pos[0] + (target_pos[0] - current_pos[0]) * speed,
            current_pos[1] + (target_pos[1] - current_pos[1]) * speed
        )

        # Update eating state
        if eating != self.is_eating:
            self.is_eating = eating
            new_image = self.open_mouth_image if self.is_eating else self.closed_mouth_image
            self.image = new_image
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)
        
        # Update invincibility
        if self.invincible:
            self.invincible_timer -= clock.get_time()
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Update power-ups
        current_time = pygame.time.get_ticks()
        expired = []
        for power_type, end_time in self.active_powerups.items():
            if current_time >= end_time:
                expired.append(power_type)
        
        for power_type in expired:
            self.deactivate_powerup(power_type)
        
        # Update ultimate
        if self.ultimate_active:
            self.ultimate_timer -= clock.get_time()
            if self.ultimate_timer <= 0:
                self.deactivate_ultimate()
        
        # Update combo timer
        if self.combo_count > 0:
            self.combo_timer -= clock.get_time()
            if self.combo_timer <= 0:
                self.combo_count = 0

    def add_score(self, points):
        multiplier = 2.0 if self.double_xp else 1.0
        
        # Combo multiplier
        if self.combo_count >= 10:
            multiplier *= 3.0
        elif self.combo_count >= 5:
            multiplier *= 2.0
        elif self.combo_count >= 3:
            multiplier *= 1.5
        
        final_points = int(points * multiplier)
        self.score += final_points
        
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
        play_sound('level_up', 0.7)
        
        if self.level < MAX_LEVEL:
            next_level_index = self.level - PLAYER_START_LEVEL
            self.score_to_next = sum(SCORE_TO_LEVEL_UP[:next_level_index + 1])
        else:
            print("KAMU ADALAH PREDATOR PUNCAK!")
    
    def add_combo(self):
        self.combo_count += 1
        self.max_combo = max(self.max_combo, self.combo_count)
        self.combo_timer = COMBO_TIMEOUT
        
        # Play combo sound
        if self.combo_count in [3, 5, 10]:
            play_sound('eat_combo', 0.8)
    
    def take_damage(self):
        if self.invincible or self.ultimate_active:
            return False
        
        self.health -= 1
        self.invincible = True
        self.invincible_timer = INVINCIBILITY_DURATION
        self.combo_count = 0
        play_sound('hit', 0.8)
        return self.health <= 0
    
    def activate_powerup(self, power_type):
        current_time = pygame.time.get_ticks()
        self.active_powerups[power_type] = current_time + POWER_UP_DURATION[power_type]
        
        if power_type == 'speed':
            self.current_speed = 2.0
        elif power_type == 'shield':
            self.invincible = True
            self.invincible_timer = POWER_UP_DURATION['shield']
        elif power_type == 'magnet':
            self.magnet_radius = 200
        elif power_type == 'double_xp':
            self.double_xp = True
        elif power_type == 'freeze':
            self.frozen_enemies = True
        elif power_type == 'size_boost':
            self.size_multiplier = 1.5
            self.load_and_scale_images()
        
        play_sound('power_up_activate', 0.6)
    
    def deactivate_powerup(self, power_type):
        del self.active_powerups[power_type]
        
        if power_type == 'speed':
            self.current_speed = 1.0
        elif power_type == 'magnet':
            self.magnet_radius = 0
        elif power_type == 'double_xp':
            self.double_xp = False
        elif power_type == 'freeze':
            self.frozen_enemies = False
        elif power_type == 'size_boost':
            self.size_multiplier = 1.0
            self.load_and_scale_images()
    
    def charge_ultimate(self, amount):
        if not self.ultimate_active:
            self.ultimate_charge = min(ULTIMATE_CHARGE_MAX, self.ultimate_charge + amount)
            if self.ultimate_charge >= ULTIMATE_CHARGE_MAX:
                play_sound('ultimate_ready', 0.7)
    
    def activate_ultimate(self):
        if self.ultimate_charge >= ULTIMATE_CHARGE_MAX and not self.ultimate_active:
            self.ultimate_active = True
            self.ultimate_timer = ULTIMATE_DURATION
            self.ultimate_charge = 0
            self.invincible = True
            play_sound('ultimate_activate', 0.8)
            return True
        return False
    
    def deactivate_ultimate(self):
        self.ultimate_active = False
        self.invincible = False
    
    def draw_indicator(self, surface):
        draw_level_indicator(surface, self.level, self.rect.centerx, self.rect.centery, is_player=True)
    
    def draw_ui(self, surface):
        # Health hearts
        heart_size = 30
        for i in range(self.max_health):
            x = 10 + i * (heart_size + 10)
            y = 100
            if i < self.health:
                color = (255, 0, 0)
            else:
                color = (100, 100, 100)
            pygame.draw.polygon(surface, color, [
                (x + heart_size // 2, y + 5),
                (x + heart_size - 5, y + heart_size // 2),
                (x + heart_size // 2, y + heart_size),
                (x + 5, y + heart_size // 2)
            ])
        
        # Ultimate bar
        bar_x, bar_y = 10, 150
        bar_width, bar_height = 200, 20
        draw_progress_bar(surface, bar_x, bar_y, bar_width, bar_height, 
                         self.ultimate_charge / ULTIMATE_CHARGE_MAX,
                         bg_color=(50, 50, 50), fill_color=(255, 215, 0))
        
        ult_text = ui_font.render("ULTIMATE", True, (255, 255, 255))
        surface.blit(ult_text, (bar_x, bar_y - 25))
        
        if self.ultimate_active:
            timer_sec = self.ultimate_timer / 1000
            timer_text = ui_font.render(f"{timer_sec:.1f}s", True, (255, 215, 0))
            surface.blit(timer_text, (bar_x + bar_width + 10, bar_y))
        
        # Active power-ups
        powerup_y = 190
        current_time = pygame.time.get_ticks()
        for power_type, end_time in self.active_powerups.items():
            remaining = (end_time - current_time) / 1000
            if remaining > 0:
                text = ui_font.render(f"{power_type.upper()}: {remaining:.1f}s", True, (255, 255, 255))
                surface.blit(text, (10, powerup_y))
                powerup_y += 30
        
        # Combo counter
        if self.combo_count >= 3:
            combo_text = combo_font.render(f"COMBO x{self.combo_count}!", True, (255, 215, 0))
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            # Outline
            for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                outline_text = combo_font.render(f"COMBO x{self.combo_count}!", True, (0, 0, 0))
                surface.blit(outline_text, (combo_rect.x + offset[0], combo_rect.y + offset[1]))
            surface.blit(combo_text, combo_rect)


class BotFish(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.level = level

        closed_base = FISH_IMAGES[level]["closed"]
        open_base = FISH_IMAGES[level]["open"]

        base_scale = FISH_BASE_SIZES[level]
        scale = base_scale * random.uniform(0.9, 1.1)
        size = (int(scale), int(scale))

        self.closed_image = pygame.transform.scale(closed_base, size)
        self.open_image = pygame.transform.scale(open_base, size)

        self.direction = random.choice([-1, 1])
        if self.direction == 1:
            start_x = -size[0]
        else:
            start_x = SCREEN_WIDTH + size[0]
            self.closed_image = pygame.transform.flip(self.closed_image, True, False)
            self.open_image = pygame.transform.flip(self.open_image, True, False)

        self.image = self.closed_image

        start_y = random.randint(int(size[1] / 2), SCREEN_HEIGHT - int(size[1] / 2))
        self.rect = self.image.get_rect(center=(start_x, start_y))

        self.speed = random.randint(1, 3) + (self.level / 3)
        self.base_speed = self.speed

        self.animation_timer = pygame.time.get_ticks()
        self.animation_interval = random.randint(500, 2000)
        
        self.frozen = False

    def update(self, player_level, player_rect, frozen=False):
        # Apply freeze effect
        if frozen:
            self.speed = self.base_speed * 0.3
        else:
            self.speed = self.base_speed
        
        # Movement
        self.rect.x += self.speed * self.direction

        # Predator behavior
        if self.level > player_level and not frozen:
            distance = math.hypot(self.rect.centerx - player_rect.centerx, self.rect.centery - player_rect.centery)
            if distance < PREDATOR_THREAT_ZONE:
                if self.rect.centery < player_rect.centery:
                    self.rect.y += 1
                elif self.rect.centery > player_rect.centery:
                    self.rect.y -= 1

        # Animation
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer > self.animation_interval:
            self.animation_timer = current_time
            center = self.rect.center
            if self.image == self.closed_image:
                self.image = self.open_image
            else:
                self.image = self.closed_image
            self.rect = self.image.get_rect(center=center)

        # Despawn
        if (self.direction == 1 and self.rect.left > SCREEN_WIDTH + 50) or \
           (self.direction == -1 and self.rect.right < -50):
            self.kill()
    
    def draw_indicator(self, surface, player_level):
        draw_level_indicator(surface, self.level, self.rect.centerx, self.rect.centery, 
                           is_player=False, player_level=player_level)


# =====================
# Game States & Pause Menu
# =====================
class PauseMenu:
    def __init__(self):
        self.active = False
        self.selected = 0
        self.options = ['Resume', 'Restart', 'Quit']
        
    def toggle(self):
        self.active = not self.active
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected]
        return None
    
    def draw(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = game_over_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        surface.blit(title, title_rect)
        
        # Options
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (255, 255, 255)
            text = notification_font.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60))
            surface.blit(text, text_rect)


# =====================
# Tutorial & Welcome Screen System
# =====================
class WelcomeScreen:
    def __init__(self):
        self.active = True
        self.alpha = 0
        self.fade_in = True
        self.fade_speed = 5
        
    def update(self):
        if self.fade_in:
            self.alpha = min(255, self.alpha + self.fade_speed)
            if self.alpha >= 255:
                self.fade_in = False
        return self.active
    
    def skip(self):
        self.active = False
    
    def draw(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(min(220, self.alpha))
        overlay.fill((0, 20, 40))
        surface.blit(overlay, (0, 0))
        
        if self.alpha < 100:
            return
        
        y_offset = SCREEN_HEIGHT // 2 - 300
        
        # Title
        title = game_over_font.render("FEEDING FRENZY", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        surface.blit(title, title_rect)
        
        subtitle = notification_font.render("Evolution", True, (255, 255, 255))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 80))
        surface.blit(subtitle, subtitle_rect)
        
        # Controls section
        y_offset += 160
        controls_title = level_font.render("=== KONTROL ===", True, (255, 215, 0))
        controls_rect = controls_title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        surface.blit(controls_title, controls_rect)
        
        controls = [
            ("🎭 Gerakkan Wajah", "Kontrol arah ikan kamu"),
            ("👄 Buka Mulut", "Makan ikan yang lebih kecil (hijau)"),
            ("⌨️  SPACE", "Aktifkan Ultimate (saat bar penuh)"),
            ("⌨️  ESC", "Pause menu"),
            ("⌨️  R", "Restart (saat game over)")
        ]
        
        y_offset += 50
        for control, description in controls:
            # Control key
            control_text = ui_font.render(control, True, (255, 255, 0))
            control_rect = control_text.get_rect(midright=(SCREEN_WIDTH // 2 - 20, y_offset))
            surface.blit(control_text, control_rect)
            
            # Description
            desc_text = ui_font.render(f"→ {description}", True, (200, 200, 200))
            desc_rect = desc_text.get_rect(midleft=(SCREEN_WIDTH // 2 + 20, y_offset))
            surface.blit(desc_text, desc_rect)
            
            y_offset += 40
        
        # Game tips
        y_offset += 30
        tips_title = level_font.render("=== TIPS ===", True, (255, 215, 0))
        tips_rect = tips_title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        surface.blit(tips_title, tips_rect)
        
        tips = [
            "🟢 Hijau = Aman dimakan  |  🔴 Merah = BAHAYA!",
            "⚡ Power-ups: Kumpulkan untuk buff sementara",
            "🔥 Combo: Makan berturut-turut = bonus score",
            "💎 Ultimate: Makan SEMUA ikan selama 5 detik!"
        ]
        
        y_offset += 45
        for tip in tips:
            tip_text = ui_font.render(tip, True, (200, 255, 200))
            tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            surface.blit(tip_text, tip_rect)
            y_offset += 35
        
        # Start prompt (blinking)
        blink = (pygame.time.get_ticks() // 500) % 2
        if blink:
            start_text = notification_font.render("Tekan SEMBARANG TOMBOL untuk Mulai", True, (255, 255, 0))
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            surface.blit(start_text, start_rect)
        
        # Additional info
        info_text = ui_font.render("(Pastikan wajah kamu terlihat di webcam)", True, (150, 150, 150))
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        surface.blit(info_text, info_rect)


class Tutorial:
    def __init__(self):
        self.tips = [
            "💡 Gerakkan wajahmu lebih cepat untuk kontrol lebih responsif!",
            "💡 Hindari ikan merah! Mereka akan mengejarmu!",
            "💡 Kumpulkan power-up berwarna untuk keuntungan!",
            "💡 Combo x3 = Score x1.5! Terus makan tanpa jeda!",
            "💡 Ultimate siap! Tekan SPACE untuk mode Feeding Frenzy!",
        ]
        self.current_tip = 0
        self.shown_tips = set()
        self.display_time = 4000
        self.tip_start_time = 0
        self.active = True
        self.show_controls = True  # Show persistent controls reminder
        
    def show_next_tip(self):
        if self.current_tip < len(self.tips):
            self.shown_tips.add(self.current_tip)
            self.tip_start_time = pygame.time.get_ticks()
            self.current_tip += 1
            return True
        return False
    
    def update(self):
        if self.current_tip > 0 and self.current_tip <= len(self.tips):
            elapsed = pygame.time.get_ticks() - self.tip_start_time
            if elapsed > self.display_time:
                return False
        return True
    
    def draw(self, surface):
        # Draw in-game tip
        if self.current_tip > 0 and self.current_tip <= len(self.tips):
            tip_text = self.tips[self.current_tip - 1]
            text = ui_font.render(tip_text, True, (255, 255, 255))
            
            # Background box
            padding = 20
            box_width = text.get_width() + padding * 2
            box_height = text.get_height() + padding
            box_x = (SCREEN_WIDTH - box_width) // 2
            box_y = SCREEN_HEIGHT - 100
            
            pygame.draw.rect(surface, (0, 0, 0, 200), (box_x, box_y, box_width, box_height))
            pygame.draw.rect(surface, (255, 215, 0), (box_x, box_y, box_width, box_height), 2)
            
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, box_y + box_height // 2))
            surface.blit(text, text_rect)
        
        # Persistent controls reminder (top right)
        if self.show_controls:
            controls_y = SCREEN_HEIGHT - 200
            controls_x = 10
            
            small_font = pygame.font.Font(None, 24)
            
            controls_list = [
                "Controls:",
                "👄 Open mouth = Eat",
                "🎭 Move face = Move",
                "SPACE = Ultimate",
                "ESC = Pause"
            ]
            
            for i, control in enumerate(controls_list):
                color = (255, 255, 0) if i == 0 else (200, 200, 200)
                text = small_font.render(control, True, color)
                surface.blit(text, (controls_x, controls_y + i * 22))


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
particle_group = pygame.sprite.Group()
powerup_group = pygame.sprite.Group()

player = Player()
all_sprites.add(player)

# Background layers
bg_layers = [
    BackgroundLayer(0, 0.5, (100, 150, 200), 'bubble'),
    BackgroundLayer(0, 1.0, (80, 120, 160), 'bubble'),
    BackgroundLayer(0, 0.3, (60, 100, 140), 'seaweed')
]

# Game state
pause_menu = PauseMenu()
tutorial = Tutorial()
save_data = SaveData()
welcome_screen = WelcomeScreen()
notifications = []

last_spawn_time = pygame.time.get_ticks()
last_powerup_spawn = pygame.time.get_ticks()

running = True
game_over = False
win = False
paused = False
game_started = False  # Game only starts after welcome screen
screen_shake_intensity = 0

# Start BGM
play_bgm('bgm_gameplay', volume=0.3)

# =====================
# Main loop
# =====================
while running:
    dt = clock.tick(30)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        running = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
             pygame.display.toggle_fullscreen()

            # Welcome screen - any key to start
            if welcome_screen.active:
                welcome_screen.skip()
                game_started = True
                tutorial.show_next_tip()  # Show first tip after welcome
                continue
            
            # Pause
            if event.key == pygame.K_ESCAPE and not game_over and not win:
                pause_menu.toggle()
                paused = pause_menu.active
            
            # Pause menu navigation
            if paused:
                action = pause_menu.handle_input(event)
                if action == 'Resume':
                    pause_menu.toggle()
                    paused = False
                elif action == 'Restart':
                    # Reset game
                    save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
                    game_over = False
                    win = False
                    paused = False
                    pause_menu.active = False
                    all_sprites.empty()
                    bot_fish_group.empty()
                    particle_group.empty()
                    powerup_group.empty()
                    player = Player()
                    all_sprites.add(player)
                    last_spawn_time = pygame.time.get_ticks()
                    notifications.clear()
                    tutorial = Tutorial()
                    tutorial.show_next_tip()
                elif action == 'Quit':
                    save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
                    running = False
            
            # Restart after game over/win
            if (game_over or win) and event.key == pygame.K_r:
                save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
                game_over = False
                win = False
                game_started = False  # Show welcome screen again
                all_sprites.empty()
                bot_fish_group.empty()
                particle_group.empty()
                powerup_group.empty()
                player = Player()
                all_sprites.add(player)
                last_spawn_time = pygame.time.get_ticks()
                notifications.clear()
                tutorial = Tutorial()
                welcome_screen = WelcomeScreen()  # Reset welcome screen
            
            # Ultimate activation
            if event.key == pygame.K_SPACE and not game_over and not win and not paused and game_started:
                if player.activate_ultimate():
                    notifications.append(Notification("FEEDING FRENZY!", (255, 215, 0), 2000, 'large'))

    # Show welcome screen
    if welcome_screen.active:
        welcome_screen.update()
        screen.fill((0, 105, 148))
        welcome_screen.draw(screen)
        pygame.display.flip()
        continue

    if paused:
        pause_menu.draw(screen)
        pygame.display.flip()
        continue

    # Camera tracking
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
        
        percent_x = (nose_tip.x - TRACKING_X_MIN) / (TRACKING_X_MAX - TRACKING_X_MIN)
        percent_y = (nose_tip.y - TRACKING_Y_MIN) / (TRACKING_Y_MAX - TRACKING_Y_MIN)

        percent_x = max(0.0, min(1.0, percent_x))
        percent_y = max(0.0, min(1.0, percent_y))

        player_x = int(percent_x * SCREEN_WIDTH)
        player_y = int(percent_y * SCREEN_HEIGHT)

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

        # === FACE CAM TO PYGAME SURFACE ===
        cam_frame = cv2.cvtColor(debug_image, cv2.COLOR_BGR2RGB)  
        cam_frame = np.rot90(cam_frame)  # orientasi biar bener  
        cam_surface = pygame.surfarray.make_surface(cam_frame)
        cam_surface = pygame.transform.scale(cam_surface, (260, 150))  # ukuran facecam


    # Only update game if started
    if not game_started:
        continue

    # Update
    if not game_over and not win:
        player.update(player_x, player_y, is_eating)
        bot_fish_group.update(player.level, player.rect, player.frozen_enemies)
        particle_group.update()
        powerup_group.update()
        
        # Magnet effect
        if player.magnet_radius > 0:
            for bot in bot_fish_group:
                if bot.level < player.level:
                    distance = math.hypot(bot.rect.centerx - player.rect.centerx, 
                                        bot.rect.centery - player.rect.centery)
                    if distance < player.magnet_radius:
                        dx = player.rect.centerx - bot.rect.centerx
                        dy = player.rect.centery - bot.rect.centery
                        bot.rect.x += dx * 0.05
                        bot.rect.y += dy * 0.05
        
        # Tutorial progression
        if player.score > 20 and 1 not in tutorial.shown_tips:
            tutorial.current_tip = 2
            tutorial.show_next_tip()
        if player.combo_count >= 3 and 5 not in tutorial.shown_tips:
            tutorial.current_tip = 6
            tutorial.show_next_tip()

    # Spawning bots
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
    
    # Spawning power-ups
    if not game_over and not win:
        current_time = pygame.time.get_ticks()
        if current_time - last_powerup_spawn > 5000:  # Check every 5 seconds
            if random.random() < POWER_UP_SPAWN_CHANCE * 100:  # Compensate for lower check frequency
                power_type = random.choice(['speed', 'shield', 'magnet', 'double_xp', 'freeze', 'size_boost'])
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(100, SCREEN_HEIGHT - 100)
                powerup = PowerUp(x, y, power_type)
                powerup_group.add(powerup)
            last_powerup_spawn = current_time

    # Collision with bots
    if not game_over and not win:
        collisions = pygame.sprite.spritecollide(player, bot_fish_group, False)
        for fish in collisions:
            if player.is_eating and (player.level >= fish.level or player.ultimate_active):
                player.add_score(fish.level)
                player.fish_eaten += 1
                player.add_combo()
                player.charge_ultimate(10)
                create_eat_particles(fish.rect.centerx, fish.rect.centery, particle_group)
                fish.kill()
                play_sound('eat', 0.5)
            elif player.level < fish.level and not player.ultimate_active:
                is_dead = player.take_damage()
                create_hit_particles(player.rect.centerx, player.rect.centery, particle_group)
                screen_shake_intensity = 15
                if is_dead:
                    game_over = True
                    play_sound('game_over', 0.8)
    
    # Collision with power-ups
    if not game_over and not win:
        powerup_collisions = pygame.sprite.spritecollide(player, powerup_group, True)
        for powerup in powerup_collisions:
            player.activate_powerup(powerup.power_type)
            notifications.append(Notification(f"{powerup.power_type.upper()} Activated!", (255, 255, 0), 1500))
            play_sound('power_up_collect', 0.7)

    # Check win condition
    if player.score >= TOTAL_SCORE_TO_WIN and not win:
        win = True
        player.level = MAX_LEVEL
        play_sound('victory', 0.8)

    # Update notifications
    notifications = [n for n in notifications if n.update()]

    # Update background
    for layer in bg_layers:
        layer.update()

    # Screen shake decay
    if screen_shake_intensity > 0:
        screen_shake_intensity -= 1

    # ===== RENDER =====
    screen.fill((0, 105, 148))
    
    # Draw background layers
    for layer in bg_layers:
        layer.draw(screen)
    
    # Apply screen shake
    shake_offset = (0, 0)
    if screen_shake_intensity > 0:
        shake_offset = apply_screen_shake(screen_shake_intensity)
    
    # Create temporary surface for shake effect
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface.fill((0, 105, 148))
    
    # Draw on game surface
    for layer in bg_layers:
        layer.draw(game_surface)
    
    # Draw sprites
    for sprite in all_sprites:
        game_surface.blit(sprite.image, sprite.rect)
    
    # Draw particles
    for particle in particle_group:
        game_surface.blit(particle.image, particle.rect)
    
    # Draw power-ups
    for powerup in powerup_group:
        game_surface.blit(powerup.image, powerup.rect)
    
    # Draw indicators
    player.draw_indicator(game_surface)
    for bot in bot_fish_group:
        bot.draw_indicator(game_surface, player.level)
    
    # Blit game surface with shake
    screen.blit(game_surface, shake_offset)
    
    # Draw UI (not affected by shake)
    score_next = player.score_to_next if player.level < MAX_LEVEL else TOTAL_SCORE_TO_WIN
    score_text = score_font.render(f'Score: {player.score} / {score_next}', True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    level_text = level_font.render(f'Level: {player.level}', True, (255, 255, 255))
    screen.blit(level_text, (10, 50))
    
    # Draw player UI
    player.draw_ui(screen)
    
    # Legend
    legend_y = 10
    legend_x = SCREEN_WIDTH - 250
    legend_title = indicator_font.render("Legend:", True, (255, 255, 255))
    screen.blit(legend_title, (legend_x, legend_y))
    legend_y += 35
    
    green_text = indicator_font.render("🟢 = Safe to Eat", True, (0, 255, 0))
    screen.blit(green_text, (legend_x, legend_y))
    legend_y += 30
    
    red_text = indicator_font.render("🔴 = DANGER!", True, (255, 0, 0))
    screen.blit(red_text, (legend_x, legend_y))
    
    # Draw notifications
    for notification in notifications:
        notification.draw(screen)
    
    # Draw tutorial
    if tutorial.active:
        tutorial.draw(screen)
        
    # === FACE CAM OVERLAY (pojok kanan bawah, SELALU tampil) ===
    if 'cam_surface' in locals():
        screen.blit(cam_surface, (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160))

        # Border
        pygame.draw.rect(screen, (255, 215, 0),
            (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160, 260, 150), 3)

    
    # Level up notification
    if player.level > PLAYER_START_LEVEL and not hasattr(player, 'last_notified_level'):
        player.last_notified_level = PLAYER_START_LEVEL
    
    if hasattr(player, 'last_notified_level') and player.level > player.last_notified_level:
        notifications.append(Notification(f"LEVEL {player.level}!", (255, 215, 0), 2000, 'large'))
        create_level_up_particles(player.rect.centerx, player.rect.centery, particle_group)
        player.last_notified_level = player.level

    # Game over screen
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        
        stats_text = notification_font.render(f"Final Score: {player.score}", True, (255, 255, 255))
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(stats_text, stats_rect)
        
        prompt_text = score_font.render("Tekan 'R' untuk Mulai Lagi", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(prompt_text, prompt_rect)

    # Win screen
    if win:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        text = win_font.render("YOU WIN!", True, (255, 215, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        
        stats_text = notification_font.render(f"Final Score: {player.score}", True, (255, 255, 255))
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(stats_text, stats_rect)
        
        prompt_text = score_font.render("Tekan 'R' untuk Main Lagi", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(prompt_text, prompt_rect)
        
        # === FACE CAM OVERLAY (pojok kanan bawah) ===
        screen.blit(cam_surface, (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160))

        # Border biar rapi
        pygame.draw.rect(screen, (255, 215, 0),
            (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160, 260, 150), 3)


    pygame.display.flip()

# Cleanup
save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
cap.release()
cv2.destroyAllWindows()
pygame.quit()