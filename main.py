from propagators import DecisionOrderPropagator
import clingo

if __name__ == '__main__':

    ctl = clingo.Control()
    p = DecisionOrderPropagator()
    ctl.register_propagator(p)
    ctl.load("logic_programs/pigeon_hole.lp")
    ctl.ground([("base", [])])
    print(ctl.solve(on_model=lambda x: print("+ MODEL FOUND:", x)))
    print("Values:")
    print(p.values)
