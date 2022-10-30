from collections import Counter, defaultdict, deque
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
MAX_BIFURCATION_LEVEL = 1
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


class NoBifurcationsLeft(Exception):
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

        self.forcing_values = nx.DiGraph()
        self.forcing_values.add_nodes_from(
            [(cell, value) for cell in self.cells for value in cell.possibles]
        )

        self.unfinalised_cells = set(self.cells)
        self.constraints_to_check = deque()
        self.attempted_bifurcations = set()
        self.end_after_bifurcation = True
        self.solution_snapshots = set()
        self.known_pairs = set()
        self.bifurcation_level = 0
        self.previous_bifurcation = None

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
        self._initialise_seen_graph()

        for constraint in sorted(self.constraints, key=lambda c: len(c.cells)):
            self.constraints_to_check.append(constraint)
            constraint.initialise()

        self.process_constraint_queue()

    def process_constraint_queue(self, constraint_limit=None):
        with tq(total=self.total_possibles, disable=True) as bar:
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

                if self.quick_bifurcation_check():
                    continue

                if not self.unfinalised_cells:
                    break

                if self.bifurcation_level < MAX_BIFURCATION_LEVEL:
                    try:
                        while True:
                            bifurcation_successful = self.bifurcate()
                            if bifurcation_successful:
                                break
                    except NoBifurcationsLeft:
                        self.attempted_bifurcations = set()
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

    def quick_bifurcation_check(self):
        to_remove = []
        for cell, value in self.forcing_values:
            out_component = list(nx.bfs_tree(self.forcing_values, (cell, value)))
            induced_seen_subgraph = self.contradiction_graph.subgraph(out_component)
            if induced_seen_subgraph.edges():
                to_remove.append((cell, value))
                print_msg(
                    "Assigning {} = {} leads to contradictions: {}. Removing this assignment.".format(
                        cell, value, list(induced_seen_subgraph.edges())
                    )
                )

        for cell, value in to_remove:
            cell.remove_possible(value)

        return bool(to_remove)

    def final_constraint_check(self):
        for constraint in self.constraints:
            constraint.check()

    def snapshot(self):
        return self.__repr__()

    def bifurcate(self):
        try:
            target_cell, target_value = self._select_bifurcation_target()

        except ValueError:
            raise NoSolutionFound("All bifurcations exhausted, no solution found.")

        before_snapshot = self.snapshot()
        self._bifurcate_on_cell_and_value(target_cell, target_value)
        return self.snapshot() != before_snapshot

    def common_constraints(self, cells):
        for constraint in self.constraints:
            if all([cell in constraint.cells for cell in cells]):
                yield constraint

    def _bifurcate_on_cell_and_value(self, cell, value):
        _stdout = sys.stdout
        bifurcation_stdout = io.StringIO()
        global msg_indent
        out_component = list(nx.bfs_tree(self.forcing_values, (cell, value)))

        sys.stdout = bifurcation_stdout
        print_msg(
            "Bifurcating on {} = {}".format(
                cell,
                value,
            )
        )
        self.attempted_bifurcations.add((cell, value))

        msg_indent += 1

        new_board = deepcopy(self)
        new_board.bifurcation_level = self.bifurcation_level + 1
        new_given_digits = []
        try:
            for forced_cell, forced_value in out_component:
                new_given_digits.append(
                    GivenDigit(
                        new_board,
                        forced_cell.row,
                        forced_cell.column,
                        forced_value,
                    )
                )
            new_board.constraints_to_check.extend(
                new_board.get_cell(cell.row, cell.column).constraints
            )
            new_board.constraints_to_check.extend(
                new_board.get_cell(cell.row, cell.column).constraints
            )
            new_board.process_constraint_queue()
            self.final_constraint_check()  # Solution found if we get to this bit
            self.add_solution_snapshot(new_board)
            sys.stdout = bifurcation_stdout
            print(bifurcation_stdout.getvalue())

        except SudokuContradiction as e:
            print_msg(
                "Contradiction found: {}. {} eliminated for {}".format(e, value, cell),
                indent_override=0,
            )
            sys.stdout = _stdout
            print(bifurcation_stdout.getvalue())
            sys.stdout.flush()
            cell.remove_possibles([value])
            self.constraints_to_check.extend(cell.constraints)

        except NoSolutionFound as e:
            print_msg(
                "No contradiction or solution found for {} = {}".format(cell, value)
            )

        msg_indent -= 1

        sys.stdout = _stdout

    def _initialise_seen_graph(self):
        self.seen_graph = nx.Graph()
        for cell in self.cells:
            self.seen_graph.add_node(cell)

        for c1, c2 in itertools.combinations(self.cells, 2):
            common_constraints = [
                constraint
                for constraint in c1.constraints
                if constraint in c2.constraints
                and issubclass(type(constraint), NoRepeatsConstraint)
            ]
            if len(common_constraints) > 0:
                self.seen_graph.add_edge(c1, c2)

        self.contradiction_graph = nx.Graph()
        for cell in self.cells:
            self.contradiction_graph.add_node(cell)

        for c1, c2 in self.seen_graph.edges():
            for value in range(1, 10):
                self.contradiction_graph.add_edge((c1, value), (c2, value))

        for cell in self.cells:
            for v1, v2 in itertools.combinations(range(1, 10), 2):
                self.contradiction_graph.add_edge((cell, v1), (cell, v2))

    def _select_bifurcation_target(self):
        possible_targets = {}
        for cell in self.cells:
            if len(cell.possibles) == 1:
                continue
            for value in cell.possibles:
                target = (cell, value)
                if target in self.attempted_bifurcations:
                    continue
                possible_targets[target] = len(nx.bfs_tree(self.forcing_values, target))

        return max(
            possible_targets,
            key=possible_targets.get,
        )


