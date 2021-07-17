# Probabilistic checkers game - you can split your move between multiple possible moves

import numpy as np
from colorama import Fore, Style
import random
import copy

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def empty_board(size):
    return np.zeros((size,size), dtype='?, c8')

class InvalidMove(Exception):
    print('Invalid move.')
    pass

class PlayerState:
    def __init__(self, size):
        self.pieces = empty_board(size)
        self.score = 0
    
    def getval(self, r, c):
        return self.pieces[r][c][0]
    def getphase(self, r, c):
        return self.pieces[r][c][1]
    def getphasedval(self, r, c):
        return self.pieces[r][c][0] * (-1) ** self.pieces[r][c][1]

    def setval(self, r, c, val):
        self.pieces[r][c][0] = val
    def setphase(self, r, c, phase):
        self.pieces[r][c][1] = phase
    
    def move(self, r1, c1, r2, c2):
        val = self.getval(r1, c1)
        phase = self.getphase(r1, c1)
        self.setval(r1, c1, 0)
        self.setphase(r1, c1, 0)
        self.setval(r2, c2, val)
        self.setphase(r2, c2, phase)

    def delete(self, r, c):
        self.setval(r, c, 0)
        self.setphase(r, c, 0)

class State:
    def __init__(self, size):
        self.size = size
        self.player0 = PlayerState(size)
        self.player1 = PlayerState(size)
        self.prob = 1
        self.inactive = False

        for r in range(round(size/2) + 1, size):
            r_even = r % 2 == 0
            for c in range(size):
                c_even = c % 2 == 0
                if (r_even and c_even) or ((not r_even) and not c_even):
                    self.player0.setval(r,c,1)
                    self.player0.score += 1

        for r in range(int(size/2) - 1):
            r_even = r % 2 == 0
            for c in range(size):
                c_even = c % 2 == 0
                if (r_even and c_even) or ((not r_even) and not c_even):
                    self.player1.setval(r,c,1)
                    self.player1.score += 1
        
    def split(self, p_split, update_self=True):
        newstate = copy.deepcopy(self)
        if update_self:
            self.prob *= (1 - p_split)
        newstate.prob = self.prob * p_split
        return newstate
    
    def expected(self, player, r, c):
        if player == 0:
            return (self.player0.getval(r, c) * self.prob, self.player0.getphase(r, c) * self.prob)
        else:
            return (self.player1.getval(r, c) * self.prob, self.player1.getphase(r, c) * self.prob)

class GameState:
    def __init__(self, size):
        self.size = size
        self.states = [State(size)]
    
    def measure(self):
        probs = [s.prob for s in self.states]
        chosen_idx = np.random.choice(range(len(self.states)), p=probs)
        chosen_state = self.states[chosen_idx]
        chosen_state.prob = 1
        self.states = [chosen_state]
    
    def score(self):
        score0 = 0
        score1 = 0
        for s in self.states:
            score0 += s.player0.score * s.prob
            score1 += s.player1.score * s.prob
        s0 = round(score0, 2)
        s1 = round(score1, 2)
        print('_' * 60)
        print('Score:')
        print('  Green: ' + str(s0))
        print('  Red:   ' + str(s1))
        print('Number of possible boards: ' + str(len(self.states)))
        return [s0, s1]
    
    def expected_vals(self):
        size = self.size
        expected_array = [np.zeros((size, size)), np.zeros((size, size))]
        for r in range(self.size):
            for c in range(self.size):
                for state in self.states:
                    prob = state.prob
                    expected_array[0][r][c] += state.player0.getval(r,c) * prob
                    expected_array[1][r][c] += state.player1.getval(r,c) * prob
        return expected_array
    
    def split(self, state, p_split, update_self=True):
        self.states.append(state.split(p_split, update_self))
    
    def do_move(self, m, playeridx):
        if m[0] is None:
            for state in [s for s in self.states if (not s.inactive)]:
                self.split(state, m[1], False)
                self.states[-1].inactive = True
            return

        r1 = m[0]
        c1 = m[1]
        r2 = m[2]
        c2 = m[3]
        prob = m[4]

        attempted_jump = (((playeridx == 0 and r1 - r2 == 2) 
                        or (playeridx == 1 and r2 - r1 == 2)) 
                      and abs(c1 - c2) == 2)
        attempted_move = (((playeridx == 0 and r1 - r2 == 1) 
                        or (playeridx == 1 and r2 - r1 == 1)) 
                      and abs(c1 - c2) == 1)

        if not (attempted_jump or attempted_move):
            raise InvalidMove()

        for state in [s for s in self.states if (not s.inactive)]:
            if playeridx == 0:
                player = state.player0
                opponent = state.player1
            else:
                player = state.player1
                opponent = state.player0

            if attempted_move:
                src = player.getval(r1, c1)
                dst_p = player.getval(r2, c2)
                dst_o = opponent.getval(r2, c2)
                if src and not (dst_p or dst_o):
                    if prob != 1:
                        self.split(state, prob, False)
                        if playeridx == 0:
                            newplayer = self.states[-1].player0
                        else:
                            newplayer = self.states[-1].player1
                    else:
                        newplayer = player
                    newplayer.move(r1, c1, r2, c2)

                    self.states[-1].inactive = True
            elif attempted_jump:
                src = player.getval(r1, c1)
                dst_p = player.getval(r2, c2)
                dst_o = opponent.getval(r2, c2)
                r_mid = int((r1 + r2)/2)
                c_mid = int((c1 + c2)/2)
                mid_p = player.getval(r_mid, c_mid)
                mid_o = opponent.getval(r_mid, c_mid)
                if src and (mid_o and not mid_p) and not (dst_o or dst_p):
                    if prob != 1:
                        self.split(state, prob, False)
                        if playeridx == 0:
                            newplayer = self.states[-1].player0
                            newopp = self.states[-1].player1
                        else:
                            newplayer = self.states[-1].player1
                            newopp = self.states[-1].player0
                    else:
                        newplayer = player
                        newopp = opponent
                    newplayer.move(r1, c1, r2, c2)
                    newopp.delete(r_mid, c_mid)
                    newopp.score -= 1
                    self.states[-1].inactive = True
        return 0
        

