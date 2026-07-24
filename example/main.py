"""Catcher — the gameship example game. Move with arrows/A-D, catch the squares.

Runs on pygame or pygame-ce. Set GAMESHIP_MAX_FRAMES=N to auto-exit (CI smoke
test; pair with SDL_VIDEODRIVER=dummy for headless runners).
"""
import os
import random
import sys

import pygame

pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Catcher (gameship example)")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

player = pygame.Rect(W // 2 - 40, H - 60, 80, 24)
blocks: list[list] = []  # [rect, color]
score, spawn_t = 0, 0.0
MAX_FRAMES = int(os.environ.get("GAMESHIP_MAX_FRAMES", "0"))
frames = 0

while True:
    dt = clock.tick(60) / 1000
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.x = max(0, player.x - int(420 * dt))
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.x = min(W - player.w, player.x + int(420 * dt))

    spawn_t += dt
    if spawn_t > 0.6:
        spawn_t = 0.0
        color = [random.randint(80, 255) for _ in range(3)]
        blocks.append([pygame.Rect(random.randint(0, W - 30), -30, 30, 30), color])

    for b in blocks[:]:
        b[0].y += int(260 * dt)
        if b[0].colliderect(player):
            blocks.remove(b)
            score += 1
        elif b[0].y > H:
            blocks.remove(b)

    screen.fill((18, 22, 32))
    pygame.draw.rect(screen, (120, 200, 255), player, border_radius=6)
    for rect, color in blocks:
        pygame.draw.rect(screen, color, rect, border_radius=4)
    screen.blit(font.render(f"SCORE {score}", True, (240, 240, 240)), (16, 12))
    pygame.display.flip()

    frames += 1
    if MAX_FRAMES and frames >= MAX_FRAMES:
        print(f"gameship example: ran {frames} frames, score={score}, ok")
        pygame.quit()
        sys.exit(0)
