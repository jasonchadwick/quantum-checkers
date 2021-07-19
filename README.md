# quantum-checkers

### probabilistic_checkers.py:

Checkers, but each "piece" is a probability distribution that spreads out over time.

The winner is the first to drop their opponent's total probability score below 1 piece.

### quantum_checkers_hexagonal.py:

A hexagonal-grid board where each tile has a value between 0 and 1. Player 0 wins if the average of all tiles gets close enough to 0, and player 1 wins if the average is close
enough to 1. See the file for more info.

### Todo (hex game)

- 2-bit gates
- AI to play against
- UI
    - option to look at the individual prob. distributions of each piece when making a move
    - option to look at the math?
- "measuring" the board during gameplay? Would this be balanced?
- Android app???