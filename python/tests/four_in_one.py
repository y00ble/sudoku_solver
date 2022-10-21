from collections import defaultdict
import itertools
import sys
import os

from tqdm import tqdm as tq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, MultipleSolutionsFound, NoSolutionFound, SudokuContradiction
from constraints import (
    InternalConsecutiveConstraint,
    InternalAverageSandwichConstraint,
    InternalSkyscraperConstraint,
    InternalOffsetXSumConstraint,
    InternalXSumConstraint,
    InternalSandwichConstraint,
    InternalUnorderedConsecutiveConstraint,
    InternalLittleKiller,
    InternalNinesNeighbours,
)


def true_cell_iter(TlRule, TrRule, BrRule, BlRule):
    for l1, l2, l3, l4 in itertools.product(
        itertools.combinations([0, 1, 2, 3], 2),
        itertools.combinations([4, 5, 6, 7], 2),
        itertools.combinations([8, 9, 10, 11], 2),
        itertools.combinations([12, 13, 14, 15], 2),
    ):
        rules_to_indices = defaultdict(list)

        rules_to_indices[TlRule].extend(l1)
        rules_to_indices[TlRule].extend([15 - i for i in l3])

        rules_to_indices[TrRule].extend([i - 8 for i in range(8, 12) if i not in l3])
        rules_to_indices[TrRule].extend(l2)

        rules_to_indices[BrRule].extend([7 - i for i in range(4, 8) if i not in l2])
        rules_to_indices[BrRule].extend([i - 8 for i in range(12, 16) if i not in l4])

        rules_to_indices[BlRule].extend([15 - i for i in l4])
        rules_to_indices[BlRule].extend([7 - i for i in range(4) if i not in l1])

        skip_yield = False
        for sandwich_rule in [
            InternalSandwichConstraint,
            InternalAverageSandwichConstraint,
        ]:
            if sandwich_rule in rules_to_indices:
                if sorted(rules_to_indices[sandwich_rule]) != [0, 3, 4, 7]:
                    skip_yield = True

        for x_rule in [InternalXSumConstraint, InternalOffsetXSumConstraint]:
            if x_rule in rules_to_indices:
                if len([i for i in rules_to_indices[x_rule] if i in {3, 4}]) == 1:
                    skip_yield = True

        # if InternalNinesNeighbours in rules_to_indices:
        #     if not all(
        #         [i in rules_to_indices[InternalNinesNeighbours] for i in {3, 4}]
        #     ):
        #         skip_yield = True

        if InternalSkyscraperConstraint in rules_to_indices:
            indices = rules_to_indices[InternalSkyscraperConstraint]
            if 1 in indices and 3 in indices:
                pass
            elif 4 in indices and 6 in indices:
                pass
            else:
                continue

        if InternalConsecutiveConstraint in rules_to_indices:
            indices = rules_to_indices[InternalConsecutiveConstraint]
            if not (0 in indices or 7 in indices):
                continue

        if InternalXSumConstraint in rules_to_indices:
            indices = rules_to_indices[InternalXSumConstraint]
            if 3 in indices or 4 in indices:
                continue

        if skip_yield:
            continue

        yield l1 + l2 + l3 + l4


def rule_permutations():
    return [[1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 4, 2]]


best_board_index = None
best_score = 9 * 9 * 9


def iter_boards():
    for four_rules in itertools.combinations(
        [
            InternalXSumConstraint,
            InternalSkyscraperConstraint,
            InternalNinesNeighbours,
            InternalConsecutiveConstraint,
        ],
        4,
    ):
        for permutation in rule_permutations():
            TlRule = four_rules[permutation[0] - 1]
            TrRule = four_rules[permutation[1] - 1]
            BrRule = four_rules[permutation[2] - 1]
            BlRule = four_rules[permutation[3] - 1]
            for true_cells in true_cell_iter(TlRule, TrRule, BrRule, BlRule):
                cell_flags = [i in true_cells for i in range(16)]
                if sum(cell_flags[:4]) != 2:
                    continue
                if sum(cell_flags[4:8]) != 2:
                    continue
                if sum(cell_flags[8:12]) != 2:
                    continue
                if sum(cell_flags[12:]) != 2:
                    continue

                board = Board()

                # Left branch
                for col in range(1, 5):
                    if cell_flags[col - 1]:
                        TlRule(
                            board,
                            board[5, col],
                            [
                                board[4, col],
                                board[3, col],
                                board[2, col],
                                board[1, col],
                            ],
                        )
                    else:
                        BlRule(
                            board,
                            board[5, col],
                            [
                                board[6, col],
                                board[7, col],
                                board[8, col],
                                board[9, col],
                            ],
                        )

                # Right branch
                for col in range(6, 10):
                    if cell_flags[col - 2]:
                        TrRule(
                            board,
                            board[5, col],
                            [
                                board[4, col],
                                board[3, col],
                                board[2, col],
                                board[1, col],
                            ],
                        )
                    else:
                        BrRule(
                            board,
                            board[5, col],
                            [
                                board[6, col],
                                board[7, col],
                                board[8, col],
                                board[9, col],
                            ],
                        )

                # Top branch
                for row in range(1, 5):
                    if cell_flags[row + 7]:
                        TlRule(
                            board,
                            board[row, 5],
                            [
                                board[row, 4],
                                board[row, 3],
                                board[row, 2],
                                board[row, 1],
                            ],
                        )
                    else:
                        TrRule(
                            board,
                            board[row, 5],
                            [
                                board[row, 6],
                                board[row, 7],
                                board[row, 8],
                                board[row, 9],
                            ],
                        )

                # Bottom branch
                for row in range(6, 10):
                    if cell_flags[row + 6]:
                        BlRule(
                            board,
                            board[row, 5],
                            [
                                board[row, 4],
                                board[row, 3],
                                board[row, 2],
                                board[row, 1],
                            ],
                        )
                    else:
                        BrRule(
                            board,
                            board[row, 5],
                            [
                                board[row, 6],
                                board[row, 7],
                                board[row, 8],
                                board[row, 9],
                            ],
                        )

                yield board


total_boards = 0
for _ in iter_boards():
    total_boards += 1

for i, board in tq(enumerate(iter_boards()), total=total_boards):
    try:
        board.solve()
        print(board)
        raise sys.exit(0)

    except (SudokuContradiction, NoSolutionFound):
        pass
    finally:
        if board.total_possibles < best_score:
            best_board_index = i
            best_score = board.total_possibles
        print(board)

print("Best board")

for best_board, _ in zip(iter_boards(), range(best_board_index + 1)):
    pass
try:
    best_board.solve()
finally:
    print(best_board)