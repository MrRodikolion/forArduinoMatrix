import pygame
import serial
from collor import ColorPicker
from time import sleep

n = 10


def quit(cells):
    with open('res.h', 'w') as f:
        f.write('int cells[100][3] = { ')
        c = 0
        for row in cells:
            if c % 2 != 0:
                roww = row[::-1]
            else:
                roww = row
            c += 1
            for cell in roww:
                if cell:
                    f.write('\t{' + ', '.join(map(str, cell[:-1])) + '},\n')
                else:
                    f.write('\t{ 0, 0, 0 },\n')
        f.write('};')


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


s = serial.Serial('COM3', 9600)


def send(cell_id: int, color=(0, 0, 0)):
    s.write(f'${str(cell_id)}_{color[0]}_{color[1]}_{color[2]};'.encode())


def clear():
    for y in range(10):
        for x in range(10):
            cell_id = y * 10
            if y % 2 == 0:
                cell_id += x
            else:
                cell_id += 9 - x
            send(cell_id)
            sleep(0.15)


def main():
    pygame.init()

    screen = pygame.display.set_mode((500, 600))

    cp = ColorPicker(0, 500, 400, 60)

    cells = [[0 for _ in range(n)] for _ in range(n)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clear()
                return
            if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
                if event.type == pygame.MOUSEBUTTONDOWN or any(event.buttons):
                    x = event.pos[0] // (screen.get_width() // n)
                    y = event.pos[1] // (screen.get_width() // n)
                    if x < 10 and y < 10:
                        cells[y][x] = cp.get_color()

                        cell_id = y * 10
                        if y % 2 == 0:
                            cell_id += x
                        else:
                            cell_id += 9 - x
                        send(cell_id, cells[y][x])
                        sleep(0.1)

        cp.update()

        screen.fill((0, 0, 0))

        color_cells(screen, cells)
        draw_cells(screen)

        cp.draw(screen)

        pygame.display.flip()


if __name__ == '__main__':
    main()
