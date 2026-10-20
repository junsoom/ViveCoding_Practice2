import math
import random
import pygame

W, H = 640, 720
COLS, ROWS = 8, 6
BRICK_W, BRICK_H, GAP, TOP = 66, 28, 6, 90
PALETTE = [(255, 154, 162), (255, 183, 139), (255, 218, 133), (181, 234, 170), (153, 214, 240), (199, 177, 240)]
INK = (84, 70, 110)
THEMES = [((255, 240, 246), (222, 233, 255)), ((255, 244, 230), (255, 222, 214)), ((232, 255, 244), (214, 236, 255))]
ITEM_COLORS = {"W": (255, 183, 139), "M": (153, 214, 240), "S": (199, 177, 240), "H": (255, 130, 160),
               "G": (255, 218, 133), "P": (200, 200, 215), "N": (181, 234, 170)}
ITEM_TIMERS = {  # item kind -> (timer name, frames); M = multi-ball, H = extra heart
    "W": ("WIDE", 600), "S": ("SLOW", 480), "G": ("GRAV", 300), "P": ("GHOST", 180), "N": ("MAGNET", 600)}
COMBO_MSG = {3: "Nice!", 5: "Wow!", 8: "Yay!"}

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cute Breakout")
clock = pygame.time.Clock()
font, small, big = (pygame.font.SysFont("arialroundedmtbold,arial", n, bold=True) for n in (26, 18, 54))

def make_background(level):
    bg = pygame.Surface((W, H))
    top, bottom = THEMES[(level - 1) % 3]
    for y in range(H):
        pygame.draw.line(bg, [int(top[i] + (bottom[i] - top[i]) * y / H) for i in range(3)], (0, y), (W, y))
    for _ in range(26):  # soft bubbles
        r = random.randint(10, 40)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 70), (r, r), r)
        bg.blit(s, (random.randint(0, W), random.randint(0, H)))
    return bg

def text(surf, msg, f, color, center):
    img = f.render(msg, True, color)
    surf.blit(img, img.get_rect(center=center))

def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)

class Paddle:
    w, h = 110, 18

    def __init__(self):
        self.rect = pygame.Rect(W // 2 - self.w // 2, H - 50, self.w, self.h)

    def update(self, keys, mouse_moved):
        if mouse_moved:
            self.rect.centerx = pygame.mouse.get_pos()[0]
        self.rect.x += 9 * (bool(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - bool(keys[pygame.K_LEFT] or keys[pygame.K_a]))
        self.rect.clamp_ip(screen.get_rect())

    def draw(self, surf):
        r, (x, y) = self.rect, self.rect.center
        pygame.draw.rect(surf, (190, 170, 220), r.move(0, 4), border_radius=9)
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=9)
        pygame.draw.rect(surf, INK, r, 3, border_radius=9)
        for dx in (-14, 14):  # tiny eyes and cheeks
            pygame.draw.circle(surf, INK, (x + dx, y), 3)
            pygame.draw.circle(surf, (255, 170, 190), (x + 2 * dx, y + 3), 3)

class Ball:
    r = 11

    def __init__(self, pos=None, vel=None, mood=None):
        self.stuck, self.off = vel is None, 0  # off: x distance from paddle centre while stuck
        self.pos = pos or pygame.Vector2(W // 2, H - 80)
        self.vel = vel or pygame.Vector2(0, 0)
        self.mood, self.mood_t = mood, 100 if mood else 0
        self.trail = []

    def launch(self, speed):
        if self.stuck:
            self.stuck = False
            self.vel = pygame.Vector2(self.off / 60 or random.choice((-1, 1)) * 0.4, -1).normalize() * speed

    def draw(self, surf):
        for i, p in enumerate(self.trail):
            s = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 150, 180, 15 + i * 8), (self.r, self.r), max(2, self.r - 8 + i))
            surf.blit(s, (p[0] - self.r, p[1] - self.r))
        c = (x, y) = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, (255, 143, 171), c, self.r)
        pygame.draw.circle(surf, INK, c, self.r, 3)
        m = self.mood if self.mood_t else ("wow" if self.vel.y > 4 and y > H - 150 else None)
        pygame.draw.circle(surf, INK, (x + 4, y - 2), 3 if m == "wow" else 2)
        if m == "wink":
            pygame.draw.line(surf, INK, (x - 6, y - 2), (x - 2, y - 2), 2)
        else:
            pygame.draw.circle(surf, INK, (x - 4, y - 2), 3 if m == "wow" else 2)
        if m == "wow":
            pygame.draw.circle(surf, INK, (x, y + 5), 3, 2)
        elif m == "cry":
            pygame.draw.arc(surf, INK, (x - 4, y + 3, 8, 6), 0, math.pi, 2)
            pygame.draw.circle(surf, (120, 190, 255), (x - 5, y + 3), 2)
        else:
            pygame.draw.arc(surf, INK, (x - 4, y - 1, 8, 6), math.pi, 2 * math.pi, 2)

