class Token:
    def __init__(self, raw_text: str):
        # Expected format: <TYPE [line,col]> or <TYPE = value [line,col]>
        # Removing < and >
        content = raw_text.strip()[1:-1]

        parts = list(map(lambda x: x.strip(), content.split()))
        self.type = parts[0]

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


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, token_file):
        self.tokens = self.load_tokens(token_file)
        self.current_idx = 0
        self.symbol_table = {}  # Stores { variable_name: "INT" or "STR" }
        self.errors = []

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

    def current_token(self):
        if self.current_idx < len(self.tokens):
            return self.tokens[self.current_idx]
        return Token("<EOF [0,0]>")

    def advance(self):
        self.current_idx += 1

    # ==========================================
    #               ERROR HANDLING
    # ==========================================

    def log_error(self, error_type, message):
        """Unified helper to format all error messages consistently"""
        token = self.current_token()
        # Format: [Type] Error at [Location]: Message
        err_msg = f"{error_type} Error at {token.location}: {message}"
        self.errors.append(err_msg)
        return err_msg

    def lexical_error(self, message):
        """Logs lexical error, DOES NOT raise (just skips token usually)"""
        self.log_error("Lexical", message)

    def syntax_error(self, message):
        """Logs syntax error and RAISES exception to trigger synchronization"""
        err_msg = self.log_error("Syntax", message)
        raise ParseError(err_msg)

    def semantic_error(self, message):
        """Logs semantic error, DOES NOT raise (allows continuation)"""
        self.log_error("Semantic", message)

    def synchronize(self):
        """
        Skips tokens until we find a statement boundary (NEWLN) or a start of a new statement.
        This prevents one error from cascading into 100 errors.
        """
        self.advance()
        while self.current_token().type != "EOF":
            # If the previous token was a newline, we are likely at a clean start
            if self.tokens[self.current_idx - 1].type == "NEWLN":
                return

            # If we see a keyword that starts a statement, we can resume parsing
            if self.current_token().type in [
                "INT",
                "STR",
                "INTO",
                "BEG",
                "PRINT",
                "NEWLN",
                "LOI",
            ]:
                return

            self.advance()

    def match(self, expected_type):
        """Consumes current token if it matches expected_type"""
        token = self.current_token()

        if token.type == expected_type:
            self.advance()
            return token

        self.syntax_error(
            f"Expected token '{expected_type}', found '{token.type}'"
        )

    # ==========================================
    #       RECURSIVE DESCENT FUNCTIONS
    # ==========================================

    def parse(self):
        """Entry point for parsing"""
        if not self.tokens:
            return False

        self.parse_program()

        # If we finish parse_program and there are tokens left (except EOF), that's an issue
        if (
            self.current_idx < len(self.tokens)
            and self.current_token().type != "EOF"
        ):
            self.semantic_error(
                "Code found after LOI. Program must end at LOI."
            )

        return True

    def parse_program(self):
        """Program ::= IOL <statements> LOI EOF"""
        try:
            self.match("IOL")
        except ParseError:
            self.synchronize()

        while self.current_token().type != "LOI":
            try:
                self.parse_statement()
            except ParseError:
                self.synchronize()

        self.match("LOI")
        self.match("EOF")

    def parse_statement(self):
        """
        Determines which statement to parse based on the current token.
        Options:
        1. Variable Def: INT/STR ...
        2. Assignment: INTO ...
        3. Input: BEG ...
        4. Output: PRINT ...
        5. Newline: NEWLN
        """
        token_type = self.current_token().type

        if token_type == "ERR_LEX":
            self.errors.append(
                f"Unknown word found: {self.current_token.value}"
            )  # lexical error
            self.advance()
        elif token_type in ["INT", "STR"]:
            self.parse_variable_declaration()
        elif token_type == "INTO":
            self.parse_assignment()
        elif token_type == "BEG":
            self.parse_input()
        elif token_type == "PRINT":
            self.parse_output()
        elif token_type == "NEWLN":
            self.match("NEWLN")
        else:
            self.syntax_error(
                f"Unexpected token '{token_type}' found in statement context."
            )

    def parse_variable_declaration(self):
        """
        VarDecl ::= 'INT' Ident [ 'IS' Expression ]
                |   'STR' Ident [ 'IS' Ident ]
        """
        type_token = self.current_token()
        declared_type = type_token.type
        self.advance()

        ident_token = self.match("IDENT")
        var_name = ident_token.value

        # SEMANTIC CHECK: Duplicate Declaration
        if var_name in self.symbol_table:
            self.semantic_error(f"Variable '{var_name}' is already defined.")

        # Register variable
        self.symbol_table[var_name] = declared_type

        # Check for optional initialization: IS value
        if self.current_token().type == "IS":
            self.advance()
            if declared_type == "INT":
                expr_type = self.parse_expression()
                if expr_type != "INT":
                    self.semantic_error(
                        f"Cannot assign {expr_type} expression to INT variable '{var_name}'"
                    )

            elif declared_type == "STR":
                val_token = self.match("IDENT")
                source_var = val_token.value

                if source_var not in self.symbol_table:
                    self.semantic_error(
                        f"Variable '{source_var}' used before definition."
                    )

                if self.symbol_table[source_var] != "STR":
                    self.semantic_error(
                        f"Cannot assign INT variable '{source_var}' to STR variable '{var_name}'"
                    )

    def parse_assignment(self):
        """
        Assignment ::= 'INTO' Ident 'IS' Expression
        """
        self.match("INTO")
        ident_token = self.match("IDENT")
        var_name = ident_token.value

        # SEMANTIC CHECK: Variable must exist
        if var_name not in self.symbol_table:
            self.semantic_error(
                f"Variable '{var_name}' used before definition."
            )
        else:
            target_type = self.symbol_table[var_name]

        self.match("IS")
        expr_type = self.parse_expression()

        # SEMANTIC CHECK: Type Compatibility
        if target_type != expr_type:
            self.semantic_error(
                f"Cannot assign {expr_type} result to {target_type} variable '{var_name}'."
            )

    def parse_input(self):
        """
        Input ::= 'BEG' Ident
        """
        self.match("BEG")
        ident_token = self.match("IDENT")
        var_name = ident_token.value

        # SEMANTIC CHECK: Variable must exist
        if var_name not in self.symbol_table:
            self.semantic_error(
                f"Variable '{var_name}' used in BEG before definition."
            )

    def parse_output(self):
        """
        Output ::= 'PRINT' Expression
        """
        self.match("PRINT")
        self.parse_expression()

    def parse_expression(self):
        """
        Parses an expression and returns its TYPE ("INT" or "STR").
        Handles:
        1. Literals (INT_LIT)
        2. Variables (IDENT)
        3. Prefix Operations (ADD, SUB, MULT, DIV, MOD)
        """
        token = self.current_token()

        # Case 1: Integer Literal
        if token.type == "INT_LIT":
            self.advance()
            return "INT"

        # Case 2: Variable
        elif token.type == "IDENT":
            var_name = token.value
            self.advance()

            # SEMANTIC CHECK: Defined?
            if var_name not in self.symbol_table:
                self.semantic_error(
                    f"Variable '{var_name}' used in expression before definition."
                )

            return self.symbol_table[var_name]

        # Case 3: Math Operations (Prefix)
        elif token.type in ["ADD", "SUB", "MULT", "DIV", "MOD"]:
            op_type = token.type
            self.advance()  # consume operator

            # Recursively parse left and right operands
            type1 = self.parse_expression()
            type2 = self.parse_expression()

            # SEMANTIC CHECK: Math requires INTs
            if type1 != "INT" or type2 != "INT":
                self.semantic_error(
                    f"Operation {op_type} requires INT operands. Found {type1} and {type2}."
                )

            return "INT"  # Result of math is always INT

        else:
            self.syntax_error(
                f"Expected expression (Literal, Variable, or Operation), found '{token.type}'"
            )
