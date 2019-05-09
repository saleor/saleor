from __future__ import print_function, division

from sympy.assumptions.ask_generated import get_known_facts_cnf
from sympy.assumptions.assume import global_assumptions, AppliedPredicate
from sympy.assumptions.sathandlers import fact_registry
from sympy.core import oo, Tuple
from sympy.logic.inference import satisfiable
from sympy.logic.boolalg import And


def satask(proposition, assumptions=True, context=global_assumptions,
    use_known_facts=True, iterations=oo):
    relevant_facts = get_all_relevant_facts(proposition, assumptions, context,
        use_known_facts=use_known_facts, iterations=iterations)

    can_be_true = satisfiable(And(proposition, assumptions,
        relevant_facts, *context))
    can_be_false = satisfiable(And(~proposition, assumptions,
        relevant_facts, *context))

    if can_be_true and can_be_false:
        return None

    if can_be_true and not can_be_false:
        return True

    if not can_be_true and can_be_false:
        return False

    if not can_be_true and not can_be_false:
        # TODO: Run additional checks to see which combination of the
        # assumptions, global_assumptions, and relevant_facts are
        # inconsistent.
        raise ValueError("Inconsistent assumptions")


def get_relevant_facts(proposition, assumptions=(True,),
    context=global_assumptions, use_known_facts=True, exprs=None,
    relevant_facts=None):

    newexprs = set()
    if not exprs:
        keys = proposition.atoms(AppliedPredicate)
        # XXX: We need this since True/False are not Basic
        keys |= Tuple(*assumptions).atoms(AppliedPredicate)
        if context:
            keys |= And(*context).atoms(AppliedPredicate)

        exprs = {key.args[0] for key in keys}

    if not relevant_facts:
        relevant_facts = set([])

    if use_known_facts:
        for expr in exprs:
            relevant_facts.add(get_known_facts_cnf().rcall(expr))

    for expr in exprs:
        for fact in fact_registry[expr.func]:
            newfact = fact.rcall(expr)
            relevant_facts.add(newfact)
            newexprs |= set([key.args[0] for key in
                newfact.atoms(AppliedPredicate)])

    return relevant_facts, newexprs - exprs


def get_all_relevant_facts(proposition, assumptions=True,
    context=global_assumptions, use_known_facts=True, iterations=oo):
    # The relevant facts might introduce new keys, e.g., Q.zero(x*y) will
    # introduce the keys Q.zero(x) and Q.zero(y), so we need to run it until
    # we stop getting new things. Hopefully this strategy won't lead to an
    # infinite loop in the future.
    i = 0
    relevant_facts = set()
    exprs = None
    while exprs != set():
        (relevant_facts, exprs) = get_relevant_facts(proposition,
                And.make_args(assumptions), context,
                use_known_facts=use_known_facts, exprs=exprs,
                relevant_facts=relevant_facts)
        i += 1
        if i >= iterations:
            return And(*relevant_facts)

    return And(*relevant_facts)
