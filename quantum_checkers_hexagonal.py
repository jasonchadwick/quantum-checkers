import numpy as np
from numpy.lib.function_base import _calculate_shapes

from gates import *
from game_utils.hex_board import HexBoard

"""
All tiles are entangled - i.e. the entire board is in a superposition of possible
states. These states have different "probability amplitudes" associated with them.
As in quantum mechanics, probability amplitudes are complex numbers. The "expected
value" of a certain board state is calculated by 

An "attack" can be thought of as a CNOT gate - Player 0 attacking a player 1 tile
essentially says "if bit A is in state 0, flip bit B"

IDEA: you can unlock different gate operations
- CNOT
- Cphase?
- SWAP
- etc
IDEA: each player has a "hand" of a few different gates, they can use a couple per turn

Can do 2-3 moves per turn?

Puzzle campaign (build up the possible gates) but also multiplayer

Mathematically, the board is a bit vector [b0, b1, ... bn] and Player 0's goal is to
make the most probable state become [0, 0, ..., 0] while Player 1's goal is to make
it become [1, 1, ..., 1]. This entire game could be described using quantum mechanics
and matrices - the only thing this board design decides is what possible unitary
manipulations are possible on our bits. In a way, you are essentially creating a
quantum computer circuit, step by step (I think this game is Turing complete..?)
So in theory this game could be physically implemented on a quantum computer, with
each tile being a qubit.

What about more than 2 players?
In quantum computing, "qubits" with more than 2 states are known as qudits (for 3-state
systems, they are called qutrits). n qudits that each have d states can represent d^n
total possible "board-states" (ex: 2 qudits of 3 states each can represent the following
8 states: 00, 01, 02, 10, 11, 12, 20, 21, 22)

board indexing (size=3):

    13  15  18
  11   4   6  17
 9   2   0   5  16
   8   1   3  14
     7  10  12

Organization:
In quantum mechanics terms, the game is in a superposition of 2^ntiles-1 possible states, each of
which has a "probability amplitude" that is related to the probability of that particular
state being observed when the board is "measured". 
Current state of game is stored as a "sparse array"
e.g. if the current state is 1/sqrt(2) (|0000...00> - |1111...11>) then
the state is a list of length 2 containing the tuples (0, 1/sqrt(2)) and (2^n-1, -1/sqrt(2)).
The first number is the state index (which tells us the value of each tile on the board)
and the second number is the probability amplitude, which can be complex.
Operations are essentially unitary matrices on the entire space, but are treated as
a series of conditionals in the code. CNOT(0, 1) is a CNOT gate with the 0 tile as control
and the 1 tile as target. It will search through the game state list, and any tiles that have
the bit patterns |10....> or |11....> will have their amplitudes flipped.

"""

