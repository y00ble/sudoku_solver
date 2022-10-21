import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from constraints import (
    InternalXSumConstraint,
    InternalNinesNeighbours,
    InternalSkyscraperConstraint,
    InternalConsecutiveConstraint,
    GivenPossibles,
)
from sudoku import Board

board = Board()

InternalConsecutiveConstraint(
    board, board[5, 1], [board[4, 1], board[3, 1], board[2, 1], board[1, 1]]
)
InternalConsecutiveConstraint(
    board, board[5, 3], [board[4, 3], board[3, 3], board[2, 3], board[1, 3]]
)
InternalConsecutiveConstraint(
    board, board[3, 5], [board[3, 4], board[3, 3], board[3, 2], board[3, 1]]
)
InternalConsecutiveConstraint(
    board, board[2, 5], [board[2, 4], board[2, 3], board[2, 2], board[2, 1]]
)

InternalSkyscraperConstraint(
    board, board[5, 2], [board[6, 2], board[7, 2], board[8, 2], board[9, 2]]
)
InternalSkyscraperConstraint(
    board, board[5, 4], [board[6, 4], board[7, 4], board[8, 4], board[9, 4]]
)
InternalSkyscraperConstraint(
    board, board[6, 5], [board[6, 4], board[6, 3], board[6, 2], board[6, 1]]
)
InternalSkyscraperConstraint(
    board, board[9, 5], [board[9, 4], board[9, 3], board[9, 2], board[9, 1]]
)

InternalNinesNeighbours(
    board, board[1, 5], [board[1, 6], board[1, 7], board[1, 8], board[1, 9]]
)
InternalNinesNeighbours(
    board, board[4, 5], [board[4, 6], board[4, 7], board[4, 8], board[4, 9]]
)
InternalNinesNeighbours(
    board, board[5, 6], [board[4, 6], board[3, 6], board[2, 6], board[1, 6]]
)
InternalNinesNeighbours(
    board, board[5, 7], [board[4, 7], board[3, 7], board[2, 7], board[1, 7]]
)

InternalXSumConstraint(
    board, board[7, 5], [board[7, 6], board[7, 7], board[7, 8], board[7, 9]]
)
InternalXSumConstraint(
    board, board[8, 5], [board[8, 6], board[8, 7], board[8, 8], board[8, 9]]
)
InternalXSumConstraint(
    board, board[5, 9], [board[6, 9], board[7, 9], board[8, 9], board[9, 9]]
)
GivenPossibles(board, board[6, 8], {2, 3})
board.solve()
print(board)