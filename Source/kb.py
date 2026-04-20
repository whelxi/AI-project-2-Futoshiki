from typing import List, Dict

class Term:
    def __init__(self, name: str, is_var: bool = False):
        self.name = name
        self.is_var = is_var

    def __eq__(self, other):
        return isinstance(other, Term) and self.name == other.name and self.is_var == other.is_var

    def __hash__(self):
        return hash((self.name, self.is_var))

    def substitute(self, var_map: Dict[str, 'Term']) -> 'Term':
        if self.is_var and self.name in var_map:
            return var_map[self.name]
        return self

    def __repr__(self):
        return self.name

class Expr:
    def to_cnf(self) -> 'Expr':
        return self.eliminate_implications().move_not_inward().distribute_or()

    def eliminate_implications(self): raise NotImplementedError
    def move_not_inward(self): raise NotImplementedError
    def distribute_or(self): raise NotImplementedError
    def substitute(self, var_map): raise NotImplementedError
    def ground(self, domain): raise NotImplementedError

class TruthValue(Expr):
    def __init__(self, value: bool):
        self.value = value
    def eliminate_implications(self): return self
    def move_not_inward(self): return self
    def distribute_or(self): return self
    def substitute(self, var_map): return self
    def ground(self, domain): return self
    def __repr__(self): return "⊤" if self.value else "⊥"

class BinaryOp(Expr):
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    def op_str(self): raise NotImplementedError
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
            return And(Or(left.left, right).distribute_or(), Or(left.right, right).distribute_or())
        if isinstance(right, And):
            return And(Or(left, right.left).distribute_or(), Or(left, right.right).distribute_or())
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
        if isinstance(self.expr, Not):
            return self.expr.expr.move_not_inward()
        if isinstance(self.expr, And):
            return Or(Not(self.expr.left).move_not_inward(), Not(self.expr.right).move_not_inward())
        if isinstance(self.expr, Or):
            return And(Not(self.expr.left).move_not_inward(), Not(self.expr.right).move_not_inward())
        return self
    def distribute_or(self):
        return self
    def substitute(self, var_map):
        return Not(self.expr.substitute(var_map))
    def ground(self, domain):
        return Not(self.expr.ground(domain))
    def __repr__(self):
        return f"¬{self.expr}"

class Implies(BinaryOp):
    def op_str(self): return "⇒"
    def eliminate_implications(self):
        return Or(Not(self.left.eliminate_implications()), self.right.eliminate_implications())
    def move_not_inward(self):
        return self.eliminate_implications().move_not_inward()
    def distribute_or(self):
        return self.eliminate_implications().distribute_or()
    def substitute(self, var_map):
        return Implies(self.left.substitute(var_map), self.right.substitute(var_map))
    def ground(self, domain):
        return Implies(self.left.ground(domain), self.right.ground(domain))

class Predicate(Expr):
    def __init__(self, name: str, args: List[Term]):
        self.name = name
        self.args = args

    def __eq__(self, other):
        return (isinstance(other, Predicate) and 
                self.name == other.name and 
                self.args == other.args)

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

    def eliminate_implications(self): return self
    def move_not_inward(self): return self
    def distribute_or(self): return self

    def substitute(self, var_map):
        return Predicate(self.name, [arg.substitute(var_map) for arg in self.args])

    def ground(self, domain):
        if self.name in ("Equal", "Less"):
            if all(not arg.is_var for arg in self.args):
                val = (self.args[0].name == self.args[1].name) if self.name == "Equal" else (int(self.args[0].name) < int(self.args[1].name))
                return TruthValue(val)
        return self

    def __repr__(self):
        return f"{self.name}({','.join(map(str, self.args))})"

class Quantifier(Expr):
    def __init__(self, var_name: str, formula: Expr):
        self.var_name = var_name
        self.formula = formula
    def substitute(self, var_map):
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
    def ground(self, domain):
        # ∀x φ → ∧_{d∈domain} φ[x/d]
        instances = [self.formula.substitute({self.var_name: d}).ground(domain) for d in domain]
        result = instances[0]
        for inst in instances[1:]:
            result = And(result, inst)
        return result
    def __repr__(self):
        return f"∀{self.var_name} ({self.formula})"

class Existential(Quantifier):
    def ground(self, domain):
        # ∃x φ → ∨_{d∈domain} φ[x/d]
        instances = [self.formula.substitute({self.var_name: d}).ground(domain) for d in domain]
        result = instances[0]
        for inst in instances[1:]:
            result = Or(result, inst)
        return result
    def __repr__(self):
        return f"∃{self.var_name} ({self.formula})"
    
class Rule:
    def __init__(self, head: Predicate, body: List[Predicate]):
        self.head = head
        self.body = body

    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        return f"{self.head} :- {', '.join(map(str, self.body))}."

