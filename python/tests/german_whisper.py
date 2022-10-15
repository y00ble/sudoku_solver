# https://www.youtube.com/watch?v=nH3vat8z9uM&t=176s
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit
from constraints import GermanWhisper, KillerCage

board = Board()

GermanWhisper(
    board,
    [board[8, 1], board[7, 1], board[7, 2], board[8, 3], board[9, 3], board[9, 2]],
)

GermanWhisper(board, [board[4, 5], board[4, 6], board[3, 7]])

GermanWhisper(
    board,
    [board[9, 6], board[8, 7], board[7, 7], board[7, 8], board[6, 9], board[5, 8]],
)

GermanWhisper(
    board,
    [
        board[6, 3],
        board[5, 2],
        board[4, 3],
        board[3, 4],
        board[2, 5],
        board[1, 6],
        board[1, 7],
        board[2, 8],
        board[3, 8],
        board[4, 7],
        board[5, 6],
        board[6, 6],
        board[7, 6],
        board[8, 5],
        board[7, 4],
    ],
)

GivenDigit(board, 1, 5, 1)
GivenDigit(board, 2, 2, 5)
GivenDigit(board, 5, 1, 6)
GivenDigit(board, 5, 9, 9)
GivenDigit(board, 7, 3, 3)
GivenDigit(board, 8, 8, 3)
GivenDigit(board, 9, 5, 3)

try:
    board.solve()
finally:
    print(board)
