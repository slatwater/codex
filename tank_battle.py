"""
坦克大战 (Tank Battle)
=====================
Controls:
  Arrow keys / WASD  - Move player tank
  Space              - Shoot
  R                  - Restart after game over
  Q / ESC            - Quit

Requires: pygame
  pip install pygame
"""

import sys
import math
import random
import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_W, SCREEN_H = 800, 600
TILE = 40           # grid cell size
COLS = SCREEN_W // TILE   # 20
ROWS = SCREEN_H // TILE   # 15

FPS = 60

# Colors
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GRAY   = (128, 128, 128)
DKGRAY = (64,  64,  64)
RED    = (220, 50,  50)
GREEN  = (50,  200, 50)
YELLOW = (230, 200, 30)
BLUE   = (50,  100, 220)
ORANGE = (230, 130, 30)
BROWN  = (139, 90,  43)

# Directions: (dx, dy, angle_deg)
DIR_UP    = (0,  -1, 0)
DIR_DOWN  = (0,   1, 180)
DIR_LEFT  = (-1,  0, 270)
DIR_RIGHT = (1,   0, 90)

PLAYER_SPEED = 3
ENEMY_SPEED  = 1.5
BULLET_SPEED = 6

PLAYER_HP = 3
ENEMY_COUNT = 6


# ---------------------------------------------------------------------------
# Helper: draw a tank shape
# ---------------------------------------------------------------------------
def _draw_tank(surface: pygame.Surface, cx: int, cy: int, size: int,
               angle: float, body_color, barrel_color):
    """Draw a simple top-down tank at (cx, cy), rotated by angle degrees."""
    half = size // 2
    body_rect = pygame.Rect(cx - half, cy - half, size, size)
    pygame.draw.rect(surface, body_color, body_rect, border_radius=4)

    # Barrel
    rad = math.radians(angle)
    barrel_len = half + 6
    bx = cx + barrel_len * math.sin(rad)
    by = cy - barrel_len * math.cos(rad)
    pygame.draw.line(surface, barrel_color, (cx, cy), (int(bx), int(by)), 5)

    # Tracks
    pygame.draw.rect(surface, DKGRAY,
                     (cx - half, cy - half, 6, size), border_radius=2)
    pygame.draw.rect(surface, DKGRAY,
                     (cx + half - 6, cy - half, 6, size), border_radius=2)


# ---------------------------------------------------------------------------
# Bullet
# ---------------------------------------------------------------------------
class Bullet:
    RADIUS = 5

    def __init__(self, x: float, y: float, dx: float, dy: float, owner: str):
        self.x = x
        self.y = y
        self.dx = dx * BULLET_SPEED
        self.dy = dy * BULLET_SPEED
        self.owner = owner  # 'player' or 'enemy'
        self.alive = True

    def update(self, walls):
        self.x += self.dx
        self.y += self.dy

        # Out of bounds
        if not (0 <= self.x <= SCREEN_W and 0 <= self.y <= SCREEN_H):
            self.alive = False
            return

        # Wall collision
        r = pygame.Rect(self.x - self.RADIUS, self.y - self.RADIUS,
                        self.RADIUS * 2, self.RADIUS * 2)
        for wall in walls:
            if wall.alive and r.colliderect(wall.rect):
                self.alive = False
                wall.hit()
                return

    def draw(self, surface: pygame.Surface):
        color = YELLOW if self.owner == 'player' else ORANGE
        pygame.draw.circle(surface, color,
                           (int(self.x), int(self.y)), self.RADIUS)


# ---------------------------------------------------------------------------
# Wall (brick)
# ---------------------------------------------------------------------------
class Wall:
    HP_BRICK = 2
    HP_STEEL = 999

    def __init__(self, col: int, row: int, wall_type: str = 'brick'):
        self.rect = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
        self.wall_type = wall_type
        self.hp = self.HP_BRICK if wall_type == 'brick' else self.HP_STEEL
        self.alive = True

    def hit(self):
        if self.wall_type == 'brick':
            self.hp -= 1
            if self.hp <= 0:
                self.alive = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        color = BROWN if self.wall_type == 'brick' else GRAY
        pygame.draw.rect(surface, color, self.rect)
        # grid lines for texture
        pygame.draw.rect(surface, DKGRAY, self.rect, 1)


