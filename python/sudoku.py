from collections import deque, Counter
from copy import deepcopy
import io
import itertools
import numpy as np
import networkx as nx
import sys
from traceback import format_exc
import uuid

from tqdm import tqdm as tq

ALL_POSSIBLE_ASSIGNMENTS_LIMIT = 1e5 + 1
BIFURCATION_LIMIT = 1e5
N_TUPLE_NAMES = {
    1: "single",
    2: "pair",
    3: "triple",
    4: "quadruple",
    5: "quintuple",
    6: "sextuple",
    7: "septuple",
    8: "octuple",
}
msg_indent = 0


def print_msg(msg, indent_override=None):
    lines = str(msg).split("\n")
    for line in lines:
        print(
            "  " * (msg_indent if indent_override is None else indent_override) + line
        )

    sys.stdout.flush()


def get_box(row, column):
    cell_index = 9 * (row - 1) + (column - 1)
    box_row = cell_index // 27
    box_col = (cell_index % 9) // 3
    return 3 * box_row + box_col + 1


class SudokuContradiction(Exception):
    pass


class NoSolutionFound(Exception):
    pass


class MultipleSolutionsFound(Exception):
    pass


class Board:
    def __init__(self):
        self.cells = []
        self.constraints = []
        for row in range(1, 10):
            for column in range(1, 10):
                Cell(self, row, column)

        for i in range(1, 10):
            Row(self, i)
            Column(self, i)
            Box(self, i)

        self.unfinalised_cells = set(self.cells)
        self.constraints_to_check = deque()
        self.unbifurcated_cells = set(self.cells)
        self.end_after_bifurcation = True
        self.solution_snapshots = set()
        self.known_pairs = set()

    def __getitem__(self, item):
        return self.get_cell(*item)

    def __repr__(self):
        output = ""
        max_possibles = max([len(cell.possibles) for cell in self.cells])
        for i, cell in enumerate(self.cells):
            if i == 0:
                pass
            elif i % 9 == 0:
                output += "\n"
                if i % 27 == 0:
                    output += "-" * ((max_possibles + 1) * 9 + 1) + "\n"
            elif i % 3 == 0:
                output += "|"
            output += "".join(map(str, sorted(cell.possibles))).ljust(max_possibles + 1)
        return output

    def get_cell(self, row, column):
        return self.cells[(row - 1) * 9 + column - 1]

    def is_solved(self):
        return not bool(self.unfinalised_cells)

    def add_known_pair(self, c1, c2):
        self.known_pairs.add((c1, c2))
        self.known_pairs.add((c2, c1))

    def solve(self):
        for constraint in sorted(self.constraints, key=lambda c: len(c.cells)):
            self.constraints_to_check.append(constraint)
            constraint.initialise_seen_graph()
            constraint.initialise_possibles()

        self.process_constraint_queue()

    def process_constraint_queue(self, constraint_limit=None, on_bifurcation=False):
        with tq(total=self.total_possibles, disable=True) as bar:
            constraints_processed = 0
            last_changed = 0
            constraints_count = 0
            while self.unfinalised_cells:
                while self.constraints_to_check:
                    start_snapshot = self.snapshot()
                    constraint = self.constraints_to_check.popleft()
                    constraint.check()
                    end_snapshot = self.snapshot()
                    board_changed = end_snapshot != start_snapshot

                    if board_changed:
                        bar.update(
                            sum([len(cell) for cell in start_snapshot])
                            - sum([len(cell) for cell in end_snapshot])
                        )
                        last_changed = constraints_count
                    else:
                        if constraints_count - last_changed > len(self.constraints):
                            break
                    constraints_count += 1

                    if constraint_limit is not None:
                        if board_changed:
                            constraints_processed += 1
                            if (
                                not (constraint_limit is None)
                                and constraints_processed > constraint_limit
                            ):
                                print_msg(
                                    "No contradiction or solution discovered within {} deductions".format(
                                        constraint_limit
                                    )
                                )
                                break

                if not self.unfinalised_cells:
                    break

                if not on_bifurcation:
                    while self.unbifurcated_cells:
                        bifurcation_successful = self.bifurcate()
                        if bifurcation_successful:
                            break

                    if (not self.unbifurcated_cells) and (
                        not self.end_after_bifurcation
                    ):
                        self.unbifurcated_cells = {
                            cell for cell in self.cells if not cell.finalised
                        }
                        self.constraints_to_check.extend(self.constraints)
                        self.end_after_bifurcation = True

                if not self.constraints_to_check:
                    raise NoSolutionFound("No solution could be found!")

            if self.unfinalised_cells:
                raise NoSolutionFound("No solution could be found!")

            self.final_constraint_check()

    @property
    def total_possibles(self):
        return sum([len(cell.possibles) for cell in self.cells])

    def add_solution_snapshot(self, board):
        snapshot = board.snapshot()
        if snapshot not in self.solution_snapshots:
            print_msg("Solution found!")
            print_msg(self)
        self.solution_snapshots.add(snapshot)
        if len(self.solution_snapshots) > 1:
            raise MultipleSolutionsFound(
                "Multiple solutions found: {}".format(
                    "\n\n".join(map(str, self.solution_snapshots))
                )
            )

    def final_constraint_check(self):
        for constraint in self.constraints:
            constraint.check()

    def snapshot(self):
        return self.__repr__()

    def bifurcate(self):
        _stdout = sys.stdout
        bifurcation_stdout = io.StringIO()
        sys.stdout = bifurcation_stdout

        global msg_indent
        bifurcation_target = min(
            self.unbifurcated_cells,
            key=lambda cell: (
                len(cell.possibles),
                -cell.bifurcation_score,
            ),
        )
        for pair in self.known_pairs:
            if bifurcation_target in pair:
                other_cell = min([cell for cell in pair if cell != bifurcation_target])
                if other_cell in self.unbifurcated_cells:
                    self.unbifurcated_cells.remove(other_cell)

        print_msg(
            "Bifurcating on {} ({}, {} bifurcations left)".format(
                bifurcation_target,
                bifurcation_target.possibles,
                len(self.unbifurcated_cells),
            )
        )
        to_remove = set()
        self.unbifurcated_cells.remove(bifurcation_target)
        msg_indent += 1
        for possible in bifurcation_target.possibles:
            possible_stdout = io.StringIO()
            sys.stdout = possible_stdout
            print_msg("Bifurcating on {}".format(possible), indent_override=0)
            new_board = deepcopy(self)
            try:
                GivenDigit(
                    new_board,
                    bifurcation_target.row,
                    bifurcation_target.column,
                    possible,
                )
                new_board.constraints_to_check.extend(
                    new_board.get_cell(
                        bifurcation_target.row, bifurcation_target.column
                    ).constraints
                )
                new_board.process_constraint_queue(
                    constraint_limit=BIFURCATION_LIMIT, on_bifurcation=True
                )
                self.final_constraint_check()
                self.add_solution_snapshot(new_board)
                sys.stdout = bifurcation_stdout
                print(possible_stdout.getvalue())

            except SudokuContradiction as e:
                print_msg("Contradiction: {}".format(e))
                print_msg(
                    "Contradiction found, {} eliminated for {}".format(
                        possible, bifurcation_target
                    ),
                    indent_override=0,
                )
                to_remove.add(possible)
                sys.stdout = bifurcation_stdout
                print(possible_stdout.getvalue())

            except NoSolutionFound as e:
                print_msg(
                    "No contradiction or solution found for {} = {}".format(
                        bifurcation_target, possible
                    )
                )
            finally:
                sys.stdout = bifurcation_stdout

        msg_indent -= 1
        bifurcation_successful = len(to_remove) > 0

        sys.stdout = _stdout

        if bifurcation_successful:
            print(bifurcation_stdout.getvalue())
            sys.stdout.flush()
            bifurcation_target.remove_possibles(to_remove)
            self.constraints_to_check.extend(bifurcation_target.constraints)
            self.end_after_bifurcation = False

        return bifurcation_successful


