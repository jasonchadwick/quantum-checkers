import numpy as np
from colorama import Fore, Style
import random

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def init_board(size):
    b0 = []
    for r in range(round(size/2) + 1, size):
        r_even = r % 2 == 0
        for c in range(size):
            c_even = c % 2 == 0
            if (r_even and c_even) or ((not r_even) and not c_even):
                board = np.zeros((size, size))
                board[r][c] = 1
                b0.append(board)
    b1 = []
    for r in range(int(size/2) - 1):
        r_even = r % 2 == 0
        for c in range(size):
            c_even = c % 2 == 0
            if (r_even and c_even) or ((not r_even) and not c_even):
                board = np.zeros((size, size))
                board[r][c] = 1
                b1.append(board)
    return [np.array(b0), np.array(b1)]

def expected(player_board, r, c):
    prob_no_piece = 1
    for piece in player_board:
        prob_no_piece *= 1-piece[r][c]
    return 1 - prob_no_piece

def expected_vals(board):
    size = len(board[0][0])
    expected_array = [np.zeros((size, size)), np.zeros((size, size))]
    for player,b in enumerate(board):    
        for r in range(size):
            for c in range(size):
                prob_no_piece = 1
                for piece in b:
                    prob_no_piece *= 1-piece[r][c]
                expected_array[player][r][c] = expected(b, r, c)
    return expected_array

def print_board(board):
    size = len(board[0][0])
    expected = expected_vals(board)
    print('')
    print('  ' + ''.join(['   ' + str(i) + '   ' for i in range(1,9)]))
    print('  ' + '-' * (7 * size))
    for r in range(size):
        for c in range(size):
            if c == 0:
                print(letters[r] + ' | ', end='')
            val = expected[0][r][c]
            if val == 0:
                print('     | ', end='')
            else:
                print(f'{Fore.GREEN}%.2f{Style.RESET_ALL} | ' % val, end='')
        print(letters[r])
        for c in range(size):
            if c == 0:
                print('  | ', end='')
            val = expected[1][r][c]
            if val == 0:
                print('     | ', end='')
            else:
                print(f'{Fore.RED}%.2f{Style.RESET_ALL} | ' % val, end='')
        print()
        print('  ' + '-' * (7 * size))
    print('  ' + ''.join(['   ' + str(i) + '   ' for i in range(1,9)]))
    print()

def do_timestep(board, n=1, spreading=0.5):
    for step in range(n):
        init_bs = np.copy(board)
        size = len(board[0][0])
        for player,b in enumerate(board):
            for r in range(size):
                for c in range(size):
                    for piece_num,piece in enumerate(b):
                        initial_val = init_bs[player][piece_num][r][c]
                        if initial_val != 0:
                            possible_expansions = [(r-1,c-1), (r-1,c+1),
                                                   (r+1,c-1), (r+1,c+1)]
                            neighbor_spread = initial_val * spreading / 4
                            for e in possible_expansions:
                                if e[0] >= 0 and e[0] < size and e[1] >= 0 and e[1] < size:
                                    piece[r][c] -= neighbor_spread
                                    piece[e[0]][e[1]] += neighbor_spread

def score_piece(p):
    return min(1, sum(p.flatten()))

def score_board(b):
    s0 = round(sum(b[0].flatten()), 2)
    s1 = round(sum(b[1].flatten()), 2)
    print('_' * 60)
    print('Score:')
    print('  Green: ' + str(s0))
    print('  Red:   ' + str(s1))
    return [s0, s1]