class Board(HexBoard):
    def __init__(self, size):
        super().__init__(size, False)
        self.ntiles = 1 + 6*(sum(range(size)))
        self.nrows = 1 + 4*(size-1)
        self.make_starting_states()
    
    def make_starting_states(self):
        # tile 0 (middle tile) is 50% chance 0 or 1
        state1 = np.zeros(self.ntiles, int)
        state1[0] = 0
        state2 = np.zeros(self.ntiles, int)
        state2[0] = 1
        for z in range(-self.size+1, self.size):
            if z < 0:
                for x in range(-self.size+1-z, self.size-1):
                    y = -x-z
                    state1[self.coords_to_idx[(x,y,z)]] = 0
                    state2[self.coords_to_idx[(x,y,z)]] = 0
            elif z == 0:
                for x in range(-self.size+1, self.size):
                    y = -x
                    if x < 0:
                        state1[self.coords_to_idx[(x,y,z)]] = 0
                        state2[self.coords_to_idx[(x,y,z)]] = 0
                    elif x > 0:
                        state1[self.coords_to_idx[(x,y,z)]] = 1
                        state2[self.coords_to_idx[(x,y,z)]] = 1
            else:
                for x in range(-self.size+1, self.size-z):
                    y = -x-z
                    state1[self.coords_to_idx[(x,y,z)]] = 1
                    state2[self.coords_to_idx[(x,y,z)]] = 1
        self.states = {self.state_idx_from_bits(state1): 1/np.sqrt(2),
                       self.state_idx_from_bits(state2): 1/np.sqrt(2)}

    def state_idx_from_bits(self, bits):
        result = 0
        for i,b in enumerate(bits):
            result += b*2**i
        return int(result)
    
    def bits_from_state_idx(self, idx):
        bits = np.zeros(self.ntiles, int)
        for i in range(self.ntiles-1, -1, -1):
            if idx >= 2**i:
                bits[i] = 1
                idx -= 2**i
        return bits

    def popstate(self, idx):
        self.states.pop(idx)

    def addstate(self, idx, amp):
        if amp == 0:
            return
        if idx in self.states:
            self.states[idx] += amp
        else:
            self.states[idx] = amp

    def prunestates(self):
        states_to_rm = []
        for idx in self.states:
            amp = self.states[idx]
            if abs(amp) < 1e-15:
                states_to_rm.append(idx)
        for idx in states_to_rm:
            self.popstate(idx)

    def onebitgate(self, target, gate):
        # TODO: use gate class instead of matrices
        states_to_rm = []
        states_to_add = []
        for idx in self.states:
            bits = self.bits_from_state_idx(idx)
            amp = self.states[idx]
            bit = bits[target]
            newbits0 = np.concatenate((bits[:target], [0], bits[target+1:]))
            amp0 = gate[0,bit] * amp
            newbits1 = np.concatenate((bits[:target], [1], bits[target+1:]))
            amp1 = gate[1,bit] * amp
            states_to_rm.append(idx)
            states_to_add.append((self.state_idx_from_bits(newbits0), amp0))
            states_to_add.append((self.state_idx_from_bits(newbits1), amp1))
        for idx in states_to_rm:
            self.popstate(idx)
        for (idx,amp) in states_to_add:
            self.addstate(idx,amp)
        self.prunestates()

    def twobitgate(self, tgtA, tgtB, gate):
        # return False if invalid gate, else True
        # TODO: use Gate class instead of matrices
        if tgtB not in self.get_adjacent_idxs(tgtA):
            return False
        if tgtA > tgtB:
            tgt1 = tgtB
            tgt2 = tgtA
        else:
            tgt1 = tgtA
            tgt2 = tgtB
        states_to_rm = []
        states_to_add = []
        for idx in self.states:
            bits = self.bits_from_state_idx(idx)
            amp = self.states[idx]
            bitA = bits[tgtA]
            bitB = bits[tgtB]
            for newA,newB in [[0,0],[0,1],[1,0],[1,1]]:
                newbits = np.concatenate((bits[:tgt1], [newA], bits[tgt1+1:tgt2], [newB], bits[tgt2+1:]))
                newamp = gate[2*newA+newB, 2*bitA+bitB] * amp
                states_to_add.append((self.state_idx_from_bits(newbits), newamp))
            states_to_rm.append(idx)
        for idx in states_to_rm:
            self.popstate(idx)
        for (idx,amp) in states_to_add:
            self.addstate(idx,amp)
        self.prunestates()
        return True
    
    def calc_expect(self):
        expected_vals = np.zeros(self.ntiles)
        for idx in self.states:
            p = abs(self.states[idx])**2
            bits = self.bits_from_state_idx(idx)
            for i in range(self.ntiles):
                if bits[i] == 1:
                    expected_vals[i] += p
        return expected_vals

    def print(self):
        expected_vals = self.calc_expect()
        super().print((lambda i : '{:.3}'.format(expected_vals[i])))

class Player():
    def __init__(self, playernum, handsize=5):
        self.playernum = playernum
        self.handsize = handsize
        # TODO

class QGame():
    def __init__(self, size=3, handsize=5, ops_per_turn=3, win_threshold=0.9):
        self.board = Board(size)
        self.score = 0
        self.deck = self.populate_deck()
        self.params = {"handsize" : 5,
                       "ops_per_turn" : 3,
                       "win_threshold" : 0.9}
    
    def populate_deck(self, preset=None):
        # TODO
        # make a deck of allowed gates that players draw their hand from
        pass

    def calc_score(self):
        # if sum of tiles is 0, player 0 wins, if 1 then player 1 wins
        expected_vals = self.board.calc_expect()
        p1_score = sum(expected_vals) / self.board.ntiles
        p2_score = 1 - p1_score
        return (p1_score, p2_score)

    def measure(self):
        # TODO
        # measures the board, picking a single possible state
        # TODO: can players do this during the game?
        pass

    def do_turn(self, player):
        # TODO
        # one player does a turn (uses `ops_per_turn` number of gates on the board)
        pass

    def play(self):
        # TODO
        # loop of player turns until there is a winner
        pass