class Constraint:
    def __init__(self, board, cells):
        self.board = board
        self.cells = list(cells)
        for cell in self.cells:
            cell.constraints.append(self)
        board.constraints.append(self)
        self.corner_marks = {}

    def initialise_seen_graph(self):
        self.seen_graph = nx.Graph()
        for cell in self.cells:
            self.seen_graph.add_node(cell)

        for c1, c2 in itertools.combinations(self.cells, 2):
            if c1 == c2:
                continue
            common_constraints = [
                constraint
                for constraint in c1.constraints
                if constraint in c2.constraints
                if issubclass(type(constraint), NoRepeatsConstraint)
            ]
            if len(common_constraints) > 0:
                self.seen_graph.add_edge(c1, c2)

    def add_corner_mark(self, digit, cells):
        """
        Returns True if any possibilities have changed as a result of this pencil mark
        """
        start_snapshot = self.snapshot_possibles()
        self.corner_marks[digit] = cells
        self.process_corner_mark(digit, cells)
        end_snapshot = self.snapshot_possibles()

        return start_snapshot != end_snapshot

    def assignment_violates_corner_marks(self, assignment):
        for digit, cells in self.corner_marks.items():
            if not any([assignment.get(cell, digit) == digit for cell in cells]):
                return True
        return False

    def partial_assignment_invalid(self, assignment):
        """
        Assignment is a dict of Cells to values, returns a boolean showing if this is valid
        """
        for c1, c2 in self.seen_graph.edges():
            if assignment.get(c1, "C1 not there") == assignment.get(c2, "C2 not there"):
                return True

        return self.assignment_violates_corner_marks(assignment)

    def check(self):
        start_snapshot = self.snapshot_possibles()
        try:
            if hasattr(self, "quick_update"):
                self.quick_update()

            self.process_check()

            end_snapshot = self.snapshot_possibles()

            # print(
            #     "Checking {} (Queue size {})".format(
            #         self.name, len(self.board.constraints_to_check)
            #     )
            # )
            if start_snapshot != end_snapshot:
                print_msg("Change detected checking {}".format(self.name))
                for cell, cell_start_snapshot, cell_end_snapshot in zip(
                    self.cells, start_snapshot, end_snapshot
                ):
                    if cell_end_snapshot != cell_start_snapshot:
                        self.board.constraints_to_check.extend(cell.constraints)
                return True
            return False
        except Exception as e:
            print_msg(
                "Exception raised checking {}:\n\n {}".format(self.name, format_exc())
            )
            raise e

    def process_check(self):
        self.update_possibles()

    def process_corner_mark(self, digit, cells):
        pass

    def initialise_possibles(self):
        for cell in self.cells:
            valid_possibles = set()
            for possible in cell.possibles:
                if not self.partial_assignment_invalid({cell: possible}):
                    valid_possibles.add(possible)
            cell.intersect_possibles(valid_possibles)

    def update_possibles(self):
        possibles_for_cells = [cell.possibles for cell in self.cells]
        if (
            np.prod([len(possibles) for possibles in possibles_for_cells])
            > ALL_POSSIBLE_ASSIGNMENTS_LIMIT
        ):
            return

        all_possible_assignments = []

        def recurse_assignments(current_assignment={}):

            possible_pivots = [
                cell for cell in self.cells if cell not in current_assignment
            ]
            if len(possible_pivots) == 0:
                return
            pivot_cell = min(
                possible_pivots,
                key=lambda cell: len(cell.possibles),
            )

            for possible in pivot_cell.possibles:
                new_assignment = {k: v for k, v in current_assignment.items()}
                new_assignment[pivot_cell] = possible
                if not self.partial_assignment_invalid(new_assignment):
                    if len(new_assignment) == len(self.cells):
                        all_possible_assignments.append(new_assignment)
                    else:
                        recurse_assignments(new_assignment)

        recurse_assignments()

        if len(all_possible_assignments) == 0:
            raise SudokuContradiction(
                "The constraint {} can no longer be satisfied with possibles {} and pencil marks {}".format(
                    self, possibles_for_cells, self.corner_marks
                )
            )

        for cell in self.cells:
            possibles = set()
            possibles.update(
                (assignment_dict[cell] for assignment_dict in all_possible_assignments)
            )
            cell.intersect_possibles(possibles)

    def snapshot_possibles(self):
        return tuple([cell.snapshot_possibles() for cell in self.cells])

    def __repr__(self):
        return self.name


