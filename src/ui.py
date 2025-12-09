import pygame
import math
import random
from .config import SCREEN_WIDTH, SCREEN_HEIGHT
from .assets import assets

# Colors
C_DARK_BG = (10, 25, 47)
C_PANEL_BG = (20, 40, 70)
C_ACCENT = (64, 224, 208)
C_HIGHLIGHT = (255, 215, 0)
C_TEXT_MAIN = (240, 248, 255)
C_TEXT_SUB = (135, 206, 235)
C_DANGER = (220, 20, 60)
C_SUCCESS = (0, 255, 127)
PAD = 20

# --- OCEAN BACKGROUND ---
def draw_ocean_background(surface, time_offset=0):
    """Smooth ocean gradient tanpa garis-garis + subtle animation"""
    gradient = pygame.Surface((1, SCREEN_HEIGHT))
    
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(10 + 25 * ratio)
        g = int(25 + 60 * ratio)
        b = int(47 + 90 * ratio)
        gradient.set_at((0, y), (r, g, b))
    
    # Scale 1px gradient menjadi full screen
    smooth_bg = pygame.transform.smoothscale(gradient, (SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.blit(smooth_bg, (0, 0))

    # Light rays (dipertahankan tapi lebih halus)
    for i in range(5):
        x = (SCREEN_WIDTH // 5) * i + int(20 * math.sin(time_offset * 0.2 + i))
        ray_surf = pygame.Surface((3, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(10 * (1 - y / SCREEN_HEIGHT))
            ray_surf.set_at((1, y), (100, 200, 255, alpha))
        surface.blit(ray_surf, (x, 0))

    # Floating particles tetap
    for i in range(15):
        t = time_offset + i * 0.5
        x = int((SCREEN_WIDTH / 15) * i + 30 * math.sin(t * 0.3))
        y = int((t * 15) % SCREEN_HEIGHT)
        alpha = int(60 + 40 * math.sin(t * 0.2))
        pygame.draw.circle(surface, (*C_ACCENT, alpha), (x, y), 2)


def draw_swimming_fish(surface, x, y, size, direction, color, t):
    """Smooth swimming fish decoration"""
    # Body
    body = pygame.Rect(x - size, y - size//2, size*2, size)
    pygame.draw.ellipse(surface, color, body)
    
    # Tail
    tail_x = x - size if direction > 0 else x + size
    tail_pts = [(tail_x, y), (tail_x - 12*direction, y - 6), (tail_x - 12*direction, y + 6)]
    pygame.draw.polygon(surface, color, tail_pts)
    
    # Eye
    eye_x = x + size//2 if direction > 0 else x - size//2
    pygame.draw.circle(surface, C_DARK_BG, (eye_x, y - 2), 3)

def draw_glass_panel(surface, rect, color=C_PANEL_BG, alpha=200, border_color=None, glow=False, radius=12):
    """Modern glass panel without heavy borders"""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    
    # Subtle top gradient
    for i in range(rect.height//4):
        a = int(20 * (1 - i/(rect.height//4)))
        pygame.draw.line(s, (255,255,255,a), (radius, i), (rect.width-radius, i))
    
    # Subtle border (no thick borders)
    if border_color:
        pygame.draw.rect(s, (*border_color, 100), s.get_rect(), 1, border_radius=radius)
    
    # Subtle glow
    if glow:
        glow_surf = pygame.Surface((rect.width+10, rect.height+10), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*C_ACCENT, 20), glow_surf.get_rect(), border_radius=radius+2)
        surface.blit(glow_surf, (rect.x-5, rect.y-5))
    
    surface.blit(s, rect)

def draw_wave_bar(surface, x, y, w, h, progress, color=C_SUCCESS):
    """Smooth progress bar"""
    pygame.draw.rect(surface, (30, 50, 70), (x, y, w, h), border_radius=h//2)
    if progress > 0:
        fill_w = int(w * min(1, progress))
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=h//2)
        
        # Subtle shine
        shine_surf = pygame.Surface((fill_w, h//2), pygame.SRCALPHA)
        pygame.draw.rect(shine_surf, (255, 255, 255, 30), shine_surf.get_rect(), border_radius=h//2)
        surface.blit(shine_surf, (x, y))

# --- HUD ---
def draw_hud(surface, player):
    """Clean modern HUD"""
    
    # Score Card
    score_font = pygame.font.Font(None, 56)
    score_s = score_font.render(f"{player.score}", True, C_HIGHLIGHT)
    card_w = max(score_s.get_width() + 70, 150)
    card_rect = pygame.Rect(PAD, PAD, card_w, 70)
    draw_glass_panel(surface, card_rect, glow=(player.combo_count >= 5))
    
    # Score with shadow
    surface.blit(score_font.render(f"{player.score}", True, (0,0,0,80)), (card_rect.x + 17, card_rect.y + 10))
    surface.blit(score_s, (card_rect.x + 15, card_rect.y + 8))
    
    # Level badge
    lvl_s = pygame.font.Font(None, 30).render(f"{player.level}", True, C_ACCENT)
    bubble_x, bubble_y = card_rect.right - 35, card_rect.centery
    pygame.draw.circle(surface, (*C_ACCENT, 30), (bubble_x, bubble_y), 20)
    pygame.draw.circle(surface, C_PANEL_BG, (bubble_x, bubble_y), 18)
    pygame.draw.circle(surface, C_ACCENT, (bubble_x, bubble_y), 18, 1)
    surface.blit(lvl_s, lvl_s.get_rect(center=(bubble_x, bubble_y)))
    
    # Label
    surface.blit(pygame.font.Font(None, 18).render("SCORE", True, C_TEXT_SUB), (card_rect.x + 15, card_rect.bottom - 20))

    # Health Bubbles
    health_w = player.health * 30 + 40
    health_rect = pygame.Rect(SCREEN_WIDTH - health_w - PAD, PAD, health_w, 55)
    draw_glass_panel(surface, health_rect)
    
    for i in range(player.health):
        bx, by = health_rect.left + 25 + i * 30, health_rect.centery
        pygame.draw.circle(surface, (*C_DANGER, 60), (bx, by), 15)
        pygame.draw.circle(surface, C_DANGER, (bx, by), 11)
        pygame.draw.circle(surface, (255, 150, 150, 80), (bx-3, by-3), 4)

    # Ultimate Bar
    bar_w, bar_h, bar_x, bar_y = 300, 12, (SCREEN_WIDTH - 300) // 2, SCREEN_HEIGHT - 85
    prog = 0.0
    bar_color, status_txt = C_ACCENT, "BUILDING POWER..."
    
    if hasattr(player, 'combo_active') and player.combo_active:
        prog = (player.combo_timer - pygame.time.get_ticks()) / player.combo_duration
        bar_color, status_txt = C_HIGHLIGHT, "★ FEEDING FRENZY ★"
    elif hasattr(player, 'combo_count'):
        prog = min(player.combo_count / 10, 1.0)
        bar_color = C_HIGHLIGHT if prog >= 1.0 else C_ACCENT
        status_txt = "⚡ ULTIMATE READY ⚡" if prog >= 1.0 else f"COMBO: {player.combo_count}/10"
    
    container = pygame.Rect(bar_x - 15, bar_y - 22, bar_w + 30, 52)
    draw_glass_panel(surface, container, alpha=190, glow=(prog >= 1.0))
    draw_wave_bar(surface, bar_x, bar_y, bar_w, bar_h, prog, bar_color)
    
    # Status text
    status_font = pygame.font.Font(None, 20)
    txt_center = (bar_x + bar_w//2, bar_y + 24)
    surface.blit(status_font.render(status_txt, True, (0,0,0,100)), status_font.render(status_txt, True, bar_color).get_rect(center=(txt_center[0]+1, txt_center[1]+1)))
    surface.blit(status_font.render(status_txt, True, bar_color), status_font.render(status_txt, True, bar_color).get_rect(center=txt_center))

# --- LOADING SCREEN ---
class LoadingScreen:
    def __init__(self):
        self.active, self.progress, self.ripples = True, 0.0, []
        
    def update(self):
        self.progress += 1.2
        if random.random() < 0.1:
            self.ripples.append({'x': SCREEN_WIDTH//2 + random.randint(-150, 150), 'y': SCREEN_HEIGHT//2 + random.randint(-100, 100), 'r': 0, 'alpha': 120})
        for ripple in self.ripples[:]:
            ripple['r'] += 2
            ripple['alpha'] -= 3
            if ripple['alpha'] <= 0: self.ripples.remove(ripple)
        if self.progress >= 100: self.active = False
        return self.active
    
    def draw(self, surface):
        t = pygame.time.get_ticks() * 0.003
        draw_ocean_background(surface, t)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # Subtle ripples
        for ripple in self.ripples:
            pygame.draw.circle(surface, (*C_ACCENT, ripple['alpha']), (int(ripple['x']), int(ripple['y'])), int(ripple['r']), 1)
        
        # Fish icon
        fish_y = cy
        pygame.draw.ellipse(surface, C_ACCENT, pygame.Rect(cx - 40, fish_y - 20, 80, 40))
        pygame.draw.polygon(surface, C_ACCENT, [(cx - 40, fish_y), (cx - 55, fish_y - 10), (cx - 55, fish_y + 10)])
        pygame.draw.circle(surface, C_DARK_BG, (cx + 20, fish_y), 5)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 22, fish_y - 2), 2)
        
        # Bubbles
        for i in range(3):
            bx, by = cx + 20 + i * 15, fish_y - 30 - i * 10
            pygame.draw.circle(surface, (*C_ACCENT, 80), (bx, by), 6)
            pygame.draw.circle(surface, C_ACCENT, (bx, by), 6, 1)
        
        # Progress bar
        bar_x, bar_y = cx - 160, cy + 100
        pygame.draw.rect(surface, (20, 40, 60), (bar_x, bar_y, 320, 12), border_radius=6)
        fill_w = int(320 * (self.progress / 100))
        if fill_w > 0:
            pygame.draw.rect(surface, C_ACCENT, (bar_x, bar_y, fill_w, 12), border_radius=6)
            shine = pygame.Surface((fill_w, 6), pygame.SRCALPHA)
            pygame.draw.rect(shine, (255, 255, 255, 40), shine.get_rect(), border_radius=6)
            surface.blit(shine, (bar_x, bar_y))
        
        # Percentage
        pct_s = pygame.font.Font(None, 40).render(f"{int(self.progress)}%", True, C_TEXT_MAIN)
        surface.blit(pct_s, pct_s.get_rect(center=(cx, bar_y + 40)))
        
        # Title - clean no wave
        title_s = pygame.font.Font(None, 72).render("FEEDING FRENZY", True, C_ACCENT)
        surface.blit(title_s, title_s.get_rect(center=(cx, cy - 120)))

# --- WELCOME SCREEN ---
class WelcomeScreen:
    def __init__(self):
        self.active, self.alpha, self.fish_positions = True, 0, []
        for i in range(10):
            self.fish_positions.append({
                'x': random.randint(50, SCREEN_WIDTH - 50), 
                'y': random.randint(100, SCREEN_HEIGHT - 100), 
                'size': random.randint(15, 25), 
                'speed': random.uniform(0.5, 1.0), 
                'direction': random.choice([-1, 1]),
                'color': random.choice([(100, 180, 200, 40), (80, 160, 220, 40), (120, 200, 180, 40)])
            })
        
    def update(self):
        self.alpha = min(255, self.alpha + 5)
        for fish in self.fish_positions:
            fish['x'] += fish['direction'] * fish['speed']
            if fish['direction'] > 0 and fish['x'] > SCREEN_WIDTH + 50: fish['x'] = -50
            elif fish['direction'] < 0 and fish['x'] < -50: fish['x'] = SCREEN_WIDTH + 50
        return self.active
    
    def skip(self):
        self.active = False
    
    def draw(self, surface):
        t = pygame.time.get_ticks() * 0.003
        draw_ocean_background(surface, t)
        
        # Background fish (subtle)
        for fish in self.fish_positions:
            body = pygame.Rect(int(fish['x']) - fish['size'], int(fish['y']) - fish['size']//2, fish['size']*2, fish['size'])
            pygame.draw.ellipse(surface, fish['color'], body)
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        card_rect = pygame.Rect((SCREEN_WIDTH - 480)//2, (SCREEN_HEIGHT - 380)//2, 480, 380)
        draw_glass_panel(surface, card_rect, alpha=230, glow=True)
        
        # Title - clean
        title_s = pygame.font.Font(None, 64).render("FEEDING FRENZY", True, C_ACCENT)
        surface.blit(title_s, title_s.get_rect(center=(cx, card_rect.top + 60)))
        
        # Subtitle
        sub_s = pygame.font.Font(None, 26).render("Ocean Evolution", True, C_TEXT_SUB)
        surface.blit(sub_s, sub_s.get_rect(center=(cx, card_rect.top + 105)))
        
        # Divider
        pygame.draw.line(surface, (*C_ACCENT, 80), (cx - 150, card_rect.top + 130), (cx + 150, card_rect.top + 130), 1)
        
        # Instructions
        instructions = [
            ("🎮", "Use your FACE to move"),
            ("🐟", "OPEN MOUTH to eat fish"),
            ("⚡", "Press SPACE for ultimate"),
        ]
        
        for i, (icon, txt) in enumerate(instructions):
            y_pos = card_rect.top + 160 + i * 50
            inst_rect = pygame.Rect(cx - 180, y_pos, 360, 40)
            draw_glass_panel(surface, inst_rect, alpha=120)
            surface.blit(pygame.font.Font(None, 28).render(icon, True, C_ACCENT), (inst_rect.left + 20, y_pos + 8))
            surface.blit(pygame.font.Font(None, 24).render(txt, True, C_TEXT_MAIN), (inst_rect.left + 60, y_pos + 10))
        
        # Prompt
        if (pygame.time.get_ticks() // 500) % 2:
            prompt_s = pygame.font.Font(None, 28).render("PRESS ANY KEY TO START", True, C_HIGHLIGHT)
            surface.blit(prompt_s, prompt_s.get_rect(center=(cx, card_rect.bottom - 50)))

# --- OTHER UI ---
class Notification:
    def __init__(self, text, color=C_TEXT_MAIN, duration=2000, size='normal'):
        self.text, self.color, self.duration, self.spawn_time, self.y_offset = text, color, duration, pygame.time.get_ticks(), 0
        
    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.duration: return False
        self.y_offset = min(20, elapsed * 0.1)
        return True
    
    def draw(self, surface):
        txt_s = pygame.font.Font(None, 32).render(self.text, True, self.color)
        rect = pygame.Rect(0, 0, txt_s.get_width() + 40, txt_s.get_height() + 20)
        rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 - self.y_offset)
        draw_glass_panel(surface, rect, alpha=220)
        surface.blit(txt_s, txt_s.get_rect(center=rect.center))

class PauseMenu:
    def __init__(self):
        self.active, self.selected, self.options = False, 0, ['Resume', 'Restart', 'Quit']
    def toggle(self): self.active = not self.active
    def set_stats(self, player, game_stats, save_data): pass
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN: self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN: return self.options[self.selected]
        return None
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(C_DARK_BG)
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        rect = pygame.Rect((SCREEN_WIDTH - 280)//2, (SCREEN_HEIGHT - 300)//2, 280, 300)
        draw_glass_panel(surface, rect, glow=True)
        surface.blit(pygame.font.Font(None, 48).render("PAUSED", True, C_ACCENT), pygame.font.Font(None, 48).render("PAUSED", True, C_ACCENT).get_rect(center=(rect.centerx, rect.top + 50)))
        for i, opt in enumerate(self.options):
            y = rect.top + 120 + i * 60
            if i == self.selected:
                pygame.draw.circle(surface, C_HIGHLIGHT, (rect.centerx - 90, y + 8), 4)
            surface.blit(pygame.font.Font(None, 32).render(opt, True, C_HIGHLIGHT if i == self.selected else C_TEXT_SUB), pygame.font.Font(None, 32).render(opt, True, C_HIGHLIGHT if i == self.selected else C_TEXT_SUB).get_rect(center=(rect.centerx, y + 8)))

class Tutorial:
    def __init__(self):
        self.tips, self.current_tip, self.shown_tips, self.start_time, self.display_time, self.active = ["Stay away from RED fish!", "Eat smaller fish to grow", "Build COMBO for ultimate", "Press SPACE when bar is full"], 0, set(), 0, 3500, True
    def show_next_tip(self):
        if self.current_tip < len(self.tips):
            self.shown_tips.add(self.current_tip)
            self.start_time = pygame.time.get_ticks()
            self.current_tip += 1
            return True
        return False
    def update(self):
        return not (self.current_tip > 0 and self.current_tip <= len(self.tips) and pygame.time.get_ticks() - self.start_time > self.display_time)
    def draw(self, surface):
        if 0 < self.current_tip <= len(self.tips):
            txt_s = pygame.font.Font(None, 26).render(self.tips[self.current_tip - 1], True, C_TEXT_MAIN)
            rect = pygame.Rect(0, 0, txt_s.get_width() + 60, txt_s.get_height() + 20)
            rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
            draw_glass_panel(surface, rect, alpha=200)
            surface.blit(txt_s, txt_s.get_rect(center=rect.center))

def draw_end_game_screen(surface, title, title_color, player, is_win=False):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill(C_DARK_BG)
    overlay.set_alpha(220)
    surface.blit(overlay, (0, 0))
    card_rect = pygame.Rect((SCREEN_WIDTH - 420)//2, (SCREEN_HEIGHT - 360)//2, 420, 360)
    draw_glass_panel(surface, card_rect, glow=True)
    surface.blit(pygame.font.Font(None, 56).render(title, True, title_color), pygame.font.Font(None, 56).render(title, True, title_color).get_rect(center=(card_rect.centerx, card_rect.top + 60)))
    stats = [("Final Score", player.score, C_HIGHLIGHT), ("Fish Eaten", player.fish_eaten, C_ACCENT), ("Max Combo", f"{player.max_combo}x", C_TEXT_MAIN)]
    for i, (label, value, col) in enumerate(stats):
        y = card_rect.top + 140 + i * 45
        surface.blit(pygame.font.Font(None, 30).render(label, True, C_TEXT_SUB), (card_rect.left + 60, y))
        surface.blit(pygame.font.Font(None, 30).render(str(value), True, col), pygame.font.Font(None, 30).render(str(value), True, col).get_rect(midright=(card_rect.right - 60, y + 5)))
    if (pygame.time.get_ticks() // 700) % 2:
        surface.blit(pygame.font.Font(None, 30).render("PRESS 'R' TO RESTART", True, C_ACCENT), pygame.font.Font(None, 30).render("PRESS 'R' TO RESTART", True, C_ACCENT).get_rect(center=(card_rect.centerx, card_rect.bottom - 50)))

def draw_level_indicator(surface, level, x, y, is_player=False, player_level=None):
    radius, offset, font_size = (22, 45, 24) if is_player else (16, 35, 20)
    color = C_ACCENT if is_player else (C_SUCCESS if level < player_level else C_HIGHLIGHT if level == player_level else C_DANGER) if player_level else C_TEXT_MAIN
    cx, cy = int(x), int(y - offset)
    pygame.draw.circle(surface, (*color, 40), (cx, cy), radius + 2)
    pygame.draw.circle(surface, C_DARK_BG, (cx, cy), radius)
    pygame.draw.circle(surface, color, (cx, cy), radius, 1)
    surface.blit(pygame.font.Font(None, font_size).render(str(level), True, color), pygame.font.Font(None, font_size).render(str(level), True, color).get_rect(center=(cx, cy)))

def draw_progress_bar(surface, x, y, width, height, progress, bg_color=(40, 50, 60), fill_color=C_SUCCESS):
    x, y, width, height, progress = int(x), int(y), int(width), int(height), max(0.0, min(1.0, float(progress)))
    pygame.draw.rect(surface, bg_color, pygame.Rect(x, y, width, height), border_radius=height//2)
    fill_width = int(width * progress)
    if fill_width > 0:
        pygame.draw.rect(surface, fill_color, pygame.Rect(x, y, fill_width, height), border_radius=height//2)
        shine = pygame.Surface((fill_width, height//2), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 30), shine.get_rect(), border_radius=height//2)
        surface.blit(shine, (x, y))

draw_modern_card = draw_glass_panel

__all__ = ['draw_hud', 'draw_level_indicator', 'draw_progress_bar', 'draw_glass_panel', 'draw_modern_card', 'draw_end_game_screen', 
           'LoadingScreen', 'Notification', 'PauseMenu', 'WelcomeScreen', 'Tutorial', 
           'C_ACCENT', 'C_HIGHLIGHT', 'C_DARK_BG', 'C_TEXT_MAIN', 'C_DANGER', 'C_SUCCESS', 'C_PANEL_BG', 'C_TEXT_SUB']