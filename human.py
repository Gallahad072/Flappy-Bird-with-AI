import os
import random

import pygame

pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
FLOOR_Y = 730
BIRD_X = 230
BG_VEL = 5
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", f"bird{i+1}.png")))
    for i in range(3)
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    BIRD_Y = 350

    def __init__(self) -> None:
        self.x = BIRD_X
        self.y = self.BIRD_Y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img_frame = 0
        self.img = self.IMGS[self.img_frame]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        if self.img_count == self.ANIMATION_TIME:
            self.img_frame = (self.img_frame + 1) % 4
            self.img = self.IMGS[[0, 1, 2, 1][self.img_frame]]
            self.img_count = 0
        else:
            self.img_count += 1

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center
        )
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    DISPLACEMENT = 600
    GAP = 200

    def __init__(self) -> None:
        self.x = self.DISPLACEMENT
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= BG_VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y) -> None:
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= BG_VEL
        self.x2 -= BG_VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        elif self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, bird, pipes, base, score, high_score):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    base.draw(win)
    bird.draw(win)

    h_score_label = STAT_FONT.render(f"High Score: {high_score}", 1, (255, 255, 255))
    score_label = STAT_FONT.render(f"Score: {score}", 1, (255, 255, 255))
    win.blit(h_score_label, (WIN_WIDTH - 10 - h_score_label.get_width(), 10))
    win.blit(score_label, (WIN_WIDTH - 10 - score_label.get_width(), 70))

    pygame.display.update()


def game():
    base = Base(FLOOR_Y)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    high_score = 0
    playing = False

    score = 0
    bird = Bird()
    pipes = [Pipe()]

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bird.jump()
                playing = True

        if playing:
            bird.move()

            add_pipe = False
            for pipe in pipes:
                if pipe.collide(bird):
                    playing = False
                if not pipe.passed and pipe.x < BIRD_X:
                    pipe.passed = True
                    add_pipe = True
                pipe.move()

            if add_pipe:
                score += 1
                pipes.append(Pipe())

            if pipes[0].x + pipes[0].PIPE_TOP.get_width() < 0:
                del pipes[0]

            if bird.y + bird.img.get_height() >= FLOOR_Y or bird.y < 50:
                playing = False

            if not playing:
                score = 0
                bird = Bird()
                pipes = [Pipe()]

            if score > high_score:
                high_score = score

        base.move()
        draw_window(win, bird, pipes, base, score, high_score)


if __name__ == "__main__":
    game()
