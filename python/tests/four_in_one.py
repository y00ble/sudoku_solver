import copy
from collections import defaultdict, namedtuple
import itertools
import sys
import os
from joblib import Parallel, delayed

from tqdm import tqdm as tq

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sudoku import Board, MultipleSolutionsFound, NoSolutionFound, SudokuContradiction
from constraints import (
    InternalConsecutiveConstraint,
    InternalAverageSandwichConstraint,
    InternalSkyscraperConstraint,
    InternalOffsetXSumConstraint,
    InternalXSumConstraint,
    InternalXMaxConstraint,
    InternalSandwichConstraint,
    InternalUnorderedConsecutiveConstraint,
    InternalLittleKiller,
    InternalNinesNeighbours,
    InternalSandwichDifferenceConstraint,
    InternalXCountConstraint,
    Constraint,
)


class DummySandwichConstraint(Constraint):
    def __init__(self, board, sum_cell, sandwich_cells):
        super().__init__(board, [sum_cell] + sandwich_cells)
        self.sum_cell = sum_cell
        self.sandwich_cells = sorted(
            sandwich_cells, key=lambda cell: cell.row + cell.column
        )
        self.name = "Dummy Sandwich {}: {}".format(self.sum_cell, self.sandwich_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return

        sum_digits = {assignment[cell] for cell in self.sandwich_cells}
        if 1 not in sum_digits or 9 not in sum_digits:
            return True


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

        # if InternalSkyscraperConstraint in rules_to_indices:
        #     indices = rules_to_indices[InternalSkyscraperConstraint]
        #     if 1 in indices and 3 in indices:
        #         pass
        #     elif 4 in indices and 6 in indices:
        #         pass
        #     else:
        #         continue

        # if InternalConsecutiveConstraint in rules_to_indices:
        #     indices = rules_to_indices[InternalConsecutiveConstraint]
        #     if not (0 in indices or 7 in indices):
        #         continue

        if InternalXSumConstraint in rules_to_indices:
            indices = rules_to_indices[InternalXSumConstraint]
            if 3 in indices or 4 in indices:
                continue

        if skip_yield:
            continue

        yield l1 + l2 + l3 + l4

        if BlRule is InternalSandwichConstraint:
            for i in range(4):
                if i not in l1:
                    amended_l1 = l1 + (i,)
                    yield amended_l1 + l2 + l3 + l4

        if TrRule is InternalSandwichConstraint:
            for i in range(8, 12):
                if i not in l3:
                    amended_l3 = l3 + (i,)
                    yield l1 + l2 + amended_l3 + l4


def rule_permutations():
    return [[1, 2, 3, 4], [1, 2, 4, 3], [1, 3, 4, 2]]


best_board_index = None
best_score = 9 * 9 * 9

# No solutions with:
# XSum, Skyscraper, Nines Neighbours (minus), Consecutive
# XSum, Skyscraper, Sandwich Difference, Consecutive
# XMax, Skyscraper, Sandwich, Consecutive


def iter_boards():
    # for four_rules in itertools.combinations(
    #     [
    #         InternalXCountConstraint,
    #         InternalSkyscraperConstraint,
    #         InternalConsecutiveConstraint,
    #         InternalSandwichConstraint,
    #     ],
    #     4,
    # ):
    four_rules = [
        InternalXSumConstraint,
        InternalSkyscraperConstraint,
        InternalConsecutiveConstraint,
        DummySandwichConstraint,
    ]
    for permutation in rule_permutations():
        TlRule = four_rules[permutation[0] - 1]
        TrRule = four_rules[permutation[1] - 1]
        BrRule = four_rules[permutation[2] - 1]
        BlRule = four_rules[permutation[3] - 1]
        for true_cells in true_cell_iter(TlRule, TrRule, BrRule, BlRule):
            cell_flags = [i in true_cells for i in range(16)]

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

multi_solution_boards = []
unsolved_boards = []

Score = namedtuple("Score", "interesting possibles outcome")


def map_board_to_scores(board):
    try:
        board.solve()
        return Score(True, board.total_possibles, "Puzzle solved")
    except SudokuContradiction:
        return Score(False, board.total_possibles, "Broke")
    except (NoSolutionFound, MultipleSolutionsFound):
        return Score(True, board.total_possibles, "No solution found")
    except KeyboardInterrupt:
        raise
    finally:
        print(board)
    return Score(False, board.total_possibles, "Unknown Outcome")


boards = list(iter_boards())
# boards_copy = copy.deepcopy(boards)

scores = [map_board_to_scores(board) for board in tq(boards)]
# scores = Parallel(n_jobs=-1)(delayed(map_board_to_scores)(board) for board in tq(boards))


def summarise_board(board):
    for constraint in board.constraints:
        print(constraint)

    try:
        board.solve()
    except:
        pass
    print(board)


sys.stdout.flush()

print("Best board")

board, score = min(zip(boards, scores), key=lambda x: x[1][1])
summarise_board(copy.deepcopy(board))

sys.stdout.flush()

print("All board summary")
for board, score in zip(boards, scores):
    print(score)
    print(board)
