import os
import random

import pygame
import neat

pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
FLOOR_Y = 730
BIRD_X = 230
BG_VEL = 5
DRAW_LINES = True
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", f"bird{i+1}.png")))
    for i in range(3)
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

# TODO no globals
gen = 0


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


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    win.blit(BG_IMG, (0, 0))
    base.draw(win)
    for pipe in pipes:
        pipe.draw(win)
    for bird in birds:
        if DRAW_LINES:
            try:
                pygame.draw.line(
                    win,
                    (255, 0, 0),
                    (
                        bird.x + bird.img.get_width() / 2,
                        bird.y + bird.img.get_height() / 2,
                    ),
                    (
                        pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2,
                        pipes[pipe_ind].height,
                    ),
                    5,
                )
                pygame.draw.line(
                    win,
                    (255, 0, 0),
                    (
                        bird.x + bird.img.get_width() / 2,
                        bird.y + bird.img.get_height() / 2,
                    ),
                    (
                        pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,
                        pipes[pipe_ind].bottom,
                    ),
                    5,
                )
            except:
                pass
        bird.draw(win)

    score_label = STAT_FONT.render(f"Score: {score}", 1, (255, 255, 255))
    gen_label = STAT_FONT.render(f"Gen: {gen}", 1, (255, 255, 255))
    alive_label = STAT_FONT.render(f"Alive: {len(birds)}", 1, (255, 255, 255))

    win.blit(score_label, (WIN_WIDTH - 10 - score_label.get_width(), 10))
    win.blit(gen_label, (10, 10))
    win.blit(alive_label, (10, 80))

    pygame.display.update()


def eval_genomes(genomes, config):
    global gen
    # TODO make list with tuple of the 3 vals instaed of 3 lists
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird())
        g.fitness = 0
        ge.append(g)

    base = Base(FLOOR_Y)
    pipes = [Pipe()]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and BIRD_X > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            gen += 1
            break

        for i, bird in enumerate(birds):
            bird.move()
            ge[i].fitness += 0.1

            output = nets[i].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )
            if output[0] >= 0.5:
                bird.jump()

        add_pipe = False
        rem = False
        for pipe in pipes:
            for i, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[i].fitness -= 1
                    # FIXME removing while iterating
                    birds.pop(i)
                    nets.pop(i)
                    ge.pop(i)

            if not pipe.passed and pipe.x < BIRD_X:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem = True

            pipe.move()

        if rem:
            del pipes[0]

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe())

        for i, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= FLOOR_Y or bird.y < 0:
                # FIXME removing while iterating
                birds.pop(i)
                nets.pop(i)
                ge.pop(i)

        if score >= 50:
            break

        base.move()
        draw_window(win, birds, pipes, base, score, gen, pipe_ind)


def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genomes, 50)
    print(f"\nBest genome:\n{winner}")


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
