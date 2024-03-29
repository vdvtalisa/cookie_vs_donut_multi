import pygame
from grid import Grid
import threading
import os
import socket

# window always appears in same place relative to upper-left corner
os.environ['SDL_VIDEO_WINDOW_POS'] = '400, 100'

# create playing surface
surface = pygame.display.set_mode((600, 600))
pygame.display.set_caption('Cookie vs. Donut')


# create a thread instance and tell it to start
# daemon threads = backgrounds tasks, okay to kill once other non-daemon threads have exited
def create_thread(target):
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()


HOST = '192.168.1.28'  # standard loopback interface address (localhost), '' or socket.gethostname()
# only processes on the host can connect to server, empty string = connections on all available IPv4 interfaces
PORT = 5555  # Port to listen on (non-privileged are > 1023)
connection_established = False
conn, addr = None, None

# 1: create socket object 2: arguments = address family(ipv4) & socket type(tcp)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # associate socket with specific network interface and port number
    sock.bind((HOST, PORT))
except socket.error as e:
    str(e)

# listen for connections, opens up the port
# number = number of clients able to connect (starts at 0?)
sock.listen(2)


def receive_data():
    # infinite while loop: don't receive data in closed connection, always check if new data coming in
    while True:
        # block main thread, amount of bytes it can receive + decode byte string to regular string
        global turn
        data = conn.recv(1024).decode()
        data = data.split('-')
        x, y = int(data[0]), int(data[1])  # receive x and y as integer from data list
        if data[2] == "yourturn":
            turn = True
        if data[3] == 'False':
            grid.game_over = True  # when playing is false, game is over
        if grid.get_cell_value(x, y) == 0:
            # don't use current_player variable, pass player so client and server blit the same image
            grid.set_cell_value(x, y, "Donut")
        print(data)


def waiting_for_connection():
    global connection_established, conn, addr
    conn, addr = sock.accept()  # until it receives a connection, the execution hangs on
    # when a client connects, accept() returns a new socket object representing the connection and a tuple holding
    # the address of the client
    print('Client is connected!')
    connection_established = True
    receive_data()


# create a thread for waiting for connection because it has to wait for external events
create_thread(waiting_for_connection)

# import grid object

grid = Grid()

# set game running to true
game_still_going = True

current_player = "Cookie"
turn = True
playing = "True"

# execute while loop while game running, game stops running when player quits
while game_still_going:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_still_going = False
        if event.type == pygame.MOUSEBUTTONDOWN and connection_established:
            # index indicates which mouse button is being pressed ([0] = left, [1] = middle, [2] = right)
            if pygame.mouse.get_pressed()[0]:
                if turn and not grid.game_over:
                    pos = pygame.mouse.get_pos()
                    # using integer division (//), we will get the integer coords of [0-2, 0-2]
                    cellX, cellY = pos[0] // 200, pos[1] // 200
                    # convert screen coords into cell coords
                    # each cell is 200x200 rectangle so divide by 200 (always divide by dimensions cell)
                    grid.get_mouse(cellX, cellY, current_player)
                    if grid.game_over:
                        playing = False
                    # communicate position with formatted string, encode to make it a byte string
                    # because you can't send regular strings through tcp network
                    send_data = f'{cellX}-{cellY}-{"yourturn"}-{playing}'.encode()
                    # connection object created when client connected
                    conn.send(send_data)
                    # flip player
                    # use switch_player variable to make sure that we don't switch when clicking on non-empty cell
                    turn = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and grid.game_over:
                grid.clear_grid()
                grid.game_over = False

                # grid.print_grid()  # print grid row by row for debugging purposes

    # fill surface with black colour
    surface.fill((0, 0, 0))

    # invoke draw method from grid object onto surface
    grid.draw(surface)

    pygame.display.flip()
