import itertools
from re import L
from sudoku import Constraint, NoRepeatsConstraint

import numpy as np


class KillerCage(NoRepeatsConstraint):
    def __init__(self, board, cells, total):
        super().__init__(board, cells)
        self.total = total
        self.name = "{} cage ({})".format(
            total, min(cells, key=lambda cell: (cell.row, cell.column))
        )

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        if len(assignment) == len(self.cells):
            return sum(assignment.values()) != self.total
        else:
            return sum(assignment.values()) > self.total


class CellsEqual(Constraint):
    def __init__(self, board, cells):
        super().__init__(board, cells)
        self.name = "Equality constraint: {}".format(
            ", ".join([str(cell) for cell in self.cells])
        )

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        return len(set(assignment.values())) != 1

    def quick_update(self):
        possibles = set.intersection(*[cell.possibles for cell in self.cells])
        for cell in self.cells:
            cell.possibles = {i for i in possibles}


class DisjointGroup(NoRepeatsConstraint):
    def __init__(self, board, index):
        cells = [cell for cell in board.cells if cell.index_in_box == index]
        super().__init__(board, cells)
        self.name = "Disjoint Group Index {}".format(index)


class DisjointGroups:
    def __init__(self, board):
        for i in range(1, 10):
            DisjointGroup(board, i)


class GermanWhisper(Constraint):
    def __init__(self, board, cells):
        super().__init__(board, cells)
        self.name = "German Whisper {}".format(
            min(cells, key=lambda cell: cell.coordinates)
        )

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        for i in range(len(self.cells) - 1):
            if self.cells[i] in assignment and self.cells[i + 1] in assignment:
                if abs(assignment[self.cells[i]] - assignment[self.cells[i + 1]]) < 5:
                    return True
        return False


class Arrow(Constraint):
    def __init__(self, board, bulb, arrow):
        cells = [bulb] + list(arrow)
        super().__init__(board, cells)
        self.bulb = bulb
        self.arrow = arrow
        self.name = "Arrow bulb {}, arrow {}".format(self.bulb, self.arrow)

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True

        arrow_assignment = {k: v for k, v in assignment.items() if k != self.bulb}
        if self.bulb in assignment:
            target = {
                assignment[self.bulb],
            }
        else:
            target = self.bulb.possibles

        if len(arrow_assignment) == len(self.arrow):
            return sum(arrow_assignment.values()) not in target
        else:
            return sum(arrow_assignment.values()) > max(target)


class GivenPossibles(Constraint):
    def __init__(self, board, cell, possibles):
        super().__init__(board, [cell])
        self.possibles = possibles
        self.name = "Given Possibles {} ({})".format(cell, possibles)

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        if self.cells[0] in assignment:
            return assignment[self.cells[0]] not in self.possibles
        return False


def nonzero_mod(v, mod):
    output = v % mod
    if output == 0:
        return mod
    return output


