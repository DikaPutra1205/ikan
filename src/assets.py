import pygame
import os
from .config import FISH_ASSET_PATHS, AUDIO_FILES, PLAYER_START_LEVEL

class AssetManager:
    def __init__(self):
        self.fish_images = {}
        self.sounds = {}
        self.fonts = {}

    def load_assets(self):
        self._load_images()
        self._load_sounds()
        self._load_fonts()

    def _load_images(self):
        print("Loading Images...")
        for level, paths in FISH_ASSET_PATHS.items():
            try:
                # Check if files exist first
                if not os.path.exists(paths["closed"]):
                    print(f"Warning: Image not found: {paths['closed']}")
                    # Create placeholder if missing? For now just skip or let pygame error
                
                self.fish_images[level] = {
                    "closed": pygame.image.load(paths["closed"]).convert_alpha(),
                    "open": pygame.image.load(paths["open"]).convert_alpha()
                }
            except Exception as e:
                print(f"Error loading fish image level {level}: {e}")
                # Create dummy surface as fallback
                dummy = pygame.Surface((50, 50))
                dummy.fill((255, 0, 255)) # Magenta for missing texture
                self.fish_images[level] = {"closed": dummy, "open": dummy}

    def _load_sounds(self):
        print("Loading Audio...")
        # Initialize mixer if not already
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        for key, path in AUDIO_FILES.items():
            try:
                if os.path.exists(path):
                    self.sounds[key] = pygame.mixer.Sound(path)
                    print(f"✓ Audio loaded: {key}")
                else:
                    print(f"⚠ Audio file not found: {path}")
                    self.sounds[key] = None
            except Exception as e:
                print(f"⚠ Error loading audio {key}: {e}")
                self.sounds[key] = None

    def _load_fonts(self):
        # Initialize font module
        if not pygame.font.get_init():
            pygame.font.init()
            
        self.fonts['score'] = pygame.font.Font(None, 50)
        self.fonts['level'] = pygame.font.Font(None, 50)
        self.fonts['game_over'] = pygame.font.Font(None, 100)
        self.fonts['win'] = pygame.font.Font(None, 100)
        self.fonts['indicator'] = pygame.font.Font(None, 36)
        self.fonts['indicator_bold'] = pygame.font.Font(None, 42)
        self.fonts['notification'] = pygame.font.Font(None, 60)
        self.fonts['combo'] = pygame.font.Font(None, 70)
        self.fonts['ui'] = pygame.font.Font(None, 32)

    def get_fish_image(self, level, state="closed"):
        if level in self.fish_images:
            return self.fish_images[level].get(state, self.fish_images[level]["closed"])
        return self.fish_images[PLAYER_START_LEVEL]["closed"] # Fallback

    def play_sound(self, key, volume=1.0):
        if key in self.sounds and self.sounds[key] is not None:
            self.sounds[key].set_volume(volume)
            self.sounds[key].play()

    def play_bgm(self, key, volume=0.5, loops=-1):
        if key in self.sounds and self.sounds[key] is not None:
            self.sounds[key].set_volume(volume)
            self.sounds[key].play(loops=loops)

# Singleton instance
assets = AssetManager()