class Constraint:
    def __init__(self, board, cells):
        self.board = board
        self.cells = list(cells)
        for cell in self.cells:
            cell.constraints.append(self)
        board.constraints.append(self)
        self.corner_marks = {}

    def add_corner_mark(self, digit, cells):
        """
        Returns True if any possibilities have changed as a result of this pencil mark
        """
        print_msg("Adding {} corner mark to {} in {}".format(digit, cells, self))
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
        for c1, c2 in itertools.combinations(self.cells, 2):
            if c1 in self.board.seen_graph[c2] and assignment.get(
                c1, "C1 absent"
            ) == assignment.get(c2, "C2 absent"):
                return True

        return self.assignment_violates_corner_marks(assignment)

    def update_all_corner_marks(self, cell):
        for digit, cells in self.corner_marks.items():
            if cell not in cells:
                continue

            if digit not in cell.possibles:
                cells.remove(cell)

            if len(cells) == 1:
                if len(cells[0].possibles) > 1:
                    print_msg(
                        "The {} in {} can only go in {}".format(digit, self, cells[0])
                    )
                cells[0].intersect_possibles(
                    {
                        digit,
                    }
                )
                self.board.constraints_to_check.appendleft(cells[0].finalise_constraint)
            elif len(cells) == 2:
                c1, c2 = cells
                for value in c1.possibles:
                    if value != digit:
                        self.board.forcing_values.add_edge((c1, value), (c2, digit))

                for value in c2.possibles:
                    if value != digit:
                        self.board.forcing_values.add_edge((c2, value), (c1, digit))

            # Check if other constraints' pencil marks need
            # updating.
            for constraint in self.board.common_constraints(cells):
                if constraint is self:
                    continue
                if not isinstance(constraint, NoRepeatsConstraint):
                    continue
                for cell in constraint.cells:
                    if cell not in cells and digit in cell.possibles:
                        cell.remove_possible(digit)

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
                for cell in self.cells:
                    print_msg(
                        "  New possibles for {} are {}".format(cell, cell.possibles)
                    )
                return True

            return False
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print_msg(
                "Exception raised checking {}:\n\n {}".format(self.name, format_exc())
            )
            raise e

    def process_check(self):
        self.update_possibles()

    def process_corner_mark(self, digit, cells):
        pass

    def initialise(self):
        for cell in self.cells:
            valid_possibles = set()
            for possible in cell.possibles:
                if not self.partial_assignment_invalid({cell: possible}):
                    valid_possibles.add(possible)
            cell.intersect_possibles(valid_possibles)

    def update_possibles(self):
        all_possible_assignments = self.get_all_possible_assignments()
        if all_possible_assignments is None:
            return
        for cell in self.cells:
            possibles = set()
            possibles.update(
                (assignment_dict[cell] for assignment_dict in all_possible_assignments)
            )
            cell.intersect_possibles(possibles)

        # Note cell values that force other cell values
        dependency_graph = nx.Graph()
        for assignment in all_possible_assignments:
            for a1, a2 in itertools.combinations(assignment.items(), 2):
                if len(a1[0].possibles) == 1 or len(a2[0].possibles) == 1:
                    continue
                dependency_graph.add_edge(a1, a2)

        for c1, c2 in itertools.combinations(self.cells, 2):
            c1_nodes = [(c1, p) for p in c1.possibles]
            c2_nodes = [(c2, p) for p in c2.possibles]
            subgraph = dependency_graph.subgraph(c1_nodes + c2_nodes)
            forcing_nodes = [v for v in subgraph if subgraph.degree(v) == 1]
            forced_edges = [(v, list(subgraph[v])[0]) for v in forcing_nodes]
            self.board.forcing_values.add_edges_from(forced_edges)

        never_co_occur_graph = nx.complement(dependency_graph)
        self.board.contradiction_graph.add_edges_from(never_co_occur_graph.edges())

    def get_all_possible_assignments(self):
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

        return all_possible_assignments

    def snapshot_possibles(self):
        return tuple([cell.snapshot_possibles() for cell in self.cells])

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


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

    def partial_assignment_invalid(self, assignment):
        output = len(set(assignment.values())) != len(assignment)
        return output

    def initialise(self):
        super().initialise()
        self._initialise_corner_marks()

    def process_check(self):
        self.remove_finalised()

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

        for marks in itertools.combinations(self.corner_marks, n):
            all_cells = {cell for mark in marks for cell in self.corner_marks[mark]}
            if len(all_cells) <= n:
                start_snapshot = self.snapshot_possibles()
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

    def _initialise_corner_marks(self):
        if len(self.cells) < 9:
            return

        for digit in range(1, 10):
            cells = [cell for cell in self.cells if digit in cell.possibles]
            self.corner_marks[digit] = cells

    def process_corner_mark(self, digit, cells):
        for cell in self.cells:
            if cell not in cells:
                cell.remove_possible(digit)

    def update_possibles(self):
        super().update_possibles()
        all_possible_assignments = (
            self.get_all_possible_assignments()
        )  # TODO caching on this
        if all_possible_assignments is None:
            return
        digit_counts = defaultdict(int)
        for assignment in all_possible_assignments:
            for digit in set(assignment.values()):
                digit_counts[digit] += 1

        for digit, count in digit_counts.items():
            if count == len(all_possible_assignments):
                if digit not in self.corner_marks:
                    self.add_corner_mark(
                        digit, [cell for cell in self.cells if digit in cell.possibles]
                    )


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
        self.cells[0].intersect_possibles(
            {
                self.digit,
            }
        )
        self.cells[0].finalise()
        for constraint in self.cells[0].constraints:
            if isinstance(constraint, NoRepeatsConstraint):
                constraint.remove_finalised()


