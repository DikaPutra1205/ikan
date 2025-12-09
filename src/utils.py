import json
import os
import random
import math
import pygame
from datetime import datetime
from .config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_LEVEL, ACHIEVEMENTS, DAILY_CHALLENGES

# Score Popup - angka muncul saat makan ikan
class ScorePopup:
    def __init__(self, x, y, score, color=(255, 255, 100)):
        self.x = x
        self.y = y
        self.score = score
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000
        self.font = pygame.font.Font(None, 36)
        
    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.lifetime:
            return False
        self.y -= 1  # Float up
        return True
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        alpha = int(255 * (1 - elapsed / self.lifetime))
        
        # Draw score with outline
        text = self.font.render(f"+{self.score}", True, self.color)
        text.set_alpha(alpha)
        
        # Outline
        outline = self.font.render(f"+{self.score}", True, (0, 0, 0))
        outline.set_alpha(alpha)
        
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surface.blit(outline, (self.x + dx - text.get_width()//2, self.y + dy))
        surface.blit(text, (self.x - text.get_width()//2, self.y))


# Bubble effect - gelembung yang naik
class Bubble:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, SCREEN_HEIGHT)  # Start anywhere first time
        
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = SCREEN_HEIGHT + 20
        self.size = random.randint(3, 12)
        self.speed = random.uniform(0.5, 2.0)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.02, 0.05)
        self.alpha = random.randint(50, 150)
        
    def update(self):
        self.y -= self.speed
        self.wobble_phase += self.wobble_speed
        self.x += math.sin(self.wobble_phase) * 0.5
        
        if self.y < -20:
            self.reset()
            
    def draw(self, surface):
        bubble_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(bubble_surface, (200, 230, 255, self.alpha), 
                          (self.size, self.size), self.size, 1)
        # Highlight
        pygame.draw.circle(bubble_surface, (255, 255, 255, self.alpha // 2),
                          (self.size - self.size//3, self.size - self.size//3), self.size // 3)
        surface.blit(bubble_surface, (int(self.x - self.size), int(self.y - self.size)))


# Water current effect
class WaterCurrent:
    def __init__(self):
        self.active = False
        self.direction = 1  # 1 = right, -1 = left
        self.strength = 0
        self.target_strength = 0
        self.change_timer = 0
        self.particles = []
        
    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Randomly change current every 10-20 seconds
        if current_time - self.change_timer > random.randint(10000, 20000):
            self.change_timer = current_time
            if random.random() < 0.3:  # 30% chance to activate/change
                self.active = True
                self.direction = random.choice([-1, 1])
                self.target_strength = random.uniform(1.0, 2.5)
            else:
                self.active = False
                self.target_strength = 0
        
        # Smooth transition
        if self.strength < self.target_strength:
            self.strength = min(self.target_strength, self.strength + 0.05)
        elif self.strength > self.target_strength:
            self.strength = max(self.target_strength, self.strength - 0.05)
    
    def apply_to_rect(self, rect):
        if self.active and self.strength > 0:
            rect.x += self.direction * self.strength
            return True
        return False
    
    def draw(self, surface):
        if self.active and self.strength > 0.5:
            # Draw current lines
            alpha = int(min(100, self.strength * 40))
            for i in range(5):
                y = (pygame.time.get_ticks() // 20 + i * 150) % SCREEN_HEIGHT
                start_x = 0 if self.direction == 1 else SCREEN_WIDTH
                end_x = SCREEN_WIDTH if self.direction == 1 else 0
                
                line_surface = pygame.Surface((SCREEN_WIDTH, 3), pygame.SRCALPHA)
                pygame.draw.line(line_surface, (150, 200, 255, alpha), (0, 1), (SCREEN_WIDTH, 1), 2)
                surface.blit(line_surface, (0, y))


# Vignette effect untuk atmosfer
class VignetteEffect:
    def __init__(self):
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._create_vignette()
        
    def _create_vignette(self):
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_dist = math.hypot(center_x, center_y)
        
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                dist = math.hypot(x - center_x, y - center_y)
                # Only darken edges
                if dist > max_dist * 0.6:
                    alpha = int(min(80, (dist - max_dist * 0.6) / (max_dist * 0.4) * 80))
                    self.surface.set_at((x, y), (0, 20, 40, alpha))
    
    def draw(self, surface):
        surface.blit(self.surface, (0, 0))


# Daily Challenge System
class DailyChallengeManager:
    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.current_challenge = None
        self.progress = 0
        self.completed = False
        self.load()
        
    def load(self):
        try:
            if os.path.exists('daily_challenge.json'):
                with open('daily_challenge.json', 'r') as f:
                    data = json.load(f)
                    if data.get('date') == self.today:
                        self.current_challenge = data.get('challenge')
                        self.progress = data.get('progress', 0)
                        self.completed = data.get('completed', False)
                    else:
                        self._generate_new_challenge()
            else:
                self._generate_new_challenge()
        except:
            self._generate_new_challenge()
    
    def _generate_new_challenge(self):
        challenge_id = random.choice(list(DAILY_CHALLENGES.keys()))
        self.current_challenge = challenge_id
        self.progress = 0
        self.completed = False
        self.save()
    
    def save(self):
        try:
            with open('daily_challenge.json', 'w') as f:
                json.dump({
                    'date': self.today,
                    'challenge': self.current_challenge,
                    'progress': self.progress,
                    'completed': self.completed
                }, f)
        except:
            pass
    
    def update_progress(self, challenge_type, value):
        if self.completed or not self.current_challenge:
            return 0
        
        challenge = DAILY_CHALLENGES.get(self.current_challenge)
        if not challenge:
            return 0
        
        # Map challenge types to progress
        if self.current_challenge == 'speed_eater' and challenge_type == 'fish_eaten':
            self.progress = value
        elif self.current_challenge == 'combo_king' and challenge_type == 'combo':
            self.progress = max(self.progress, value)
        elif self.current_challenge == 'survivor_pro' and challenge_type == 'survival_time':
            self.progress = value
        elif self.current_challenge == 'boss_rush' and challenge_type == 'boss_defeated':
            self.progress = value
        elif self.current_challenge == 'powerup_master' and challenge_type == 'powerups':
            self.progress = value
        
        # Check completion
        if self.progress >= challenge['target'] and not self.completed:
            self.completed = True
            self.save()
            return challenge['reward']
        
        self.save()
        return 0
    
    def draw(self, surface, y_offset=10):
        if not self.current_challenge:
            return
        
        challenge = DAILY_CHALLENGES.get(self.current_challenge)
        if not challenge:
            return
        
        # Draw challenge box
        box_width = 300
        box_height = 60
        box_x = SCREEN_WIDTH - box_width - 10
        box_y = y_offset
        
        # Background
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        color = (0, 100, 0, 180) if self.completed else (0, 0, 0, 150)
        pygame.draw.rect(box_surface, color, (0, 0, box_width, box_height), border_radius=8)
        border_color = (0, 255, 0) if self.completed else (255, 215, 0)
        pygame.draw.rect(box_surface, border_color, (0, 0, box_width, box_height), 2, border_radius=8)
        surface.blit(box_surface, (box_x, box_y))
        
        # Title
        font_title = pygame.font.Font(None, 22)
        title_text = font_title.render(f"Daily: {challenge['name']}", True, (255, 215, 0))
        surface.blit(title_text, (box_x + 10, box_y + 8))
        
        # Progress bar
        bar_width = box_width - 20
        bar_height = 12
        bar_x = box_x + 10
        bar_y = box_y + 32
        
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        progress_pct = min(1.0, self.progress / challenge['target'])
        if progress_pct > 0:
            pygame.draw.rect(surface, (0, 255, 100), (bar_x, bar_y, int(bar_width * progress_pct), bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Progress text
        font_prog = pygame.font.Font(None, 18)
        status = "Complete!" if self.completed else f"{self.progress}/{challenge['target']}"
        prog_text = font_prog.render(status, True, (255, 255, 255))
        surface.blit(prog_text, (bar_x + bar_width // 2 - prog_text.get_width() // 2, bar_y + 16))


# Light ray effect (biar ada ambiencenya coy)
class LightRay:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.width = random.randint(20, 80)
        self.alpha = random.randint(10, 30)
        self.speed = random.uniform(0.1, 0.3)
        self.angle = random.uniform(-0.2, 0.2)
        
    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 100:
            self.x = -100
            self.width = random.randint(20, 80)
            
    def draw(self, surface):
        # Create gradient light ray
        ray_surface = pygame.Surface((self.width, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(SCREEN_HEIGHT):
            alpha = int(self.alpha * (1 - i / SCREEN_HEIGHT) * 0.7)
            width_at_y = int(self.width * (0.3 + 0.7 * i / SCREEN_HEIGHT))
            pygame.draw.line(ray_surface, (255, 255, 200, alpha), 
                           (self.width//2 - width_at_y//2, i),
                           (self.width//2 + width_at_y//2, i))
        surface.blit(ray_surface, (int(self.x), 0))


# Achievement System
class AchievementManager:
    def __init__(self):
        self.unlocked = set()
        self.pending_notifications = []
        self.load()
        
    def load(self):
        try:
            if os.path.exists('achievements.json'):
                with open('achievements.json', 'r') as f:
                    data = json.load(f)
                    self.unlocked = set(data.get('unlocked', []))
        except:
            self.unlocked = set()
    
    def save(self):
        try:
            with open('achievements.json', 'w') as f:
                json.dump({'unlocked': list(self.unlocked)}, f)
        except Exception as e:
            print(f"Error saving achievements: {e}")
    
    def unlock(self, achievement_id):
        if achievement_id not in self.unlocked and achievement_id in ACHIEVEMENTS:
            self.unlocked.add(achievement_id)
            achievement = ACHIEVEMENTS[achievement_id]
            self.pending_notifications.append({
                'name': achievement['name'],
                'desc': achievement['desc'],
                'icon': achievement['icon'],
                'time': pygame.time.get_ticks()
            })
            self.save()
            return True
        return False
    
    def check_achievements(self, player, stats):
        # First Blood
        if player.fish_eaten >= 1:
            self.unlock('first_blood')
        
        # Combo Master
        if player.max_combo >= 10:
            self.unlock('combo_master')
        
        # Survivor
        if stats.get('damage_taken', 0) >= 5 and player.health > 0:
            self.unlock('survivor')
        
        # Speed Demon
        if stats.get('fish_in_10s', 0) >= 10:
            self.unlock('speed_demon')
        
        # Ultimate User
        if stats.get('ultimates_used', 0) >= 3:
            self.unlock('ultimate_user')
        
        # Collector
        if len(stats.get('powerups_collected', set())) >= 6:
            self.unlock('collector')
        
        # Apex Predator
        if player.level >= MAX_LEVEL:
            self.unlock('apex_predator')
    
    def draw_notifications(self, surface):
        current_time = pygame.time.get_ticks()
        y_offset = 150
        
        for notif in self.pending_notifications[:]:
            elapsed = current_time - notif['time']
            if elapsed > 4000:
                self.pending_notifications.remove(notif)
                continue
            
            # Slide in/out animation
            if elapsed < 500:
                x_offset = int(-300 + (300 * elapsed / 500))
            elif elapsed > 3500:
                x_offset = int(-300 * (elapsed - 3500) / 500)
            else:
                x_offset = 0
            
            # Draw achievement box
            box_width = 280
            box_height = 70
            box_x = SCREEN_WIDTH - box_width - 20 + x_offset
            box_y = y_offset
            
            # Background
            box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(box_surface, (0, 0, 0, 200), (0, 0, box_width, box_height), border_radius=10)
            pygame.draw.rect(box_surface, (255, 215, 0), (0, 0, box_width, box_height), 3, border_radius=10)
            surface.blit(box_surface, (box_x, box_y))
            
            # Icon
            font_icon = pygame.font.Font(None, 40)
            icon_text = font_icon.render(notif['icon'], True, (255, 255, 255))
            surface.blit(icon_text, (box_x + 15, box_y + 15))
            
            # Title
            font_title = pygame.font.Font(None, 28)
            title_text = font_title.render("Achievement Unlocked!", True, (255, 215, 0))
            surface.blit(title_text, (box_x + 55, box_y + 10))
            
            # Name
            font_name = pygame.font.Font(None, 24)
            name_text = font_name.render(notif['name'], True, (255, 255, 255))
            surface.blit(name_text, (box_x + 55, box_y + 35))
            
            y_offset += 80


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

    # Ensure the weight for player's exact level is 0 (avoid spawning same size if desired, or keep it low)
    # if player_level <= MAX_LEVEL:
    #     weights[player_level - 1] = 0.0

    if sum(weights) == 0:
        return 1

    chosen_level = random.choices(possible_levels, weights=weights, k=1)[0]
    return chosen_level

def apply_screen_shake(intensity=10):
    """Return random offset untuk screen shake"""
    return (random.randint(-intensity, intensity), random.randint(-intensity, intensity))
