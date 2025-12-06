from lexer import TokenType


class ASTNode:
    pass


class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"Program({self.statements})"


class VarDecl(ASTNode):
    def __init__(self, var_type, var_name, value=None):
        self.var_type = var_type  # TokenType
        self.var_name = var_name  # str
        self.value = value  # ASTNode, optional

    def __repr__(self):
        value_repr = (
            f", value={repr(self.value)}" if self.value is not None else ""
        )
        return f"VarDecl({self.var_type.name}, {self.var_name}{value_repr})"


class Assignment(ASTNode):
    def __init__(self, var_name, expr):
        self.var_name = var_name  # str
        self.expr = expr  # ASTNode

    def __repr__(self):
        return f"Assignment({self.var_name}, {self.expr})"


class InputStmt(ASTNode):
    def __init__(self, var_name):
        self.var_name = var_name

    def __repr__(self):
        return f"InputStmt({self.var_name})"


class OutputStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"Output({self.expr})"


class NewlineStmt(ASTNode):
    def __init__(self):
        pass

    def __repr__(self):
        return "NewlineStmt()"


class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        op_str = self.op.name if hasattr(self.op, "name") else repr(self.op)
        return f"BinOp({op_str}, {self.left}, {self.right})"


class IntLiteral(ASTNode):
    def __init__(self, value: int):
        self.value = value
        self.eval_type = TokenType.INT

    def __repr__(self):
        return f"IntLit({self.value})"


class VarUsage(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"VarUsage({self.name})"