class Particle:
    def __init__(self, pos, color):
        a = random.uniform(0, 2 * math.pi)
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(math.cos(a), math.sin(a)) * random.uniform(1, 4)
        self.life, self.color, self.size = random.randint(25, 45), color, random.randint(3, 6)

    def update(self):
        self.pos += self.vel
        self.vel.y += 0.15
        self.life -= 1

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, self.pos, max(1, int(self.size * self.life / 40)))

class Pop:  # bouncing combo message, shares the Particle interface
    def __init__(self, pos, msg):
        self.pos, self.msg, self.life = pygame.Vector2(pos), msg, 50

    def update(self):
        self.pos.y -= 1.2
        self.life -= 1

    def draw(self, surf):
        text(surf, self.msg, font, (255, 105, 140), (self.pos.x, self.pos.y - abs(math.sin(self.life * 0.3)) * 10))

class Item:
    def __init__(self, pos):
        self.kind = random.choice("WMSHGPN")
        self.rect = pygame.Rect(pos[0] - 17, pos[1] - 12, 34, 24)

    def draw(self, surf):
        c = ITEM_COLORS[self.kind]
        pygame.draw.rect(surf, shade(c, 0.8), self.rect.move(0, 3), border_radius=12)
        pygame.draw.rect(surf, c, self.rect, border_radius=12)
        pygame.draw.rect(surf, INK, self.rect, 2, border_radius=12)
        text(surf, self.kind, small, INK, self.rect.center)

def make_bricks(level):  # brick = (rect, color, is_bomb)
    bricks = []
    start_x = (W - (COLS * BRICK_W + (COLS - 1) * GAP)) // 2
    for row in range(ROWS):
        for col in range(COLS):
            if level % 2 == 0 and (row + col) % 2:  # checker pattern on even levels
                continue
            rect = pygame.Rect(start_x + col * (BRICK_W + GAP), TOP + row * (BRICK_H + GAP), BRICK_W, BRICK_H)
            bricks.append((rect, PALETTE[row % len(PALETTE)], random.random() < 0.08))
    return bricks

def draw_brick(surf, rect, color, bomb):
    pygame.draw.rect(surf, shade(color, 0.8), rect.move(0, 3), border_radius=10)
    pygame.draw.rect(surf, color, rect, border_radius=10)
    pygame.draw.rect(surf, shade(color, 1.12), (rect.x + 6, rect.y + 4, rect.w - 12, 6), border_radius=3)
    if bomb:  # star mark
        pts = [(rect.centerx + (9, 4)[i % 2] * math.sin(i * math.pi / 5),
                rect.centery - (9, 4)[i % 2] * math.cos(i * math.pi / 5)) for i in range(10)]
        pygame.draw.polygon(surf, (255, 255, 255), pts)
        pygame.draw.polygon(surf, INK, pts, 2)

def draw_heart(surf, x, y, filled):
    color = (255, 105, 140) if filled else (225, 215, 235)
    pygame.draw.circle(surf, color, (x - 5, y), 6)
    pygame.draw.circle(surf, color, (x + 5, y), 6)
    pygame.draw.polygon(surf, color, [(x - 11, y + 2), (x + 11, y + 2), (x, y + 15)])

def hit_brick(ball, bricks, ghost):  # ghost: pass through without bouncing
    for i, (rect, color, bomb) in enumerate(bricks):
        cx = max(rect.left, min(ball.pos.x, rect.right))
        cy = max(rect.top, min(ball.pos.y, rect.bottom))
        if (ball.pos.x - cx) ** 2 + (ball.pos.y - cy) ** 2 <= ball.r ** 2:
            if not ghost:
                horiz = abs(ball.pos.x - rect.centerx) / rect.w > abs(ball.pos.y - rect.centery) / rect.h
                ball.vel.update(-ball.vel.x if horiz else ball.vel.x, ball.vel.y if horiz else -ball.vel.y)
            return bricks.pop(i)
    return None

