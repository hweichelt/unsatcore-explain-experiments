import clingo
from clingo.symbol import Function
from clingo.propagator import Propagator
from clingo.control import Control


class PigeonHoleVerbosePropagator(Propagator):

    def __init__(self):
        self.pigeon = {}
        self.place = {}
        self.state = []

    def init(self, init) -> None:
        for atom in init.symbolic_atoms.by_signature("place", 2):
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.place[solver_literal] = atom.symbol.arguments[1]
            self.pigeon[solver_literal] = atom.symbol.arguments[0]
            init.add_watch(solver_literal)
        self.state = [{} for _ in range(init.number_of_threads)]

    def propagate(self, control, changes) -> None:
        holes = self.state[control.thread_id]
        print(control.thread_id, holes)
        for solver_literal in changes:
            hole = self.place[solver_literal]
            prev = holes.setdefault(hole, solver_literal)
            print("- hole", hole, "← pigeon", self.pigeon[solver_literal], f"({solver_literal})")
            if prev != solver_literal and not control.add_nogood([solver_literal, prev]):
                print("\tpigeon (", self.pigeon[prev], "↯", self.pigeon[solver_literal], ") in hole", hole)
                print("CONFLICT")
                return

    def undo(self, thread_id: int, assignment, changes) -> None:
        print(thread_id, "UNDO", changes)
        holes = self.state[thread_id]
        for solver_literal in changes:
            hole = self.place[solver_literal]
            if holes.get(hole) == solver_literal:
                del holes[hole]


class PigeonHoleOrderPropagator(Propagator):

    def __init__(self):
        self.pigeon = {}
        self.place = {}
        self.state = []
        self.decisions = 0
        self.slit_to_symbol = {}

    def init(self, init) -> None:
        for atom in init.symbolic_atoms:
            self.slit_to_symbol[atom.literal] = str(atom.symbol)
        print("\n".join([f"{k}: {v}" for k, v in self.slit_to_symbol.items()]))
        for atom in init.symbolic_atoms.by_signature("place", 2):
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.place[solver_literal] = atom.symbol.arguments[1]
            self.pigeon[solver_literal] = atom.symbol.arguments[0]
            init.add_watch(solver_literal)
        self.state = [{} for _ in range(init.number_of_threads)]
        print([x for x in init.assignment.trail])

    def propagate(self, control, changes) -> None:
        holes = self.state[control.thread_id]
        print(control.thread_id, holes)
        print([x for x in control.assignment.trail])
        self.decisions += 1
        leveled_trail = self.get_trail_levels(control.assignment.trail, control.assignment)
        print(leveled_trail)
        for solver_literal in changes:
            hole = self.place[solver_literal]
            prev = holes.setdefault(hole, solver_literal)
            print("- hole", hole, "← pigeon", self.pigeon[solver_literal], f"({solver_literal})")
            if prev != solver_literal and not control.add_nogood([solver_literal, prev]):
                print("\tpigeon (", self.pigeon[prev], "↯", self.pigeon[solver_literal], ") in hole", hole)
                print("CONFLICT")
                return

    @staticmethod
    def get_trail_levels(trail, assigment):
        i = 0
        leveled_trail = []
        try:
            while True:
                level_start_offset = trail.begin(i)
                level_end_offset = trail.end(i)
                leveled_trail.append(trail[level_start_offset:level_end_offset])
                print(assigment.decision(i))
                i += 1
        except RuntimeError:
            return leveled_trail

    def undo(self, thread_id: int, assignment, changes) -> None:
        print(thread_id, "UNDO", changes)
        holes = self.state[thread_id]
        for solver_literal in changes:
            hole = self.place[solver_literal]
            if holes.get(hole) == solver_literal:
                del holes[hole]


class DecisionOrderPropagator(Propagator):

    def __init__(self):
        self.decision_levels = []
        self._slit_symbol_lookup = {}

    def init(self, init):
        self._slit_symbol_lookup = {}
        print("SOLVER LITERALS:", sorted([init.solver_literal(a.literal) for a in init.symbolic_atoms]))
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self._slit_symbol_lookup[solver_literal] = atom.symbol
            init.add_watch(solver_literal)
            init.add_watch(-solver_literal)

    def propagate(self, control, changes):
        decisions, entailments = self.get_decisions(control.assignment)
        self.decision_levels = [[d] + list(entailments[d]) if d in entailments else [d] for d in decisions]
        # print(f"\nPROPAGATION STEP", "-" * 30)
        # for i, literal in enumerate(decisions):
        #     final_decision = i == len(decisions) - 1
        #     print(f"{'└──' if final_decision else '├──'}({i})", literal)
        #     if literal in entailments:
        #         print("    └──" if final_decision else "│   └──" , entailments[literal])

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

    def get_symbolic_decision_levels(self):
        output = []
        for decision_level in self.decision_levels:
            symbolic_level = []
            for slit in decision_level:
                if slit in self._slit_symbol_lookup:
                    symbolic_level.append(str(self._slit_symbol_lookup[slit]))
                elif -slit in self._slit_symbol_lookup:
                    symbolic_level.append(f"- {str(self._slit_symbol_lookup[-slit])}")
                else:
                    symbolic_level.append(f"internal_literal({slit})")
            output.append(symbolic_level)
        return output

    def get_decisions_as_logic_program(self):
        output = []
        for l, level in enumerate(self.decision_levels):
            for s, slit in enumerate(level):
                if slit in self._slit_symbol_lookup:
                    symbol = self._slit_symbol_lookup[slit]
                    name = "in_model"
                elif -slit in self._slit_symbol_lookup:
                    symbol = self._slit_symbol_lookup[-slit]
                    name = "not_in_model"
                else:
                    continue

                output.append(clingo.parse_term(f"{name}({str(symbol)})"))
                if s == 0:
                    output.append(clingo.parse_term(f"decision_order({l}, {str(symbol)})"))
                else:
                    output.append(clingo.parse_term(f"entailed_by_decision({l}, {str(symbol)})"))
        return output


class DecisionOrderPropagatorSingle(DecisionOrderPropagator):
    def __init__(self, query_atom):
        self.query_atom = clingo.parse_term(query_atom)

    def init(self, init):
        self._slit_symbol_lookup = {}
        print(f"SINGLE D.O. PROPAGATOR: query_atom='{str(self.query_atom)}'")
        print("SOLVER LITERALS:", sorted([init.solver_literal(a.literal) for a in init.symbolic_atoms]))
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self._slit_symbol_lookup[solver_literal] = atom.symbol

        if self.query_atom in init.symbolic_atoms:
            program_literal = init.symbolic_atoms[self.query_atom].literal
            solver_literal = init.solver_literal(program_literal)
            init.add_watch(solver_literal)
            init.add_watch(-solver_literal)
        else:
            raise ValueError("query_atom has to be a valid atom contained in init.symbolic_atoms")
