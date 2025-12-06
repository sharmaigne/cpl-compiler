class ASTNode:
    pass


class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements


class VarDecl(ASTNode):
    def __init__(self, var_type: str, name: str, value_expr=None):
        self.var_type = var_type
        self.name = name
        self.value = value_expr  # This will be an expression Node


class Assignment(ASTNode):
    def __init__(self, name: str, value_expr):
        self.name = name
        self.value = value_expr


class InputStmt(ASTNode):
    def __init__(self, name):
        self.name = name


class OutputStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr


class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
        self.eval_type = "INT"  # Math always results in INT


class Literal(ASTNode):
    def __init__(self, value: str | int, eval_type: str):
        self.value = value
        self.eval_type = eval_type  # "INT" or "STR"


class VarUsage(ASTNode):
    def __init__(self, name: str, eval_type: str):
        self.name = name
        self.eval_type = eval_type
