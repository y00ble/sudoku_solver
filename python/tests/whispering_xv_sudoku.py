import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit
from constraints import GermanWhisper, X, V

board = Board()

V(board, board[2, 1], board[2, 2])
V(board, board[1, 8], board[2, 8])
V(board, board[8, 2], board[9, 2])
V(board, board[8, 8], board[8, 9])

X(board, board[2, 5], board[3, 5])
X(board, board[8, 5], board[7, 5])
X(board, board[6, 3], board[5, 3])
X(board, board[5, 7], board[4, 7])

X(board, board[4, 4], board[5, 4])
X(board, board[5, 9], board[6, 9])
X(board, board[3, 6], board[3, 7])

GermanWhisper(
    board,
    [
        board[2, 5],
        board[3, 6],
        board[3, 7],
        board[4, 7],
        board[5, 8],
        board[6, 7],
        board[7, 7],
        board[7, 6],
        board[8, 5],
        board[7, 4],
        board[7, 3],
        board[6, 3],
        board[5, 2],
        board[4, 3],
        board[3, 3],
        board[3, 4],
        board[2, 5],
    ],
)

try:
    board.solve()
finally:
    print(board)
