import sys
import os

# ==============================================================================
# ### --- BAGIAN PATCH (JANGAN DIHAPUS) --- ###
# Bagian ini memperbaiki library Google Protobuf & MediaPipe secara paksa di memori
# tanpa perlu Anda melakukan instalasi ulang atau downgrade library.
# ==============================================================================
try:
    import google.protobuf.message_factory
    
    # Cek apakah fungsi 'GetMessageClass' hilang (penyebab error Anda)
    if not hasattr(google.protobuf.message_factory, 'GetMessageClass'):
        
        def _GetMessageClass_Patch(descriptor):
            """
            Fungsi pengganti buatan sendiri untuk menjembatani
            MediaPipe (lama) dengan Protobuf (baru).
            """
            from google.protobuf import symbol_database
            try:
                # Cara Modern (Protobuf 4.x)
                return symbol_database.Default().GetPrototype(descriptor)
            except:
                # Cara Alternatif jika cara modern gagal
                from google.protobuf import message_factory
                # GetMessages mengembalikan dictionary {nama_lengkap: kelas}
                messages = message_factory.GetMessages([descriptor.file])
                return messages.get(descriptor.full_name)

        # Suntikkan fungsi ini ke dalam library yang sedang berjalan
        google.protobuf.message_factory.GetMessageClass = _GetMessageClass_Patch
        # print(">> SYSTEM: Library Patch Applied Successfully.")

except ImportError:
    pass # Jika library belum terinstall sama sekali, biarkan error normal terjadi nanti
# ==============================================================================


import pygame
import cv2
import mediapipe as mp
import numpy as np
import math
import random

# Import konfigurasi dan aset
from src.config import *
from src.assets import assets

# Import sprites
from src.sprites import Player, BotFish, BossFish, Particle, PowerUp, TrailParticle

# Import utilities
from src.utils import (SaveData, BackgroundLayer, LightRay, AchievementManager, 
                       get_random_spawn_level, apply_screen_shake, ScorePopup, 
                       Bubble, WaterCurrent, VignetteEffect, DailyChallengeManager)

# Import UI Modern yang baru
from src.ui import (PauseMenu, WelcomeScreen, Tutorial, Notification, LoadingScreen,
                    draw_hud, draw_modern_card, C_ACCENT, C_HIGHLIGHT, C_DARK_BG, 
                    C_TEXT_MAIN, C_DANGER, C_SUCCESS)

