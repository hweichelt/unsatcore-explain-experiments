import clingo
from clingo.symbol import Function
from clingo.propagator import Propagator
from clingo.control import Control
from typing import List

DecisionLevel = List[int]
DecisionLevelList = List[DecisionLevel]


class DecisionOrderPropagatorSingle:

    def __init__(self, query_atom, verbose=0):
        self.query_atom = clingo.parse_term(query_atom)
        self.slit_symbol_lookup = {}
        self.decision_levels_history = []
        self.verbose = verbose

    def init(self, init):
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.slit_symbol_lookup[solver_literal] = atom.symbol

        if self.query_atom in init.symbolic_atoms:
            query_program_literal = init.symbolic_atoms[self.query_atom].literal
            query_solver_literal = init.solver_literal(query_program_literal)
            init.add_watch(query_solver_literal)
            init.add_watch(-query_solver_literal)
        else:
            raise ValueError("query_atom has to be a valid atom contained in init.symbolic_atoms")

    def propagate(self, control, changes) -> None:
        decisions, entailments = self.get_decisions(control.assignment)
        decision_levels_with_entailments = [[d] + list(entailments[d]) if d in entailments else [d] for d in decisions]
        self.decision_levels_history.append(decision_levels_with_entailments)

    def undo(self, thread_id: int, assignment, changes) -> None:
        if self.verbose > 0:
            print("UNDO")

    @staticmethod
    def get_decisions(assignment):
        level = 0
        decisions = []
        entailments = {}
        try:
            while True:
                decision = assignment.decision(level)
                decisions.append(decision)

                trail = assignment.trail
                level_offset_start = trail.begin(level)
                level_offset_end = trail.end(level)
                level_offset_diff = level_offset_end - level_offset_start
                if level_offset_diff > 1:
                    entailments[decision] = trail[(level_offset_start + 1):level_offset_end]
                level += 1
        except RuntimeError:
            return decisions, entailments

    def get_symbol(self, literal) -> clingo.Symbol:
        try:
            if literal > 0:
                symbol = self.slit_symbol_lookup[literal]
            else:
                # negate symbol
                symbol = clingo.parse_term(f"-{str(self.slit_symbol_lookup[-literal])}")
        except KeyError:
            # internal literals
            symbol = None
        return symbol

    def get_decision_history(self) -> List[DecisionLevelList]:
        return self.decision_levels_history
