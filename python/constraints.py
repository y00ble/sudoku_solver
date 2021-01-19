from sudoku import Constraint, NoRepeatsConstraint


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