# =====================
# Setup Mediapipe (Face Tracking)
# =====================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def init_camera():
    """Inisialisasi kamera menggunakan OpenCV"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    return cap

def draw_end_game_screen(surface, title, title_color, player, is_win=False):
    """
    Menggambar layar Game Over / Win menggunakan style 'Card' modern
    """
    # 1. Overlay Gelap Blur
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill(C_DARK_BG)
    overlay.set_alpha(220)
    surface.blit(overlay, (0, 0))

    # 2. Container Card Utama
    card_w, card_h = 500, 400
    card_rect = pygame.Rect((SCREEN_WIDTH - card_w)//2, (SCREEN_HEIGHT - card_h)//2, card_w, card_h)
    
    # Efek border warna tergantung menang/kalah
    border_col = C_HIGHLIGHT if is_win else C_DANGER
    draw_modern_card(surface, card_rect, color=(20, 30, 45), alpha=255, border_color=border_col, radius=20)

    # 3. Konten
    cx = card_rect.centerx
    
    # Judul Besar
    title_surf = assets.fonts['game_over'].render(title, True, title_color)
    surface.blit(title_surf, title_surf.get_rect(center=(cx, card_rect.top + 60)))
    
    # Sub-judul / Status
    sub_text = "MISSION COMPLETE" if is_win else "SYSTEM FAILURE"
    sub_surf = assets.fonts['notification'].render(sub_text, True, (150, 160, 170))
    surface.blit(sub_surf, sub_surf.get_rect(center=(cx, card_rect.top + 110)))

    # Garis Pemisah
    pygame.draw.line(surface, (255, 255, 255, 30), (card_rect.left + 50, card_rect.top + 130), (card_rect.right - 50, card_rect.top + 130), 2)

    # Statistik Akhir
    font_stats = pygame.font.Font(None, 36)
    stats = [
        ("Final Score", player.score, C_HIGHLIGHT),
        ("Fish Eaten", player.fish_eaten, C_ACCENT),
        ("Max Combo", f"{player.max_combo}x", C_TEXT_MAIN)
    ]

    start_y = card_rect.top + 160
    for i, (label, value, col) in enumerate(stats):
        y_pos = start_y + i * 40
        lbl = font_stats.render(label, True, (200, 200, 200))
        surface.blit(lbl, (card_rect.left + 80, y_pos))
        val = font_stats.render(str(value), True, col)
        val_rect = val.get_rect(midright=(card_rect.right - 80, y_pos + 10))
        surface.blit(val, val_rect)

    # Tombol / Instruksi (Blinking)
    if (pygame.time.get_ticks() // 800) % 2:
        prompt_surf = assets.fonts['ui'].render("PRESS 'R' TO RESTART", True, C_ACCENT)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=(cx, card_rect.bottom - 50)))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Feeding Frenzy: Evolution")
    clock = pygame.time.Clock()

    # ==========================================
    # 1. LOAD ASSETS DULUAN
    # ==========================================
    # Load assets sebelum UI apapun digambar
    # agar font tersedia untuk Loading Screen
    assets.load_assets()
    assets.play_bgm('bgm_gameplay', volume=0.3)

    # ==========================================
    # 2. LOADING SCREEN PHASE
    # ==========================================
    loading_screen = LoadingScreen()
    
    # Loop Loading (Animasi Transisi)
    while loading_screen.active:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        loading_screen.update()
        loading_screen.draw(screen)
        pygame.display.flip()

    # ==========================================
    # 3. INIT CAMERA & SYSTEMS
    # ==========================================
    cap = init_camera()
    if not cap:
        screen.fill((0, 0, 0))
        # Fallback font jika terjadi masalah
        try:
            font = assets.fonts['notification']
        except:
            font = pygame.font.Font(None, 40)
            
        text = font.render("Error: Camera not found.", True, C_DANGER)
        screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        pygame.display.flip()
        pygame.time.wait(3000)
        return

    # Sprite Groups
    all_sprites = pygame.sprite.Group()
    bot_fish_group = pygame.sprite.Group()
    particle_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()
    trail_group = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)

    # Environmental Systems
    bg_layers = [
        BackgroundLayer(0, 0.5, (100, 150, 200), 'bubble'),
        BackgroundLayer(0, 1.0, (80, 120, 160), 'bubble'),
        BackgroundLayer(0, 0.3, (60, 100, 140), 'seaweed')
    ]
    
    light_rays = [LightRay() for _ in range(5)]
    bubbles = [Bubble() for _ in range(30)]
    water_current = WaterCurrent()
    vignette = VignetteEffect()
    
    # Game Logic Systems
    score_popups = []
    daily_challenge = DailyChallengeManager()
    achievement_manager = AchievementManager()
    save_data = SaveData()
    
    # UI Systems
    pause_menu = PauseMenu()
    welcome_screen = WelcomeScreen()
    tutorial = Tutorial()
    notifications = []
    
    # Game State Variables
    current_boss = None
    boss_defeated_levels = set()
    game_stats = {
        'damage_taken': 0, 'fish_in_10s': 0, 'fish_timestamps': [],
        'ultimates_used': 0, 'powerups_collected': set(), 'bosses_defeated': 0,
        'survival_time': 0, 'game_start_time': pygame.time.get_ticks(),
        'last_damage_time': pygame.time.get_ticks()
    }
    
    last_spawn_time = pygame.time.get_ticks()
    last_powerup_spawn = pygame.time.get_ticks()
    frame_count = 0 
    last_face_x, last_face_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    last_is_eating = False
    
    running = True
    game_over = False
    win = False
    paused = False
    game_started = False
    screen_shake_intensity = 0

    # --- Internal Helper: Reset Game ---
    def reset_game():
        nonlocal game_over, win, paused, game_started, player, last_spawn_time, notifications, tutorial, welcome_screen
        nonlocal current_boss, boss_defeated_levels, game_stats, trail_group, score_popups
        
        save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
        
        game_over = False
        win = False
        all_sprites.empty()
        bot_fish_group.empty()
        particle_group.empty()
        powerup_group.empty()
        boss_group.empty()
        trail_group.empty()
        score_popups = []
        
        current_boss = None
        boss_defeated_levels = set()
        game_stats = {
            'damage_taken': 0, 'fish_in_10s': 0, 'fish_timestamps': [],
            'ultimates_used': 0, 'powerups_collected': set(), 'bosses_defeated': 0,
            'survival_time': 0, 'game_start_time': pygame.time.get_ticks(),
            'last_damage_time': pygame.time.get_ticks()
        }
        
        player = Player()
        all_sprites.add(player)
        last_spawn_time = pygame.time.get_ticks()
        notifications = []
        tutorial = Tutorial()

    def quick_restart():
        reset_game()
        tutorial.show_next_tip()

    # ==========================================
    # 4. MAIN GAME LOOP
    # ==========================================
    while running:
        dt = clock.tick(FPS)
        
        # --- Input Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if welcome_screen.active:
                    welcome_screen.skip()
                    game_started = True
                    tutorial.show_next_tip()
                    continue
                
                if paused:
                    action = pause_menu.handle_input(event)
                    if action == 'Resume':
                        pause_menu.toggle(); paused = False
                    elif action == 'Restart':
                        quick_restart(); paused = False; pause_menu.active = False
                    elif action == 'Quit':
                        running = False
                
                # Global Keys
                if event.key == pygame.K_ESCAPE and not game_over and not win:
                    pause_menu.toggle()
                    paused = pause_menu.active
                    if paused:
                        pause_menu.set_stats(player, game_stats, save_data)
                
                if (game_over or win) and event.key == pygame.K_r:
                    reset_game()
                
                if event.key == pygame.K_SPACE and not game_over and not win and not paused and game_started:
                    if player.activate_ultimate():
                        notifications.append(Notification("FEEDING FRENZY!", C_HIGHLIGHT, 2000, 'large'))
                        game_stats['ultimates_used'] += 1
                
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

        # --- Scene: Welcome Screen ---
        if welcome_screen.active:
            welcome_screen.update()
            screen.fill(C_DARK_BG)
            welcome_screen.draw(screen)
            pygame.display.flip()
            continue

        # --- Scene: Pause Menu ---
        if paused:
            pause_menu.draw(screen)
            pygame.display.flip()
            continue

        # --- Camera Processing (Optimized) ---
        success, image = cap.read()
        if not success: continue

        image = cv2.flip(image, 1)
        debug_image = image.copy()
        
        frame_count += 1
        player_x, player_y = last_face_x, last_face_y
        is_eating = last_is_eating
        
        if frame_count % FACE_DETECTION_SKIP_FRAMES == 0:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0].landmark
                nose_tip = face_landmarks[1]
                
                percent_x = (nose_tip.x - TRACKING_X_MIN) / (TRACKING_X_MAX - TRACKING_X_MIN)
                percent_y = (nose_tip.y - TRACKING_Y_MIN) / (TRACKING_Y_MAX - TRACKING_Y_MIN)

                percent_x = max(0.0, min(1.0, percent_x))
                percent_y = max(0.0, min(1.0, percent_y))

                player_x = int(percent_x * SCREEN_WIDTH)
                player_y = int(percent_y * SCREEN_HEIGHT)
                last_face_x, last_face_y = player_x, player_y

                lip_top = face_landmarks[13]
                lip_bottom = face_landmarks[14]
                lip_distance = abs(lip_top.y - lip_bottom.y)
                is_eating = lip_distance > MOUTH_OPEN_THRESHOLD
                last_is_eating = is_eating

        # Prepare Camera Surface
        cam_frame = cv2.cvtColor(debug_image, cv2.COLOR_BGR2RGB)  
        cam_frame = np.rot90(cam_frame)  
        cam_surface = pygame.surfarray.make_surface(cam_frame)
        cam_surface = pygame.transform.scale(cam_surface, (260, 150)) 

        if not game_started: continue

        # ================= LOGIC UPDATE =================
        if not game_over and not win:
            current_time = pygame.time.get_ticks()
            
            # Stats update
            if game_stats.get('game_start_time'):
                time_since_damage = (current_time - game_stats.get('last_damage_time', current_time)) / 1000
                game_stats['survival_time'] = int(time_since_damage)
            
            water_current.update()
            
            # Trail
            if random.random() < 0.3:
                trail = TrailParticle(player.rect.centerx, player.rect.centery, int(player.current_size * 0.3))
                trail_group.add(trail)
            
            player.update(player_x, player_y, is_eating)
            water_current.apply_to_rect(player.rect)
            
            bot_fish_group.update(player.level, player.rect, player.frozen_enemies)
            for bot in bot_fish_group:
                water_current.apply_to_rect(bot.rect)
            
            particle_group.update()
            powerup_group.update()
            trail_group.update()
            score_popups = [p for p in score_popups if p.update()]
            
            # Daily Challenge
            reward = daily_challenge.update_progress('combo', player.combo_count)
            if reward > 0:
                player.add_score(reward)
                notifications.append(Notification(f"Daily Complete! +{reward}", C_SUCCESS, 3000, 'large'))
            
            # Boss Logic
            if current_boss:
                current_boss.update(player.rect)
                if current_boss.defeated:
                    player.add_score(current_boss.boss_level * 20)
                    game_stats['bosses_defeated'] += 1
                    notifications.append(Notification("BOSS DEFEATED!", C_HIGHLIGHT, 3000, 'large'))
                    
                    # Boss explosion particles
                    for _ in range(30):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 8)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        color = random.choice([C_HIGHLIGHT, C_DANGER, (255, 255, 100)])
                        p = Particle(current_boss.rect.centerx, current_boss.rect.centery, color, velocity, 1500, 8, 'star')
                        particle_group.add(p)
                    
                    boss_group.remove(current_boss)
                    current_boss = None
                    daily_challenge.update_progress('boss_defeated', game_stats['bosses_defeated'])
                    if game_stats['bosses_defeated'] == 1:
                        achievement_manager.unlock('boss_slayer')
            
            # Spawn Boss
            for boss_level in BOSS_SPAWN_LEVELS:
                if player.level >= boss_level and boss_level not in boss_defeated_levels and current_boss is None:
                    current_boss = BossFish(boss_level)
                    boss_group.add(current_boss)
                    boss_defeated_levels.add(boss_level)
                    notifications.append(Notification(" BOSS INCOMING! ", C_DANGER, 3000, 'large'))
                    assets.play_sound('boss_spawn', 0.9)
                    break
            
            # Magnet
            if player.magnet_radius > 0:
                for bot in bot_fish_group:
                    if bot.level < player.level:
                        distance = math.hypot(bot.rect.centerx - player.rect.centerx, bot.rect.centery - player.rect.centery)
                        if distance < player.magnet_radius:
                            dx = player.rect.centerx - bot.rect.centerx
                            dy = player.rect.centery - bot.rect.centery
                            bot.rect.x += dx * 0.05
                            bot.rect.y += dy * 0.05
            
            # Tutorial Trigger
            if player.score > 20 and 1 not in tutorial.shown_tips:
                tutorial.current_tip = 2; tutorial.show_next_tip()
            if player.combo_count >= 3 and 5 not in tutorial.shown_tips:
                tutorial.current_tip = 3; tutorial.show_next_tip()

            # Spawn Bots
            if len(bot_fish_group) < MAX_TOTAL_BOTS:
                if current_time - last_spawn_time > SPAWN_INTERVAL_GENERAL:
                    num_to_spawn = random.randint(1, 3)
                    for _ in range(num_to_spawn):
                        spawn_level = get_random_spawn_level(player.level)
                        bot = BotFish(level=spawn_level)
                        all_sprites.add(bot)
                        bot_fish_group.add(bot)
                    last_spawn_time = current_time
            
            # Spawn Powerup
            if current_time - last_powerup_spawn > 5000:
                if random.random() < POWER_UP_SPAWN_CHANCE * 100:
                    power_type = random.choice(['speed', 'shield', 'magnet', 'double_xp', 'freeze', 'size_boost'])
                    x = random.randint(100, SCREEN_WIDTH - 100)
                    y = random.randint(100, SCREEN_HEIGHT - 100)
                    powerup = PowerUp(x, y, power_type)
                    powerup_group.add(powerup)
                last_powerup_spawn = current_time
            
            # --- Collision Detection ---
            # 1. Player vs Fish
            collisions = pygame.sprite.spritecollide(player, bot_fish_group, False)
            for fish in collisions:
                if player.is_eating and (player.level >= fish.level or player.ultimate_active):
                    player.add_score(fish.level)
                    player.fish_eaten += 1
                    player.add_combo()
                    player.charge_ultimate(10)
                    
                    # Logic statistik
                    current_time = pygame.time.get_ticks()
                    game_stats['fish_timestamps'].append(current_time)
                    game_stats['fish_timestamps'] = [t for t in game_stats['fish_timestamps'] if current_time - t < 10000]
                    game_stats['fish_in_10s'] = len(game_stats['fish_timestamps'])
                    daily_challenge.update_progress('fish_eaten', game_stats['fish_in_10s'])
                    
                    # Popup Score
                    score_value = fish.level * (2 if player.double_xp else 1)
                    if player.combo_count >= 10: score_value *= 3
                    elif player.combo_count >= 5: score_value *= 2
                    elif player.combo_count >= 3: score_value = int(score_value * 1.5)
                    
                    popup_col = C_HIGHLIGHT if player.combo_count >= 5 else (255, 255, 100)
                    score_popups.append(ScorePopup(fish.rect.centerx, fish.rect.centery - 20, score_value, popup_col))
                    
                    # Particles
                    for _ in range(8):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 5)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        p = Particle(fish.rect.centerx, fish.rect.centery, (255, 200, 50), velocity, 500, 4, 'circle')
                        particle_group.add(p)
                        
                    fish.kill()
                    assets.play_sound('eat', 0.5)

                elif player.level < fish.level and not player.ultimate_active:
                    is_dead = player.take_damage()
                    screen_shake_intensity = 15
                    game_stats['damage_taken'] += 1
                    game_stats['last_damage_time'] = pygame.time.get_ticks()
                    
                    # Blood particles - menyebar merata ke segala arah
                    for _ in range(12):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 4)  # Speed lebih rendah agar tidak terlalu cepat
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        # Variasi warna merah untuk efek lebih natural
                        red_shade = random.choice([C_DANGER, (255, 100, 100), (200, 50, 50)])
                        p = Particle(player.rect.centerx, player.rect.centery, red_shade, velocity, 500, random.randint(3, 6), 'circle')
                        particle_group.add(p)
                        
                    if is_dead:
                        game_over = True
                        assets.play_sound('game_over', 0.8)

            # 2. Player vs Boss
            if current_boss and pygame.sprite.collide_rect(player, current_boss):
                if player.is_eating and player.ultimate_active:
                    current_boss.take_damage()
                    screen_shake_intensity = 10
                elif not player.invincible:
                    is_dead = player.take_damage()
                    screen_shake_intensity = 20
                    game_stats['damage_taken'] += 1
                    if is_dead:
                        game_over = True
                        assets.play_sound('game_over', 0.8)

            # 3. Player vs Powerup
            for powerup in pygame.sprite.spritecollide(player, powerup_group, True):
                player.activate_powerup(powerup.power_type)
                game_stats['powerups_collected'].add(powerup.power_type)
                notifications.append(Notification(f"{powerup.power_type.upper()}!", C_ACCENT, 1500))
                assets.play_sound('power_up_collect', 0.7)
                daily_challenge.update_progress('powerups', len(game_stats['powerups_collected']))

            daily_challenge.update_progress('survival_time', game_stats['survival_time'])
            achievement_manager.check_achievements(player, game_stats)

            # Win Condition
            if player.score >= TOTAL_SCORE_TO_WIN and not win:
                win = True
                player.level = MAX_LEVEL
                assets.play_sound('victory', 0.8)

        # Update Notifications & Background
        notifications = [n for n in notifications if n.update()]
        for layer in bg_layers: layer.update()
        for ray in light_rays: ray.update()
        for bubble in bubbles: bubble.update()
        if screen_shake_intensity > 0: screen_shake_intensity -= 1

        # ================= DRAWING (RENDER) =================
        screen.fill((0, 105, 148))
        
        # 1. Background Elements
        for ray in light_rays: ray.draw(screen)
        for bubble in bubbles: bubble.draw(screen)
        water_current.draw(screen)
        for layer in bg_layers: layer.draw(screen)
        
        # 2. Game Surface (Sprite Layer with Shake)
        shake_offset = (0, 0)
        if screen_shake_intensity > 0:
            shake_offset = apply_screen_shake(screen_shake_intensity)
        
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # Transparent surface
        
        # Draw all sprites onto game_surface
        for trail in trail_group: game_surface.blit(trail.image, trail.rect)
        for sprite in all_sprites: game_surface.blit(sprite.image, sprite.rect)
        for particle in particle_group: game_surface.blit(particle.image, particle.rect)
        for powerup in powerup_group: game_surface.blit(powerup.image, powerup.rect)
        for boss in boss_group: game_surface.blit(boss.image, boss.rect)
        
        # Draw Indicators (Level numbers over heads)
        player.draw_indicator(game_surface)
        for bot in bot_fish_group:
            bot.draw_indicator(game_surface, player.level)
            
        screen.blit(game_surface, shake_offset)
        
        # 3. Post-Processing & UI Layer (No Shake)
        for popup in score_popups: popup.draw(screen)
        vignette.draw(screen)
        
        if current_boss: current_boss.draw_health_bar(screen)
        daily_challenge.draw(screen, y_offset=100)

        # --- MODERN HUD INTEGRATION ---
        draw_hud(screen, player) # Menggantikan manual render score/level lama
        
        for notification in notifications: notification.draw(screen)
        achievement_manager.draw_notifications(screen)
            
        if tutorial.active: tutorial.draw(screen)
        
        # --- MODERN FACECAM UI ---
        if 'cam_surface' in locals():
            cam_x, cam_y = SCREEN_WIDTH - 280, SCREEN_HEIGHT - 170
            cam_w, cam_h = 260, 150
            
            # Frame Background (Slate)
            cam_bg = pygame.Rect(cam_x - 5, cam_y - 25, cam_w + 10, cam_h + 35)
            draw_modern_card(screen, cam_bg, color=(20, 25, 30), alpha=240, border_color=(100, 100, 100), radius=10)
            
            # Label "LIVE FEED"
            lbl_font = pygame.font.Font(None, 20)
            lbl = lbl_font.render("LIVE FEED", True, C_ACCENT)
            screen.blit(lbl, (cam_x, cam_y - 20))
            
            # Blinking Rec Dot
            if (pygame.time.get_ticks() // 1000) % 2:
                pygame.draw.circle(screen, C_DANGER, (cam_x + cam_w - 10, cam_y - 15), 5)
            
            # The Camera Image
            screen.blit(cam_surface, (cam_x, cam_y))
            # Border tipis di sekitar gambar
            pygame.draw.rect(screen, (50, 60, 70), (cam_x, cam_y, cam_w, cam_h), 2)

        # Level Up Check & Notification
        if player.level > PLAYER_START_LEVEL and not hasattr(player, 'last_notified_level'):
            player.last_notified_level = PLAYER_START_LEVEL
        if hasattr(player, 'last_notified_level') and player.level > player.last_notified_level:
            notifications.append(Notification(f"LEVEL UP! -> {player.level}", C_HIGHLIGHT, 2000, 'large'))
            assets.play_sound('power_up_collect', 0.6)
            player.last_notified_level = player.level

        # --- MODERN END SCREEN ---
        if game_over:
            draw_end_game_screen(screen, "GAME OVER", C_DANGER, player, is_win=False)
        elif win:
            draw_end_game_screen(screen, "VICTORY", C_HIGHLIGHT, player, is_win=True)

        pygame.display.flip()

    # Cleanup
    save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

if __name__ == "__main__":
    main()