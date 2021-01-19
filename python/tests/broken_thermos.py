# https://app.crackingthecryptic.com/sudoku/Tbff7DQgHt
from copy import deepcopy
import io
import sys
import os
import traceback
from tqdm import tqdm as tq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, GivenDigit, SudokuContradiction
from constraints import BrokenThermometer

circle_cells = [
    (6, 3),
    (7, 4),
    (7, 5),
    (7, 6),
    (6, 7),
    (5, 7),
    (4, 7),
    (3, 6),
    (3, 5),
    (3, 4),
    (4, 3),
    (5, 3),
]

for i in range(2):
    for j in tq(range(len(circle_cells))):
        circle_cells = circle_cells[1:] + [circle_cells[0]]

        board = Board()

        BrokenThermometer(
            board,
            [
                # board[5, 1],
                board[4, 1],
                board[3, 1],
                board[2, 1],
                board[1, 1],
                board[1, 2],
                board[1, 3],
                board[1, 4],
                board[1, 5],
                board[1, 6],
                board[1, 7],
                board[1, 8],
                board[1, 9],
                board[2, 9],
                board[3, 9],
                board[4, 9],
                # board[5, 9],
            ],
        )

        BrokenThermometer(
            board,
            [
                board[6, 9],
                board[7, 9],
                board[8, 9],
                board[9, 9],
                board[9, 8],
                board[9, 7],
                board[9, 6],
                board[9, 5],
                board[9, 4],
                board[9, 3],
                board[9, 2],
                board[9, 1],
                board[8, 1],
                board[7, 1],
                board[6, 1],
            ],
        )

        BrokenThermometer(
            board,
            [board[coords] for coords in circle_cells],
        )
        _stdout = sys.stdout
        steps_stream = io.StringIO()
        try:
            sys.stdout = steps_stream
            board.solve()
            sys.stdout = _stdout
            print("Solution!")
            print(steps_stream.getvalue())
            print(circle_cells)
            print(board)
        except SudokuContradiction:
            continue
        except KeyboardInterrupt as e:
            raise e
        except:
            sys.stdout = _stdout
            traceback.print_exc()
            sys.stdout = _stdout
            print("Final state")
            print(steps_stream.getvalue())
            print(circle_cells)
            print(board)

    circle_cells = list(reversed(circle_cells))
