import random
import pygame


class Anvil:
    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.width = 40
        self.height = 32
        self.x = random.randint(20, screen_width - self.width - 20)
        self.y = -self.height
        self.speed = random.uniform(4.5, 7.0)

    def update(self):
        self.y += self.speed

    def is_off_screen(self, screen_height):
        return self.y > screen_height + 10

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def render(self, surface):
        # Interpolate from normal grey at minimum speed to a warm tint at maximum speed.
        speed_ratio = (self.speed - 4.5) / (7.0 - 4.5)
        speed_ratio = max(0.0, min(1.0, speed_ratio))

        grey_top = (120, 120, 130)
        warm_top = (220, 100, 60)
        top_color = tuple(int(g + (w - g) * speed_ratio) for g, w in zip(grey_top, warm_top))

        grey_base = (80, 80, 90)
        warm_base = (150, 55, 45)
        base_color = tuple(int(g + (w - g) * speed_ratio) for g, w in zip(grey_base, warm_base))

        grey_outline = (200, 200, 210)
        warm_outline = (240, 170, 100)
        outline_color = tuple(int(g + (w - g) * speed_ratio) for g, w in zip(grey_outline, warm_outline))

        top_rect = pygame.Rect(int(self.x) + 4, int(self.y), self.width - 8, 14)
        pygame.draw.rect(surface, top_color, top_rect, border_radius=2)

        base_rect = pygame.Rect(int(self.x), int(self.y) + 14, self.width, 18)
        pygame.draw.rect(surface, base_color, base_rect, border_radius=3)
        pygame.draw.rect(surface, outline_color, base_rect, width=1, border_radius=3)
