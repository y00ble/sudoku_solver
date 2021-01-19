from copy import deepcopy
import io
import sys
import os
import time
import traceback
from tqdm import tqdm as tq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit, SudokuContradiction
from constraints import Arrow, KillerCage

board = Board()

# KillerCage(board, [board[1, 2], board[1, 3], board[1, 4], board[2, 2], board[2, 3]], 23)
KillerCage(board, [board[2, 1], board[3, 1], board[3, 2], board[3, 3], board[4, 1]], 23)
KillerCage(board, [board[6, 7], board[6, 8], board[6, 9], board[7, 8], board[7, 9]], 18)

Arrow(
    board,
    board[1, 4],
    [board[2, 5], board[3, 6], board[4, 7], board[4, 8], board[4, 9]],
)
Arrow(
    board,
    board[4, 1],
    [board[5, 1], board[6, 2], board[6, 3], board[6, 4], board[5, 5]],
)

try:
    board.solve()
finally:
    time.sleep(1)
    print(board)