def convert_to_horn(kb: List[Expr]) -> List[Rule]:
    horn_kb = []
    for expr in kb:
        curr = expr
        while isinstance(curr, Quantifier):
            curr = curr.formula
        
        if isinstance(curr, Predicate):
            horn_kb.append(Rule(curr, []))
        
        elif isinstance(curr, Implies):
            if isinstance(curr.right, Implies):
                head = curr.right.right
                body_exprs = []
                
                if isinstance(curr.left, And):
                    body_exprs.extend([curr.left.left, curr.left.right])
                else:
                    body_exprs.append(curr.left)
                    
                if isinstance(curr.right.left, And):
                    body_exprs.extend([curr.right.left.left, curr.right.left.right])
                else:
                    body_exprs.append(curr.right.left)
                    
                horn_kb.append(Rule(head, body_exprs))
            else:
                head = curr.right
                body_exprs = []
                if isinstance(curr.left, And):
                    body_exprs.extend([curr.left.left, curr.left.right])
                else:
                    body_exprs.append(curr.left)
                horn_kb.append(Rule(head, body_exprs))
        
    return horn_kb

def build_fol_kb(n: int, given_facts: List[tuple], less_h: List[tuple], greater_h: List[tuple],
                 less_v: List[tuple], greater_v: List[tuple]) -> List[Expr]:
    kb = []

    def t(s: str, is_var=False): return Term(s, is_var)
    def var(s): return Term(s, is_var=True)

    indices = [t(str(i)) for i in range(1, n+1)]
    values = [t(str(v)) for v in range(1, n+1)]

    for i in indices:
        for j in indices:
            kb.append(Existential("v", Predicate("Val", [i, j, var("v")])))

    for i in indices:
        for j in indices:
            v1, v2 = var("v1"), var("v2")
            kb.append(Universal("v1", Universal("v2",
                Implies(And(Predicate("Val", [i, j, v1]), Predicate("Val", [i, j, v2])),
                        Predicate("Equal", [v1, v2])))))

    for i in indices:
        for v in values:
            j1, j2 = var("j1"), var("j2")
            kb.append(Universal("j1", Universal("j2",
                Implies(And(Predicate("Val", [i, j1, v]), Predicate("Val", [i, j2, v])),
                        Predicate("Equal", [j1, j2])))))

    for j in indices:
        for v in values:
            i1, i2 = var("i1"), var("i2")
            kb.append(Universal("i1", Universal("i2",
                Implies(And(Predicate("Val", [i1, j, v]), Predicate("Val", [i2, j, v])),
                        Predicate("Equal", [i1, i2])))))

    for (i, j, v) in given_facts:
        given_pred = Predicate("Given", [t(str(i)), t(str(j)), t(str(v))])
        val_pred = Predicate("Val", [t(str(i)), t(str(j)), t(str(v))])
        kb.append(given_pred)
        kb.append(Implies(given_pred, val_pred))

    for (i, j) in less_h:
        i_term, j_term = t(str(i)), t(str(j))
        j_next = t(str(j+1))
        v1, v2 = var("v1"), var("v2")
        axiom = Implies(Predicate("LessH", [i_term, j_term]),
                        Universal("v1", Universal("v2",
                            Implies(And(Predicate("Val", [i_term, j_term, v1]),
                                        Predicate("Val", [i_term, j_next, v2])),
                                    Predicate("Less", [v1, v2])))))
        kb.append(axiom)
        kb.append(Predicate("LessH", [i_term, j_term]))

    for (i, j) in greater_h:
        i_term, j_term = t(str(i)), t(str(j))
        j_next = t(str(j+1))
        v1, v2 = var("v1"), var("v2")
        axiom = Implies(Predicate("GreaterH", [i_term, j_term]),
                        Universal("v1", Universal("v2",
                            Implies(And(Predicate("Val", [i_term, j_term, v1]),
                                        Predicate("Val", [i_term, j_next, v2])),
                                    Predicate("Less", [v2, v1])))))
        kb.append(axiom)
        kb.append(Predicate("GreaterH", [i_term, j_term]))

    for (i, j) in less_v:
        i_term, j_term = t(str(i)), t(str(j))
        i_next = t(str(i+1))
        v1, v2 = var("v1"), var("v2")
        axiom = Implies(Predicate("LessV", [i_term, j_term]),
                        Universal("v1", Universal("v2",
                            Implies(And(Predicate("Val", [i_term, j_term, v1]),
                                        Predicate("Val", [i_next, j_term, v2])),
                                    Predicate("Less", [v1, v2])))))
        kb.append(axiom)
        kb.append(Predicate("LessV", [i_term, j_term]))

    for (i, j) in greater_v:
        i_term, j_term = t(str(i)), t(str(j))
        i_next = t(str(i+1))
        v1, v2 = var("v1"), var("v2")
        axiom = Implies(Predicate("GreaterV", [i_term, j_term]),
                        Universal("v1", Universal("v2",
                            Implies(And(Predicate("Val", [i_term, j_term, v1]),
                                        Predicate("Val", [i_next, j_term, v2])),
                                    Predicate("Less", [v2, v1])))))
        kb.append(axiom)
        kb.append(Predicate("GreaterV", [i_term, j_term]))

    return kb

