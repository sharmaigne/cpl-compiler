import io
from parser import Parser


def run_parser(token_lines):
    """
    Helper to run the parser on a list of token strings.
    Returns True if valid, False if invalid.
    """
    file_content = "\n".join(token_lines)
    file_obj = io.StringIO(file_content)

    parser = Parser(file_obj)
    # The parse() method catches exceptions and prints them.
    # We want to ensure it returns False on error.
    return parser.parse()


def assert_error_message(capsys, expected_snippet):
    """
    Helper to verify that the specific error message was printed.
    """
    captured = capsys.readouterr()
    output = captured.out + captured.err

    if expected_snippet not in output:
        # Failed to find error, print what we DID find for debugging
        print(f"\n[DEBUG] Expected error: '{expected_snippet}'")
        print(f"[DEBUG] Actual output: {output}")

    assert expected_snippet in output


# ==========================================
#              TEST CASES
# ==========================================


def test_minimal_program():
    tokens = ["<IOL [1,1]>", "<LOI [2,1]>", "<EOF [3,1]>"]
    assert run_parser(tokens) is True


def test_missing_iol(capsys):
    tokens = ["<INT [1,1]>", "<LOI [2,1]>", "<EOF [3,1]>"]
    assert run_parser(tokens) is False
    assert_error_message(capsys, "Expected token 'IOL'")


def test_code_after_loi(capsys):
    tokens = ["<IOL [1,1]>", "<LOI [2,1]>", "<INT [3,1]>", "<EOF [4,1]>"]
    assert run_parser(tokens) is False
    assert_error_message(capsys, "Expected token 'EOF'")


def test_duplicate_variable_declaration(capsys):
    tokens = [
        "<IOL [1,1]>",
        "<INT [2,1]>",
        "<IDENT = x [2,5]>",
        "<INT [3,1]>",
        "<IDENT = x [3,5]>",
        "<LOI [4,1]>",
        "<EOF [5,1]>",
    ]
    assert run_parser(tokens) is False
    assert_error_message(capsys, "Variable 'x' is already defined")


def test_undefined_variable_usage(capsys):
    tokens = [
        "<IOL [1,1]>",
        "<PRINT [2,1]>",
        "<IDENT = y [2,7]>",
        "<LOI [3,1]>",
        "<EOF [4,1]>",
    ]
    assert run_parser(tokens) is False
    assert_error_message(
        capsys, "Variable 'y' used in expression before definition"
    )


def test_int_initialization_invalid_type(capsys):
    tokens = [
        "<IOL [1,1]>",
        "<STR [2,1]>",
        "<IDENT = s [2,5]>",
        "<INT [3,1]>",
        "<IDENT = x [3,5]>",
        "<IS [3,10]>",
        "<IDENT = s [3,13]>",
        "<LOI [4,1]>",
        "<EOF [5,1]>",
    ]
    assert run_parser(tokens) is False
    assert_error_message(
        capsys, "Cannot assign STR expression to INT variable 'x'"
    )


def test_str_initialization_invalid_literal(capsys):
    """STR cannot be initialized by a literal (Parser logic check)"""
    tokens = [
        "<IOL [1,1]>",
        "<STR [2,1]>",
        "<IDENT = a [2,5]>",
        "<IS [2,10]>",
        "<INT_LIT = 5 [2,13]>",
        "<LOI [3,1]>",
        "<EOF [4,1]>",
    ]
    assert run_parser(tokens) is False
    # Expect failure because STR decl expects IDENT, not INT_LIT
    assert_error_message(capsys, "Expected token 'IDENT', found 'INT_LIT'")


def test_math_type_mismatch(capsys):
    tokens = [
        "<IOL [1,1]>",
        "<STR [2,1]>",
        "<IDENT = s [2,5]>",
        "<PRINT [3,1]>",
        "<ADD [3,7]>",
        "<INT_LIT = 5 [3,11]>",
        "<IDENT = s [3,13]>",
        "<LOI [4,1]>",
        "<EOF [5,1]>",
    ]
    assert run_parser(tokens) is False
    assert_error_message(capsys, "Operation ADD requires INT operands")