def measure_board(board):
    # Right now, pieces can be measured on top of one another - should this be allowed?
    size = len(board[0][0])
    cart_prod = np.transpose([np.tile([0,1], len(board[0])), np.repeat(range(len(board[0])), len([0,1]))])
    np.random.shuffle(cart_prod)
    cart_prod = [tuple(x) for x in cart_prod]

    for player,piece in cart_prod:
        prob_no_piece = 1 - score_piece(board[player][piece])
        if prob_no_piece < 0:
            print('WTF')
            print(prob_no_piece)
        reshape = np.append(board[player][piece].reshape(size*size), prob_no_piece)
        location = np.random.choice(range(len(reshape)), p=reshape)
        location_filled = np.array([int(x == location) for x in range(size*size)])
        board[player][piece] = location_filled.reshape(size,size)
        #print(board[player][piece])
    return board

def inspect_board(board, player, piece):
    npieces = len(board[0])
    size = len(board[0][0])
    displayboard = [np.zeros((npieces, size, size)), np.zeros((npieces, size, size))]
    displayboard[player][piece] = board[player][piece]
    print_board(displayboard)
    input('Press enter to go back to full board')
    print_board(board)

def player_move(board, player):
    valid_move = False
    while not valid_move:
        if player == 0:
            print(f'{Fore.GREEN}Player ' + str(player) + f'\'s turn.{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Player ' + str(player) + f'\'s turn.{Style.RESET_ALL}')

        print('Move format ex: \"a1 b3\" jumps from A1 to B3')
        print('Type \"i 6\" to inspect your 6th piece')
        move1 = input('Input move (p to pass, m to measure, i to inspect): ')
        
        if move1 == 'p':
            print('Player ' + str(player) + ' passed.')
            return
        elif move1 == 'm':
            board = measure_board(board)
            print('Player ' + str(player) + ' has measured the board! ')
            return
        elif move1[0] == 'i'[0]:
            inspect_board(board, player, int(move1[2]))
            continue
        r1 = ord(move1[0]) - 97
        c1 = int(move1[1]) - 1

        r2 = ord(move1[3]) - 97
        c2 = int(move1[4]) - 1

        attempted_jump = (((player == 0 and r1 - r2 == 2) 
                        or (player == 1 and r2 - r1 == 2)) 
                      and abs(c1 - c2) == 2)
        attempted_move = (((player == 0 and r1 - r2 == 1) 
                        or (player == 1 and r2 - r1 == 1)) 
                      and abs(c1 - c2) == 1)

        valid_move = attempted_jump or attempted_move

        opponent = 1 - player

        b = board[player]
        b_x = board[opponent]

        for p in b:
            src = p[r1][c1]
            dst = p[r2][c2]
            dst_sum = expected(b, r2, c2)
            dst_x = expected(b_x, r2, c2)

            if attempted_move:
                prob_no_move = dst_sum + dst_x
                p[r2][c2] = (1 - prob_no_move) * src + dst
                p[r1][c1] = prob_no_move * src
            
            elif attempted_jump:
                jmp = [int((r1 + r2) / 2), int((c1 + c2) / 2)]
                prob_jump = expected(b_x,jmp[0],jmp[1]) * (1 - (dst_sum + dst_x))
                print(prob_jump)
                p[r2][c2] = prob_jump * src + dst
                p[r1][c1] = (1-prob_jump) * src
                print(p[r1][c1])
                for p_x in b_x:
                    p_x[jmp[0]][jmp[1]] = (1-prob_jump) * p_x[jmp[0]][jmp[1]]


def play(size=8, spreading=0.1):
    playing = True
    b = init_board(size)

    def win(winner):
        print('\n\n')
        print('Player ' + str(winner) + ' wins!!!')
        play_again = input('Play again? y/n')
        if play_again != 'y':
            playing = False

    score_board(b)
    while playing:
        do_timestep(b, spreading=spreading)
        print_board(b)
        player_move(b, 0)
        score_board(b)
        print_board(b)
        player_move(b,1)
        score = score_board(b)
        if (score[0] < 1):
            win(1)
        elif (score[1] < 1):
            win(0)
    return

#b=init_board(8)
#score_board(b)
#do_timestep(b, spreading=0.1)
#print_board(b)

play()