class FinaliseConstraint(Constraint):
    def __init__(self, board, cell):
        super().__init__(board, [cell])
        self.name = "Finalise {}".format(cell)

    def process_check(self):
        if len(self.cells[0].possibles) == 1:
            self.cells[0].finalise()

    def partial_assignment_invalid(self, assignment):
        return False


class NoRepeatsConstraint(Constraint):
    def __init__(self, board, cells):
        super().__init__(board, cells)
        self.tuples_noted = set()

    def initialise_seen_graph(self):
        self.seen_graph = nx.Graph()
        for cell in self.cells:
            self.seen_graph.add_node(cell)

    def partial_assignment_invalid(self, assignment):
        output = len(set(assignment.values())) != len(assignment)
        return output

    def process_check(self):
        self.remove_finalised()

        for digit in range(1, 10):
            self.detect_corner_marks(digit)

        for n in range(1, 9 - len([cell for cell in self.cells if cell.finalised])):
            self.check_for_corner_mark_tuples(n)
            self.detect_and_action_n_tuples(n)

        super().process_check()

    def remove_finalised(self):
        finalised_digits = {cell.value for cell in self.cells if cell.finalised}

        for cell in self.cells:
            cell.remove_possibles(finalised_digits)

    def check_for_corner_mark_tuples(self, n):
        if len(self.corner_marks) <= n:
            return

        start_snapshot = self.snapshot_possibles()
        for marks in itertools.combinations(self.corner_marks, n):
            all_cells = {cell for mark in marks for cell in self.corner_marks[mark]}
            if len(all_cells) <= n:
                for cell in all_cells:
                    cell.intersect_possibles(marks)

        if start_snapshot != self.snapshot_possibles():
            print_msg(
                "Pencil marks tell me that cells {} must be from {}.".format(
                    ", ".join(map(str, all_cells)), ", ".join(map(str, marks))
                )
            )

    def detect_and_action_n_tuples(self, n):
        """
        If repeats are allowed in this constraint, detect pairs, triples etc and remove possibles
        accordingly.
        """
        unfinalised_cells = [cell for cell in self.cells if not cell.finalised]

        for combination in itertools.combinations(unfinalised_cells, n):
            combination = tuple(sorted(combination))
            complement_combination = tuple(
                sorted(
                    [
                        cell
                        for cell in self.cells
                        if not cell.finalised and not cell in combination
                    ]
                )
            )
            if combination in self.tuples_noted:
                continue

            if any((cell.finalised for cell in combination)):
                continue
            all_possibles = {
                possible for cell in combination for possible in cell.possibles
            }
            if len(all_possibles) <= n:
                start_snapshot = self.snapshot_possibles()
                for cell in self.cells:
                    if cell not in combination:
                        try:
                            cell.remove_possibles(all_possibles)
                        except Exception as e:
                            print_msg(
                                "{} {} found in {}".format(
                                    "".join(map(str, sorted(all_possibles))),
                                    N_TUPLE_NAMES[n],
                                    self.name,
                                )
                            )
                            raise e

                if self.snapshot_possibles() != start_snapshot:
                    if len(complement_combination) > 1:
                        print_msg(
                            "{} {} found in {}".format(
                                "".join(map(str, sorted(all_possibles))),
                                N_TUPLE_NAMES[n],
                                self.name,
                            )
                        )
                    else:
                        possibles = {
                            possible
                            for possible in complement_combination[0].possibles
                            if possible not in all_possibles
                        }
                        print_msg(
                            "Where can the {} go in {}?".format(min(possibles), self)
                        )
                self.note_tuple(combination)
                self.note_tuple(complement_combination)

    def note_tuple(self, to_note):
        to_note = tuple(sorted(to_note))
        self.tuples_noted.add(to_note)
        if len(to_note) == 2:
            self.board.known_pairs.add(to_note)

    def detect_corner_marks(self, digit):
        if len(self.cells) < 9:
            return
        possible_cells = [
            cell
            for cell in self.cells
            if digit in cell.possibles and not cell.finalised
        ]
        if len(possible_cells) == 1:
            possible_cells[0].possibles = {
                digit,
            }
            print_msg(
                "The {} in {} can only go in {}".format(digit, self, possible_cells[0])
            )
            self.board.constraints_to_check.appendleft(
                possible_cells[0].finalise_constraint
            )
            return

        constraints = Counter(
            (constraint for cell in possible_cells for constraint in cell.constraints)
        )
        common_constraints = [
            constraint
            for constraint, count in constraints.items()
            if count == len(possible_cells) and constraint != self
        ]
        if not common_constraints:
            return
        cells_to_edit = []

        # Capture print output from pencil marks (we want to explain the deduction before presenting to the user)
        stdout = sys.stdout
        changelog = io.StringIO()
        sys.stdout = changelog
        changed = False
        try:
            if common_constraints:
                for constraint in common_constraints:
                    changed = changed or constraint.add_corner_mark(
                        digit, possible_cells
                    )
        finally:
            sys.stdout = stdout

        if changed:
            print_msg(
                "The {} in {} must go in one of {}".format(
                    digit, self, ", ".join(map(str, possible_cells))
                )
            )
            change_string = changelog.getvalue().strip()
            if change_string:
                print_msg(change_string)

            for cell in cells_to_edit:
                cell.remove_possible(digit)

    def process_corner_mark(self, digit, cells):
        for cell in self.cells:
            if cell not in cells:
                cell.remove_possible(digit)


