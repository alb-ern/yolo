import threading
import random
import pygame
from main import run_detection

# Head tracking
latest = 0.0


def detection_thread():
    global latest
    for d, _ in run_detection():
        latest = d


threading.Thread(target=detection_thread, daemon=True).start()

# Game setup
pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)

# Game state
player_x = W // 2
obstacles = []  # [(x, z)] where z is distance
score = 0
speed = 5


def spawn_obstacle():
    lane = random.choice([-1, 0, 1])  # left, center, right
    obstacles.append([lane * 150, 800])  # x offset from center, z distance


def project(x, z):
    """Simple 3D projection - returns screen coords and scale."""
    if z <= 0:
        z = 1
    scale = 300 / z
    sx = W // 2 + x * scale
    sy = H // 2 + 100 * scale  # ground level
    return int(sx), int(sy), scale


# Initial obstacles
for i in range(5):
    obstacles.append([random.choice([-1, 0, 1]) * 150, 200 + i * 150])

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    # Update player position based on head direction
    target_x = W // 2 + latest * 250  # -1 to 1 maps to left-right
    player_x += (target_x - player_x) * 0.15  # smooth follow

    # Update obstacles
    for obs in obstacles:
        obs[1] -= speed  # move closer

    # Remove passed obstacles, add score
    new_obs = []
    for obs in obstacles:
        if obs[1] < 0:
            score += 1
        else:
            new_obs.append(obs)
    obstacles = new_obs

    # Spawn new obstacles
    if len(obstacles) < 5 or (obstacles and obstacles[-1][1] < 600):
        spawn_obstacle()

    # Collision check
    for obs in obstacles:
        if 10 < obs[1] < 80:  # close to player
            obs_screen_x = W // 2 + obs[0] * (300 / max(obs[1], 1))
            if abs(obs_screen_x - player_x) < 60:
                print(f"Game Over! Score: {score}")
                # running = False

    # Draw
    screen.fill((20, 20, 40))  # dark sky

    # Ground
    pygame.draw.polygon(screen, (40, 80, 40), [(0, H), (W, H), (W // 2 + 200, H // 2), (W // 2 - 200, H // 2)])

    # Road
    pygame.draw.polygon(screen, (60, 60, 60), [(W // 2 - 300, H), (W // 2 + 300, H), (W // 2 + 50, H // 2), (W // 2 - 50, H // 2)])

    # Obstacles (sorted by z for proper layering)
    for obs in sorted(obstacles, key=lambda o: -o[1]):
        sx, sy, scale = project(obs[0], obs[1])
        size = int(40 * scale)
        if size > 2:
            pygame.draw.rect(screen, (200, 50, 50), (sx - size // 2, sy - size, size, size))

    # Player
    px = int(player_x)
    pygame.draw.polygon(screen, (50, 150, 255), [
        (px, H - 20),
        (px - 30, H - 60),
        (px + 30, H - 60)
    ])

    # UI
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (20, 20))
    screen.blit(font.render(f"Dir: {latest:.2f}", True, (200, 200, 200)), (20, 60))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
