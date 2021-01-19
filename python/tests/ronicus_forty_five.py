# https://app.crackingthecryptic.com/sudoku/Tbff7DQgHt
from copy import deepcopy
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit
from constraints import CellsEqual, KillerCage, DisjointGroups

board = Board()
givens = [
    [0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 5, 6, 0, 0],
    [0, 0, 0, 0, 0, 8, 0, 0, 9],
    [0, 7, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

killer_cages = [
    [1, 1, 0, 2, 2, 2, 3, 3, 3],
    [1, 1, 1, 0, 2, 2, 2, 0, 3],
    [1, 1, 1, 1, 2, 2, 2, 3, 3],
    [6, 0, 5, 5, 5, 4, 3, 3, 3],
    [6, 5, 5, 5, 4, 4, 4, 4, 4],
    [6, 5, 5, 5, 4, 0, 0, 4, 4],
    [6, 6, 6, 7, 7, 0, 8, 8, 0],
    [6, 0, 7, 7, 7, 8, 8, 8, 8],
    [6, 6, 7, 7, 7, 7, 8, 8, 8],
]

for i, digits in enumerate(givens):
    for j, digit in enumerate(digits):
        if digit != 0:
            row = i + 1
            column = j + 1
            GivenDigit(board, row, column, digit)

CellsEqual(board, [board[1, 5], board[6, 7]])
CellsEqual(board, [board[3, 8], board[9, 3]])

for cage_index in range(1, 9):
    KillerCage(
        board,
        [
            board[i + 1, j + 1]
            for i in range(9)
            for j in range(9)
            if killer_cages[i][j] == cage_index
        ],
        45,
    )

DisjointGroups(board)

try:
    board.solve()
finally:
    print(board)
