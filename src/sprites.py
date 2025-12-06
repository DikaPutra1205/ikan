import pygame
import math
import random
from .config import *
from .assets import assets
from .ui import draw_level_indicator, draw_progress_bar


class TrailParticle(pygame.sprite.Sprite):
    def __init__(self, x, y, size, color=(100, 200, 255)):
        super().__init__()
        self.x = x
        self.y = y
        self.size = size
        self.alpha = 150
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*color, self.alpha), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = pygame.time.get_ticks()
        
    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > 300:
            self.kill()
            return
        self.alpha = int(150 * (1 - elapsed / 300))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (100, 200, 255, self.alpha), (self.size//2, self.size//2), self.size//2)

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

class BotFish(pygame.sprite.Sprite):
    def __init__(self, level, behavior='normal'):
        super().__init__()
        self.level = level
        self.behavior = behavior if behavior != 'normal' else random.choice(FISH_BEHAVIORS)
        
        # Get images from AssetManager
        closed_base = assets.get_fish_image(level, "closed")
        open_base = assets.get_fish_image(level, "open")

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
        
        # Behavior variables
        self.zigzag_phase = random.uniform(0, math.pi * 2)
        self.zigzag_amplitude = random.randint(30, 60)
        self.flee_distance = 150
        self.school_target = None
        self.original_y = start_y

    def update(self, player_level, player_rect, frozen=False):
        # Apply freeze effect
        if frozen:
            self.speed = self.base_speed * 0.3
        else:
            self.speed = self.base_speed
        
        # Base movement
        self.rect.x += self.speed * self.direction
        
        # Behavior-specific movement
        if self.behavior == 'zigzag':
            self.zigzag_phase += 0.1
            self.rect.y = self.original_y + math.sin(self.zigzag_phase) * self.zigzag_amplitude
            
        elif self.behavior == 'flee' and self.level < player_level:
            # Flee from player if we're prey
            distance = math.hypot(self.rect.centerx - player_rect.centerx, 
                                 self.rect.centery - player_rect.centery)
            if distance < self.flee_distance:
                # Run away!
                if self.rect.centery < player_rect.centery:
                    self.rect.y -= 3
                else:
                    self.rect.y += 3
                # Speed boost when fleeing
                self.rect.x += self.speed * self.direction * 0.5
                
        elif self.behavior == 'chase' and self.level > player_level and not frozen:
            # Actively chase player if we're predator
            distance = math.hypot(self.rect.centerx - player_rect.centerx, 
                                 self.rect.centery - player_rect.centery)
            if distance < PREDATOR_THREAT_ZONE * 1.5:
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                dist = max(1, math.hypot(dx, dy))
                self.rect.x += (dx / dist) * 2
                self.rect.y += (dy / dist) * 2

        # Original Predator behavior (for normal behavior type)
        elif self.behavior == 'normal':
            if self.level > player_level and not frozen:
                distance = math.hypot(self.rect.centerx - player_rect.centerx, 
                                     self.rect.centery - player_rect.centery)
                if distance < PREDATOR_THREAT_ZONE:
                    if self.rect.centery < player_rect.centery:
                        self.rect.y += 1
                    elif self.rect.centery > player_rect.centery:
                        self.rect.y -= 1
        
        # Keep in bounds (Y axis)
        self.rect.y = max(30, min(SCREEN_HEIGHT - 30, self.rect.y))

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


# Boss Fish Class
class BossFish(pygame.sprite.Sprite):
    def __init__(self, boss_level):
        super().__init__()
        self.level = min(boss_level + 2, MAX_LEVEL)
        self.boss_level = boss_level
        self.health = BOSS_HEALTH.get(boss_level, 5)
        self.max_health = self.health
        
        # Get images
        closed_base = assets.get_fish_image(self.level, "closed")
        open_base = assets.get_fish_image(self.level, "open")
        
        base_scale = FISH_BASE_SIZES[self.level] * BOSS_SIZE_MULTIPLIER
        size = (int(base_scale), int(base_scale))
        
        self.closed_image = pygame.transform.scale(closed_base, size)
        self.open_image = pygame.transform.scale(open_base, size)
        
        # Tint boss red
        self.closed_image.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)
        self.open_image.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)
        
        self.direction = random.choice([-1, 1])
        if self.direction == -1:
            self.closed_image = pygame.transform.flip(self.closed_image, True, False)
            self.open_image = pygame.transform.flip(self.open_image, True, False)
        
        self.image = self.closed_image
        
        start_x = -size[0] if self.direction == 1 else SCREEN_WIDTH + size[0]
        start_y = SCREEN_HEIGHT // 2
        self.rect = self.image.get_rect(center=(start_x, start_y))
        
        self.speed = BOSS_SPEED
        self.phase = 0
        self.attack_pattern = 'chase'
        self.pattern_timer = pygame.time.get_ticks()
        self.invincible = False
        self.invincible_timer = 0
        self.defeated = False
        
    def update(self, player_rect):
        current_time = pygame.time.get_ticks()
        
        # Change attack pattern every 3 seconds
        if current_time - self.pattern_timer > 3000:
            self.attack_pattern = random.choice(['chase', 'sweep', 'charge'])
            self.pattern_timer = current_time
        
        # Update invincibility
        if self.invincible:
            if current_time > self.invincible_timer:
                self.invincible = False
        
        # Movement based on pattern
        if self.attack_pattern == 'chase':
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += (dx / dist) * self.speed * 2
            self.rect.y += (dy / dist) * self.speed * 2
            
        elif self.attack_pattern == 'sweep':
            self.phase += 0.05
            self.rect.y = SCREEN_HEIGHT // 2 + math.sin(self.phase) * 200
            self.rect.x += self.speed * 3 * self.direction
            if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
                self.direction *= -1
                self.flip_images()
                
        elif self.attack_pattern == 'charge':
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            self.rect.x += (dx / dist) * self.speed * 4
            self.rect.y += (dy / dist) * self.speed * 4
        
        # Animation
        self.image = self.open_image if (current_time // 500) % 2 else self.closed_image
        
        # Flash when invincible
        if self.invincible and (current_time // 100) % 2:
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)
    
    def flip_images(self):
        self.closed_image = pygame.transform.flip(self.closed_image, True, False)
        self.open_image = pygame.transform.flip(self.open_image, True, False)
    
    def take_damage(self):
        if self.invincible:
            return False
        self.health -= 1
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks() + 500
        assets.play_sound('boss_hit', 0.8)
        if self.health <= 0:
            self.defeated = True
            assets.play_sound('boss_defeated', 0.9)
        return self.defeated
    
    def draw_health_bar(self, surface):
        bar_width = 200
        bar_height = 20
        x = SCREEN_WIDTH // 2 - bar_width // 2
        y = 20
        
        # Background
        pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_width, bar_height))
        # Health
        health_width = int(bar_width * (self.health / self.max_health))
        pygame.draw.rect(surface, (255, 0, 0), (x, y, health_width, bar_height))
        # Border
        pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_width, bar_height), 2)
        # Text
        boss_text = assets.fonts['indicator_bold'].render(f"BOSS LV.{self.level}", True, (255, 255, 0))
        text_rect = boss_text.get_rect(center=(SCREEN_WIDTH // 2, y + bar_height + 15))
        surface.blit(boss_text, text_rect)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.level = PLAYER_START_LEVEL
        self.score = 0
        self.score_to_next = SCORE_TO_LEVEL_UP[0]
        self.current_size = FISH_BASE_SIZES[self.level]
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
        # Get raw images from AssetManager
        raw_closed = assets.get_fish_image(self.level, "closed")
        raw_open = assets.get_fish_image(self.level, "open")
        
        self.closed_mouth_image = pygame.transform.scale(raw_closed, (size, size))
        self.open_mouth_image = pygame.transform.scale(raw_open, (size, size))
        self.image = self.open_mouth_image if self.is_eating else self.closed_mouth_image
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)

    def update(self, x, y, eating):
        current_time = pygame.time.get_ticks()
        
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
            # We need dt. Let's approximate 30FPS -> 33ms per frame if dt not passed
            # Or simpler: check against end time.
            # Original used self.invincible_timer -= clock.get_time()
            # Let's change logic to use timestamps for robustness
            if not hasattr(self, 'invincible_end_time'):
                self.invincible_end_time = current_time + self.invincible_timer
            
            if current_time > self.invincible_end_time:
                self.invincible = False
                del self.invincible_end_time
        
        # Update power-ups
        expired = []
        for power_type, end_time in self.active_powerups.items():
            if current_time >= end_time:
                expired.append(power_type)
        
        for power_type in expired:
            self.deactivate_powerup(power_type)
        
        # Update ultimate
        if self.ultimate_active:
             if not hasattr(self, 'ultimate_end_time'):
                 self.ultimate_end_time = current_time + self.ultimate_timer
             
             if current_time > self.ultimate_end_time:
                 self.deactivate_ultimate()
        
        # Update combo timer
        if self.combo_count > 0:
            if not hasattr(self, 'combo_end_time'):
                 self.combo_end_time = current_time + self.combo_timer
            
            if current_time > self.combo_end_time:
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
        assets.play_sound('level_up', 0.7)
        
        if self.level < MAX_LEVEL:
            next_level_index = self.level - PLAYER_START_LEVEL
            self.score_to_next = sum(SCORE_TO_LEVEL_UP[:next_level_index + 1])
        else:
            print("KAMU ADALAH PREDATOR PUNCAK!")
    
    def add_combo(self):
        self.combo_count += 1
        self.max_combo = max(self.max_combo, self.combo_count)
        self.combo_timer = COMBO_TIMEOUT
        self.combo_end_time = pygame.time.get_ticks() + COMBO_TIMEOUT
        
        # Play combo sound with increasing pitch feel
        if self.combo_count == 3:
            assets.play_sound('combo_3', 0.6)
        elif self.combo_count == 5:
            assets.play_sound('combo_5', 0.7)
        elif self.combo_count == 10:
            assets.play_sound('combo_10', 0.9)
        elif self.combo_count > 10 and self.combo_count % 5 == 0:
            assets.play_sound('combo_10', 1.0)
    
    def take_damage(self):
        if self.invincible or self.ultimate_active:
            return False
        
        self.health -= 1
        self.invincible = True
        self.invincible_timer = INVINCIBILITY_DURATION
        self.invincible_end_time = pygame.time.get_ticks() + INVINCIBILITY_DURATION
        self.combo_count = 0
        assets.play_sound('hit', 0.8)
        return self.health <= 0
    
    def activate_powerup(self, power_type):
        current_time = pygame.time.get_ticks()
        self.active_powerups[power_type] = current_time + POWER_UP_DURATION[power_type]
        
        if power_type == 'speed':
            self.current_speed = 2.0
        elif power_type == 'shield':
            self.invincible = True
            self.invincible_timer = POWER_UP_DURATION['shield']
            self.invincible_end_time = current_time + self.invincible_timer
        elif power_type == 'magnet':
            self.magnet_radius = 200
        elif power_type == 'double_xp':
            self.double_xp = True
        elif power_type == 'freeze':
            self.frozen_enemies = True
        elif power_type == 'size_boost':
            self.size_multiplier = 1.5
            self.load_and_scale_images()
        
        assets.play_sound('power_up_collect', 0.6)
    
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
                assets.play_sound('ultimate_ready', 0.7)
    
    def activate_ultimate(self):
        if self.ultimate_charge >= ULTIMATE_CHARGE_MAX and not self.ultimate_active:
            self.ultimate_active = True
            self.ultimate_timer = ULTIMATE_DURATION
            self.ultimate_end_time = pygame.time.get_ticks() + ULTIMATE_DURATION
            self.ultimate_charge = 0
            self.invincible = True
            assets.play_sound('ultimate_activate', 0.8)
            return True
        return False
    
    def deactivate_ultimate(self):
        self.ultimate_active = False
        self.invincible = False
        del self.ultimate_end_time
    
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
        
        ult_text = assets.fonts['ui'].render("ULTIMATE", True, (255, 255, 255))
        surface.blit(ult_text, (bar_x, bar_y - 25))
        
        if self.ultimate_active:
            timer_sec = max(0, (self.ultimate_end_time - pygame.time.get_ticks()) / 1000)
            timer_text = assets.fonts['ui'].render(f"{timer_sec:.1f}s", True, (255, 215, 0))
            surface.blit(timer_text, (bar_x + bar_width + 10, bar_y))
        
        # Active power-ups
        powerup_y = 190
        current_time = pygame.time.get_ticks()
        for power_type, end_time in self.active_powerups.items():
            remaining = (end_time - current_time) / 1000
            if remaining > 0:
                text = assets.fonts['ui'].render(f"{power_type.upper()}: {remaining:.1f}s", True, (255, 255, 255))
                surface.blit(text, (10, powerup_y))
                powerup_y += 30
        
        # Combo counter
        if self.combo_count >= 3:
            combo_text = assets.fonts['combo'].render(f"COMBO x{self.combo_count}!", True, (255, 215, 0))
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            # Outline
            for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                outline_text = assets.fonts['combo'].render(f"COMBO x{self.combo_count}!", True, (0, 0, 0))
                surface.blit(outline_text, (combo_rect.x + offset[0], combo_rect.y + offset[1]))
            surface.blit(combo_text, combo_rect)
