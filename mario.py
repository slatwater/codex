"""
马里奥小游戏 (Mario Mini Game)
Controls:
  ← → / A D  : Move left / right
  Space / ↑ / W : Jump
  R           : Restart (on Game Over or Win screen)
  ESC         : Quit
"""

import pygame
import sys
import math

# ─────────────────────────────────────────
# Constants
# ─────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 500
FPS = 60
TILE = 32

# Colors
SKY        = (107, 140, 255)
GROUND_TOP = (139, 90,  43)
GROUND_BOT = (101, 60,  20)
GRASS      = ( 34, 139,  34)
BRICK_A    = (180,  80,  20)
BRICK_B    = (160,  60,   0)
PIPE_GREEN = ( 50, 160,  50)
PIPE_DARK  = ( 30, 120,  30)
COIN_Y     = (255, 215,   0)
COIN_DARK  = (200, 160,   0)
MARIO_RED  = (220,  20,  20)
MARIO_SKIN = (255, 200, 150)
MARIO_BLUE = ( 30,  80, 200)
MARIO_BRWN = (120,  60,  20)
GOOMBA_BRN = (139,  90,  10)
GOOMBA_DRK = (100,  60,   5)
GOOMBA_EYE = (  0,   0,   0)
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
RED        = (200,  20,  20)
YELLOW     = (255, 200,   0)
HUD_BG     = (  0,   0,   0)
FLAG_POLE  = (200, 200, 200)
FLAG_COLOR = (220,  20,  20)

GRAVITY = 0.55
MAX_FALL = 14
JUMP_FORCE = -13
WALK_SPEED = 4
CAMERA_LAG = 0.12

WORLD_W = 4800   # pixels wide


# ─────────────────────────────────────────
# Tile helpers
# ─────────────────────────────────────────
def tile(col, row):
    return pygame.Rect(col * TILE, row * TILE, TILE, TILE)


# ─────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────
def draw_mario(surf, x, y, w, h, facing_right=True, jumping=False):
    """Draw a simple pixel-art Mario."""
    cx = int(x + w / 2)
    top = int(y)
    # hat
    pygame.draw.rect(surf, MARIO_RED,  (cx - 10, top,      20, 6))
    pygame.draw.rect(surf, MARIO_RED,  (cx - 7,  top - 4,  14, 4))
    # face
    pygame.draw.rect(surf, MARIO_SKIN, (cx - 8,  top + 6,  16, 10))
    # eyes
    ex = cx + (4 if facing_right else -4)
    pygame.draw.rect(surf, BLACK,      (ex,       top + 8,   3,  3))
    # mustache
    pygame.draw.rect(surf, MARIO_BRWN, (cx - 7,  top + 14,  14, 3))
    # body (overalls)
    pygame.draw.rect(surf, MARIO_BLUE, (cx - 8,  top + 16,  16, 10))
    pygame.draw.rect(surf, MARIO_RED,  (cx - 8,  top + 16,   4, 10))
    pygame.draw.rect(surf, MARIO_RED,  (cx + 4,  top + 16,   4, 10))
    # arms
    pygame.draw.rect(surf, MARIO_RED,  (cx - 14, top + 16,   8, 8))
    pygame.draw.rect(surf, MARIO_RED,  (cx + 6,  top + 16,   8, 8))
    pygame.draw.rect(surf, MARIO_SKIN, (cx - 14, top + 22,   6, 4))
    pygame.draw.rect(surf, MARIO_SKIN, (cx + 8,  top + 22,   6, 4))
    # legs
    leg_spread = 4 if not jumping else 8
    pygame.draw.rect(surf, MARIO_BLUE, (cx - 8,  top + 26,   7, 8))
    pygame.draw.rect(surf, MARIO_BLUE, (cx + 1,  top + 26,   7, 8))
    pygame.draw.rect(surf, MARIO_BRWN, (cx - 10, top + 32,   9, 4))
    pygame.draw.rect(surf, MARIO_BRWN, (cx + 1,  top + 32,   9, 4))