# ---------------------------------------------------------------------------
# Tank base
# ---------------------------------------------------------------------------
class Tank:
    SIZE = 32
    SHOOT_COOLDOWN = 45   # frames

    def __init__(self, x: float, y: float, body_color, barrel_color):
        self.x = x
        self.y = y
        self.body_color = body_color
        self.barrel_color = barrel_color
        self.angle = 0.0   # degrees; 0 = up
        self.dx = 0.0
        self.dy = -1.0     # facing up by default
        self.alive = True
        self.shoot_timer = 0

    @property
    def rect(self):
        half = self.SIZE // 2
        return pygame.Rect(int(self.x) - half, int(self.y) - half,
                           self.SIZE, self.SIZE)

    def shoot(self, bullets: list):
        if self.shoot_timer > 0:
            return
        self.shoot_timer = self.SHOOT_COOLDOWN
        owner = 'player' if isinstance(self, PlayerTank) else 'enemy'
        bullets.append(Bullet(self.x, self.y, self.dx, self.dy, owner))

    def _try_move(self, nx: float, ny: float, walls, tanks) -> bool:
        """Return True if move is valid (no collision)."""
        half = self.SIZE // 2
        r = pygame.Rect(int(nx) - half, int(ny) - half, self.SIZE, self.SIZE)

        # Wall collision
        for wall in walls:
            if wall.alive and r.colliderect(wall.rect):
                return False

        # Tank-tank collision
        for tank in tanks:
            if tank is self or not tank.alive:
                continue
            if r.colliderect(tank.rect):
                return False

        # Screen bounds
        if nx - half < 0 or nx + half > SCREEN_W:
            return False
        if ny - half < 0 or ny + half > SCREEN_H:
            return False

        return True

    def update_timer(self):
        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    def draw(self, surface: pygame.Surface):
        _draw_tank(surface, int(self.x), int(self.y),
                   self.SIZE, self.angle, self.body_color, self.barrel_color)


