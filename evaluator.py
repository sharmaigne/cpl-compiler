from lexer import TokenType


class RuntimeException(Exception):
    pass


class Evaluator:
    def __init__(self, ast_root, on_print=print, on_input=input):
        self.ast = ast_root
        # Structure: { "var_name": { "type": TokenType.INT, "value": 0 } }
        self.symbol_table = {}
        self.on_print = on_print
        self.on_input = on_input

    def evaluate(self):
        try:
            # The root is a Program node containing a list of statements
            for statement in self.ast.statements:
                self.visit(statement)

        except RuntimeException as e:
            self.on_print(f"\n[Runtime Error] {e}")

    def visit(self, node):
        """Dispatcher method to visit different AST nodes."""
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise RuntimeException(
            f"No visit method defined for {type(node).__name__}"
        )

    # ==========================================
    #             STATEMENT VISITORS
    # ==========================================

    def visit_VarDecl(self, node):
        # Spec 4: Define variable with default values [cite: 45]
        # INT defaults to 0, STR defaults to ""
        default_val = 0 if node.var_type == TokenType.INT else ""

        # If there is an initialization (e.g., INT x IS 5)
        current_val = default_val
        if node.value is not None:
            current_val = self.visit(node.value)

        self.symbol_table[node.var_name] = {
            "type": node.var_type,
            "value": current_val,
        }

    def visit_Assignment(self, node):
        # Spec 5: Assign value to existing variable [cite: 49]
        var_name = node.var_name
        new_value = self.visit(node.expr)

        # Semantic analysis already checked types, but we ensure existence
        if var_name in self.symbol_table:
            self.symbol_table[var_name]["value"] = new_value
        else:
            raise RuntimeException(f"Variable '{var_name}' not defined.")

    def visit_InputStmt(self, node):
        var_name = node.var_name
        target_meta = self.symbol_table.get(var_name)

        if not target_meta:
            raise RuntimeException(
                f"Cannot input into undefined variable '{var_name}'."
            )

        # Use the spec's suggested prompt format
        user_input = self.on_input(f"Input for {var_name}: ")
        if user_input is None:
            raise RuntimeException("Program execution cancelled by user.")
        self.on_print(f"Input for {var_name}: {user_input}\n")

        if target_meta["type"] == TokenType.INT:
            try:
                val = int(user_input)
                target_meta["value"] = val
            except ValueError:
                raise RuntimeException(
                    f"Invalid input. Expected Integer for '{var_name}', got '{user_input}'."
                )
        else:
            # String input is always valid for STR type
            target_meta["value"] = user_input

    def visit_OutputStmt(self, node):
        # Spec 5: PRINT expr [cite: 55]
        # We use end="" because NEWLN is a separate command in IOL
        val = self.visit(node.expr)
        self.on_print(f"{str(val)}")

    def visit_NewlineStmt(self, node):
        self.on_print("\n")

    # ==========================================
    #             EXPRESSION VISITORS
    # ==========================================
    def visit_BinOp(self, node):
        # Recursively evaluate left and right operands
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        # Spec 6: Numerical Expressions [cite: 66-80]
        # Lexer token types assumed based on parser usage
        match node.op:
            case TokenType.ADD:
                return left_val + right_val
            case TokenType.SUB:
                return left_val - right_val
            case TokenType.MULT:
                return left_val * right_val
            case TokenType.DIV:
                if right_val == 0:
                    raise RuntimeException("Division by zero.")
                return int(left_val / right_val)  # Integer division
            case TokenType.MOD:
                if right_val == 0:
                    raise RuntimeException("Modulo by zero.")
                return left_val % right_val
            case _:
                raise RuntimeException(f"Unknown operation {node.op}")

    def visit_IntLiteral(self, node):
        return node.value

    def visit_VarUsage(self, node):
        # Retrieve value from symbol table
        name = (
            node.name if hasattr(node, "name") else node.var_name
        )  # Handle potential naming diffs
        if name in self.symbol_table:
            return self.symbol_table[name]["value"]
        raise RuntimeException(f"Variable '{name}' used before definition.")
