from abc import ABC, abstractmethod
from typing import List, Dict

# ----------------------------------------------------------------------
# Terms (constants / variables) – not logical formulas
# ----------------------------------------------------------------------
class Term:
    def __init__(self, name: str, is_var: bool = False):
        self.name = name
        self.is_var = is_var

    def substitute(self, var_map: Dict[str, 'Term']) -> 'Term':
        """Replace variable if name in map, otherwise return self."""
        if self.is_var and self.name in var_map:
            return var_map[self.name]
        return self

    def __repr__(self):
        return self.name

# ----------------------------------------------------------------------
# Logical expressions
# ----------------------------------------------------------------------
class Expr(ABC):
    def to_cnf(self) -> 'Expr':
        """Full pipeline: eliminate implications → NNF → distribute ∨ over ∧."""
        return self.eliminate_implications().move_not_inward().distribute_or()

    @abstractmethod
    def eliminate_implications(self) -> 'Expr':
        pass

    @abstractmethod
    def move_not_inward(self) -> 'Expr':
        pass

    @abstractmethod
    def distribute_or(self) -> 'Expr':
        pass

    @abstractmethod
    def substitute(self, var_map: Dict[str, Term]) -> 'Expr':
        """Replace free variables according to var_map."""
        pass

    @abstractmethod
    def ground(self, domain: List[Term]) -> 'Expr':
        """Eliminate all quantifiers over the finite domain (∧ for ∀, ∨ for ∃)."""
        pass

# ----------------------------------------------------------------------
# Propositional connectives
# ----------------------------------------------------------------------
class BinaryOp(Expr):
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

    @abstractmethod
    def op_str(self):
        pass

    def __repr__(self):
        return f"({self.left} {self.op_str()} {self.right})"

class And(BinaryOp):
    def op_str(self): return "∧"

    def eliminate_implications(self):
        return And(self.left.eliminate_implications(), self.right.eliminate_implications())

    def move_not_inward(self):
        return And(self.left.move_not_inward(), self.right.move_not_inward())

    def distribute_or(self):
        return And(self.left.distribute_or(), self.right.distribute_or())

    def substitute(self, var_map):
        return And(self.left.substitute(var_map), self.right.substitute(var_map))

    def ground(self, domain):
        return And(self.left.ground(domain), self.right.ground(domain))

class Or(BinaryOp):
    def op_str(self): return "∨"

    def eliminate_implications(self):
        return Or(self.left.eliminate_implications(), self.right.eliminate_implications())

    def move_not_inward(self):
        return Or(self.left.move_not_inward(), self.right.move_not_inward())

    def distribute_or(self):
        left = self.left.distribute_or()
        right = self.right.distribute_or()
        if isinstance(left, And):
            return And(Or(left.left, right).distribute_or(),
                       Or(left.right, right).distribute_or())
        if isinstance(right, And):
            return And(Or(left, right.left).distribute_or(),
                       Or(left, right.right).distribute_or())
        return Or(left, right)

    def substitute(self, var_map):
        return Or(self.left.substitute(var_map), self.right.substitute(var_map))

    def ground(self, domain):
        return Or(self.left.ground(domain), self.right.ground(domain))

class Not(Expr):
    def __init__(self, expr: Expr):
        self.expr = expr

    def eliminate_implications(self):
        return Not(self.expr.eliminate_implications())

    def move_not_inward(self):
        # Double negation
        if isinstance(self.expr, Not):
            return self.expr.expr.move_not_inward()
        # De Morgan
        if isinstance(self.expr, And):
            return Or(Not(self.expr.left).move_not_inward(),
                      Not(self.expr.right).move_not_inward())
        if isinstance(self.expr, Or):
            return And(Not(self.expr.left).move_not_inward(),
                       Not(self.expr.right).move_not_inward())
        # Already at literal (Predicate) – stop
        return self

    def distribute_or(self):
        return self   # negation only on literals after NNF

    def substitute(self, var_map):
        return Not(self.expr.substitute(var_map))

    def ground(self, domain):
        return Not(self.expr.ground(domain))

    def __repr__(self):
        return f"¬{self.expr}"