def ground_kb(n: int, kb: List[Expr]) -> List[Expr]:
    domain = [Term(str(i)) for i in range(1, n+1)]
    grounded_kb = []
    for expr in kb:
        grounded_kb.append(expr.ground(domain))
    return grounded_kb

def is_variable(x):
    return isinstance(x, Term) and x.is_var

def unify(x, y, theta):
    if theta is None:
        return None
    if isinstance(x, str) and isinstance(y, str):
        return theta if x == y else None
    if is_variable(x):
        return unify_var(x, y, theta)
    if is_variable(y):
        return unify_var(y, x, theta)
    if isinstance(x, Term) and isinstance(y, Term):
        return theta if x.name == y.name else None
    if isinstance(x, Predicate) and isinstance(y, Predicate):
        if x.name != y.name or len(x.args) != len(y.args):
            return None
        return unify(x.args, y.args, theta)
    if isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            return None
        if len(x) == 0:
            return theta
        return unify(x[1:], y[1:], unify(x[0], y[0], theta))
    if x == y:
        return theta
    return None

def unify_var(var, x, theta):
    if var.name in theta:
        return unify(theta[var.name], x, theta)
    if is_variable(x) and x.name in theta:
        return unify(var, theta[x.name], theta)
    new_theta = theta.copy()
    new_theta[var.name] = x
    return new_theta

def simplify_builtins(expr: Expr) -> Expr:
    if isinstance(expr, Predicate) and expr.name in ("Equal", "Less"):
        if all(not arg.is_var for arg in expr.args):
            if expr.name == "Equal":
                val = expr.args[0].name == expr.args[1].name
            else:
                v1, v2 = int(expr.args[0].name), int(expr.args[1].name)
                val = v1 < v2
            return TruthValue(val)
    elif isinstance(expr, BinaryOp):
        return type(expr)(simplify_builtins(expr.left), simplify_builtins(expr.right))
    elif isinstance(expr, Not):
        return Not(simplify_builtins(expr.expr))
    elif isinstance(expr, Quantifier):
        return type(expr)(expr.var_name, simplify_builtins(expr.formula))
    return expr

def collect_clauses(expr: Expr, var_map: Dict[Predicate, int]) -> List[List[int]]:
    """Recursively extract clauses from a CNF expression, return list of lists for SAT solver."""
    if isinstance(expr, And):
        clauses = []
        for sub in [expr.left, expr.right]:
            clauses.extend(collect_clauses(sub, var_map))
        return clauses
    elif isinstance(expr, Or):
        literals = set()
        def gather_lits(e):
            if isinstance(e, Or):
                gather_lits(e.left)
                gather_lits(e.right)
            elif isinstance(e, Not):
                if isinstance(e.expr, TruthValue):
                    if not e.expr.value:
                        literals.add(None)   
                    return
                if not isinstance(e.expr, Predicate):
                    raise ValueError("Expected predicate under Not")
                pred = e.expr
                if pred not in var_map:
                    var_map[pred] = len(var_map) + 1
                literals.add(-var_map[pred])
            elif isinstance(e, Predicate):
                if e not in var_map:
                    var_map[e] = len(var_map) + 1
                literals.add(var_map[e])
            elif isinstance(e, TruthValue):
                if e.value:
                    literals.add(None)   
            else:
                raise ValueError(f"Unexpected literal type: {type(e)}")
        gather_lits(expr)
        if None in literals:
            return []      
        literals.discard(None)
        if not literals:
            return [[]]  
        return [list(literals)]
    elif isinstance(expr, Predicate):
        if expr not in var_map:
            var_map[expr] = len(var_map) + 1
        return [[var_map[expr]]]
    elif isinstance(expr, Not):
        if isinstance(expr.expr, TruthValue):
            if not expr.expr.value:
                return []   
            else:
                return [[]]    
        if not isinstance(expr.expr, Predicate):
            raise ValueError("Expected predicate under Not")
        pred = expr.expr
        if pred not in var_map:
            var_map[pred] = len(var_map) + 1
        return [[-var_map[pred]]]
    elif isinstance(expr, TruthValue):
        if not expr.value:
            return [[]]   
        return []         
    else:
        raise ValueError(f"Unexpected CNF node: {type(expr)}")
