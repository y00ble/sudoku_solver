# https://www.youtube.com/watch?v=nH3vat8z9uM&t=176s
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import (
    Board,
    GivenDigit,
    NoSolutionFound,
    SudokuContradiction,
    MultipleSolutionsFound,
)
from constraints import Arrow, KillerCage, Skyscraper, BlackKropki, Palindrome
from itertools import combinations, product
from tqdm import tqdm as tq
import numpy as np

arrow_builders = [
    lambda board: Arrow(
        board,
        board[3, 5],
        [board[2, 5], board[1, 4], board[1, 3], board[2, 2], board[2, 3]],
    ),
    lambda board: Arrow(
        board,
        board[5, 7],
        [board[5, 8], board[4, 9], board[3, 9], board[3, 8], board[3, 7]],
    ),
    lambda board: Arrow(board, board[6, 1], [board[7, 1], board[8, 1]]),
    lambda board: Arrow(board, board[9, 3], [board[9, 2], board[8, 2], board[7, 2]]),
    lambda board: Arrow(board, board[7, 5], [board[7, 6], board[8, 6]]),
    lambda board: Arrow(board, board[6, 7], [board[7, 7], board[8, 7]]),
]

black_kropki_builders = [
    lambda board: BlackKropki(board, board[7, 6], board[8, 6]),
    lambda board: BlackKropki(board, board[9, 7], board[9, 8]),
    lambda board: BlackKropki(board, board[9, 8], board[9, 9]),
]

killer_cage_builders = [
    lambda board: KillerCage(board, [board[2, 1], board[2, 2]], 8),
    lambda board: KillerCage(
        board, [board[3, 1], board[3, 2], board[4, 1], board[5, 1]], 12
    ),
    lambda board: KillerCage(board, [board[2, 7], board[2, 8]], 10),
    lambda board: KillerCage(board, [board[6, 8], board[6, 9]], 13),
    lambda board: KillerCage(
        board, [board[3, 5], board[4, 4], board[4, 5], board[4, 6], board[5, 4]], 21
    ),
    lambda board: KillerCage(
        board, [board[6, 4], board[6, 5], board[6, 6], board[5, 6], board[5, 7]], 25
    ),
]

skyscraper_builder = [
    lambda board: Skyscraper(board, "top", 1, 4),
    lambda board: Skyscraper(board, "left", 6, 3),
]

palindrome_builders = [
    lambda board: Palindrome(board, [board[7, 3], board[8, 3], board[8, 4]]),
    lambda board: Palindrome(
        board,
        [board[7, 6], board[7, 7], board[7, 8], board[6, 9], board[5, 9], board[4, 9]],
    ),
]


builders = [
    arrow_builders,
    black_kropki_builders,
    killer_cage_builders,
    skyscraper_builder,
    palindrome_builders,
]

possible_solutions = []

expected_invalid_builder_indices = (3, 1, 4, 1, 0)

for i, invalid_builders in enumerate(
    tq(
        product(*builders),
        total=np.prod([len(builder_list) for builder_list in builders]),
    )
):
    invalid_builder_indices = tuple(
        [
            builder_list.index(invalid_builder)
            for builder_list, invalid_builder in zip(builders, invalid_builders)
        ]
    )
    print("-" * 50)
    print("Solving without {}".format(invalid_builder_indices))
    if invalid_builder_indices == expected_invalid_builder_indices:
        print("THIS ONE!!!")
    else:
        continue

    valid_builders = [
        builder
        for builder_list in builders
        for builder in builder_list
        if builder not in invalid_builders
    ]

    board = Board()
    for builder in valid_builders:
        builder(board)

    try:
        print()
        board.solve()
        print(board)
        possible_solutions.append(invalid_builder_indices)
    except NoSolutionFound:
        possible_solutions.append(invalid_builder_indices)
    except MultipleSolutionsFound:
        possible_solutions.append(invalid_builder_indices)
    except SudokuContradiction:
        print()
        print(board)

print(possible_solutions)