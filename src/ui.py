import pygame
from .config import SCREEN_WIDTH, SCREEN_HEIGHT
from .assets import assets

def draw_progress_bar(surface, x, y, width, height, progress, bg_color=(50, 50, 50), fill_color=(0, 255, 0)):
    """Draw progress bar"""
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    fill_width = int(width * progress)
    if fill_width > 0:
        pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)

def draw_level_indicator(surface, level, x, y, is_player=False, player_level=None):
    if is_player:
        color = (0, 255, 255)
        text = assets.fonts['indicator_bold'].render(f"LV.{level}", True, (0, 0, 0))
        bg_text = assets.fonts['indicator_bold'].render(f"LV.{level}", True, color)
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
        
        text = assets.fonts['indicator'].render(f"{level}", True, (0, 0, 0))
        bg_text = assets.fonts['indicator'].render(f"{level}", True, color)
    
    text_rect = text.get_rect(center=(x, y - 35))
    
    for offset_x in [-2, 0, 2]:
        for offset_y in [-2, 0, 2]:
            if offset_x != 0 or offset_y != 0:
                shadow_rect = text_rect.copy()
                shadow_rect.x += offset_x
                shadow_rect.y += offset_y
                surface.blit(text, shadow_rect)
    
    surface.blit(bg_text, text_rect)

class Notification:
    def __init__(self, text, color=(255, 255, 255), duration=2000, size='normal'):
        self.text = text
        self.color = color
        self.duration = duration
        self.spawn_time = pygame.time.get_ticks()
        self.font = assets.fonts['combo'] if size == 'large' else assets.fonts['notification']
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
        title = assets.fonts['game_over'].render("PAUSED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        surface.blit(title, title_rect)
        
        # Options
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (255, 255, 255)
            text = assets.fonts['notification'].render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60))
            surface.blit(text, text_rect)

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
        title = assets.fonts['game_over'].render("FEEDING FRENZY", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        surface.blit(title, title_rect)
        
        subtitle = assets.fonts['notification'].render("Evolution", True, (255, 255, 255))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 80))
        surface.blit(subtitle, subtitle_rect)
        
        # Controls section
        y_offset += 160
        controls_title = assets.fonts['level'].render("=== KONTROL ===", True, (255, 215, 0))
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
            control_text = assets.fonts['ui'].render(control, True, (255, 255, 0))
            control_rect = control_text.get_rect(midright=(SCREEN_WIDTH // 2 - 20, y_offset))
            surface.blit(control_text, control_rect)
            
            # Description
            desc_text = assets.fonts['ui'].render(f"→ {description}", True, (200, 200, 200))
            desc_rect = desc_text.get_rect(midleft=(SCREEN_WIDTH // 2 + 20, y_offset))
            surface.blit(desc_text, desc_rect)
            
            y_offset += 40
        
        # Game tips
        y_offset += 30
        tips_title = assets.fonts['level'].render("=== TIPS ===", True, (255, 215, 0))
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
            tip_text = assets.fonts['ui'].render(tip, True, (200, 255, 200))
            tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            surface.blit(tip_text, tip_rect)
            y_offset += 35
        
        # Start prompt (blinking)
        blink = (pygame.time.get_ticks() // 500) % 2
        if blink:
            start_text = assets.fonts['notification'].render("Tekan SEMBARANG TOMBOL untuk Mulai", True, (255, 255, 0))
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            surface.blit(start_text, start_rect)
        
        # Additional info
        info_text = assets.fonts['ui'].render("(Pastikan wajah kamu terlihat di webcam)", True, (150, 150, 150))
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
            text = assets.fonts['ui'].render(tip_text, True, (255, 255, 255))
            
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
