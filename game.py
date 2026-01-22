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
pygame.display.set_caption('BBF Avoider')
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)
entity_img = pygame.image.load("entity.png").convert_alpha()

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

game_over = False
big_font = pygame.font.Font(None, 72)


def reset_game():
    global obstacles, score, world_offset, game_over
    obstacles = [[random.choice((-1, 1)) * LANE_WIDTH, 200 + i * OBS_GAP] for i in range(5)]
    score = 0
    world_offset = 0
    game_over = False


# === MAIN LOOP ===
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.MOUSEBUTTONDOWN and game_over:
            # check restart button click
            mx, my = e.pos
            if W // 2 - 80 < mx < W // 2 + 80 and H // 2 + 40 < my < H // 2 + 90:
                reset_game()
        if e.type == pygame.KEYDOWN and game_over:
            reset_game()

    if game_over:
        # draw game over screen
        screen.fill((20, 20, 40))

        go_text = big_font.render("AI SLOP", True, (255, 50, 50))
        screen.blit(go_text, (W // 2 - go_text.get_width() // 2, H // 2 - 80))

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (W // 2 - score_text.get_width() // 2, H // 2 - 20))

        # restart button
        pygame.draw.rect(screen, (50, 150, 50), (W // 2 - 80, H // 2 + 40, 160, 50))
        restart_text = font.render("RESTART", True, (255, 255, 255))
        screen.blit(restart_text, (W // 2 - restart_text.get_width() // 2, H // 2 + 50))

        pygame.display.flip()
        clock.tick(60)
        continue

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

    # collision (only when visually touching - obstacle half-width)
    for obs in obstacles:
        if 0 < obs[1] < 20 and abs(obs[0] + world_offset) < LANE_WIDTH // 2:
            game_over = True

    # === DRAW ===
    screen.fill((20, 20, 40))
    pygame.draw.circle(screen,(100,30,20),(W/2,H/2),100)

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
            scaled = pygame.transform.scale(entity_img, (size, size))
            screen.blit(scaled, (sx - size // 2, sy - size))

    # ui
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