def main():
    bg = make_background(1)
    paddle, balls = Paddle(), [Ball()]
    bricks, particles, items = make_bricks(1), [], []
    score, lives, level, combo, state, shake = 0, 3, 1, 0, "play", 0
    t = dict.fromkeys(("WIDE", "SLOW", "GRAV", "GHOST", "MAGNET"), 0)  # item effect timers (frames)
    last_mouse = pygame.mouse.get_pos()
    while True:
        speed = (8.5 + level * 0.7) * (0.65 if t["SLOW"] else 1)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            go = e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE)
            if go and state == "play":
                for b in balls:
                    b.launch(speed)
            elif go:  # restart after game over / win
                return main()
        mouse = pygame.mouse.get_pos()
        paddle.update(pygame.key.get_pressed(), mouse != last_mouse)
        last_mouse = mouse
        t = {k: max(0, v - 1) for k, v in t.items()}
        paddle.rect.inflate_ip((170 if t["WIDE"] else 110) - paddle.rect.w, 0)
        if state == "play":
            for ball in balls[:]:
                if ball.stuck:
                    ball.pos.update(paddle.rect.centerx + ball.off, paddle.rect.top - ball.r - 2)
                    continue
                ball.mood_t = max(0, ball.mood_t - 1)
                if t["GRAV"]:  # bend the flight path upwards
                    ball.vel.y -= 0.12
                ball.vel.scale_to_length(speed)
                ball.trail = (ball.trail + [ball.pos.copy()])[-8:]
                ball.pos += ball.vel
                if ball.pos.x < ball.r or ball.pos.x > W - ball.r:
                    ball.vel.x *= -1
                    ball.pos.x = max(ball.r, min(W - ball.r, ball.pos.x))
                if ball.pos.y < ball.r:
                    ball.vel.y *= -1
                    ball.pos.y = ball.r
                if ball.vel.y > 0 and paddle.rect.inflate(ball.r, 0).collidepoint(ball.pos.x, ball.pos.y + ball.r):
                    rel = ball.pos.x - paddle.rect.centerx
                    ang = math.radians(-90 + max(-1, min(1, rel / (paddle.rect.w / 2))) * 60)
                    ball.vel = pygame.Vector2(math.cos(ang), math.sin(ang)) * speed
                    ball.pos.y = paddle.rect.top - ball.r
                    combo = 0
                    if t["MAGNET"]:
                        ball.stuck, ball.off = True, rel
                hit = hit_brick(ball, bricks, t["GHOST"] > 0)
                if hit:
                    near = [b for b in bricks if hit[2] and pygame.Vector2(b[0].center).distance_to(hit[0].center) < 80]
                    for b in near:  # bomb blast
                        bricks.remove(b)
                    for rect, color, _ in [hit] + near:
                        score += 10
                        particles += [Particle(rect.center, color) for _ in range(14)]
                    combo += 1
                    if combo in COMBO_MSG:
                        particles.append(Pop(ball.pos, COMBO_MSG[combo]))
                    if random.random() < 0.22:
                        items.append(Item(hit[0].center))
                    shake = 12 if near else 5
                    ball.mood, ball.mood_t = "wink", 20
                if ball.pos.y > H + 20:
                    balls.remove(ball)
            for it in items[:]:
                it.rect.y += 3
                if it.rect.colliderect(paddle.rect):
                    items.remove(it)
                    score += 50
                    if it.kind in ITEM_TIMERS:
                        t[ITEM_TIMERS[it.kind][0]] = ITEM_TIMERS[it.kind][1]
                    elif it.kind == "H":
                        lives = min(3, lives + 1)
                    else:  # multi-ball: split every flying ball in three
                        for b in [b for b in balls if not b.stuck]:
                            for deg in (-25, 25):
                                balls.append(Ball(b.pos.copy(), b.vel.rotate(deg)))
                elif it.rect.top > H:
                    items.remove(it)
            if not balls:
                lives, combo = lives - 1, 0
                balls, items, t = [Ball(mood="cry")], [], dict.fromkeys(t, 0)
                if lives <= 0:
                    state = "over"
            if not bricks:
                level += 1
                bg = make_background(level)
                bricks, balls, items, t = make_bricks(level), [Ball()], [], dict.fromkeys(t, 0)
                if level > 6:
                    state = "win"
        for p in particles:
            p.update()
        particles = [p for p in particles if p.life > 0]
        canvas = pygame.Surface((W, H))
        canvas.blit(bg, (0, 0))
        for rect, color, bomb in bricks:
            draw_brick(canvas, rect, color, bomb)
        paddle.draw(canvas)
        for obj in balls + items + particles:
            obj.draw(canvas)
        text(canvas, f"SCORE {score}", font, INK, (90, 36))
        text(canvas, f"LV {level}", font, INK, (W // 2, 36))
        for i in range(3):
            draw_heart(canvas, W - 100 + i * 34, 34, i < lives)
        for i, (name, left) in enumerate([kv for kv in t.items() if kv[1]]):
            text(canvas, f"{name} {left // 60 + 1}s", small, INK, (60 + i * 90, 66))
        if state == "play" and balls[0].stuck:
            text(canvas, "click or space to launch!", font, (160, 140, 190), (W // 2, H // 2 + 80))
        if state != "play":
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 255, 255, 170))
            canvas.blit(veil, (0, 0))
            text(canvas, "You Win!" if state == "win" else "Oh no...", big, INK, (W // 2, H // 2 - 30))
            text(canvas, f"score {score}  -  click to retry", font, INK, (W // 2, H // 2 + 30))
        off = (random.randint(-shake, shake), random.randint(-shake, shake)) if shake else (0, 0)
        shake = max(0, shake - 1)
        screen.blit(canvas, off)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
