import threading
import random
import pygame
from yolo import run_detection

# === CONFIG (tweak these) ===
LANE_WIDTH = 150      # distance between lanes
LANE_COUNT = 3        # number of lanes (-1, 0, 1)
ROAD_NEAR = 0        # road start z
ROAD_FAR = 800        # road end z (horizon)
OBS_SPAWN_Z = 800     # where obstacles spawn
OBS_GAP = 150         # distance between obstacles
OBS_SIZE = 155         # obstacle size
MOVE_SPEED = 3        # how fast obstacles approach
STEER_SPEED = 4       # head movement sensitivity
PROJ_SCALE = 80      # projection focal length

# === HEAD TRACKING ===
latest = 0.0


def detection_thread():
    global latest
    for d, _ in run_detection():
        latest = d


threading.Thread(target=detection_thread, daemon=True).start()

# === GAME SETUP ===
pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)

world_offset = 0
obstacles = []
score = 0


def project(x, z):
    """3D to 2D projection."""
    z = max(z, 1)
    scale = PROJ_SCALE / z
    return int(W // 2 + x * scale), int(H // 2 + 100 * scale), scale


def spawn():
    lane = random.randint(-(LANE_COUNT // 2), LANE_COUNT // 2)
    obstacles.append([lane * LANE_WIDTH, OBS_SPAWN_Z])


# initial obstacles
for i in range(5):
    obstacles.append([random.choice((-1, 1)) * LANE_WIDTH, 200 + i * OBS_GAP])

# === MAIN LOOP ===
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    # move world based on head
    world_offset -= latest * STEER_SPEED
    world_offset = max(-LANE_WIDTH, min(LANE_WIDTH, world_offset))

    # move obstacles closer
    for obs in obstacles:
        obs[1] -= MOVE_SPEED

    # remove passed, add score
    obstacles = [o for o in obstacles if o[1] > 0 or (score := score + 1) and False]

    # spawn new
    if len(obstacles) < 5 or obstacles[-1][1] < OBS_SPAWN_Z - OBS_GAP:
        spawn()

    # collision (player at center, obstacle hitbox = half lane each side)
    for obs in obstacles:
        if 10 < obs[1] < 80 and abs(obs[0] + world_offset) < LANE_WIDTH // 2 + 15:
            print(f"Game Over! Score: {score}")

    # === DRAW ===
    screen.fill((20, 20, 40))

    # road bounds
    road_w = LANE_WIDTH * (LANE_COUNT // 2 + 1)
    ground_w = road_w * 3

    # ground
    g = [(project(-ground_w + world_offset, ROAD_NEAR)[0], H),
         (project(ground_w + world_offset, ROAD_NEAR)[0], H),
         (project(ground_w + world_offset, ROAD_FAR)[0], project(0, ROAD_FAR)[1]),
         (project(-ground_w + world_offset, ROAD_FAR)[0], project(0, ROAD_FAR)[1])]
    pygame.draw.polygon(screen, (40, 80, 40), g)

    # road
    r = [(project(-road_w + world_offset, ROAD_NEAR)[0], project(0, ROAD_NEAR)[1]),
         (project(road_w + world_offset, ROAD_NEAR)[0], project(0, ROAD_NEAR)[1]),
         (project(road_w + world_offset, ROAD_FAR)[0], project(0, ROAD_FAR)[1]),
         (project(-road_w + world_offset, ROAD_FAR)[0], project(0, ROAD_FAR)[1])]
    pygame.draw.polygon(screen, (60, 60, 60), r)

    # obstacles (visual matches hitbox = LANE_WIDTH)
    for obs in sorted(obstacles, key=lambda o: -o[1]):
        sx, sy, scale = project(obs[0] + world_offset, obs[1])
        size = int(LANE_WIDTH * scale)
        if size > 2:
            pygame.draw.rect(screen, (200, 50, 50), (sx - size // 2, sy - size, size, size))

    # player
    pygame.draw.polygon(screen, (50, 150, 255), [(W // 2, H - 20), (W // 2 - 30, H - 60), (W // 2 + 30, H - 60)])

    # ui
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (20, 20))
    screen.blit(font.render(f"Dir: {latest:.2f}", True, (200, 200, 200)), (20, 60))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
