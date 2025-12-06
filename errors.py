class ErrorCode:
    # Lexical
    UNKNOWN_WORD = "Variable or keyword '{word}' is not recognized."

    # Syntax
    UNEXPECTED_TOKEN = "Expected token '{expected}', found '{actual}'."
    UNEXPECTED_STATEMENT = (
        "Unexpected token '{token}' found in statement context."
    )
    MISSING_IOL = "Program must start with 'IOL'."
    MISSING_LOI = "Program must end with 'LOI'."
    CODE_AFTER_LOI = "Code found after 'LOI'. Program must end there."

    # Semantic (Variables)
    DUPLICATE_VAR = "Variable '{name}' is already defined."
    UNDEFINED_VAR = "Variable '{name}' used before definition."

    # Semantic (Types)
    TYPE_MISMATCH = (
        "Cannot assign {expr_type} to {target_type} variable '{name}'."
    )
    MATH_OPERAND_ERROR = (
        "Operation {op} requires INT operands. Found {t1} and {t2}."
    )