class BrokenThermometer(Constraint):
    def __init__(self, board, cells):
        """
        Cells is a list of cells with the bulb first.
        """
        super().__init__(board, cells)
        self.name = "Broken Thermo {}".format(self.cells)

    def quick_update(self):
        # print("Quick update {}".format(self))

        def get_possible_values(cell):
            # print(
            #     "Getting possible values for {}, current possibles are {}".format(
            #         cell, cell.possibles
            #     )
            # )
            cell_index = self.cells.index(cell)
            distance_to_start = cell_index
            distance_to_end = len(self.cells) - 1 - cell_index
            max_value = 18 - distance_to_end
            min_value = distance_to_start + 1

            return {
                value
                for value in range(min_value, max_value + 1)
                if nonzero_mod(value, 9) in cell.possibles
            }

        changed = True
        while changed:
            changed = False
            for i, cell in enumerate(self.cells):
                # print("-" * 10)
                # print(cell)
                possible_values = get_possible_values(cell)
                # print(possible_values)
                if i < len(self.cells) - 1:
                    max_value_next_cell = max(get_possible_values(self.cells[i + 1]))
                    possible_values = {
                        value
                        for value in possible_values
                        if value <= max_value_next_cell - 1
                    }
                    # print("Next cell has a max of {}".format(max_value_next_cell))
                    # print(possible_values)
                if i > 0:
                    min_value_previous_cell = min(
                        get_possible_values(self.cells[i - 1])
                    )
                    possible_values = {
                        value
                        for value in possible_values
                        if min_value_previous_cell <= value - 1
                    }

                    # print(
                    #     "Previous cell has a min of {}".format(min_value_previous_cell)
                    # )
                    # print(possible_values)
                possibles_before = {i for i in cell.possibles}
                cell.intersect_possibles(
                    {nonzero_mod(value, 9) for value in possible_values}
                )
                possibles_after = {i for i in cell.possibles}
                if possibles_before != possibles_after:
                    changed = True

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True

        if len(assignment) == 1:
            cell = min(assignment)
            value = assignment[cell]
            cell_index = self.cells.index(cell)
            distance_to_start = cell_index
            distance_to_end = len(self.cells) - 1 - cell_index

            max_value = 18 - distance_to_end
            min_value = distance_to_start + 1

            possibles = {nonzero_mod(v, 9) for v in range(min_value, max_value + 1)}
            return value not in possibles
        else:
            break_count = 0
            sorted_cells = list(sorted(assignment, key=lambda x: self.cells.index(x)))
            for i in range(len(sorted_cells) - 1):
                c1 = sorted_cells[i]
                c2 = sorted_cells[i + 1]

                if assignment[c1] >= assignment[c2]:
                    break_count += 1
                    if break_count > 1:
                        return True

            if len(assignment) == len(self.cells):
                if break_count != 1:
                    return True
            return False


class BlackKropki(NoRepeatsConstraint):
    def __init__(self, board, cell_1, cell_2):
        super().__init__(board, [cell_1, cell_2])
        self.name = "Black Kropki {} {}".format(cell_1, cell_2)

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        if self.cells[0] in assignment and self.cells[1] in assignment:
            return min(assignment.values()) * 2 != max(assignment.values())


class Palindrome(Constraint):
    def __init__(self, board, cells):
        super().__init__(board, cells)
        self.name = "Palindrome {}".format(self.cells)

    def get_inverse_cell(self, cell):
        this_cell_index = self.cells.index(cell)
        return self.cells[-(this_cell_index + 1)]

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True
        for cell in assignment:
            inverse_cell = self.get_inverse_cell(cell)
            if inverse_cell in assignment:
                if assignment[cell] != assignment[inverse_cell]:
                    return True


class Skyscraper(Constraint):
    def __init__(self, board, side, index, value):
        """
        Side must be one of ["top", "bottom", "left" or "right"]
        """
        if side in {"top", "bottom"}:
            cells = [cell for cell in board.cells if cell.column == index]

        if side in {"left", "right"}:
            cells = [cell for cell in board.cells if cell.row == index]

        if side in {"bottom", "right"}:
            cells = list(reversed(cells))

        self.value = value
        self.name = "{} skyscraper {} {}".format(self.value, side, index)
        super().__init__(board, cells)

    def partial_assignment_invalid(self, assignment):
        if super().partial_assignment_invalid(assignment):
            return True

        visible_height = 0
        unassigned_cells_seen = 0
        assigned_visible_cells_seen = 0

        for cell in self.cells:
            if cell in assignment:
                if assignment[cell] > visible_height:
                    visible_height = assignment[cell]
                    assigned_visible_cells_seen += 1
                    if (
                        (9 - visible_height)
                        + assigned_visible_cells_seen
                        + unassigned_cells_seen
                        < self.value
                    ):
                        return True
                    if assigned_visible_cells_seen > self.value:
                        return True
            else:
                unassigned_cells_seen += 1


