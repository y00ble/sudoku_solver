# https://app.crackingthecryptic.com/sudoku/Tbff7DQgHt
from copy import deepcopy
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit

board = Board()
givens = [
    [0, 5, 0, 0, 4, 0, 0, 8, 0],
    [6, 0, 9, 0, 0, 0, 0, 7, 0],
    [8, 0, 4, 0, 0, 0, 0, 6, 2],
    [3, 0, 1, 0, 0, 0, 9, 0, 0],
    [0, 9, 5, 0, 2, 8, 0, 0, 0],
    [0, 0, 0, 3, 0, 1, 0, 0, 0],
    [0, 0, 0, 5, 7, 0, 0, 9, 6],
    [0, 0, 0, 0, 0, 9, 0, 0, 7],
    [0, 8, 0, 0, 1, 0, 2, 0, 3],
]
# https://f-puzzles.com/?id=y355ot2x

for i, digits in enumerate(givens):
    for j, digit in enumerate(digits):
        if digit != 0:
            row = i + 1
            column = j + 1
            GivenDigit(board, row, column, digit)

try:
    board.solve()
finally:
    print(board)
