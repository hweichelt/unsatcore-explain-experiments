from propagators import DecisionOrderPropagator
import clingo


def print_leveled_list(leveled_list, name=None):
    if name is not None:
        print(f"[{name}]")
    for l, level in enumerate(leveled_list):
        last_level = l == len(leveled_list) - 1
        print("└──" if last_level else "├──", level[0])
        if len(level) > 1:
            for i in range(1,len(level)):
                prefix = " " if last_level else "│"
                print(f"{prefix}   └──" if i == len(level) - 1 else f"{prefix}   ├──", level[i])


if __name__ == '__main__':

    ctl = clingo.Control()
    dop = DecisionOrderPropagator()
    ctl.register_propagator(dop)
    ctl.load("logic_programs/pigeon_hole.lp")
    ctl.ground([("base", [])])
    print(ctl.solve(on_model=lambda x: print("+ MODEL FOUND:", x)))
    print(dop.decision_levels)
    sym_decision_levels = dop.get_symbolic_decision_levels()

    print()
    print_leveled_list(sym_decision_levels, name="Solver Decisions")

    print()
    print("\n".join(sorted([str(s) for s in dop.get_decisions_as_logic_program()])))
