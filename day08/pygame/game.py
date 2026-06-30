import pygame
import math
import random

pygame.init()
pygame.mixer.init()

# Load sound effects and background music
gunshot_sound = pygame.mixer.Sound("mixkit-game-gun-shot-1662.wav")
game_over_sound = pygame.mixer.Sound("game-over-arcade-6435.wav")
pygame.mixer.music.load("[FREE] DRAKE x TRAVIS SCOTT TYPE BEAT - INSIDE.wav")
music_volume = 0.3
pygame.mixer.music.set_volume(music_volume)
pygame.mixer.music.play(-1)  # Loop background music forever

# screen ki
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SHOOT THE ENEMY")

clock = pygame.time.Clock()
FPS = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
RED = (255, 0, 0)
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 215, 0)
BROWN = (139, 69, 19)
PINK = (255, 105, 180)  # Pink for Game Over background

font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont('Arial Black', 100, bold=True, italic=True)

# Cloud class
class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(20, 150)
        self.speed = random.uniform(0.5, 1.5)
        self.size = random.randint(50, 100)

    def move(self):
        self.x += self.speed
        if self.x - self.size > WIDTH:
            self.x = -self.size
            self.y = random.randint(20, 150)
            self.speed = random.uniform(0.5, 1.5)
            self.size = random.randint(50, 100)