class X(KillerCage):
    def __init__(self, board, cell_1, cell_2):
        super().__init__(board, [cell_1, cell_2], 10)
        self.name = "X ({}, {})".format(cell_1, cell_2)


class V(KillerCage):
    def __init__(self, board, cell_1, cell_2):
        super().__init__(board, [cell_1, cell_2], 5)
        self.name = "V ({}, {})".format(cell_1, cell_2)


class XI(KillerCage):
    def __init__(self, board, cell_1, cell_2):
        super().__init__(board, [cell_1, cell_2], 11)
        self.name = "XI ({}, {})".format(cell_1, cell_2)


class IX(KillerCage):
    def __init__(self, board, cell_1, cell_2):
        super().__init__(board, [cell_1, cell_2], 9)
        self.name = "IX ({}, {})".format(cell_1, cell_2)


class LiarSumConstraint(Constraint):
    def __init__(self, board, c1, c2, avoid_sum):
        super().__init__(board, [c1, c2])
        self.avoid_sum = avoid_sum
        self.name = "{} + {} != {}".format(c1, c2, avoid_sum)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) == len(self.cells):
            return sum(assignment.values()) == self.avoid_sum


class NegativeSumConstraint:
    def __init__(self, board, avoid_sum):
        positive_pairs = set()
        for constraint in board.constraints:
            if isinstance(constraint, KillerCage):
                if len(constraint.cells) == 2 and constraint.total == avoid_sum:
                    c1, c2 = constraint.cells
                    positive_pairs.add((c1, c2))
                    positive_pairs.add((c2, c1))

        for row, col in itertools.product([1, 2, 3, 4, 5, 6, 7, 8, 9], repeat=2):
            c1 = board[row, col]
            if row < 9:
                c2 = board[row + 1, col]
                if (c1, c2) not in positive_pairs:
                    LiarSumConstraint(board, c1, c2, avoid_sum)

            if col < 9:
                c2 = board[row, col + 1]
                if (c1, c2) not in positive_pairs:
                    LiarSumConstraint(board, c1, c2, avoid_sum)


class InternalSkyscraperConstraint(Constraint):
    def __init__(self, board, visibility_cell, cells):
        super().__init__(board, cells + [visibility_cell])
        self.skyscraper_cells = sorted(
            cells,
            key=lambda c: abs(c.row - visibility_cell.row)
            + abs(c.column - visibility_cell.column),
        )
        self.visibility_cell = visibility_cell
        self.name = "Skyscraper {}: {}".format(
            self.visibility_cell, self.skyscraper_cells
        )

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        should_be_visible = assignment[self.visibility_cell]

        current_height = 0
        are_visible = 0
        for cell in self.skyscraper_cells:
            value = assignment[cell]
            if value > current_height:
                are_visible += 1
                current_height = value

        return should_be_visible != are_visible

    def quick_update(self):
        self.visibility_cell.possibles = self.visibility_cell.possibles.intersection(
            {i + 1 for i, _ in enumerate(self.skyscraper_cells)}
        )


