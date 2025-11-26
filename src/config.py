import os

# ==================================
# KONFIGURASI DISPLAY & GAMEPLAY
# ==================================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 30

# Player Defaults
PLAYER_START_LEVEL = 2
PLAYER_BASE_SIZE = 60
PLAYER_GROWTH_FACTOR = 1.15
MAX_HEALTH = 3

# Leveling System
SCORE_TO_LEVEL_UP = [
    10, 30, 70, 130, 200, 300, 450, 600, 800, 1000, 1250, 1500, 2000
]
MAX_LEVEL = 15
TOTAL_SCORE_TO_WIN = sum(SCORE_TO_LEVEL_UP)

# Database ukuran ikan (Level: Ukuran)
FISH_BASE_SIZES = {
    1: 30, 2: 60, 3: 50, 4: 55, 5: 80,
    6: 65, 7: 60, 8: 75, 9: 70, 10: 90,
    11: 85, 12: 80, 13: 100, 14: 120, 15: 250
}

# Spawn Config
MAX_TOTAL_BOTS = 15
SPAWN_INTERVAL_GENERAL = 2000  # ms
PREDATOR_THREAT_ZONE = 250

# Computer Vision Config
MOUTH_OPEN_THRESHOLD = 0.03
TRACKING_X_MIN = 0.2
TRACKING_X_MAX = 0.8
TRACKING_Y_MIN = 0.25
TRACKING_Y_MAX = 0.75

# Power-up Config
INVINCIBILITY_DURATION = 2000  # ms
POWER_UP_SPAWN_CHANCE = 0.02   # chance per check
POWER_UP_DURATION = {
    'speed': 5000,
    'shield': 8000,
    'magnet': 10000,
    'double_xp': 10000,
    'freeze': 5000,
    'size_boost': 7000
}

# Ultimate Config
ULTIMATE_CHARGE_MAX = 100
ULTIMATE_DURATION = 5000

# Combo Config
COMBO_TIMEOUT = 3000
COMBO_MULTIPLIERS = {1: 1.0, 3: 1.5, 5: 2.0, 10: 3.0}

# =====================
# ASSET PATHS
# =====================
# Gunakan path absolute atau relative yang aman
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')

FISH_ASSET_PATHS = {
    1:  {"closed": os.path.join(ASSETS_DIR, "Basic Fish 2.png"),      "open": os.path.join(ASSETS_DIR, "Basic Fish 1.png")},
    2:  {"closed": os.path.join(ASSETS_DIR, "Anglar Fish 2.png"),     "open": os.path.join(ASSETS_DIR, "Anglar Fish 1.png")},
    3:  {"closed": os.path.join(ASSETS_DIR, "Clownfish 2.png"),       "open": os.path.join(ASSETS_DIR, "Clownfish 1.png")},
    4:  {"closed": os.path.join(ASSETS_DIR, "White Fish 2.png"),      "open": os.path.join(ASSETS_DIR, "White Fish 1.png")},
    5:  {"closed": os.path.join(ASSETS_DIR, "Jellyfish 2.png"),       "open": os.path.join(ASSETS_DIR, "Jellyfish 1.png")},
    6:  {"closed": os.path.join(ASSETS_DIR, "Surgeon Fish 2.png"),    "open": os.path.join(ASSETS_DIR, "Surgeon Fish 1.png")},
    7:  {"closed": os.path.join(ASSETS_DIR, "Purple Fish 2.png"),     "open": os.path.join(ASSETS_DIR, "Purple Fish 1.png")},
    8:  {"closed": os.path.join(ASSETS_DIR, "Flounder 2.png"),        "open": os.path.join(ASSETS_DIR, "Flounder 1.png")},
    9:  {"closed": os.path.join(ASSETS_DIR, "Pattern Fish 2.png"),    "open": os.path.join(ASSETS_DIR, "Pattern Fish 1.png")},
    10: {"closed": os.path.join(ASSETS_DIR, "Puffer Fish 2.png"),     "open": os.path.join(ASSETS_DIR, "Puffer Fish 1.png")},
    11: {"closed": os.path.join(ASSETS_DIR, "Dapper Fish 2.png"),     "open": os.path.join(ASSETS_DIR, "Dapper Fish 1.png")},
    12: {"closed": os.path.join(ASSETS_DIR, "Ninja Fish 2.png"),      "open": os.path.join(ASSETS_DIR, "Ninja Fish 1.png")},
    13: {"closed": os.path.join(ASSETS_DIR, "Broadhammer Fish 2.png"),"open": os.path.join(ASSETS_DIR, "Broadhammer Fish 1.png")},
    14: {"closed": os.path.join(ASSETS_DIR, "Swordfish 2.png"),       "open": os.path.join(ASSETS_DIR, "Swordfish 1.png")},
    15: {"closed": os.path.join(ASSETS_DIR, "Whale 2.png"),           "open": os.path.join(ASSETS_DIR, "Whale 1.png")}
}

AUDIO_FILES = {
    'eat': os.path.join(SOUNDS_DIR, 'eat.mp3'),
    'level_up': os.path.join(SOUNDS_DIR, 'level-up.mp3'),
    'power_up_collect': os.path.join(SOUNDS_DIR, 'power-up-collect.mp3'),
    'ultimate_ready': os.path.join(SOUNDS_DIR, 'powerup-ready.mp3'),
    'ultimate_activate': os.path.join(SOUNDS_DIR, 'ultimate_activate.mp3'),
    'hit': os.path.join(SOUNDS_DIR, 'hit.mp3'),
    'game_over': os.path.join(SOUNDS_DIR, 'game-over.mp3'),
    'victory': os.path.join(SOUNDS_DIR, 'win.mp3'),
    'bgm_gameplay': os.path.join(SOUNDS_DIR, 'bgm-gameplay.mp3'),
    'bgm_menu': os.path.join(SOUNDS_DIR, 'ibgm-menu.mp3'),
}
