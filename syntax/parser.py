import syntax.ast_nodes as ast_nodes
from lexer import TokenType
from syntax.errors import ErrorCode, ParseError


class Token:
    def __init__(self, raw_text: str):
        # Expected format: <TYPE [line,col]> or <TYPE = value [line,col]>
        content = raw_text.strip()[1:-1]  # remove < and >

        parts = list(map(lambda x: x.strip(), content.split()))
        self.type = TokenType[parts[0]]

        # Parsing parts
        if parts[1] == "=":
            # Case: IDENT = num1 [2,5] or INT_LIT = 10 [2,13]
            self.value = parts[2]
            self.location = parts[3]  # [line,col]

        else:
            # Case: IOL [1,1] or ADD [13,6]
            self.value = None
            self.location = parts[1]

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.location})"


class Parser:
    def __init__(self, token_file):
        self.tokens: list[Token] = self.load_tokens(token_file)
        self.current_idx = 0
        self.symbol_table: dict[str, TokenType] = (
            {}
        )  # Stores { variable_name: TokenType.INT or TokenType.STR }
        self.errors = []
        self.ast = None

    def load_tokens(self, file_obj):
        token_list = []

        try:
            # Ensure we are at the start of the file
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)

            lines = file_obj.readlines()
            for line in lines:
                stripped = line.strip()
                if stripped:
                    token_list.append(Token(stripped))

        except Exception as e:
            print(f"Error reading token file: {e}")

        return token_list

    def current_token(self) -> Token:
        if self.current_idx < len(self.tokens):
            return self.tokens[self.current_idx]
        return Token(f"<{TokenType.EOF.name} [0,0]>")

    def advance(self):
        self.current_idx += 1

    # ==========================================
    #               ERROR HANDLING
    # ==========================================

    def log_error(self, error_type, template, **kwargs):
        """
        Args:
            error_type (str): "Syntax", "Semantic", or "Lexical"
            template (str): The string from ErrorCode class with {placeholders}
            **kwargs: The variables to fill the placeholders (e.g., name="var1")
        """
        token = self.current_token()

        # 1. Fill the placeholders in the message
        try:
            formatted_message = template.format(**kwargs)
        except KeyError as e:
            formatted_message = f"{template} (Missing info: {e})"

        # 2. Add the location info
        final_msg = (
            f"[{error_type}] Error at {token.location}: {formatted_message}"
        )
        self.errors.append(final_msg)
        return final_msg

    def lexical_error(self, template, **kwargs):
        """Logs lexical error, DOES NOT raise (just skips token usually)"""
        self.log_error("Lexical", template, **kwargs)

    def syntax_error(self, template, **kwargs):
        """Logs syntax error and RAISES exception to trigger synchronization"""
        err_msg = self.log_error("Syntax", template, **kwargs)
        raise ParseError(err_msg)

    def semantic_error(self, template, **kwargs):
        """Logs semantic error, DOES NOT raise (allows continuation)"""
        self.log_error("Semantic", template, **kwargs)

    def synchronize(self):
        """
        Skips tokens until we find a statement boundary (NEWLN) or a start of a new statement.
        This prevents one error from cascading into 100 errors.
        """
        self.advance()
        while self.current_token().type != TokenType.EOF:
            # If the previous token was a newline, we are likely at a clean start
            if self.tokens[self.current_idx - 1].type == TokenType.NEWLN:
                return

            # If we see a keyword that starts a statement, we can resume parsing
            if self.current_token().type in [
                TokenType.INT,
                TokenType.STR,
                TokenType.INTO,
                TokenType.BEG,
                TokenType.PRINT,
                TokenType.NEWLN,
                TokenType.LOI,
            ]:
                return

            self.advance()

    def match(self, expected_type: TokenType):
        """Consumes current token if it matches expected_type"""
        token = self.current_token()

        if token.type == expected_type:
            self.advance()
            return token

        self.syntax_error(
            ErrorCode.UNEXPECTED_TOKEN,
            expected=expected_type.name,
            actual=token.type.name,
        )

    # ==========================================
    #       RECURSIVE DESCENT FUNCTIONS
    # ==========================================

    def parse(self) -> ast_nodes.Program:
        """Entry point for parsing"""
        if not self.tokens:
            return ast_nodes.Program([])  # Empty program

        program = self.parse_program()

        # If we finish parse_program and there are tokens left (except EOF), that's an issue
        if (
            self.current_idx < len(self.tokens)
            and self.current_token().type != TokenType.EOF
        ):
            self.semantic_error(ErrorCode.CODE_AFTER_LOI)

        self.ast = program
        return program

    def parse_program(self) -> ast_nodes.Program:
        """Program ::= IOL <statements> LOI EOF"""

        statements = []
        try:
            self.match(TokenType.IOL)
        except ParseError:
            self.synchronize()

        while self.current_token().type != TokenType.LOI:
            try:
                print("Parsing statement at token:", self.current_token())
                statement = self.parse_statement()
                statements.append(statement)
            except ParseError:
                self.synchronize()

        self.match(TokenType.LOI)
        self.match(TokenType.EOF)

        return ast_nodes.Program(statements)

    def parse_statement(self) -> ast_nodes.ASTNode:
        """
        Determines which statement to parse based on the current token.
        """
        token_type = self.current_token().type
        statement_node = None

        if token_type == TokenType.ERR_LEX:
            self.lexical_error(
                ErrorCode.UNKNOWN_WORD, word=self.current_token().value
            )
            self.advance()
        elif token_type in [TokenType.INT, TokenType.STR]:
            statement_node = self.parse_variable_declaration()
        elif token_type == TokenType.INTO:
            statement_node = self.parse_assignment()
        elif token_type == TokenType.BEG:
            statement_node = self.parse_input()
        elif token_type == TokenType.PRINT:
            statement_node = self.parse_output()
        elif token_type == TokenType.NEWLN:
            self.match(TokenType.NEWLN)
        else:
            self.syntax_error(
                ErrorCode.UNEXPECTED_STATEMENT, token=token_type.name
            )

        print("node: ", statement_node)
        return statement_node

    def parse_variable_declaration(self) -> ast_nodes.VarDecl:
        """
        VarDecl ::= 'INT' Ident [ 'IS' Expression ]
                |   'STR' Ident [ 'IS' Ident ]
        """
        type_token = self.current_token()
        declared_type = type_token.type
        self.advance()

        ident_token = self.match(TokenType.IDENT)
        var_name = ident_token.value

        # SEMANTIC CHECK: Duplicate Declaration
        if var_name in self.symbol_table:
            self.semantic_error(ErrorCode.DUPLICATE_VAR, name=var_name)

        self.symbol_table[var_name] = declared_type.name  # register variable

        init_expr = None

        # Check for optional initialization: IS value
        if self.current_token().type == TokenType.IS:
            self.advance()
            if declared_type == TokenType.INT:
                init_expr = self.parse_expression()

                if init_expr.eval_type != TokenType.INT:
                    self.semantic_error(
                        ErrorCode.TYPE_MISMATCH,
                        expr_type=init_expr.eval_type,
                        target_type=TokenType.INT,
                        name=var_name,
                    )

            elif declared_type == TokenType.STR:
                val_token = self.match(TokenType.IDENT)
                source_var = val_token.value

                if source_var not in self.symbol_table:
                    self.semantic_error(
                        ErrorCode.UNDEFINED_VAR, name=source_var
                    )

                if self.symbol_table[source_var] != TokenType.STR:
                    self.semantic_error(
                        ErrorCode.TYPE_MISMATCH,
                        expr_type=self.symbol_table[source_var],  # INT
                        target_type=TokenType.STR,
                        name=var_name,
                    )

                init_expr = ast_nodes.VarUsage(source_var, TokenType.STR)

        return ast_nodes.VarDecl(declared_type, var_name, init_expr)

    def parse_assignment(self) -> ast_nodes.Assignment:
        """
        Assignment ::= 'INTO' Ident 'IS' Expression
        """
        self.match(TokenType.INTO)
        ident_token = self.match(TokenType.IDENT)
        var_name = ident_token.value

        # SEMANTIC CHECK: Variable must exist
        if var_name not in self.symbol_table:
            self.semantic_error(ErrorCode.UNDEFINED_VAR, name=var_name)
        else:
            target_type = self.symbol_table[var_name]

        self.match(TokenType.IS)
        expr_node = self.parse_expression()
        expr_type = expr_node.eval_type

        # SEMANTIC CHECK: Type Compatibility
        if target_type != expr_type:
            self.semantic_error(
                ErrorCode.TYPE_MISMATCH,
                expr_type=expr_type.name,
                target_type=target_type.name,
                name=var_name,
            )

        return ast_nodes.Assignment(var_name, expr_node)

    def parse_input(self) -> ast_nodes.InputStmt:
        """
        Input ::= 'BEG' Ident
        """
        self.match(TokenType.BEG)
        ident_token = self.match(TokenType.IDENT)
        var_name = ident_token.value

        # SEMANTIC CHECK: Variable must exist
        if var_name not in self.symbol_table:
            self.semantic_error(ErrorCode.UNDEFINED_VAR, name=var_name)

        return ast_nodes.InputStmt(var_name)

    def parse_output(self) -> ast_nodes.OutputStmt:
        """
        Output ::= 'PRINT' Expression
        """
        self.match(TokenType.PRINT)
        expr = self.parse_expression()
        return ast_nodes.OutputStmt(expr)

    def parse_expression(self) -> ast_nodes.ASTNode | None:
        """
        Parses an expression and returns its TYPE (TokenType.INT or TokenType.STR).
        Handles:
        1. Literals (INT_LIT)
        2. Variables (IDENT)
        3. Prefix Operations (ADD, SUB, MULT, DIV, MOD)
        """
        token = self.current_token()

        # Case 1: Integer Literal
        if token.type == TokenType.INT_LIT:
            self.advance()
            return ast_nodes.IntLiteral(int(token.value))

        # Case 2: Variable
        elif token.type == TokenType.IDENT:
            var_name = token.value
            self.advance()

            # SEMANTIC CHECK: Defined?
            if var_name not in self.symbol_table:
                self.semantic_error(ErrorCode.UNDEFINED_VAR, name=var_name)
                return ast_nodes.VarUsage(
                    var_name, TokenType.ERR_LEX
                )  # unknown type

            return ast_nodes(var_name, self.symbol_table[var_name])

        # Case 3: Math Operations (Prefix)
        elif token.type in [
            TokenType.ADD,
            TokenType.SUB,
            TokenType.MULT,
            TokenType.DIV,
            TokenType.MOD,
        ]:
            op_type = token.type
            self.advance()  # consume operator

            # Recursively parse left and right operands
            left_node = self.parse_expression()
            right_node = self.parse_expression()

            # SEMANTIC CHECK: Math requires INTs
            if (
                left_node.eval_type != TokenType.INT
                or right_node.eval_type != TokenType.INT
            ):
                self.semantic_error(
                    ErrorCode.MATH_OPERAND_ERROR,
                    op=op_type.name,
                    t1=left_node.eval_type.name,
                    t2=right_node.eval_type.name,
                )

            return ast_nodes.BinOp(op_type, left_node, right_node)

        else:
            self.syntax_error(
                ErrorCode.INVALID_EXPRESSION, token=token.type.name
            )