def print_board(game):
    size = game.size
    expected = game.expected_vals()
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

def print_boards(g):
    for state in g.states:
        game = GameState(g.size)
        game.states = [state]
        size = game.size
        expected = game.expected_vals()
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

def player_move(game, playeridx):
    # TODO: add ways to split with a pass instead of another move
    valid_move = False
    while not valid_move:
        try:
            if playeridx == 0:
                print(f'{Fore.GREEN}Player ' + str(playeridx+1) + f'\'s turn.{Style.RESET_ALL}')
            else:
                print(f'{Fore.RED}Player ' + str(playeridx+1) + f'\'s turn.{Style.RESET_ALL}')

            print('Move format ex: \"a1 b3\" jumps from A1 to B3')
            print('Type \"i 6\" to inspect your 6th piece')
            move = input('Input move (p to pass, m to measure, i to inspect): ')
            
            if move == 'm':
                game.measure()
                print('Player ' + str(playeridx) + ' has measured the board! ')
                return

            split_moves = move.split()
            n_moves = 0
            movelist = []
            while len(split_moves) > 0:
                first = split_moves[0]
                if first == 'p':
                    movelist.append([None, 1])
                    split_moves = split_moves[1:]
                else:
                    try:
                        second = split_moves[1]

                        r1 = ord(first[0]) - 97
                        c1 = int(first[1]) - 1

                        r2 = ord(second[0]) - 97
                        c2 = int(second[1]) - 1
                    except:
                        raise InvalidMove()

                    m = [r1, c1, r2, c2, 1]

                    try:
                        idx = [x[:4] for x in movelist].index(m[:4])
                        movelist[idx][-1] += 1
                    except ValueError:
                        movelist.append(m)
                    
                    split_moves = split_moves[2:]
                n_moves += 1
            
            if n_moves == 0:
                raise InvalidMove()
            else:
                p_move = 1/n_moves

                len_states = len(game.states)
                for m in movelist:
                    m[-1] *= p_move
                    game.do_move(m, playeridx)

                if n_moves > 1:
                    game.states = game.states[len_states:]

                for state in game.states:
                    state.inactive = False
                
                valid_move = True

        except InvalidMove:
            continue

def play(size=8, spreading=0.1):
    playing = True
    game = GameState(size)

    def win(winner):
        print('\n\n')
        print('Player ' + str(winner) + ' wins!!!')
        play_again = input('Play again? y/n')
        if play_again == 'y':
            return True
        return False

    game.score()
    while playing:
        #do_timestep(b, spreading=spreading)
        print_board(game)
        player_move(game, 0)
        score = game.score()
        if (score[0] < 1):
            playing = win(1)
        elif (score[1] < 1):
            playing = win(0)

        print_board(game)
        player_move(game,1)
        score = game.score()
        if (score[0] < 1):
            playing = win(1)
        elif (score[1] < 1):
            playing = win(0)
    return

play()