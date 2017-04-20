"""
Implementation of Sarah B. Lawsky's "order of application" variant of default logic.
"""

from nltk.inference import TableauProver, Mace, ParallelProverBuilder
from nltk.sem.logic import Expression


class SupernormalDefaultTheory:
    def __init__(self, background_theory, default_rules):
        if not isinstance(background_theory, list):
            raise TypeError("'background_theory' should be an instance of list")
        for formula in background_theory:
            if not isinstance(formula, Expression):
                raise TypeError("'background_theory' should only contain instances of Expression")
        if not isinstance(default_rules, list):
            raise TypeError("'default_rules' should be an instance of list")
        for rule in default_rules:
            if not isinstance(rule, Expression):
                raise TypeError("'default_rules' should only contain instances of Expression")
        self.background_theory = background_theory
        # Ordered by priority in decreasing order
        # That is: default_rules[0] > default_rules[1] > ...
        self.default_rules = default_rules
        self.preferred_extension = None
        # Prover and model builder, used for proofs and consistency checks
        # Using TableauProver as prover and Mace as model builder (with maximum of 500 models)
        self.parallel_prover_builder = ParallelProverBuilder(TableauProver(), Mace(end_size=500))

    def _C(self):
        if self.preferred_extension is not None:
            return
        current_theory = self.background_theory
        for default_rule in self.default_rules:
            if self._is_active(current_theory, default_rule):
                current_theory.append(default_rule)
            else:
                break
        self.preferred_extension = current_theory

    def _is_new_rule(self, rule, formulas):
        return not self.parallel_prover_builder.prove(goal=rule, assumptions=formulas)

    def _is_consistent(self, rule, formulas):
        assumptions = list(formulas) + [rule]
        return self.parallel_prover_builder.build_model(assumptions=assumptions)

    def _is_active(self, formulas, rule):
        return self._is_new_rule(rule, formulas) and self._is_consistent(rule, formulas)

    def get_preferred_extension(self):
        self._C()
        return self.preferred_extension

    def prove(self, goal, print_proof=False):
        return self.parallel_prover_builder.prove(goal=goal, assumptions=self.get_preferred_extension(), verbose=print_proof)


def example_template(num, background_theory, default_rules, goal, print_proofs=False):
    theory = SupernormalDefaultTheory(background_theory, default_rules)
    # print theory.get_preferred_extension()
    goal_proved = theory.prove(goal, print_proof=print_proofs)
    not_goal_proved = theory.prove(-goal, print_proof=print_proofs)
    assert isinstance(goal_proved, bool) and isinstance(not_goal_proved, bool)
    assert goal_proved is not not_goal_proved
    print("*"*25)
    print("EXAMPLE {}".format(num))
    print("Background Theory:")
    print("\n".join(["\t{}".format(expr) for expr in background_theory]))
    print("Default Rules:")
    print("\n".join(["\t{}".format(expr) for expr in default_rules]))
    print("Goal:")
    print("\t{}".format(goal))
    print("Result:")
    if goal_proved:
        print("\tSUCCESS")
    else:
        print("\tFAILURE")
    print("*"*25)

def example1():
    background_theory = [
        Expression.fromstring(u"UnitedStates(Henry)"),
        Expression.fromstring(u"Young(Henry)")
    ]
    default_rules = [
        Expression.fromstring(u"all x.(Young(x) -> -Read(x))"),
        Expression.fromstring(u"all x.(UnitedStates(x) -> Read(x))")
    ]
    goal = Expression.fromstring(u"-Read(Henry)")
    example_template(1, background_theory, default_rules, goal)

def example2():
    background_theory = [
        Expression.fromstring(u"Personal(y)"),
        Expression.fromstring(u"all x.(Personal(x) -> Interest(x))"),
        Expression.fromstring(u"all x.(QRI(x) -> Personal(x))")
    ]
    default_rules = [
        Expression.fromstring(u"all x.(QRI(x) -> Deductible(x))"),
        Expression.fromstring(u"all x.(Personal(x) -> -Deductible(x))"),
        Expression.fromstring(u"all x.(Interest(x) -> Deductible(x))")
    ]
    goal = Expression.fromstring(u"-Deductible(y)")
    example_template(2, background_theory, default_rules, goal)


if __name__ == "__main__":
    example1()
    example2()

 