# ---------------------------------------------------------------------------
# Player Tank
# ---------------------------------------------------------------------------
class PlayerTank(Tank):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, GREEN, WHITE)
        self.hp = PLAYER_HP
        self.score = 0
        self.invincible = 0   # invincibility frames after being hit

    def handle_input(self, keys, walls, tanks, bullets):
        move_dir = None
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_dir = DIR_UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_dir = DIR_DOWN
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir = DIR_LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir = DIR_RIGHT

        if move_dir:
            self.dx, self.dy, self.angle = move_dir
            nx = self.x + self.dx * PLAYER_SPEED
            ny = self.y + self.dy * PLAYER_SPEED
            if self._try_move(nx, ny, walls, tanks):
                self.x, self.y = nx, ny

        if keys[pygame.K_SPACE]:
            self.shoot(bullets)

    def take_hit(self):
        if self.invincible > 0:
            return
        self.hp -= 1
        self.invincible = FPS * 2   # 2 s invincibility
        if self.hp <= 0:
            self.alive = False

    def update(self, keys, walls, tanks, bullets):
        self.update_timer()
        if self.invincible > 0:
            self.invincible -= 1
        self.handle_input(keys, walls, tanks, bullets)

    def draw(self, surface: pygame.Surface):
        # Blink while invincible
        if self.invincible > 0 and (self.invincible // 6) % 2 == 0:
            return
        super().draw(surface)
        # HP hearts
        for i in range(self.hp):
            pygame.draw.circle(surface, RED,
                               (10 + i * 18, SCREEN_H - 12), 7)


# ---------------------------------------------------------------------------
# Enemy Tank  (simple AI)
# ---------------------------------------------------------------------------
class EnemyTank(Tank):
    MOVE_INTERVAL = 60   # frames between direction changes
    SHOOT_INTERVAL = 90

    def __init__(self, x: float, y: float):
        super().__init__(x, y, RED, YELLOW)
        self.move_timer = random.randint(0, self.MOVE_INTERVAL)
        self.auto_shoot_timer = random.randint(0, self.SHOOT_INTERVAL)
        # random initial direction
        self._pick_direction()

    def _pick_direction(self):
        d = random.choice([DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT])
        self.dx, self.dy, self.angle = d

    def update(self, walls, tanks, bullets, player):
        self.update_timer()

        # Periodically re-aim toward player (50 % chance) or random
        self.move_timer -= 1
        if self.move_timer <= 0:
            self.move_timer = self.MOVE_INTERVAL
            if player and player.alive and random.random() < 0.5:
                # point roughly toward player
                pdx = player.x - self.x
                pdy = player.y - self.y
                if abs(pdx) > abs(pdy):
                    d = DIR_RIGHT if pdx > 0 else DIR_LEFT
                else:
                    d = DIR_DOWN if pdy > 0 else DIR_UP
                self.dx, self.dy, self.angle = d
            else:
                self._pick_direction()

        # Move
        nx = self.x + self.dx * ENEMY_SPEED
        ny = self.y + self.dy * ENEMY_SPEED
        if not self._try_move(nx, ny, walls, tanks):
            self._pick_direction()
        else:
            self.x, self.y = nx, ny

        # Auto shoot
        self.auto_shoot_timer -= 1
        if self.auto_shoot_timer <= 0:
            self.auto_shoot_timer = self.SHOOT_INTERVAL + random.randint(0, 30)
            self.shoot(bullets)


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------
def build_map() -> list:
    """Return list of Wall objects."""
    walls = []

    # Border walls (steel)
    for c in range(COLS):
        walls.append(Wall(c, 0, 'steel'))
        walls.append(Wall(c, ROWS - 1, 'steel'))
    for r in range(1, ROWS - 1):
        walls.append(Wall(0, r, 'steel'))
        walls.append(Wall(COLS - 1, r, 'steel'))

    # Interior brick obstacles (hand-crafted + random)
    fixed = [
        (3, 3), (4, 3), (3, 4),
        (8, 2), (8, 3), (8, 4),
        (12, 3), (13, 3),
        (16, 2), (16, 3), (16, 4),
        (3, 8), (4, 8), (3, 9),
        (8, 7), (8, 8), (8, 9),
        (12, 8), (13, 8),
        (16, 7), (16, 8), (16, 9),
        (6, 6), (7, 6),
        (11, 5), (11, 6),
        (14, 6), (15, 6),
    ]
    occupied = set()
    for c, r in fixed:
        if 1 <= c < COLS - 1 and 1 <= r < ROWS - 1:
            walls.append(Wall(c, r, 'brick'))
            occupied.add((c, r))

    # Random extras
    for _ in range(20):
        c = random.randint(2, COLS - 3)
        r = random.randint(2, ROWS - 3)
        if (c, r) not in occupied:
            walls.append(Wall(c, r, 'brick'))
            occupied.add((c, r))

    return walls


# ---------------------------------------------------------------------------
# Spawn helpers
# ---------------------------------------------------------------------------
def _safe_spawn(col: int, row: int) -> tuple:
    return col * TILE + TILE // 2, row * TILE + TILE // 2


def spawn_enemies(count: int) -> list:
    positions = [
        (2, 2), (10, 2), (17, 2),
        (2, 7), (10, 7), (17, 7),
        (5, 2), (14, 2), (5, 7), (14, 7),
    ]
    random.shuffle(positions)
    enemies = []
    for i in range(min(count, len(positions))):
        c, r = positions[i]
        enemies.append(EnemyTank(*_safe_spawn(c, r)))
    return enemies


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
def draw_hud(surface: pygame.Surface, font: pygame.font.Font,
             player: PlayerTank, enemies: list, level: int):
    # Score
    score_surf = font.render(f"Score: {player.score}", True, WHITE)
    surface.blit(score_surf, (SCREEN_W // 2 - score_surf.get_width() // 2, 4))

    # Remaining enemies
    enemy_surf = font.render(f"Enemies: {sum(e.alive for e in enemies)}", True, RED)
    surface.blit(enemy_surf, (SCREEN_W - enemy_surf.get_width() - 8, 4))

    # Level
    lvl_surf = font.render(f"Level: {level}", True, YELLOW)
    surface.blit(lvl_surf, (8, 4))


def draw_overlay(surface: pygame.Surface, big_font: pygame.font.Font,
                 small_font: pygame.font.Font, message: str, sub: str = ""):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    msg_surf = big_font.render(message, True, YELLOW)
    surface.blit(msg_surf,
                 (SCREEN_W // 2 - msg_surf.get_width() // 2,
                  SCREEN_H // 2 - msg_surf.get_height() // 2 - 20))

    if sub:
        sub_surf = small_font.render(sub, True, WHITE)
        surface.blit(sub_surf,
                     (SCREEN_W // 2 - sub_surf.get_width() // 2,
                      SCREEN_H // 2 + 20))


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("坦克大战 Tank Battle")
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.SysFont(None, 28)
        self.font_big   = pygame.font.SysFont(None, 64)

        self.level = 1
        self._new_game()

    def _new_game(self):
        self.walls   = build_map()
        self.player  = PlayerTank(*_safe_spawn(10, 12))
        enemy_count  = ENEMY_COUNT + (self.level - 1) * 2
        self.enemies = spawn_enemies(enemy_count)
        self.bullets: list[Bullet] = []
        self.state   = 'playing'   # 'playing' | 'won' | 'lost'

    # ------------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()
            if self.state == 'playing':
                self._update()
            self._draw()

    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and self.state != 'playing':
                    self.level = 1
                    self._new_game()
                # Next level shortcut (N) when won
                if event.key == pygame.K_n and self.state == 'won':
                    self.level += 1
                    score_carry = self.player.score
                    self._new_game()
                    self.player.score = score_carry

    # ------------------------------------------------------------------
    def _update(self):
        keys = pygame.key.get_pressed()
        all_tanks = [self.player] + self.enemies

        # Player
        if self.player.alive:
            self.player.update(keys, self.walls, all_tanks, self.bullets)

        # Enemies
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(self.walls, all_tanks, self.bullets, self.player)

        # Bullets
        for bullet in self.bullets:
            bullet.update(self.walls)

        # Bullet vs tanks
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            r = pygame.Rect(bullet.x - Bullet.RADIUS, bullet.y - Bullet.RADIUS,
                            Bullet.RADIUS * 2, Bullet.RADIUS * 2)
            if bullet.owner == 'player':
                for enemy in self.enemies:
                    if enemy.alive and r.colliderect(enemy.rect):
                        enemy.alive = False
                        bullet.alive = False
                        self.player.score += 100
                        break
            else:  # enemy bullet
                if self.player.alive and r.colliderect(self.player.rect):
                    self.player.take_hit()
                    bullet.alive = False

        # Bullet vs bullet (cancel)
        live = [b for b in self.bullets if b.alive]
        for i in range(len(live)):
            for j in range(i + 1, len(live)):
                bi, bj = live[i], live[j]
                if (abs(bi.x - bj.x) < Bullet.RADIUS * 2 and
                        abs(bi.y - bj.y) < Bullet.RADIUS * 2):
                    bi.alive = False
                    bj.alive = False

        # Purge dead bullets
        self.bullets = [b for b in self.bullets if b.alive]

        # Win / lose check
        if not self.player.alive:
            self.state = 'lost'
        elif all(not e.alive for e in self.enemies):
            self.state = 'won'

    # ------------------------------------------------------------------
    def _draw(self):
        self.screen.fill(BLACK)

        # Walls
        for wall in self.walls:
            wall.draw(self.screen)

        # Bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)

        # Tanks
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(self.screen)
        if self.player.alive:
            self.player.draw(self.screen)

        # HUD
        draw_hud(self.screen, self.font_small,
                 self.player, self.enemies, self.level)

        # Overlays
        if self.state == 'won':
            draw_overlay(self.screen, self.font_big, self.font_small,
                         "YOU WIN!", "Press N for next level  |  R to restart  |  Q to quit")
        elif self.state == 'lost':
            draw_overlay(self.screen, self.font_big, self.font_small,
                         "GAME OVER",
                         f"Score: {self.player.score}  |  Press R to restart  |  Q to quit")

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
