import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit
from constraints import GermanWhisper, KillerCage

board = Board()

KillerCage(board, [board[1, 1], board[1, 2]], 11)

KillerCage(board, [board[1, 8], board[1, 9], board[2, 9]], 18)

KillerCage(board, [board[5, 1], board[6, 1], board[7, 1]], 18)

KillerCage(board, [board[9, 1], board[9, 2], board[9, 3]], 16)

KillerCage(board, [board[7, 5], board[8, 4], board[8, 5], board[9, 4], board[9, 5]], 18)

KillerCage(board, [board[8, 6], board[8, 7], board[9, 6]], 18)

KillerCage(board, [board[9, 7], board[9, 8]], 10)

GermanWhisper(board, [board[4, 1], board[3, 1], board[2, 1], board[3, 2]])

GermanWhisper(board, [board[4, 2], board[3, 1]])

GermanWhisper(board, [board[2, 3], board[1, 4], board[2, 5]])

GermanWhisper(board, [board[3, 3], board[2, 4], board[3, 5]])

GermanWhisper(board, [board[5, 2], board[4, 3], board[3, 4], board[4, 5], board[5, 6]])

GermanWhisper(board, [board[6, 2], board[5, 3], board[4, 4], board[5, 5], board[6, 6]])

GermanWhisper(board, [board[5, 4], board[6, 4], board[7, 4]])

GermanWhisper(board, [board[6, 7], board[5, 8], board[6, 9]])

GermanWhisper(board, [board[7, 7], board[6, 8], board[7, 9]])

GermanWhisper(board, [board[7, 8], board[8, 8]])

GivenDigit(board, 7, 4, 7)

try:
    board.solve()
finally:
    print(board)