class Row(NoRepeatsConstraint):
    def __init__(self, board, index):
        cells = [cell for cell in board.cells if cell.row == index]
        self.name = "Row {}".format(index)
        super().__init__(board, cells)


class Column(NoRepeatsConstraint):
    def __init__(self, board, index):
        cells = [cell for cell in board.cells if cell.column == index]
        self.name = "Column {}".format(index)
        super().__init__(board, cells)


class Box(NoRepeatsConstraint):
    def __init__(self, board, index):
        cells = [cell for cell in board.cells if cell.box == index]
        self.name = "Box {}".format(index)
        super().__init__(board, cells)


class GivenDigit(Constraint):
    def __init__(self, board, row, column, digit):
        cells = [board.get_cell(row, column)]
        self.digit = digit
        self.name = "Given {} in row {} column {}".format(digit, row, column)
        super().__init__(board, cells)
        self.finalise_cell()

    def partial_assignment_invalid(self, assignment):
        if self.cells[0] in assignment:
            return assignment[self.cells[0]] != self.digit
        return False

    def finalise_cell(self):
        self.cells[0].possibles = {
            self.digit,
        }
        self.cells[0].finalise()
        for constraint in self.cells[0].constraints:
            if type(constraint) in [Row, Column, Box]:
                constraint.remove_finalised()


