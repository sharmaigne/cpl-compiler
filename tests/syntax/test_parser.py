import io

import syntax.ast_nodes as ast_nodes
from lexer import Lexer, TokenType
from syntax.parser import Parser

# ==========================================
#           INTEGRATION HELPER
# ==========================================


def create_parser_from_source(source_code: str) -> Parser:
    """
    Simulates the full workflow:
    1. Source Code -> Lexer -> Token Objects
    2. Token Objects -> .tkn file format (String)
    3. .tkn file (StringIO) -> Parser -> AST
    """
    # 1. Run Lexer
    lexer_stream = io.StringIO(source_code)
    lexer = Lexer(lexer_stream)
    tokens = lexer.tokenize()

    # 2. Simulate writing to a .tkn file
    # We use the __str__ method of the Lexer's Token class which
    # formats it exactly how the Parser expects (e.g., "<INT_LIT = 5 [1,1]>")
    tkn_file_content = ""
    for token in tokens:
        tkn_file_content += str(token) + "\n"

    # 3. Create a file-like object for the Parser to read
    tkn_file_obj = io.StringIO(tkn_file_content)

    # 4. Initialize Parser with this file object
    parser = Parser(tkn_file_obj)
    print(parser.ast)
    return parser


# ==========================================
#                TEST CASES
# ==========================================


def test_minimal_program():
    """Test: IOL LOI"""
    source = "IOL LOI"
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    assert isinstance(ast, ast_nodes.Program)
    assert len(ast.statements) == 0


def test_variable_declaration_int():
    """Test: INT x IS 5"""
    source = """
    IOL
    INT x IS 5
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    stmt = ast.statements[0]
    assert isinstance(stmt, ast_nodes.VarDecl)
    assert stmt.var_type == TokenType.INT
    assert stmt.var_name == "x"
    assert stmt.value.value == 5


def test_variable_declaration_str():
    """Test: STR y"""
    source = """
    IOL
    STR y
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    stmt = ast.statements[0]
    assert isinstance(stmt, ast_nodes.VarDecl)
    assert stmt.var_type == TokenType.STR


def test_assignment():
    """Test: INTO x IS 10"""
    source = """
    IOL
    INT x
    INTO x IS 10
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    # stmt 0 is Decl, stmt 1 is Assignment
    assign_stmt = ast.statements[1]
    assert isinstance(assign_stmt, ast_nodes.Assignment)
    assert assign_stmt.var_name == "x"
    assert assign_stmt.expr.value == 10


def test_input():
    """Test: BEG x"""
    source = """
    IOL
    INT x
    BEG x
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    stmt = ast.statements[1]
    assert isinstance(stmt, ast_nodes.InputStmt)
    assert stmt.var_name == "x"


def test_output_math():
    """Test: PRINT ADD 5 10"""
    source = """
    IOL
    PRINT ADD 5 10
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    stmt = ast.statements[0]
    assert isinstance(stmt, ast_nodes.OutputStmt)
    assert stmt.expr.op == TokenType.ADD
    assert stmt.expr.left.value == 5
    assert stmt.expr.right.value == 10


def test_complex_expression():
    """Test: MULT ADD 1 2 3"""
    source = """
    IOL
    PRINT MULT ADD 1 2 3
    LOI
    """
    parser = create_parser_from_source(source)
    ast = parser.parse()

    assert parser.errors == []
    # Should correspond to (1+2) * 3
    mult_node = ast.statements[0].expr
    assert mult_node.op == TokenType.MULT
    assert mult_node.right.value == 3
    assert mult_node.left.op == TokenType.ADD


# ==========================================
#           ERROR HANDLING TESTS
# ==========================================


def test_syntax_error_missing_iol():
    """Test program not starting with IOL."""
    source = """
    INT x
    LOI
    """
    parser = create_parser_from_source(source)
    parser.parse()

    assert len(parser.errors) > 0
    assert "Expected token 'IOL'" in parser.errors[0]


def test_semantic_undefined_var():
    """Test using undefined variable."""
    source = """
    IOL
    PRINT x
    LOI
    """
    parser = create_parser_from_source(source)
    parser.parse()

    assert len(parser.errors) == 1
    assert "used before definition" in parser.errors[0]


def test_semantic_duplicate_var():
    """Test duplicate declaration."""
    source = """
    IOL
    INT x
    INT x
    LOI
    """
    parser = create_parser_from_source(source)
    parser.parse()

    assert len(parser.errors) == 1
    assert "already defined" in parser.errors[0]


def test_semantic_type_mismatch():
    """Test assigning INT to STR."""
    source = """
    IOL
    STR s
    INTO s IS 5
    LOI
    """
    parser = create_parser_from_source(source)
    parser.parse()

    assert len(parser.errors) > 0
    # Note: Depending on implementation details, this might verify exact error message
    assert "Cannot assign" in parser.errors[0]


def test_lexical_error():
    """Test invalid token handling."""
    source = """
    IOL
    INT x IS 5
    @InvalidToken
    LOI
    """
    parser = create_parser_from_source(source)
    parser.parse()

    # Lexer marks it as ERR_LEX, Parser checks for ERR_LEX in parse_statement
    assert len(parser.errors) > 0
    assert "Lexical" in parser.errors[0]
