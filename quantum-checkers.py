import numpy as np
from colorama import Fore, Style
import random

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def init_board(size):
    b2 = np.zeros((size, size))
    for r in range(int(size/2) - 1):
        r_even = r % 2 == 0
        for c in range(size):
            c_even = c % 2 == 0
            if (r_even and c_even) or ((not r_even) and not c_even):
                b2[r][c] = 1
    b1 = np.zeros((size, size))
    for r in range(round(size/2) + 1, size):
        r_even = r % 2 == 0
        for c in range(size):
            c_even = c % 2 == 0
            if (r_even and c_even) or ((not r_even) and not c_even):
                b1[r][c] = 1
    return [b1, b2]

def print_board(board):
    size = len(board[0])
    print('')
    print('  ' + '-' * (7 * size))
    for r in range(size):
        for c in range(size):
            if c == 0:
                print(letters[r] + ' | ', end='')
            val = board[0][r][c]
            if val == 0:
                print('     | ', end='')
            else:
                print(f'{Fore.GREEN}%.2f{Style.RESET_ALL} | ' % val, end='')
        print()
        for c in range(size):
            if c == 0:
                print('  | ', end='')
            val = board[1][r][c]
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
        size = len(board[0])
        for i,b in enumerate(board):
            for r in range(size):
                for c in range(size):
                    initial_val = init_bs[i][r][c]
                    if initial_val != 0:
                        possible_expansions = [(r-1,c-1), (r-1,c+1),
                                               (r+1,c-1), (r+1,c+1)]
                        neighbor_spread = initial_val * spreading / 4
                        for e in possible_expansions:
                            if e[0] >= 0 and e[0] < size and e[1] >= 0 and e[1] < size:
                                b[r][c] -= neighbor_spread
                                b[e[0]][e[1]] += neighbor_spread

def measure(val0, val1):
    rolls = [1, 1]
    while(rolls[0] and rolls[1]):
        rolls[0] = int(random.random() < val0)
        rolls[1] = int(random.random() < val1)
    return rolls

def measure_board(board):
    size = len(board[0])
    for r in range(size):
        for c in range(size):
            rolls = measure(board[0][r][c], board[1][r][c])
            board[0][r][c] = rolls[0]
            board[1][r][c] = rolls[1]
    return board

def player_move(board, player):
    valid_move = False
    while not valid_move:
        if player == 0:
            print(f'{Fore.GREEN}Player ' + str(player) + f'\'s turn.{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Player ' + str(player) + f'\'s turn.{Style.RESET_ALL}')

        print('Move format ex: a1 b3 jumps from A1 to B3')
        move1 = input('Input move (p to pass, m to measure): ')
        
        if move1 == 'p':
            print('Player ' + str(player) + ' passed.')
            return
        elif move1 == 'm':
            measure_board(board)
            print('Player ' + str(player) + ' has measured the board! ')
            return
        r1 = ord(move1[0]) - 97
        c1 = int(move1[1]) - 1

        #move2 = input('Destination: ')
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
        b1 = board[opponent]

        src = b[r1][c1]
        src1 = b1[r1][c1]
        dst = b[r2][c2]
        dst1 = b1[r2][c2]

        if attempted_move:
            print('Move')
            prob_no_move = dst + dst1
            b[r2][c2] = (1 - prob_no_move) * src + dst
            b[r1][c1] = prob_no_move * src
        
        elif attempted_jump:
            print('Jump')
            jmp = [int((r1 + r2) / 2), int((c1 + c2) / 2)]
            prob_jump = b1[jmp[0]][jmp[1]] * (1 - (dst + dst1))
            b[r2][c2] = prob_jump * src + dst
            b[r1][c1] = (1-prob_jump) * src
            b1[jmp[0]][jmp[1]] = (1-prob_jump) * b1[jmp[0]][jmp[1]]

    #return board

def score_board(b):
    s0 = round(sum([sum(r) for r in b[0]]), 2)
    s1 = round(sum([sum(r) for r in b[1]]), 2)
    print('_' * 60)
    print('Score:')
    print('  Green: ' + str(s0))
    print('  Red:   ' + str(s1))
    return [s0, s1]

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

play()