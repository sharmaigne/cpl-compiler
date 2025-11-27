## Development

Make sure to run the following lines for local development:

```bash
uv sync
uv run pre-commit install

uv run pytest # for testing
```

### Grammar

| Category               | Token Type          | Lexeme / Pattern                  |
| ---------------------- | ------------------- | --------------------------------- |
| Program Delimiters     | IOL                 | IOL                               |
|                        | LOI                 | LOI                               |
| Data Types             | INT                 | INT                               |
|                        | STR                 | STR                               |
| KEYWORD                | INTO                | INTO                              |
|                        | IS                  | IS                                |
|                        | BEG                 | BEG                               |
|                        | PRINT               | PRINT                             |
| Operators              | ADD                 | ADD                               |
|                        | SUB                 | SUB                               |
|                        | MULT                | MULT                              |
|                        | DIV                 | DIV                               |
|                        | MOD                 | MOD                               |
| Built-in Commands      | NEWLN               | NEWLN                             |
| Literals               | INT_LIT             | A sequence of digits (e.g., 123)  |
| Variables              | IDENT               | Starts with a letter (e.g., num)  |
| Special                | EOF                 | (End of File)                     |
| Error                  | ERR_LEX             | Any error                         |


EBNF
```
Program			::= 'IOL' Statements 'LOI' 'EOF'
StatementList	::= { Statement }

Statement		::= VarDecl
				|	Assignment
				|	Input
				|	Output
				|	Newline

VarDecl      	::= 'INT' Ident [ 'IS' Expression ]
				|	'STR' Ident [ 'IS' Ident ]
Assignment   ::= 'INTO' Ident 'IS' Expression
Input        ::= 'BEG' Ident
Output       ::= 'PRINT' Expression
Newline      ::= 'NEWLN'

Expression   ::= IntLiteral
               | Ident
               | MathOp Expression Expression

MathOp       ::= 'ADD' | 'SUB' | 'MULT' | 'DIV' | 'MOD'

Ident        ::= Letter { Letter | Digit }
IntLiteral   ::= Digit { Digit }
Letter       ::= 'a'...'z' | 'A'...'Z'
Digit        ::= '0'...'9'
```
