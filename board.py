import pygame
from random import shuffle
from os.path import exists
import zlib
import hashlib

EVENTMOVEDOWN = pygame.USEREVENT + 1


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_ACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.ready = False
        self.active = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.ready = True
                elif event.key == pygame.K_BACKSPACE:
                    if len(self.text) > 16:
                        self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


class Board:
    # создание поля
    def __init__(self, width, height, screen):
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]
        # значения по умолчанию
        self.left = 10
        self.top = 10
        self.cell_size = 20
        self.score = 0
        self.level = 1
        self.time = 0.8
        self.lines = 0
        self.frequency = {'I': 0, 'O': 0, 'T': 0, 'S': 0, 'Z': 0, 'J': 0, 'L': 0}
        self.pool = ['I', 'O', 'T', 'S', 'Z', 'J', 'L'] * 5
        shuffle(self.pool)
        self.next_piece = None
        self.piece = self.new_piece()
        self.screen = screen

    def set_timer(self):
        time = (0.8 - ((self.level - 1) * 0.007)) ** (self.level - 1)
        pygame.time.set_timer(EVENTMOVEDOWN, int(time * 1000))

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def game_over(self):
        self.print_hiscore()
        quit(0)

    def render(self):
        for i in range(2, self.height):
            for j in range(self.width):
                if self.board[i][j] != 0:
                    pygame.draw.rect(screen, self.board[i][j], (j * self.cell_size + self.left,
                                                                (i - 2) * self.cell_size + self.top,
                                                                self.cell_size,
                                                                self.cell_size), 0)
                else:
                    pygame.draw.circle(self.screen, (255, 255, 255), (j * self.cell_size + self.left + self.cell_size // 2,
                                                                 (
                                                                             i - 2) * self.cell_size + self.top + self.cell_size // 2),
                                       1)
        y0 = self.piece.y
        for row in self.piece.matrix:
            x0 = self.piece.x
            for cell in row:
                if cell > 0:
                    pygame.draw.rect(self.screen, self.piece.color, (x0 * self.cell_size + self.left,
                                                                (y0 - 2) * self.cell_size + self.top,
                                                                self.cell_size,
                                                                self.cell_size), 0)
                x0 += 1
            y0 += 1
        self.draw_stat()

    def draw_stat(self):
        font = pygame.font.SysFont("Times new roman", 20)
        text = font.render(f"Level:{self.level}", True, (100, 255, 100))
        text_x = 230
        text_y = self.top + 10
        self.screen.blit(text, (text_x, text_y))
        text = font.render(f"Lines:{self.lines} ", True, (100, 255, 100))
        text_x = self.left + 220
        text_y = self.top + 60
        self.screen.blit(text, (text_x, text_y))
        text = font.render(f"Scores:{self.score} ", True, (100, 255, 100))
        text_x = self.left + 220
        text_y = self.top + 110
        self.screen.blit(text, (text_x, text_y))

    def create_piece(self, name):
        self.check_gameover()
        new_piece = None
        if name == 'I':
            new_piece = Piece_I((3, 0))
            new_piece.color = (0, 255, 255)
        elif name == 'O':
            new_piece = Piece_O((4, 0))
            new_piece.color = (255, 255, 0)
        elif name == 'T':
            new_piece = Piece_T((4, 0))
            new_piece.color = (148, 0, 211)
        elif name == 'S':
            new_piece = Piece_S((4, 0))
            new_piece.color = (0, 255, 0)
        elif name == 'Z':
            new_piece = Piece_Z((4, 0))
            new_piece.color = (255, 0, 0)
        elif name == 'J':
            new_piece = Piece_J((4, 0))
            new_piece.color = (0, 0, 255)
        elif name == 'L':
            new_piece = Piece_L((4, 0))
            new_piece.color = (255, 165, 0)
        return new_piece

    def new_piece(self):
        # Cyan I    0 255 255 
        # Yellow O  255 255 0 
        # Purple T  148 0 211
        # Green S   0 255 0
        # Red Z     255 0 0
        # Blue J    0 0 255
        # Orange L  255 165 0
        if self.next_piece is None:
            piece_type = self.pool.pop()
            self.frequency[piece_type] += 1
            self.piece = self.create_piece(piece_type)
            self.piece.move('down')
            if piece_type == "I":
                self.piece.move('down')
            piece_type = self.pool.pop()
            self.frequency[piece_type] += 1
            self.next_piece = self.create_piece(piece_type)
        else:
            self.piece = self.next_piece
            self.piece.move('down')
            if isinstance(self.piece, Piece_I):
                self.piece.move('down')
            if len(self.pool) > 30:
                piece_type = self.pool.pop()
                self.frequency[piece_type] += 1
                self.next_piece = self.create_piece(piece_type)
            else:
                piece_types = [x[0] for x in list(self.frequency.items()) if x[1] == min(self.frequency.values())]
                shuffle(piece_types)
                piece_type = self.pool.pop()
                self.frequency[piece_type] += 1
                self.next_piece = self.create_piece(piece_type)
                self.pool.append(piece_types[0])
                shuffle(self.pool)

    def check_gameover(self):
        for i in range(2):
            for j in range(4, 6):
                if self.board[i + 1][j] != 0:
                    self.game_over()

    def fix_piece(self):
        y0 = self.piece.y
        for row in self.piece.matrix:
            x0 = self.piece.x
            for cell in row:
                if cell > 0:
                    self.board[y0][x0] = self.piece.color
                x0 += 1
            y0 += 1

    def check_fills(self):
        i = self.height - 1
        amount = 0
        while i > 0:
            if self.board[i].count(0) == 0:
                del self.board[i]
                self.board.insert(0, [0] * self.width)
                amount += 1
            else:
                i -= 1
        self.lines += amount
        if amount == 1:
            self.score += 40 * (self.level + 1)
        elif amount == 2:
            self.score += 100 * (self.level + 1)
        elif amount == 3:
            self.score += 300 * (self.level + 1)
        elif amount == 4:
            self.score += 1200 * (self.level + 1)
        if self.lines < 200:
            self.level = self.lines // 10 + 1
            self.set_timer()

    def can_move(self, direction):
        if direction == 'left' and self.piece.x == 0:
            return False
        if direction == 'left' and self.piece.x > 0:
            for i in range(self.piece.height):
                for j in range(self.piece.width):
                    if self.piece.matrix[i][j] == 0:
                        continue
                    if self.board[self.piece.y + i][self.piece.x + j - 1] != 0:
                        return False
        if direction == 'right' and self.piece.x == self.width - self.piece.width:
            return False
        if direction == 'right' and self.piece.x < self.width - self.piece.width:
            for i in range(self.piece.height):
                for j in range(self.piece.width):
                    if self.board[self.piece.y + i][self.piece.x + j + 1] != 0:
                        return False
        if direction == 'down' and self.piece.y == self.height - self.piece.height:
            self.fix_piece()
            self.check_fills()
            self.new_piece()
            return False
        if direction == 'down':
            flag = False
            for i in range(self.piece.height):
                for j in range(self.piece.width):
                    # print(i, j, self.piece.matrix, self.piece)
                    if self.piece.matrix[i][j] == 0:
                        continue
                    if self.board[self.piece.y + i + 1][self.piece.x + j] != 0:
                        self.fix_piece()
                        self.check_fills()
                        self.new_piece()
                        flag = True
                        break
                if flag:
                    break
        return True

    def can_rotate(self, direction):
        return True

    def move_piece(self, direction):
        if self.can_move(direction):
            self.piece.move(direction)

    def rotate_piece(self, direction):
        if self.can_rotate(direction):
            self.piece.rotate(direction)

    def add_hash(self, text):
        hash_object = hashlib.sha1(text)
        hex_dig = hash_object.hexdigest().encode("utf-8")
        return hex_dig + text

    def check_hash(self, text):
        hex_dig = text[:40]
        text = text[40:]
        hash_object = hashlib.sha1(text)
        return hex_dig == hash_object.hexdigest().encode("utf-8")

    def print_hiscore(self):
        pygame.key.set_repeat(500)
        ib = InputBox(10, 120, 300, 60, text="Enter your name: Player")
        leaders = []
        while not ib.ready:
            self.screen.fill((0, 0, 0))
            ib.draw(self.screen)
            for event in pygame.event.get():
                ib.handle_event(event)
                ib.update()
            pygame.display.flip()
        _, self.name = ib.text.split(":")
        self.name = self.name.strip()
        if exists("hiscores.dat"):
            try:
                with open("hiscores.dat", mode="rb") as f:
                    data = f.read()
                decompressed_data = zlib.decompress(data)
                if self.check_hash(decompressed_data):
                    decompressed_data = decompressed_data[40:].decode("utf-8").strip()
                    lines = decompressed_data.split("\n")
                    for row in lines:
                        if ':' in row:
                            name, score = row.split(':')
                            score = int(score.strip())
                            leaders.append([name.strip(), score])
                    leaders.append([self.name, self.score])
                    leaders.sort(key=lambda x: -x[1])
                    with open("hiscores.dat", mode="wb") as f:
                        text = ''
                        for lead in leaders:
                            text += f'{lead[0]}:{lead[1]}\n'
                        text = self.add_hash(text[:-1].encode("utf-8"))
                        comp = zlib.compress(text, zlib.Z_BEST_COMPRESSION)
                        f.write(comp)
                else:
                    with open("hiscores.dat", mode="wb") as f:
                        text = f"{self.name}:{self.score}"
                        text = self.add_hash(text[:-1].encode("utf-8"))
                        leaders.append([self.name, self.score])
                        comp = zlib.compress(text.encode, zlib.Z_BEST_COMPRESSION)
                        f.write(comp)
            except Exception:
                print("Error: \n", Exception)
        else:
            try:
                with open("hiscores.dat", mode="wb") as f:
                    text = f"{self.name}:{self.score}".encode("utf-8")
                    text = self.add_hash(text)
                    leaders.append([self.name, self.score])
                    comp = zlib.compress(text, zlib.Z_BEST_COMPRESSION)
                    f.write(comp)
            except Exception:
                print("Error: \n", Exception)
        self.screen.fill((125, 125, 125))
        font = pygame.font.SysFont("Times new roman", 30)
        for i in range(len(leaders)):
            text = font.render(f"{i + 1}) {leaders[i][0]}:{leaders[i][1]}", True, (100, 255, 100))
            self.screen.blit(text, (40, 10 + i * 35))
        text = font.render("Press any key to exit", True, (100, 255, 100))
        self.screen.blit(text, (40, 10 + len(leaders) * 35))
        pygame.display.flip()
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN:
                    run = False


class Piece:
    def __init__(self, position):
        self.x = position[0]
        self.y = position[1]
        self.width = 1
        self.height = 1
        self.color = (255, 255, 255)

    def move(self, direction):
        if direction == "left":
            self.x -= 1
        elif direction == "right":
            self.x += 1
        elif direction == "down":
            self.y += 1

    def get_position(self):
        return self.x, self.y


class Piece_O(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[1, 1], [1, 1]]
        self.width = 2
        self.height = 2

    def rotate(self, direction):
        pass


class Piece_I(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[1, 1, 1, 1]]
        self.width = 4
        self.height = 1
        self.state = 0

    def rotate(self, direction):
        if self.state == 0:
            self.matrix = [[1], [1], [1], [1]]
            self.width = 1
            self.height = 4
            self.state = 1
            self.x += 1
            self.y -= 1
        else:
            self.matrix = [[1, 1, 1, 1]]
            self.width = 4
            self.height = 1
            self.state = 0
            self.x -= 1
            self.y += 1


class Piece_T(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[0, 1, 0], [1, 1, 1]]
        self.width = 3
        self.height = 2
        self.state = 0

    def rotate(self, direction):
        if direction == 'right':
            self.state = (self.state + 1) % 4
        else:
            self.state = (self.state + 3) % 4
        if self.state == 0:
            self.matrix = [[0, 1, 0], [1, 1, 1]]
            self.width = 3
            self.height = 2
        elif self.state == 1:
            self.matrix = [[1, 0], [1, 1], [1, 0]]
            self.width = 2
            self.height = 3
            self.x += 1
        elif self.state == 2:
            self.matrix = [[1, 1, 1], [0, 1, 0]]
            self.width = 3
            self.height = 2
            self.x -= 1
            self.y += 1
        elif self.state == 3:
            self.matrix = [[0, 1], [1, 1], [0, 1]]
            self.width = 2
            self.height = 3
            self.y -= 1


class Piece_L(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[0, 0, 1], [1, 1, 1]]
        self.width = 3
        self.height = 2
        self.state = 0

    def rotate(self, direction):
        if direction == 'right':
            self.state = (self.state + 1) % 4
        else:
            self.state = (self.state + 3) % 4
        if self.state == 0:
            self.matrix = [[0, 0, 1], [1, 1, 1]]
            self.width = 3
            self.height = 2
        elif self.state == 1:
            self.matrix = [[1, 0], [1, 0], [1, 1]]
            self.width = 2
            self.height = 3
            self.x += 1
        elif self.state == 2:
            self.matrix = [[1, 1, 1], [1, 0, 0]]
            self.width = 3
            self.height = 2
        elif self.state == 3:
            self.matrix = [[1, 1], [0, 1], [0, 1]]
            self.width = 2
            self.height = 3
            self.x -= 1


class Piece_J(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[1, 0, 0], [1, 1, 1]]
        self.width = 3
        self.height = 2
        self.state = 0

    def rotate(self, direction):
        if direction == 'right':
            self.state = (self.state + 1) % 4
        else:
            self.state = (self.state + 3) % 4
        if self.state == 0:
            self.matrix = [[1, 0, 0], [1, 1, 1]]
            self.width = 3
            self.height = 2
        elif self.state == 1:
            self.matrix = [[1, 1], [1, 0], [1, 0]]
            self.width = 2
            self.height = 3
            self.x += 1
        elif self.state == 2:
            self.matrix = [[1, 1, 1], [0, 0, 1]]
            self.width = 3
            self.height = 2
            self.x -= 1
        elif self.state == 3:
            self.matrix = [[0, 1], [0, 1], [1, 1]]
            self.width = 2
            self.height = 3


class Piece_S(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[0, 1, 1], [1, 1, 0]]
        self.width = 3
        self.height = 2
        self.state = 0

    def rotate(self, direction):
        if self.state == 0:
            self.matrix = [[1, 0], [1, 1], [0, 1]]
            self.width = 2
            self.height = 3
            self.state = 1
        else:
            self.matrix = [[0, 1, 1], [1, 1, 0]]
            self.width = 3
            self.height = 2
            self.state = 0


class Piece_Z(Piece):
    def __init__(self, position):
        super().__init__(position)
        self.matrix = [[1, 1, 0], [0, 1, 1]]
        self.width = 3
        self.height = 2
        self.state = 0

    def rotate(self, direction):
        if self.state == 0:
            self.matrix = [[0, 1], [1, 1], [1, 0]]
            self.width = 2
            self.height = 3
            self.state = 1
        else:
            self.matrix = [[1, 1, 0], [0, 1, 1]]
            self.width = 3
            self.height = 2
            self.state = 0


def pause_game(screen):
    pygame.draw.rect(screen, (125, 125, 125), (100, 80, 150, 220), 0, 3)
    font = pygame.font.SysFont("Times new roman", 40)
    text = font.render("Paused", True, (100, 255, 100))
    screen.blit(text, (115, 85))
    font = pygame.font.SysFont("Times new roman", 20)
    text = font.render("← Move left", True, (100, 255, 100))
    screen.blit(text, (118, 145))
    text = font.render("→ Move right", True, (100, 255, 100))
    screen.blit(text, (118, 185))
    text = font.render("↓   Drop(soft)", True, (100, 255, 100))
    screen.blit(text, (118, 225))
    text = font.render("Esc,F1 Pause", True, (100, 255, 100))
    screen.blit(text, (118, 265))
    pygame.display.flip()
    run = True
    pygame.key.set_repeat(500)
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_F1:
                    run = False
    pygame.key.set_repeat(100)
    screen.fill((0, 0, 0))
    return


if __name__ == '__main__':
    pygame.init()
    size = width, height = 350, 450
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Тетрис')
    board = Board(10, 22, screen)
    board.new_piece()
    running = True
    pygame.key.set_repeat(100)
    pygame.time.set_timer(EVENTMOVEDOWN, 800)
    FONT = pygame.font.SysFont("Arial", 30)
    COLOR_INACTIVE = pygame.Color('lightskyblue3')
    COLOR_ACTIVE = pygame.Color('dodgerblue2')
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    board.move_piece('left')
                elif event.key == pygame.K_RIGHT:
                    board.move_piece('right')
                elif event.key == pygame.K_DOWN:
                    board.move_piece('down')
                elif event.key == pygame.K_UP:
                    board.rotate_piece('right')
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_F1:
                    pause_game(screen)
            if event.type == EVENTMOVEDOWN:
                board.move_piece('down')
        screen.fill((0, 0, 0))
        board.render()
        pygame.display.flip()
    pygame.quit()