def draw_goomba(surf, x, y, w, h, squished=False):
    """Draw a Goomba."""
    cx = int(x + w / 2)
    top = int(y)
    if squished:
        pygame.draw.ellipse(surf, GOOMBA_BRN, (cx - 14, top + h - 8, 28, 8))
        return
    # body
    pygame.draw.ellipse(surf, GOOMBA_BRN, (cx - 12, top + 8,  24, 20))
    # head
    pygame.draw.ellipse(surf, GOOMBA_BRN, (cx - 12, top,      24, 18))
    # angry brows
    pygame.draw.line(surf, GOOMBA_DRK, (cx - 10, top + 5),  (cx - 2, top + 8),  3)
    pygame.draw.line(surf, GOOMBA_DRK, (cx + 10, top + 5),  (cx + 2, top + 8),  3)
    # eyes
    pygame.draw.circle(surf, WHITE,      (cx - 5, top + 10), 4)
    pygame.draw.circle(surf, WHITE,      (cx + 5, top + 10), 4)
    pygame.draw.circle(surf, GOOMBA_EYE, (cx - 4, top + 11), 2)
    pygame.draw.circle(surf, GOOMBA_EYE, (cx + 6, top + 11), 2)
    # feet
    pygame.draw.ellipse(surf, GOOMBA_DRK, (cx - 14, top + 24, 12, 8))
    pygame.draw.ellipse(surf, GOOMBA_DRK, (cx + 2,  top + 24, 12, 8))


def draw_coin(surf, x, y, w, h, frame):
    """Draw an animated coin."""
    cx = int(x + w / 2)
    cy = int(y + h / 2)
    scale = abs(math.cos(frame * 0.08))
    rw = max(2, int(12 * scale))
    pygame.draw.ellipse(surf, COIN_Y,    (cx - rw, cy - 12, rw * 2, 24))
    pygame.draw.ellipse(surf, COIN_DARK, (cx - max(1, rw - 3), cy - 10, max(2, (rw - 3) * 2), 20))


def draw_platform(surf, rect, cam_x):
    """Draw a brick platform."""
    r = pygame.Rect(rect.x - cam_x, rect.y, rect.w, rect.h)
    # top grass strip
    pygame.draw.rect(surf, GRASS, (r.x, r.y, r.w, 6))
    # body
    pygame.draw.rect(surf, GROUND_TOP, (r.x, r.y + 6, r.w, r.h - 6))
    # brick lines horizontal
    for dy in range(6, r.h, 14):
        pygame.draw.line(surf, GROUND_BOT, (r.x, r.y + dy), (r.x + r.w, r.y + dy), 1)
    # brick lines vertical (staggered)
    row = 0
    for dy in range(6, r.h, 14):
        offset = 0 if row % 2 == 0 else TILE // 2
        for dx in range(offset, r.w + 1, TILE):
            pygame.draw.line(surf, GROUND_BOT, (r.x + dx, r.y + dy), (r.x + dx, r.y + dy + 13), 1)
        row += 1


