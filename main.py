from propagators import DecisionOrderPropagator
import clingo

if __name__ == '__main__':

    ctl = clingo.Control()
    ctl.register_propagator(DecisionOrderPropagator())
    ctl.load("logic_programs/pigeon_hole.lp")
    ctl.ground([("base", [])])
    print(ctl.solve(on_model=lambda x: print("+ MODEL FOUND:", x)))