class Implies(BinaryOp):
    def op_str(self): return "⇒"

    def eliminate_implications(self):
        return Or(Not(self.left.eliminate_implications()),
                  self.right.eliminate_implications())

    # The following methods are never called if we always use to_cnf(),
    # but we keep them for completeness.
    def move_not_inward(self):
        return self.eliminate_implications().move_not_inward()

    def distribute_or(self):
        return self.eliminate_implications().distribute_or()

    def substitute(self, var_map):
        return Implies(self.left.substitute(var_map), self.right.substitute(var_map))

    def ground(self, domain):
        return Implies(self.left.ground(domain), self.right.ground(domain))

# ----------------------------------------------------------------------
# Predicate (atomic formula)
# ----------------------------------------------------------------------
class Predicate(Expr):
    def __init__(self, name: str, args: List[Term]):
        self.name = name
        self.args = args

    def eliminate_implications(self):
        return self

    def move_not_inward(self):
        return self

    def distribute_or(self):
        return self

    def substitute(self, var_map):
        new_args = [arg.substitute(var_map) for arg in self.args]
        return Predicate(self.name, new_args)

    def ground(self, domain):
        return self   # no quantifiers to eliminate

    def __repr__(self):
        return f"{self.name}({','.join(map(str, self.args))})"

# ----------------------------------------------------------------------
# Quantifiers
# ----------------------------------------------------------------------
class Quantifier(Expr):
    def __init__(self, var_name: str, formula: Expr):
        self.var_name = var_name
        self.formula = formula

    def substitute(self, var_map):
        # Remove binding occurrence to avoid capture
        new_map = var_map.copy()
        new_map.pop(self.var_name, None)
        return type(self)(self.var_name, self.formula.substitute(new_map))

    def eliminate_implications(self):
        return type(self)(self.var_name, self.formula.eliminate_implications())

    def move_not_inward(self):
        return type(self)(self.var_name, self.formula.move_not_inward())

    def distribute_or(self):
        return type(self)(self.var_name, self.formula.distribute_or())

class Universal(Quantifier):
    def ground(self, domain: List[Term]) -> Expr:
        """∀x φ → ∧_{d∈domain} φ[x/d] (with recursive grounding)."""
        grounded_instances = []
        for val in domain:
            substituted = self.formula.substitute({self.var_name: val})
            grounded_instances.append(substituted.ground(domain))
        # Combine with And
        result = grounded_instances[0]
        for inst in grounded_instances[1:]:
            result = And(result, inst)
        return result

    def __repr__(self):
        return f"∀{self.var_name} ({self.formula})"

class Existential(Quantifier):
    def ground(self, domain: List[Term]) -> Expr:
        """∃x φ → ∨_{d∈domain} φ[x/d] (with recursive grounding)."""
        grounded_instances = []
        for val in domain:
            substituted = self.formula.substitute({self.var_name: val})
            grounded_instances.append(substituted.ground(domain))
        # Combine with Or
        result = grounded_instances[0]
        for inst in grounded_instances[1:]:
            result = Or(result, inst)
        return result

    def __repr__(self):
        return f"∃{self.var_name} ({self.formula})"

# ----------------------------------------------------------------------
# Example usage (corrected)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Domain: constants 1,2,3
    domain = [Term(str(n)) for n in range(1, 3)]

    # Build formula: ∀i ∀j ∃v Val(i,j,v)
    i_var = Term("i", is_var=True)
    j_var = Term("j", is_var=True)
    v_var = Term("v", is_var=True)

    inner_pred = Predicate("Val", [i_var, j_var, v_var])
    exists_v = Existential("v", inner_pred)
    forall_j = Universal("j", exists_v)
    forall_i = Universal("i", forall_j)

    print("Original FOL formula:", forall_i)

    # Fully ground over the finite domain (eliminates all quantifiers)
    grounded = forall_i.ground(domain)
    print("\nFully grounded (quantifier-free):", grounded)

    # Convert to CNF
    cnf = grounded.to_cnf()
    print("\nCNF:", cnf)