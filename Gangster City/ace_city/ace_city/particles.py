import pygame


class Particle:
    def __init__(self, pos, vel, color, lifetime, size=3):
        self.pos = list(pos)
        self.vel = list(vel)
        self.color = color
        self.lifetime = lifetime
        self.size = size

    def update(self, dt):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.vel[0] *= 0.95
        self.vel[1] *= 0.95
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surf, cam):
        if self.lifetime <= 0:
            return
        pygame.draw.circle(surf, self.color, (int(self.pos[0] - cam[0]), int(self.pos[1] - cam[1])), max(1, int(self.size)))


class DamageNumber:
    def __init__(self, pos, text, color):
        self.pos = list(pos)
        self.text = str(text)
        self.color = color
        self.life = 1.0
        self.offset = 0

    def update(self, dt):
        self.life -= dt
        self.offset += dt * 50
        return self.life > 0

    def draw(self, surf, cam, font):
        text = font.render(self.text, True, self.color)
        x = int(self.pos[0] - cam[0] - text.get_width() // 2)
        y = int(self.pos[1] - cam[1] - self.offset)
        surf.blit(text, (x, y))
