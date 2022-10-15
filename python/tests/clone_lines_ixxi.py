# fmt: off
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from constraints import CellsEqual, IX, XI, NegativeSumConstraint
from sudoku import Board, GivenDigit
# fmt: on


board = Board()

# CellsEqual(board, [
#     board[1, 3],
#     board[2, 4],
#     board[3, 7],
#     board[7, 5],
#     board[8, 8]
# ])

# CellsEqual(board, [
#     board[3, 9],
#     board[4, 8],
#     board[5, 3],
#     board[7, 7],
#     board[8, 2]
# ])

# CellsEqual(board, [
#     board[2, 2],
#     board[3, 5],
#     board[7, 3],
#     board[8, 6],
#     board[9, 7]
# ])

# CellsEqual(board, [
#     board[3, 3],
#     board[2, 8],
#     board[5, 7],
#     board[6, 2],
#     board[7, 1]
# ])

# CellsEqual(board, [
#     board[2, 3],
#     board[3, 4],
#     board[7, 6],
#     board[8, 7]
# ])

# CellsEqual(board, [
#     board[3, 8],
#     board[4, 7],
#     board[6, 3],
#     board[7, 2],
# ])

# CellsEqual(board, [
#     board[2, 9],
#     board[3, 2],
#     board[4, 3],
#     board[6, 7],
#     board[7, 8],
#     board[8, 1]
# ])

# CellsEqual(board, [
#     board[1, 2],
#     board[2, 7],
#     board[3, 6],
#     board[7, 4],
#     board[8, 3],
#     board[9, 8]
# ])

# CellsEqual(board, [
#     board[1, 7],
#     board[2, 6],
#     board[3, 1],
#     board[4, 2],
#     board[5, 5],
#     board[6, 8],
#     board[7, 9],
#     board[8, 4],
#     board[9, 3]
# ])

CellsEqual(board, [board[2, 2], board[7, 3]])
CellsEqual(board, [board[1, 2], board[7, 4]])
CellsEqual(board, [board[1, 3], board[7, 5]])
CellsEqual(board, [board[2, 3], board[7, 6]])
CellsEqual(board, [board[3, 2], board[6, 7]])
CellsEqual(board, [board[4, 2], board[6, 8]])

CellsEqual(board, [board[2, 8], board[3, 3]])
CellsEqual(board, [board[2, 9], board[4, 3]])
CellsEqual(board, [board[3, 9], board[5, 3]])
CellsEqual(board, [board[3, 8], board[6, 3]])
CellsEqual(board, [board[2, 7], board[7, 4]])
CellsEqual(board, [board[2, 6], board[8, 4]])

CellsEqual(board, [board[8, 8], board[3, 7]])
CellsEqual(board, [board[9, 8], board[3, 6]])
CellsEqual(board, [board[9, 7], board[3, 5]])
CellsEqual(board, [board[8, 7], board[3, 4]])
CellsEqual(board, [board[7, 8], board[4, 3]])
CellsEqual(board, [board[6, 8], board[4, 2]])

CellsEqual(board, [board[8, 2], board[7, 7]])
CellsEqual(board, [board[8, 1], board[6, 7]])
CellsEqual(board, [board[7, 1], board[5, 7]])
CellsEqual(board, [board[7, 2], board[4, 7]])
CellsEqual(board, [board[8, 3], board[3, 6]])
CellsEqual(board, [board[8, 4], board[2, 6]])

IX(board, board[1, 1], board[1, 2])
IX(board, board[2, 1], board[3, 1])
IX(board, board[5, 5], board[5, 6])
IX(board, board[8, 2], board[8, 3])
IX(board, board[7, 9], board[8, 9])

XI(board, board[1, 7], board[1, 8])
XI(board, board[5, 5], board[6, 5])
XI(board, board[8, 1], board[9, 1])
XI(board, board[9, 2], board[9, 3])
XI(board, board[7, 8], board[8, 8])

NegativeSumConstraint(board, 9)
NegativeSumConstraint(board, 11)

try:
    board.solve()
finally:
    print(board)