#cloud ka shape
    def draw(self):
        pygame.draw.ellipse(screen, WHITE, (self.x, self.y, self.size, self.size//2))
        pygame.draw.ellipse(screen, WHITE, (self.x + self.size//3, self.y - self.size//4, self.size//2, self.size//2))
        pygame.draw.ellipse(screen, WHITE, (self.x + self.size//2, self.y, self.size, self.size//2))


clouds = [Cloud() for _ in range(5)]  # Create 5 clouds

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 60)
        self.radius = 20
        self.color = (0, 0, 128)
        self.speed = 2
        self.y_velocity = 0
        self.jump = False
        self.gravity = 0.8
        self.health = 100
        self.gun_length = 40
        self.gun_angle = 0.0
        self.using_keyboard_aim = False

    def move(self, keys):
        if keys[pygame.K_a] and self.pos.x - self.radius > 0:
            self.pos.x -= self.speed
        if keys[pygame.K_d] and self.pos.x + self.radius < WIDTH:
            self.pos.x += self.speed
        if self.jump:
            self.y_velocity += self.gravity
            self.pos.y += self.y_velocity
            if self.pos.y >= HEIGHT - 60:
                self.pos.y = HEIGHT - 60
                self.jump = False
                self.y_velocity = 0
        if keys[pygame.K_w] and not self.jump:
            self.jump = True
            self.y_velocity = -15

        # Aiming with arrow keys
        aim_x = 0
        aim_y = 0
        if keys[pygame.K_LEFT]:
            aim_x = -1
        if keys[pygame.K_RIGHT]:
            aim_x = 1
        if keys[pygame.K_UP]:
            aim_y = -1
        if keys[pygame.K_DOWN]:
            aim_y = 1

        if aim_x != 0 or aim_y != 0:
            self.gun_angle = math.atan2(aim_y, aim_x)
            self.using_keyboard_aim = True

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        face_radius = self.radius - 5
        pygame.draw.circle(screen, (255, 224, 189), (int(self.pos.x), int(self.pos.y) - 5), face_radius)
        pygame.draw.circle(screen, BLACK, (int(self.pos.x - face_radius // 3), int(self.pos.y) - 10), face_radius // 6)
        pygame.draw.circle(screen, BLACK, (int(self.pos.x + face_radius // 3), int(self.pos.y) - 10), face_radius // 6)
        pygame.draw.arc(screen, (150, 0, 0), (int(self.pos.x - face_radius // 2), int(self.pos.y), face_radius, face_radius // 2), math.pi, 0, 3)
        
        if not self.using_keyboard_aim:
            mouse_pos = pygame.mouse.get_pos()
            dx, dy = mouse_pos[0] - self.pos.x, mouse_pos[1] - self.pos.y
            self.gun_angle = math.atan2(dy, dx)
            
        self.draw_gun(self.gun_angle)

    def draw_gun(self, angle):
        end_x = self.pos.x + self.gun_length * math.cos(angle)
        end_y = self.pos.y + self.gun_length * math.sin(angle)
        pygame.draw.line(screen, (139, 69, 19), (self.pos.x, self.pos.y), (end_x, end_y), 8)

    def hit(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0

class Bird:
    def __init__(self):
        self.ground_level = HEIGHT - 60
        spawn_side = random.choice(['top', 'left', 'right'])
        if spawn_side == 'top':
            self.pos = pygame.Vector2(random.randint(0, WIDTH), -20)
        elif spawn_side == 'left':
            self.pos = pygame.Vector2(-20, random.randint(HEIGHT//2, HEIGHT-100))
        else:
            self.pos = pygame.Vector2(WIDTH + 20, random.randint(HEIGHT//2, HEIGHT-100))
        self.radius = 15
        self.color = RED
        self.speed = 3
        self.health = 30
        self.direction = 1 if self.pos.x < WIDTH // 2 else -1

    def move(self):
        self.pos.x += self.speed * self.direction
        self.pos.y += random.uniform(-0.5, 0.5)
        self.pos.y = max(40, min(HEIGHT - 100, self.pos.y))

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.line(screen, BLACK, (self.pos.x - 15, self.pos.y), (self.pos.x - 30, self.pos.y - 10), 3)
        pygame.draw.line(screen, BLACK, (self.pos.x - 15, self.pos.y), (self.pos.x - 30, self.pos.y + 10), 3)

    def hit(self, damage):
        self.health -= damage

class GroundEnemy:
    def __init__(self):
        self.ground_level = HEIGHT - 60
        self.pos = pygame.Vector2(WIDTH + 40, self.ground_level)
        self.radius = 15
        self.color = BROWN
        self.speed = 2.5
        self.health = 50
        self.direction = -1  # always move left

        self.arm_up = True
        self.arm_anim_counter = 0

    def move(self):
        self.pos.x += self.speed * self.direction
        self.arm_anim_counter += 1
        if self.arm_anim_counter > 15:
            self.arm_up = not self.arm_up
            self.arm_anim_counter = 0

    def draw(self):
        body_rect = pygame.Rect(0, 0, 20, 40)
        body_rect.center = (int(self.pos.x), int(self.pos.y) - 10)
        pygame.draw.rect(screen, self.color, body_rect)
        pygame.draw.circle(screen, (255, 224, 189), (int(self.pos.x), int(self.pos.y) - 35), 15)
        pygame.draw.circle(screen, BLACK, (int(self.pos.x - 6), int(self.pos.y) - 40), 4)
        pygame.draw.circle(screen, BLACK, (int(self.pos.x + 6), int(self.pos.y) - 40), 4)
        pygame.draw.line(screen, BLACK, (self.pos.x - 5, self.pos.y), (self.pos.x - 10, self.pos.y + 20), 5)
        pygame.draw.line(screen, BLACK, (self.pos.x + 5, self.pos.y), (self.pos.x + 10, self.pos.y + 20), 5)

        arm_y = self.pos.y - 15
        if self.arm_up:
            pygame.draw.line(screen, BLACK, (self.pos.x - 10, arm_y), (self.pos.x - 20, arm_y - 10), 5)
            pygame.draw.line(screen, BLACK, (self.pos.x + 10, arm_y), (self.pos.x + 20, arm_y - 10), 5)
        else:
            pygame.draw.line(screen, BLACK, (self.pos.x - 10, arm_y), (self.pos.x - 20, arm_y + 10), 5)
            pygame.draw.line(screen, BLACK, (self.pos.x + 10, arm_y), (self.pos.x + 20, arm_y + 10), 5)

    def hit(self, damage):
        self.health -= damage

class Bullet:
    def __init__(self, x, y, angle):
        self.pos = pygame.Vector2(x, y)
        self.speed = 20
        self.dir = pygame.Vector2(math.cos(angle), math.sin(angle))
        self.radius = 5

    def move(self):
        self.pos += self.dir * self.speed

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.pos.x), int(self.pos.y)), self.radius)

player = Player()
bullets = []
birds = []
ground_enemies = []
kills = 0
high_score = 0

spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(spawn_event, 1500)

font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont('Arial Black', 100, bold=True, italic=True)

paused = False
music_volume = 0.3

def draw_health_bar(x, y, health, max_health):
    ratio = health / max_health
    pygame.draw.rect(screen, RED, (x, y, 100, 10))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, 100 * ratio, 10))

# Start screen function
start_font = pygame.font.SysFont('Arial', 60, bold=True)
BLUE_BG = (0, 102, 204)  # Blue background for start screen

def start_screen():
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 5000:  # 5 seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.fill(BLUE_BG)
        start_text = start_font.render("Start the Game", True, WHITE)

        start_rect = start_text.get_rect(center=(WIDTH//2, HEIGHT//2))

        screen.blit(start_text, start_rect)

        pygame.display.flip()
        clock.tick(FPS)

start_screen()  # Show start screen for 5 seconds

# Clouds class & instances
class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(20, 150)
        self.speed = random.uniform(0.5, 1.5)
        self.size = random.randint(50, 100)

    def move(self):
        self.x += self.speed
        if self.x - self.size > WIDTH:
            self.x = -self.size
            self.y = random.randint(20, 150)
            self.speed = random.uniform(0.5, 1.5)
            self.size = random.randint(50, 100)

    def draw(self):
        pygame.draw.ellipse(screen, WHITE, (self.x, self.y, self.size, self.size//2))
        pygame.draw.ellipse(screen, WHITE, (self.x + self.size//3, self.y - self.size//4, self.size//2, self.size//2))
        pygame.draw.ellipse(screen, WHITE, (self.x + self.size//2, self.y, self.size, self.size//2))

clouds = [Cloud() for _ in range(5)]


while True:
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()

    # Move clouds and draw them
    for cloud in clouds:
        cloud.move()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.MOUSEMOTION:
            player.using_keyboard_aim = False
        if event.type == spawn_event and not paused:
            if random.random() < 0.6:
                birds.append(Bird())
            else:
                ground_enemies.append(GroundEnemy())

        if not paused:
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.using_keyboard_aim = False
                dx, dy = mouse_pos[0] - player.pos.x, mouse_pos[1] - player.pos.y
                angle = math.atan2(dy, dx)
                bullets.append(Bullet(player.pos.x + player.radius, player.pos.y, angle))
                gunshot_sound.play()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bullets.append(Bullet(player.pos.x + player.radius, player.pos.y, player.gun_angle))
                gunshot_sound.play()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_PAGEDOWN):
                    music_volume = max(0.0, music_volume - 0.1)
                    pygame.mixer.music.set_volume(music_volume)
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEUP):
                    music_volume = min(1.0, music_volume + 0.1)
                    pygame.mixer.music.set_volume(music_volume)

    keys = pygame.key.get_pressed()
    if not paused:
        player.move(keys)

    # Draw background, clouds, ground
    screen.fill(SKY_BLUE)
    for cloud in clouds:
        cloud.draw()
    pygame.draw.rect(screen, GREEN, (0, HEIGHT - 50, WIDTH, 50))

    if not paused:
        for bullet in bullets[:]:
            bullet.move()
            bullet.draw()
            if bullet.pos.x < 0 or bullet.pos.x > WIDTH or bullet.pos.y < 0 or bullet.pos.y > HEIGHT:
                bullets.remove(bullet)

        for bird in birds[:]:
            bird.move()
            bird.draw()
            bullet_hit = False
            for bullet in bullets[:]:
                if bullet.pos.distance_to(bird.pos) < bird.radius + bullet.radius:
                    if not bullet_hit:
                        bird.hit(30)
                        bullet_hit = True
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if bird.health <= 0:
                            birds.remove(bird)
                            kills += 1
                    if kills > high_score:
                        high_score = kills
                    break
            if bird.pos.distance_to(player.pos) < bird.radius + player.radius:
                player.hit(20)

        for enemy in ground_enemies[:]:
            enemy.move()
            enemy.draw()
            bullet_hit = False
            for bullet in bullets[:]:
                if bullet.pos.distance_to(enemy.pos) < enemy.radius + bullet.radius:
                    if not bullet_hit:
                        enemy.hit(25)
                        bullet_hit = True
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if enemy.health <= 0:
                            ground_enemies.remove(enemy)
                            kills += 1
                    if kills > high_score:
                        high_score = kills
                    break
            if enemy.pos.distance_to(player.pos) < enemy.radius + player.radius:
                player.hit(20)

    player.draw()

    draw_health_bar(10, 10, player.health, 100)
    kill_text = font.render(f"Killed: {kills}", True, BLACK)
    screen.blit(kill_text, (WIDTH - 180, 10))
    high_score_text = font.render(f"High Score: {high_score}", True, BLACK)
    screen.blit(high_score_text, (WIDTH - 180, 40))
    pause_text = font.render("Press P: Pause | [/] or PgUp/PgDn: Vol | Arrows: Aim | Space: Shoot", True, BLACK)
    screen.blit(pause_text, (10, HEIGHT - 40))

    if paused:
        pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill((0, 0, 0, 150))
        screen.blit(pause_overlay, (0, 0))
        paused_text = font.render("Paused", True, WHITE)
        screen.blit(paused_text, (WIDTH//2 - 50, HEIGHT//2 - 20))

    if player.health <= 0:
        game_over_sound.play()
        screen.fill(PINK)  # Pink background
        game_over_text = large_font.render("Game Over!!!", True, BLACK)  # Large aesthetic font
        text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(game_over_text, text_rect)
        pygame.display.flip()
        pygame.time.delay(3000)
        break

    pygame.display.flip()

pygame.quit()
