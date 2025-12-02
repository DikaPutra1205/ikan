import json
import os
import random
import math
import pygame
from .config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_LEVEL

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
