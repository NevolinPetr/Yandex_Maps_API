import pygame


class Button:
    def __init__(self, text, x, y, h):
        font = pygame.font.Font(None, h)
        self.text = text
        self.txt_surface = font.render(text, True, (0, 0, 0))
        self.rect = pygame.Rect(x, y, self.txt_surface.get_width(), self.txt_surface.get_height())

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