class Cell:
    def __init__(self, board, row, column):
        self.row = row
        self.column = column
        self.board = board
        self.box = get_box(row, column)
        self.finalised = False

        self.possibles = set(range(1, 10))
        self.constraints = []
        self.board.cells.append(self)
        self.finalise_constraint = FinaliseConstraint(board, self)

    def __repr__(self):
        return "R{}C{}".format(self.row, self.column, self.possibles)

    def __hash__(self):
        if not hasattr(self, "id"):
            self.id = uuid.uuid4()
        return hash(self.id)

    def __lt__(self, other):
        return hash(self) < hash(other)

    def finalise(self):
        if self.finalised:
            return
        assert (
            len(self.possibles) == 1
        ), "Error: attempting to finalise a cell that can still take two values!"

        self.value = min(self.possibles)
        if not any([type(constraint) is GivenDigit for constraint in self.constraints]):
            print_msg("Finalising {} as {}".format(self, self.value))
        self.finalised = True

        for constraint in self.constraints:
            if hasattr(constraint, "remove_finalised"):
                constraint.remove_finalised()

        self.board.unfinalised_cells.remove(self)
        if self in self.board.unbifurcated_cells:
            self.board.unbifurcated_cells.remove(self)

    def remove_possible(self, value):
        if value not in self.possibles:
            return
        self.remove_possibles([value])

    def remove_possibles(self, values):
        if self.finalised:
            return

        for value in values:
            if value in self.possibles:
                self.possibles.remove(value)
                if len(self.possibles) == 0:
                    raise SudokuContradiction("No values left in {}".format(self))
                if len(self.possibles) == 1:
                    self.board.constraints_to_check.appendleft(self.finalise_constraint)

    def snapshot_possibles(self):
        return tuple(sorted({i for i in self.possibles}))

    @property
    def coordinates(self):
        return (self.row, self.column)

    @property
    def index_in_box(self):
        sorted_box_cells = list(
            sorted(
                [cell for cell in self.board.cells if cell.box == self.box],
                key=lambda cell: cell.coordinates,
            )
        )
        return sorted_box_cells.index(self) + 1

    @property
    def bifurcation_score(self):
        cells_sharing_constraint = {
            cell
            for constraint in self.constraints
            for cell in constraint.cells
            if issubclass(type(constraint), NoRepeatsConstraint)
            and not cell.finalised
            and cell.possibles.intersection(self.possibles)
        }
        return sum([1 / len(cell.possibles) ** 3 for cell in cells_sharing_constraint])

    def intersect_possibles(self, others):
        to_remove = set()
        for possible in self.possibles:
            if possible not in others:
                to_remove.add(possible)
        if to_remove:
            self.remove_possibles(to_remove)

    def manhattan_distance(self, other_cell):
        return abs(self.coordinates[0] - other_cell.coordinates[0]) + abs(
            self.coordinates[1] - other_cell.coordinates[1]
        )