class Cell:
    def __init__(self, board, row, column):
        self.row = row
        self.column = column
        self.board = board
        self.box = get_box(row, column)
        self.finalised = False

        self._possibles = set(range(1, 10))
        self.constraints = []
        self.board.cells.append(self)
        self.finalise_constraint = FinaliseConstraint(board, self)

    def __repr__(self):
        return "R{}C{}".format(self.row, self.column)

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
            len(self._possibles) == 1
        ), "Error: attempting to finalise a cell that can still take two values!"

        self.value = min(self._possibles)
        if not any([type(constraint) is GivenDigit for constraint in self.constraints]):
            print_msg("Finalising {} as {}".format(self, self.value))
        self.finalised = True

        for constraint in self.constraints:
            if hasattr(constraint, "remove_finalised"):
                constraint.remove_finalised()

        self.board.unfinalised_cells.remove(self)
        nodes_to_remove = [v for v in self.board.forcing_values if v[0] == self]
        self.board.forcing_values.remove_nodes_from(nodes_to_remove)

    def remove_possible(self, value):
        if value not in self._possibles:
            return
        self.remove_possibles([value])

    def remove_possibles(self, values):
        if self.finalised:
            return

        to_remove = {value for value in values if value in self._possibles}

        for value in to_remove:
            self._possibles.remove(value)

            if (self, value) in self.board.forcing_values:
                self.board.forcing_values.remove_node((self, value))

            if len(self._possibles) == 0:
                raise SudokuContradiction("No values left in {}".format(self))
            if len(self._possibles) == 1:
                self.board.constraints_to_check.appendleft(self.finalise_constraint)

        if to_remove:
            for constraint in self.constraints:
                if constraint not in self.board.constraints_to_check:
                    self.board.constraints_to_check.append(constraint)

                constraint.update_all_corner_marks(self)

    def snapshot_possibles(self):
        return tuple(sorted({i for i in self._possibles}))

    @property
    def possibles(self):
        return self._possibles

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
            and cell.possibles.intersection(self._possibles)
        }
        return sum([1 / len(cell.possibles) ** 3 for cell in cells_sharing_constraint])

    def intersect_possibles(self, others):
        to_remove = set()
        for possible in self._possibles:
            if possible not in others:
                to_remove.add(possible)
        if to_remove:
            self.remove_possibles(to_remove)

    def manhattan_distance(self, other_cell):
        return abs(self.coordinates[0] - other_cell.coordinates[0]) + abs(
            self.coordinates[1] - other_cell.coordinates[1]
        )
