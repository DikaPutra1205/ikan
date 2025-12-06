import pygame
import cv2
import mediapipe as mp
import numpy as np
import math
import random

from src.config import *
from src.assets import assets
from src.sprites import Player, BotFish, BossFish, Particle, PowerUp, TrailParticle
from src.utils import (SaveData, BackgroundLayer, LightRay, AchievementManager, 
                       get_random_spawn_level, apply_screen_shake, ScorePopup, 
                       Bubble, WaterCurrent, VignetteEffect, DailyChallengeManager)
from src.ui import PauseMenu, WelcomeScreen, Tutorial, Notification, draw_progress_bar

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

def init_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    return cap

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Feeding Frenzy: Evolution (Modular)")
    clock = pygame.time.Clock()
    
    # Load Assets
    assets.load_assets()
    assets.play_bgm('bgm_gameplay', volume=0.3)

    # Init Camera
    cap = init_camera()
    if not cap:
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 50)
        text = font.render("Error: Tidak bisa membuka kamera.", True, (255, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)
        return

    # Groups
    all_sprites = pygame.sprite.Group()
    bot_fish_group = pygame.sprite.Group()
    particle_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)

    # Systems
    bg_layers = [
        BackgroundLayer(0, 0.5, (100, 150, 200), 'bubble'),
        BackgroundLayer(0, 1.0, (80, 120, 160), 'bubble'),
        BackgroundLayer(0, 0.3, (60, 100, 140), 'seaweed')
    ]
    
    # Light rays for underwater effect
    light_rays = [LightRay() for _ in range(5)]
    
    # Bubbles for atmosphere
    bubbles = [Bubble() for _ in range(30)]
    
    # Water current effect
    water_current = WaterCurrent()
    
    # Vignette effect
    vignette = VignetteEffect()
    
    # Score popups
    score_popups = []
    
    # Daily challenge
    daily_challenge = DailyChallengeManager()
    
    # Trail particles group
    trail_group = pygame.sprite.Group()
    
    # Boss system
    boss_group = pygame.sprite.Group()
    current_boss = None
    boss_defeated_levels = set()
    
    # Achievement system
    achievement_manager = AchievementManager()
    game_stats = {
        'damage_taken': 0,
        'fish_in_10s': 0,
        'fish_timestamps': [],
        'ultimates_used': 0,
        'powerups_collected': set(),
        'bosses_defeated': 0,
        'survival_time': 0,
        'game_start_time': pygame.time.get_ticks(),
        'last_damage_time': pygame.time.get_ticks()
    }
    
    save_data = SaveData()
    pause_menu = PauseMenu()
    welcome_screen = WelcomeScreen()
    tutorial = Tutorial()
    notifications = []
    
    last_spawn_time = pygame.time.get_ticks()
    last_powerup_spawn = pygame.time.get_ticks()
    frame_count = 0  # For face detection optimization
    last_face_x, last_face_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    last_is_eating = False
    
    running = True
    game_over = False
    win = False
    paused = False
    game_started = False
    screen_shake_intensity = 0

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
            'damage_taken': 0,
            'fish_in_10s': 0,
            'fish_timestamps': [],
            'ultimates_used': 0,
            'powerups_collected': set(),
            'bosses_defeated': 0,
            'survival_time': 0,
            'game_start_time': pygame.time.get_ticks(),
            'last_damage_time': pygame.time.get_ticks()
        }
        
        player = Player()
        all_sprites.add(player)
        last_spawn_time = pygame.time.get_ticks()
        notifications = []
        tutorial = Tutorial()
        welcome_screen = WelcomeScreen()

    def quick_restart():
        nonlocal game_over, win, paused, player, last_spawn_time, notifications, tutorial
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
            'damage_taken': 0,
            'fish_in_10s': 0,
            'fish_timestamps': [],
            'ultimates_used': 0,
            'powerups_collected': set(),
            'bosses_defeated': 0,
            'survival_time': 0,
            'game_start_time': pygame.time.get_ticks(),
            'last_damage_time': pygame.time.get_ticks()
        }
        
        player = Player()
        all_sprites.add(player)
        last_spawn_time = pygame.time.get_ticks()
        notifications = []
        tutorial = Tutorial()
        tutorial.show_next_tip()

    while running:
        dt = clock.tick(FPS)
        
        # Pygame Events
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
                        pause_menu.toggle()
                        paused = False
                    elif action == 'Restart':
                        quick_restart()
                        paused = False
                        pause_menu.active = False
                    elif action == 'Quit':
                        running = False
                
                if event.key == pygame.K_ESCAPE and not game_over and not win:
                    pause_menu.toggle()
                    paused = pause_menu.active
                    if paused:
                        pause_menu.set_stats(player, game_stats, save_data)
                
                if (game_over or win) and event.key == pygame.K_r:
                    reset_game()
                    game_started = False # Back to welcome screen
                
                if event.key == pygame.K_SPACE and not game_over and not win and not paused and game_started:
                    if player.activate_ultimate():
                        notifications.append(Notification("FEEDING FRENZY!", (255, 215, 0), 2000, 'large'))
                        game_stats['ultimates_used'] += 1
                
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

        # Draw Welcome Screen
        if welcome_screen.active:
            welcome_screen.update()
            screen.fill((0, 105, 148))
            welcome_screen.draw(screen)
            pygame.display.flip()
            continue

        # Draw Pause Menu
        if paused:
            pause_menu.draw(screen)
            pygame.display.flip()
            continue

        # Process Camera (optimized - skip frames)
        success, image = cap.read()
        if not success: continue

        image = cv2.flip(image, 1)
        debug_image = image.copy()
        
        frame_count += 1
        player_x, player_y = last_face_x, last_face_y
        is_eating = last_is_eating
        
        # Only process face detection every N frames for better performance
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

                mp.solutions.drawing_utils.draw_landmarks(
                    image=debug_image,
                    landmark_list=results.multi_face_landmarks[0],
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style()
                )
        
        # === FACE CAM TO PYGAME SURFACE ===
        # Prepare camera frame for display in Pygame
        cam_frame = cv2.cvtColor(debug_image, cv2.COLOR_BGR2RGB)  
        cam_frame = np.rot90(cam_frame)  # Orientation fix
        cam_surface = pygame.surfarray.make_surface(cam_frame)
        cam_surface = pygame.transform.scale(cam_surface, (260, 150))  # Facecam size

        # cv2.imshow("CV Tracking Feed (Tekan 'q' untuk Keluar)", debug_image) # REMOVED

        if not game_started:
            continue

        # Game Logic
        if not game_over and not win:
            # Update survival time for daily challenge
            current_time = pygame.time.get_ticks()
            if game_stats.get('game_start_time'):
                time_since_damage = (current_time - game_stats.get('last_damage_time', current_time)) / 1000
                game_stats['survival_time'] = int(time_since_damage)
            
            # Update water current
            water_current.update()
            
            # Create trail particles for player movement
            if random.random() < 0.3:
                trail = TrailParticle(player.rect.centerx, player.rect.centery, 
                                     int(player.current_size * 0.3))
                trail_group.add(trail)
            
            player.update(player_x, player_y, is_eating)
            
            # Apply water current to player
            water_current.apply_to_rect(player.rect)
            
            bot_fish_group.update(player.level, player.rect, player.frozen_enemies)
            
            # Apply water current to bot fish
            for bot in bot_fish_group:
                water_current.apply_to_rect(bot.rect)
            
            particle_group.update()
            powerup_group.update()
            trail_group.update()
            
            # Update score popups
            score_popups = [p for p in score_popups if p.update()]
            
            # Update daily challenge progress
            reward = daily_challenge.update_progress('combo', player.combo_count)
            if reward > 0:
                player.add_score(reward)
                notifications.append(Notification(f"🎁 Daily Complete! +{reward}", (0, 255, 100), 3000, 'large'))
            
            # Boss Logic
            if current_boss:
                current_boss.update(player.rect)
                if current_boss.defeated:
                    # Boss defeated rewards
                    player.add_score(current_boss.boss_level * 20)
                    game_stats['bosses_defeated'] += 1
                    notifications.append(Notification("BOSS DEFEATED!", (255, 215, 0), 3000, 'large'))
                    
                    # Spawn particles
                    for _ in range(30):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 8)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        color = random.choice([(255, 215, 0), (255, 100, 100), (255, 255, 100)])
                        p = Particle(current_boss.rect.centerx, current_boss.rect.centery, 
                                   color, velocity, 1500, 8, 'star')
                        particle_group.add(p)
                    
                    boss_group.remove(current_boss)
                    current_boss = None
                    
                    # Update daily challenge
                    daily_challenge.update_progress('boss_defeated', game_stats['bosses_defeated'])
                    
                    # Achievement check
                    if game_stats['bosses_defeated'] == 1:
                        achievement_manager.unlock('boss_slayer')
            
            # Check for boss spawn
            for boss_level in BOSS_SPAWN_LEVELS:
                if player.level >= boss_level and boss_level not in boss_defeated_levels and current_boss is None:
                    current_boss = BossFish(boss_level)
                    boss_group.add(current_boss)
                    boss_defeated_levels.add(boss_level)
                    notifications.append(Notification("⚠️ BOSS INCOMING! ⚠️", (255, 0, 0), 3000, 'large'))
                    assets.play_sound('boss_spawn', 0.9)
                    break
            
            # Magnet Logic
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
            
            # Tutorial Logic
            if player.score > 20 and 1 not in tutorial.shown_tips:
                tutorial.current_tip = 2
                tutorial.show_next_tip()
            if player.combo_count >= 3 and 5 not in tutorial.shown_tips:
                tutorial.current_tip = 6
                tutorial.show_next_tip()

            # Spawning Logic
            current_time = pygame.time.get_ticks()
            if len(bot_fish_group) < MAX_TOTAL_BOTS:
                if current_time - last_spawn_time > SPAWN_INTERVAL_GENERAL:
                    num_to_spawn = random.randint(1, 3)
                    for _ in range(num_to_spawn):
                        spawn_level = get_random_spawn_level(player.level)
                        bot = BotFish(level=spawn_level)
                        all_sprites.add(bot)
                        bot_fish_group.add(bot)
                    last_spawn_time = current_time
            
            # Powerup Spawning
            if current_time - last_powerup_spawn > 5000:
                if random.random() < POWER_UP_SPAWN_CHANCE * 100:
                    power_type = random.choice(['speed', 'shield', 'magnet', 'double_xp', 'freeze', 'size_boost'])
                    x = random.randint(100, SCREEN_WIDTH - 100)
                    y = random.randint(100, SCREEN_HEIGHT - 100)
                    powerup = PowerUp(x, y, power_type)
                    powerup_group.add(powerup)
                last_powerup_spawn = current_time
            
            # Collisions
            # Player vs Bots
            collisions = pygame.sprite.spritecollide(player, bot_fish_group, False)
            for fish in collisions:
                if player.is_eating and (player.level >= fish.level or player.ultimate_active):
                    player.add_score(fish.level)
                    player.fish_eaten += 1
                    player.add_combo()
                    player.charge_ultimate(10)
                    
                    # Track fish eaten timestamps for speed demon achievement
                    current_time = pygame.time.get_ticks()
                    game_stats['fish_timestamps'].append(current_time)
                    # Keep only last 10 seconds of timestamps
                    game_stats['fish_timestamps'] = [t for t in game_stats['fish_timestamps'] 
                                                      if current_time - t < 10000]
                    game_stats['fish_in_10s'] = len(game_stats['fish_timestamps'])
                    
                    # Update daily challenge
                    daily_challenge.update_progress('fish_eaten', game_stats['fish_in_10s'])
                    
                    # Create Score Popup
                    score_value = fish.level * (2 if player.double_xp else 1)
                    if player.combo_count >= 10:
                        score_value *= 3
                    elif player.combo_count >= 5:
                        score_value *= 2
                    elif player.combo_count >= 3:
                        score_value = int(score_value * 1.5)
                    popup_color = (255, 215, 0) if player.combo_count >= 5 else (255, 255, 100)
                    score_popups.append(ScorePopup(fish.rect.centerx, fish.rect.centery - 20, score_value, popup_color))
                    
                    # Create Eat Particles
                    for _ in range(8):
                         angle = random.uniform(0, 2 * math.pi)
                         speed = random.uniform(2, 5)
                         velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                         color = random.choice([(255, 255, 100), (255, 200, 50), (255, 150, 0)])
                         p = Particle(fish.rect.centerx, fish.rect.centery, color, velocity, 500, 4, 'circle')
                         particle_group.add(p)
                         
                    fish.kill()
                    assets.play_sound('eat', 0.5)
                elif player.level < fish.level and not player.ultimate_active:
                    is_dead = player.take_damage()
                    screen_shake_intensity = 15
                    game_stats['damage_taken'] += 1
                    game_stats['last_damage_time'] = pygame.time.get_ticks()  # Reset survival timer
                    
                    # Hit Particles
                    for _ in range(12):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 6)
                        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                        p = Particle(player.rect.centerx, player.rect.centery, (255, 0, 0), velocity, 700, 5, 'circle')
                        particle_group.add(p)
                        
                    if is_dead:
                        game_over = True
                        assets.play_sound('game_over', 0.8)
            
            # Player vs Boss
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

            # Player vs Powerups
            powerup_collisions = pygame.sprite.spritecollide(player, powerup_group, True)
            for powerup in powerup_collisions:
                player.activate_powerup(powerup.power_type)
                game_stats['powerups_collected'].add(powerup.power_type)
                notifications.append(Notification(f"{powerup.power_type.upper()} Activated!", (255, 255, 0), 1500))
                assets.play_sound('power_up_collect', 0.7)
                
                # Update daily challenge
                daily_challenge.update_progress('powerups', len(game_stats['powerups_collected']))
            
            # Update daily challenge for survival time
            daily_challenge.update_progress('survival_time', game_stats['survival_time'])
            
            # Check achievements
            achievement_manager.check_achievements(player, game_stats)
            
            # Win Check
            if player.score >= TOTAL_SCORE_TO_WIN and not win:
                win = True
                player.level = MAX_LEVEL
                assets.play_sound('victory', 0.8)

        # Update Notifications & Background
        notifications = [n for n in notifications if n.update()]
        for layer in bg_layers:
            layer.update()
        
        # Update light rays
        for ray in light_rays:
            ray.update()
        
        # Update bubbles
        for bubble in bubbles:
            bubble.update()
        
        if screen_shake_intensity > 0:
            screen_shake_intensity -= 1

        # ================= Render =================
        screen.fill((0, 105, 148))
        
        # Light rays (behind everything)
        for ray in light_rays:
            ray.draw(screen)
        
        # Bubbles (background layer)
        for bubble in bubbles:
            bubble.draw(screen)
        
        # Water current visualization
        water_current.draw(screen)
        
        # Background
        for layer in bg_layers:
            layer.draw(screen)
        
        # Shake Surface
        shake_offset = (0, 0)
        if screen_shake_intensity > 0:
            shake_offset = apply_screen_shake(screen_shake_intensity)
        
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_surface.fill((0, 105, 148)) # We will blit this onto screen
        # To make shake affect background, we need to draw background on game_surface too.
        # Redrawing bg on game_surface
        for layer in bg_layers:
            layer.draw(game_surface)
        
        # Draw trail particles (behind player)
        for trail in trail_group:
            game_surface.blit(trail.image, trail.rect)
            
        for sprite in all_sprites:
            game_surface.blit(sprite.image, sprite.rect)
        
        for particle in particle_group:
            game_surface.blit(particle.image, particle.rect)
            
        for powerup in powerup_group:
            game_surface.blit(powerup.image, powerup.rect)
        
        # Draw boss
        for boss in boss_group:
            game_surface.blit(boss.image, boss.rect)
            
        player.draw_indicator(game_surface)
        for bot in bot_fish_group:
            bot.draw_indicator(game_surface, player.level)
            
        screen.blit(game_surface, shake_offset)
        
        # Draw score popups
        for popup in score_popups:
            popup.draw(screen)
        
        # Vignette effect (on top of game, before UI)
        vignette.draw(screen)
        
        # Boss health bar (no shake)
        if current_boss:
            current_boss.draw_health_bar(screen)
        
        # Daily Challenge UI
        daily_challenge.draw(screen, y_offset=100)
        
        # UI (No Shake)
        score_next = player.score_to_next if player.level < MAX_LEVEL else TOTAL_SCORE_TO_WIN
        score_text = assets.fonts['score'].render(f'Score: {player.score} / {score_next}', True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        
        level_text = assets.fonts['level'].render(f'Level: {player.level}', True, (255, 255, 255))
        screen.blit(level_text, (10, 50))
        
        player.draw_ui(screen)
        
        # Legend
        legend_y = 10
        legend_x = SCREEN_WIDTH - 250
        legend_title = assets.fonts['indicator'].render("Legend:", True, (255, 255, 255))
        screen.blit(legend_title, (legend_x, legend_y))
        
        green_text = assets.fonts['indicator'].render("🟢 = Safe to Eat", True, (0, 255, 0))
        screen.blit(green_text, (legend_x, legend_y + 35))
        
        red_text = assets.fonts['indicator'].render("🔴 = DANGER!", True, (255, 0, 0))
        screen.blit(red_text, (legend_x, legend_y + 65))
        
        for notification in notifications:
            notification.draw(screen)
        
        # Draw achievement notifications
        achievement_manager.draw_notifications(screen)
            
        if tutorial.active:
            tutorial.draw(screen)
        
        # === FACE CAM OVERLAY (pojok kanan bawah, SELALU tampil) ===
        if 'cam_surface' in locals():
            screen.blit(cam_surface, (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160))
            # Border
            pygame.draw.rect(screen, (255, 215, 0),
                (SCREEN_WIDTH - 270, SCREEN_HEIGHT - 160, 260, 150), 3)

        # Level Up Notification Check
        if player.level > PLAYER_START_LEVEL and not hasattr(player, 'last_notified_level'):
            player.last_notified_level = PLAYER_START_LEVEL
    
        if hasattr(player, 'last_notified_level') and player.level > player.last_notified_level:
            notifications.append(Notification(f"LEVEL {player.level}!", (255, 215, 0), 2000, 'large'))
            # Level Up Particles
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(3, 8)
                velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
                color = random.choice([(255, 215, 0), (255, 255, 100), (255, 200, 255)])
                p = Particle(player.rect.centerx, player.rect.centery, color, velocity, 1000, 6, 'star')
                particle_group.add(p)
            player.last_notified_level = player.level

        # Game Over / Win Screens
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            text = assets.fonts['game_over'].render("GAME OVER", True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(text, text_rect)
            
            stats_text = assets.fonts['notification'].render(f"Final Score: {player.score}", True, (255, 255, 255))
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            screen.blit(stats_text, stats_rect)
            
            prompt_text = assets.fonts['score'].render("Tekan 'R' untuk Mulai Lagi", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(prompt_text, prompt_rect)

        if win:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            text = assets.fonts['win'].render("YOU WIN!", True, (255, 215, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(text, text_rect)
            
            stats_text = assets.fonts['notification'].render(f"Final Score: {player.score}", True, (255, 255, 255))
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            screen.blit(stats_text, stats_rect)
            
            prompt_text = assets.fonts['score'].render("Tekan 'R' untuk Main Lagi", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(prompt_text, prompt_rect)

        pygame.display.flip()

    # Cleanup
    save_data.update_stats(player.score, player.fish_eaten, player.level, player.max_combo)
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

if __name__ == "__main__":
    main()