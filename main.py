from propagators import DecisionOrderPropagator, DecisionOrderPropagatorSingle
import clingo


def print_leveled_list(leveled_list, name=None):
    if name is not None:
        print(f"[{name}]")
    for l, level in enumerate(leveled_list):
        last_level = l == len(leveled_list) - 1
        print("└──" if last_level else "├──", level[0])
        if len(level) > 1:
            for i in range(1, len(level)):
                prefix = " " if last_level else "│"
                print(f"{prefix}   └──" if i == len(level) - 1 else f"{prefix}   ├──", level[i])


if __name__ == '__main__':

    ctl = clingo.Control()
    dop = DecisionOrderPropagatorSingle("place(2,2)", verbose=1)
    ctl.register_propagator(dop)
    ctl.load("logic_programs/pigeon_hole.lp")
    ctl.ground([("base", [])])
    print(ctl.solve(on_model=lambda x: print("+ MODEL FOUND:", x)))

    for decision_levels in dop.get_decision_history():
        level_symbolic = [[str(dop.get_symbol(lit)) for lit in level] for level in decision_levels]
        print("\n" + "*"*100 + "\n")
        print(level_symbolic)
        print_leveled_list(level_symbolic)