class InternalSandwichConstraint(Constraint):
    def __init__(self, board, sum_cell, sandwich_cells):
        super().__init__(board, [sum_cell] + sandwich_cells)
        self.sum_cell = sum_cell
        self.sandwich_cells = sorted(
            sandwich_cells, key=lambda cell: cell.row + cell.column
        )
        self.name = "Sandwich {}: {}".format(self.sum_cell, self.sandwich_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        if 1 not in assignment.values() or 9 not in assignment.values():
            return True

        in_sandwich = False
        current_sum = 0
        for cell in self.sandwich_cells:
            value = assignment[cell]
            if not in_sandwich and value in {1, 9}:
                in_sandwich = True
            elif in_sandwich and value not in {1, 9}:
                current_sum += value
            elif in_sandwich and value in {1, 9}:
                return current_sum != assignment[self.sum_cell]

    def quick_update(self):
        if len(self.sandwich_cells) <= 4:
            self.sandwich_cells[0].possibles = {1, 9}
            self.sandwich_cells[-1].possibles = {1, 9}


class InternalAverageSandwichConstraint(Constraint):
    def __init__(self, board, sum_cell, sandwich_cells):
        super().__init__(board, [sum_cell] + sandwich_cells)
        self.sum_cell = sum_cell
        self.sandwich_cells = sorted(
            sandwich_cells, key=lambda cell: cell.row + cell.column
        )
        self.name = "Sandwich {}: {}".format(self.sum_cell, self.sandwich_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        if 1 not in assignment.values() or 9 not in assignment.values():
            return True

        in_sandwich = False
        count_in_sandwich = 0
        current_sum = 0
        for cell in self.sandwich_cells:
            value = assignment[cell]
            if not in_sandwich and value in {1, 9}:
                in_sandwich = True
            elif in_sandwich and value not in {1, 9}:
                current_sum += value
                count_in_sandwich += 1
            elif in_sandwich and value in {1, 9}:
                return current_sum / count_in_sandwich != assignment[self.sum_cell]

    def quick_update(self):
        if len(self.sandwich_cells) <= 4:
            self.sandwich_cells[0].possibles = {1, 9}
            self.sandwich_cells[-1].possibles = {1, 9}


class InternalXSumConstraint(Constraint):
    def __init__(self, board, sum_cell, summand_cells):
        super().__init__(board, [sum_cell] + summand_cells)
        self.sum_cell = sum_cell
        self.summand_cells = sorted(
            summand_cells,
            key=lambda c: abs(c.row - sum_cell.row) + abs(c.column - sum_cell.column),
        )
        self.x_cell = self.summand_cells[0]
        self.name = "X-sum {}: {}".format(self.sum_cell, self.summand_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        current_sum = 0
        for cell in self.summand_cells[: assignment[self.x_cell]]:
            current_sum += assignment[cell]

        return current_sum != assignment[self.sum_cell]

    def quick_update(self):
        self.x_cell.possibles = self.x_cell.possibles.intersection({2, 3})


class InternalOffsetXSumConstraint(Constraint):
    def __init__(self, board, sum_cell, summand_cells):
        super().__init__(board, [sum_cell] + summand_cells)
        self.sum_cell = sum_cell
        self.summand_cells = sorted(
            summand_cells,
            key=lambda c: abs(c.row - sum_cell.row) + abs(c.column - sum_cell.column),
        )
        self.x_cell = self.summand_cells.pop(0)
        self.name = "X-sum {}: {}".format(self.sum_cell, self.summand_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        current_sum = 0
        for cell in self.summand_cells[: assignment[self.x_cell]]:
            current_sum += assignment[cell]

        return current_sum != assignment[self.sum_cell]

    def quick_update(self):
        self.x_cell.possibles = self.x_cell.possibles.intersection({2, 3})


class InternalConsecutiveConstraint(Constraint):
    def __init__(self, board, count_cell, subject_cells):
        super().__init__(board, [count_cell] + subject_cells)
        self.count_cell = count_cell
        self.subject_cells = sorted(
            subject_cells,
            key=lambda c: abs(c.row - count_cell.row)
            + abs(c.column - count_cell.column),
        )
        self.name = "Consecutive {}: {}".format(self.count_cell, self.subject_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        max_run = 0
        current_run = 0
        previous_cell_value = None
        for cell in self.subject_cells:
            if (
                previous_cell_value is None
                or abs(assignment[cell] - previous_cell_value) == 1
            ):
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                current_run = 1
            previous_cell_value = assignment[cell]

        return max_run != assignment[self.count_cell]

    def quick_update(self):
        self.count_cell.possibles = self.count_cell.possibles.intersection(
            {i + 1 for i, _ in enumerate(self.subject_cells)}
        )


class InternalUnorderedConsecutiveConstraint(Constraint):
    def __init__(self, board, count_cell, subject_cells):
        super().__init__(board, [count_cell] + subject_cells)
        self.count_cell = count_cell
        self.subject_cells = sorted(
            subject_cells,
            key=lambda c: abs(c.row - count_cell.row)
            + abs(c.column - count_cell.column),
        )
        self.name = "Unordered consecutive {}: {}".format(
            self.count_cell, self.subject_cells
        )

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return None

        if len(set(assignment.values())) != len(self.cells):
            return True

        max_run = 0
        current_run = 0
        previous_cell_value = None
        for value in sorted([assignment[cell] for cell in self.subject_cells]):
            if previous_cell_value is None or abs(value - previous_cell_value) == 1:
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                current_run = 1
            previous_cell_value = value

        return max_run != assignment[self.count_cell]

    def quick_update(self):
        self.count_cell.possibles = self.count_cell.possibles.intersection(
            {i + 1 for i, _ in enumerate(self.subject_cells)}
        )


class InternalLittleKiller(Constraint):
    def __init__(self, board, sum_cell, direction_indicator_cells):
        unnormalised_direction = np.array(sum_cell.coordinates) - np.array(
            direction_indicator_cells[0].coordinates
        )
        direction = (
            unnormalised_direction // np.linalg.norm(unnormalised_direction)
        ).astype(int)

        d1 = direction.copy()
        d1[d1 == 0] = 1

        d2 = direction.copy()
        d2[d2 == 0] = -1

        def generate_diagonal(d):
            diagonal = []
            current_cell = (np.array(sum_cell.coordinates) + d).astype(int)
            while all(i not in current_cell for i in {0, 5, 10}):
                diagonal.append(board[tuple(current_cell)])
                current_cell += d
            return diagonal

        self.diagonal_1 = generate_diagonal(d1)
        self.diagonal_2 = generate_diagonal(d2)
        self.sum_cell = sum_cell

        super().__init__(board, [sum_cell] + self.diagonal_1 + self.diagonal_2)
        self.name = (
            f"Internal Little Killer {sum_cell}: {self.diagonal_1} or {self.diagonal_2}"
        )

    def partial_assignment_invalid(self, assignment):
        if self.sum_cell not in assignment:
            return

        if all([c in assignment for c in self.diagonal_1]) and self.diagonal_1:
            diagonal_1_sum = sum([assignment[c] for c in self.diagonal_1])
            diagonal_1_valid = diagonal_1_sum == assignment[self.sum_cell]
        else:
            diagonal_1_valid = True

        if all([c in assignment for c in self.diagonal_2]) and self.diagonal_2:
            diagonal_2_sum = sum([assignment[c] for c in self.diagonal_2])
            diagonal_2_valid = diagonal_2_sum == assignment[self.sum_cell]
        else:
            diagonal_2_valid = True

        if not diagonal_1_valid and not diagonal_2_valid:
            return True


class InternalNinesNeighbours(Constraint):
    def __init__(self, board, sum_cell, subject_cells):
        super().__init__(board, [sum_cell] + subject_cells)
        self.sum_cell = sum_cell
        self.subject_cells = subject_cells
        self.name = "Nine's neighbours {}: {}".format(self.sum_cell, self.subject_cells)

    def partial_assignment_invalid(self, assignment):
        if len(assignment) != len(self.cells):
            return

        if len(set(assignment.values())) != len(self.cells):
            return True

        if 9 not in assignment.values():
            return True

        if assignment[self.sum_cell] == 9:
            return True

        nine_cell = [cell for cell in self.subject_cells if assignment[cell] == 9][0]
        nine_neighbours = [
            cell
            for cell in self.subject_cells
            if cell.manhattan_distance(nine_cell) == 1
        ]
        nine_neighbours_sum = 9 - sum([assignment[cell] for cell in nine_neighbours])

        return nine_neighbours_sum != assignment[self.sum_cell]