def draw_brick_block(surf, rect, cam_x):
    r = pygame.Rect(rect.x - cam_x, rect.y, rect.w, rect.h)
    pygame.draw.rect(surf, BRICK_A, r)
    pygame.draw.line(surf, BRICK_B, (r.x, r.y + r.h // 2), (r.x + r.w, r.y + r.h // 2), 2)
    pygame.draw.line(surf, BRICK_B, (r.x + r.w // 2, r.y), (r.x + r.w // 2, r.y + r.h // 2), 2)
    pygame.draw.line(surf, BRICK_B, (r.x + r.w // 4, r.y + r.h // 2), (r.x + r.w // 4, r.y + r.h), 2)
    pygame.draw.line(surf, BRICK_B, (r.x + 3 * r.w // 4, r.y + r.h // 2), (r.x + 3 * r.w // 4, r.y + r.h), 2)
    pygame.draw.rect(surf, BRICK_B, r, 2)


def draw_pipe(surf, px, py, cam_x):
    sx = px - cam_x
    # shaft
    pygame.draw.rect(surf, PIPE_GREEN, (sx + 4, py + 28, 24, 60))
    # highlight
    pygame.draw.rect(surf, (80, 200, 80), (sx + 5, py + 28, 5, 60))
    # head
    pygame.draw.rect(surf, PIPE_GREEN, (sx, py, 32, 28))
    pygame.draw.rect(surf, PIPE_DARK,  (sx, py, 32, 28), 3)
    pygame.draw.rect(surf, (80, 200, 80), (sx + 2, py + 2, 6, 24))


def draw_flag(surf, fx, fy, cam_x):
    sx = fx - cam_x
    # pole
    pygame.draw.rect(surf, FLAG_POLE, (sx + 3, fy - 120, 4, 120))
    # flag
    pygame.draw.polygon(surf, FLAG_COLOR, [
        (sx + 7, fy - 120), (sx + 30, fy - 108), (sx + 7, fy - 96)
    ])


def draw_background(surf, cam_x):
    surf.fill(SKY)
    # clouds
    cloud_positions = [
        (200, 60), (500, 40), (900, 70), (1300, 50), (1800, 65),
        (2200, 45), (2700, 70), (3200, 55), (3700, 60), (4200, 50)
    ]
    for cpx, cpy in cloud_positions:
        sx = (cpx - cam_x * 0.3) % (WORLD_W + 200) - 100
        pygame.draw.ellipse(surf, WHITE, (sx,      cpy, 80, 30))
        pygame.draw.ellipse(surf, WHITE, (sx + 20, cpy - 20, 60, 35))
        pygame.draw.ellipse(surf, WHITE, (sx + 50, cpy, 70, 25))

    # mountains in background
    mountain_positions = [300, 800, 1400, 2000, 2600, 3200, 3900, 4500]
    for mpx in mountain_positions:
        sx = int(mpx - cam_x * 0.5)
        pygame.draw.polygon(surf, (160, 170, 190), [
            (sx, SCREEN_H - 80), (sx + 80, SCREEN_H - 200), (sx + 160, SCREEN_H - 80)
        ])


def draw_hud(surf, score, lives, timer_left, font_big, font_small):
    # HUD bar at top
    pygame.draw.rect(surf, (0, 0, 0, 180), (0, 0, SCREEN_W, 36))
    pygame.draw.rect(surf, YELLOW, (0, 0, SCREEN_W, 36), 2)

    score_txt = font_small.render(f"SCORE: {score:06d}", True, WHITE)
    lives_txt = font_small.render(f"× {lives}", True, WHITE)
    time_txt  = font_small.render(f"TIME: {max(0, timer_left):03d}", True, WHITE)
    mario_txt = font_small.render("♥", True, MARIO_RED)

    surf.blit(score_txt, (16, 8))
    surf.blit(time_txt,  (SCREEN_W // 2 - 50, 8))
    surf.blit(mario_txt, (SCREEN_W - 120, 8))
    surf.blit(lives_txt, (SCREEN_W - 95,  8))


# ─────────────────────────────────────────
# Game Objects
# ─────────────────────────────────────────
class Player:
    W, H = 28, 36

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.alive = True
        self.score = 0
        self.lives = 3
        self.invincible = 0   # frames of invincibility after hurt
        self.frame = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def handle_input(self, keys):
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump  = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        if left:
            self.vx = -WALK_SPEED
            self.facing_right = False
        elif right:
            self.vx = WALK_SPEED
            self.facing_right = True
        else:
            self.vx *= 0.8  # friction

        if jump and self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False

    def apply_gravity(self):
        self.vy = min(self.vy + GRAVITY, MAX_FALL)

    def move_and_collide(self, platforms):
        self.on_ground = False
        # Horizontal
        self.x += self.vx
        self.x = max(0, min(self.x, WORLD_W - self.W))
        pr = self.rect
        for p in platforms:
            if pr.colliderect(p):
                if self.vx > 0:
                    self.x = p.left - self.W
                elif self.vx < 0:
                    self.x = p.right
                self.vx = 0
                pr = self.rect

        # Vertical
        self.y += self.vy
        pr = self.rect
        for p in platforms:
            if pr.colliderect(p):
                if self.vy > 0:
                    self.y = p.top - self.H
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = p.bottom
                    self.vy = 0
                pr = self.rect

    def update(self, keys, platforms):
        if self.invincible > 0:
            self.invincible -= 1
        self.frame += 1
        self.handle_input(keys)
        self.apply_gravity()
        self.move_and_collide(platforms)

        # Fell off screen
        if self.y > SCREEN_H + 100:
            self.die()

    def die(self):
        if self.invincible > 0:
            return
        self.lives -= 1
        self.invincible = 120
        if self.lives <= 0:
            self.alive = False
        else:
            self.x = 80
            self.y = 300
            self.vx = 0
            self.vy = 0

    def draw(self, surf, cam_x):
        if self.invincible > 0 and (self.frame // 4) % 2 == 0:
            return  # blink during invincibility
        sx = int(self.x - cam_x)
        sy = int(self.y)
        jumping = not self.on_ground
        draw_mario(surf, sx, sy, self.W, self.H, self.facing_right, jumping)


class Goomba:
    W, H = 28, 28
    SPEED = 1.5

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = -self.SPEED
        self.vy = 0.0
        self.alive = True
        self.squished = False
        self.squish_timer = 0
        self.frame = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, platforms):
        if self.squished:
            self.squish_timer -= 1
            if self.squish_timer <= 0:
                self.alive = False
            return

        self.frame += 1
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.x += self.vx

        # Clamp to world
        if self.x < 0:
            self.x = 0
            self.vx = self.SPEED
        if self.x > WORLD_W - self.W:
            self.x = WORLD_W - self.W
            self.vx = -self.SPEED

        # Horizontal collision
        gr = self.rect
        for p in platforms:
            if gr.colliderect(p):
                if self.vx > 0:
                    self.x = p.left - self.W
                    self.vx = -self.SPEED
                elif self.vx < 0:
                    self.x = p.right
                    self.vx = self.SPEED
                gr = self.rect

        # Vertical collision
        self.y += self.vy
        gr = self.rect
        on_ground = False
        for p in platforms:
            if gr.colliderect(p):
                if self.vy > 0:
                    self.y = p.top - self.H
                    self.vy = 0
                    on_ground = True
                elif self.vy < 0:
                    self.y = p.bottom
                    self.vy = 0
                gr = self.rect

        # Reverse at platform edges (look-ahead)
        if on_ground:
            probe = pygame.Rect(int(self.x + self.vx * 8), int(self.y + self.H + 4), self.W, 4)
            has_floor = any(probe.colliderect(p) for p in platforms)
            if not has_floor:
                self.vx *= -1

        if self.y > SCREEN_H + 100:
            self.alive = False

    def squish(self):
        self.squished = True
        self.squish_timer = 30

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)
        draw_goomba(surf, sx, sy, self.W, self.H, self.squished)


class Coin:
    W, H = 20, 24

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.collected = False
        self.frame = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self):
        self.frame += 1

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)
        draw_coin(surf, sx, sy, self.W, self.H, self.frame)


class Particle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.vx = (pygame.math.Vector2(1, 0).rotate(
            __import__('random').uniform(0, 360))).x * 3
        self.vy = __import__('random').uniform(-5, -1)
        self.color = color
        self.life = 30

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1

    def draw(self, surf, cam_x):
        if self.life > 0:
            alpha = int(255 * self.life / 30)
            pygame.draw.circle(surf, self.color,
                               (int(self.x - cam_x), int(self.y)), 4)


# ─────────────────────────────────────────
# Level definition
# ─────────────────────────────────────────
def build_level():
    platforms = []
    bricks = []
    pipes_data = []    # (px, py) — just visual decorations + collision
    coins_data = []
    goombas_data = []
    flag_x = WORLD_W - 200

    # ── Ground ──────────────────────────────────────
    # Main ground spans the whole world in chunks (with one pit)
    ground_sections = [
        (0,     100, 384, 16),   # px, py in tiles: start_col, end_col
        (14,    100, 176, 16),
        (21,    100, WORLD_W // TILE, 16),
    ]
    # Build ground as one big rect per section
    platforms.append(pygame.Rect(0,              SCREEN_H - TILE * 2, 13 * TILE, TILE * 2))
    platforms.append(pygame.Rect(17 * TILE,      SCREEN_H - TILE * 2, (WORLD_W - 17 * TILE), TILE * 2))

    # ── Floating platforms ───────────────────────────
    float_platforms = [
        # col, row, width in tiles
        (6,  9, 3),
        (12, 8, 4),
        (20, 9, 3),
        (28, 7, 5),
        (38, 8, 4),
        (46, 9, 3),
        (55, 7, 6),
        (65, 8, 4),
        (75, 9, 3),
        (82, 7, 5),
        (92, 8, 4),
        (100, 9, 3),
        (108, 7, 6),
        (115, 8, 4),
        (125, 6, 5),
        (134, 9, 3),
    ]
    for col, row, wt in float_platforms:
        platforms.append(pygame.Rect(col * TILE, row * TILE, wt * TILE, TILE))

    # ── Brick blocks (also solid) ────────────────────
    brick_groups = [
        (5, 7, 4), (11, 6, 3), (19, 7, 5), (27, 6, 3),
        (37, 7, 4), (45, 6, 3), (54, 6, 5), (64, 7, 4),
        (74, 6, 3), (81, 6, 4), (91, 7, 3), (99, 6, 5),
        (107, 6, 4), (114, 5, 3), (124, 5, 5),
    ]
    for col, row, wt in brick_groups:
        r = pygame.Rect(col * TILE, row * TILE, wt * TILE, TILE)
        bricks.append(r)
        platforms.append(r)

    # ── Pipes ────────────────────────────────────────
    pipe_cols = [10, 25, 40, 58, 70, 85, 105, 120, 138]
    for pc in pipe_cols:
        px = pc * TILE
        py = SCREEN_H - TILE * 2 - 60
        pipes_data.append((px, py))
        # pipe collision block
        platforms.append(pygame.Rect(px + 4, py, 24, 60 + TILE * 2))

    # ── Coins on top of floating platforms ──────────
    for col, row, wt in float_platforms:
        for ci in range(wt):
            coins_data.append(((col + ci) * TILE + TILE // 2 - 10, (row - 1) * TILE))
    # Coins on brick tops
    for col, row, wt in brick_groups:
        for ci in range(0, wt, 2):
            coins_data.append(((col + ci) * TILE + TILE // 2 - 10, (row - 1) * TILE))

    # ── Goombas ──────────────────────────────────────
    goomba_cols = [8, 15, 23, 31, 42, 50, 60, 68, 78, 88, 96, 110, 118, 128, 136]
    for gc in goomba_cols:
        goombas_data.append((gc * TILE, SCREEN_H - TILE * 2 - Goomba.H))

    return platforms, bricks, pipes_data, coins_data, goombas_data, flag_x


# ─────────────────────────────────────────
# Overlay screens
# ─────────────────────────────────────────
def draw_overlay(surf, font_big, font_small, title, subtitle, color):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    t1 = font_big.render(title, True, color)
    t2 = font_small.render(subtitle, True, WHITE)
    surf.blit(t1, t1.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 40)))
    surf.blit(t2, t2.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))


# ─────────────────────────────────────────
# Main Game
# ─────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("马里奥小游戏")
    clock = pygame.time.Clock()

    try:
        font_big   = pygame.font.SysFont("Arial", 52, bold=True)
        font_small = pygame.font.SysFont("Arial", 22)
    except Exception:
        font_big   = pygame.font.Font(None, 64)
        font_small = pygame.font.Font(None, 28)

    def new_game():
        platforms, bricks, pipes_data, coins_data, goombas_data, fx = build_level()
        player = Player(80, 300)
        goombas = [Goomba(gx, gy) for gx, gy in goombas_data]
        coins   = [Coin(cx, cy)   for cx, cy in coins_data]
        particles = []
        cam_x = 0.0
        timer = 300 * FPS  # 300 seconds
        won = False
        game_over = False
        return {
            "platforms": platforms,
            "bricks": bricks,
            "pipes_data": pipes_data,
            "flag_x": fx,
            "player": player,
            "goombas": goombas,
            "coins": coins,
            "particles": particles,
            "cam_x": cam_x,
            "timer": timer,
            "won": won,
            "game_over": game_over,
        }

    state = new_game()
    running = True
    frame_count = 0

    while running:
        dt = clock.tick(FPS)
        frame_count += 1

        p     = state["player"]
        gooms = state["goombas"]
        coins = state["coins"]
        parts = state["particles"]
        plats = state["platforms"]
        cam   = state["cam_x"]

        # ── Events ──────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and (state["game_over"] or state["won"]):
                    state = new_game()

        if state["game_over"] or state["won"]:
            # Redraw last frame + overlay
            draw_background(screen, int(state["cam_x"]))
            for r in state["platforms"]:
                draw_platform(screen, r, int(state["cam_x"]))
            for r in state["bricks"]:
                draw_brick_block(screen, r, int(state["cam_x"]))
            for px2, py2 in state["pipes_data"]:
                draw_pipe(screen, px2, py2, int(state["cam_x"]))
            for c in state["coins"]:
                if not c.collected:
                    c.draw(screen, int(state["cam_x"]))
            for g in gooms:
                if g.alive:
                    g.draw(screen, int(state["cam_x"]))
            p.draw(screen, int(state["cam_x"]))
            draw_hud(screen, p.score, p.lives,
                     max(0, state["timer"] // FPS), font_big, font_small)
            if state["game_over"]:
                draw_overlay(screen, font_big, font_small,
                             "GAME OVER", "按 R 重新开始 | ESC 退出", RED)
            else:
                draw_overlay(screen, font_big, font_small,
                             "通 关 ！", f"得分: {p.score:06d}  按 R 重玩 | ESC 退出", YELLOW)
            pygame.display.flip()
            continue

        # ── Update timer ────────────────────────────
        state["timer"] -= 1
        if state["timer"] <= 0:
            p.die()

        # ── Update player ───────────────────────────
        keys = pygame.key.get_pressed()
        p.update(keys, plats)
        if not p.alive:
            state["game_over"] = True

        # ── Camera ──────────────────────────────────
        target_cam = p.x - SCREEN_W * 0.35
        target_cam = max(0, min(target_cam, WORLD_W - SCREEN_W))
        state["cam_x"] += (target_cam - state["cam_x"]) * CAMERA_LAG
        cam = state["cam_x"]

        # ── Update goombas ──────────────────────────
        for g in gooms:
            g.update(plats)

        # ── Update coins ────────────────────────────
        for c in coins:
            c.update()

        # ── Coin collection ─────────────────────────
        for c in coins:
            if not c.collected and p.rect.colliderect(c.rect):
                c.collected = True
                p.score += 100
                for _ in range(8):
                    parts.append(Particle(c.x + c.W // 2, c.y, COIN_Y))

        # ── Player-Goomba collision ──────────────────
        for g in gooms:
            if g.squished or not g.alive:
                continue
            if p.rect.colliderect(g.rect) and p.invincible == 0:
                # Stomp check: player falling onto top of goomba
                pr = p.rect
                gr = g.rect
                overlap_top = pr.bottom - gr.top
                if p.vy > 0 and overlap_top < 20 and pr.bottom > gr.top:
                    g.squish()
                    p.vy = JUMP_FORCE * 0.6  # bounce
                    p.score += 200
                    for _ in range(10):
                        parts.append(Particle(g.x + g.W // 2, g.y, GOOMBA_BRN))
                else:
                    p.die()

        # ── Flag / goal ──────────────────────────────
        flag_rect = pygame.Rect(state["flag_x"], SCREEN_H - TILE * 2 - 120, 10, 120)
        if p.rect.colliderect(flag_rect):
            p.score += max(0, state["timer"] // FPS) * 10
            state["won"] = True

        # ── Update particles ─────────────────────────
        for pt in parts:
            pt.update()
        state["particles"] = [pt for pt in parts if pt.life > 0]
        parts = state["particles"]

        # ── Draw ─────────────────────────────────────
        draw_background(screen, int(cam))

        # platforms
        for r in plats:
            draw_platform(screen, r, int(cam))

        # bricks (redraw on top)
        for r in state["bricks"]:
            draw_brick_block(screen, r, int(cam))

        # pipes
        for px2, py2 in state["pipes_data"]:
            draw_pipe(screen, px2, py2, int(cam))

        # flag
        draw_flag(screen, state["flag_x"], SCREEN_H - TILE * 2, int(cam))

        # coins
        for c in coins:
            if not c.collected:
                c.draw(screen, int(cam))

        # goombas
        for g in gooms:
            if g.alive:
                g.draw(screen, int(cam))

        # player
        p.draw(screen, int(cam))

        # particles
        for pt in parts:
            pt.draw(screen, int(cam))

        # HUD
        draw_hud(screen, p.score, p.lives,
                 max(0, state["timer"] // FPS), font_big, font_small)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
