import pygame
from collor import ColorPicker

n = 10


def quit(cells):
    with open('res.h', 'w') as f:
        f.write('int cells[][] = { ')
        for row in cells:
            for cell in row:
                if cell:
                    f.write('\t{' + ', '.join(map(str, cell[:-1])) + '},\n')
                else:
                    f.write('\t{ 0, 0, 0 },\n')
        f.write('}')


def draw_cells(screen: pygame.Surface) -> None:
    w = screen.get_width()
    h = screen.get_height()
    for y in range(n + 1):
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (0, y * (w // n)),
            (w, y * (w // n))
        )
    for x in range(n + 1):
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (x * (w // n), 0),
            (x * (w // n), w)
        )


def color_cells(screen: pygame.Surface, cells):
    w = screen.get_width()
    h = screen.get_height()
    for y in range(n):
        for x in range(n):
            if not cells[y][x]:
                continue
            pygame.draw.rect(
                screen,
                cells[y][x],
                (x * (w // n), y * (w // n),
                 (w // n), (w // n))
            )


def main():
    pygame.init()

    screen = pygame.display.set_mode((500, 600))

    cp = ColorPicker(0, 500, 400, 60)

    cells = [[0 for _ in range(n)] for _ in range(n)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit(cells)
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                x = event.pos[0] // (screen.get_width() // n)
                y = event.pos[1] // (screen.get_width() // n)
                if x < 10 and y < 10:
                    cells[y][x] = cp.get_color()

        cp.update()

        screen.fill((0, 0, 0))

        draw_cells(screen)
        color_cells(screen, cells)

        cp.draw(screen)

        pygame.display.flip()


if __name__ == '__main__':
    main()
