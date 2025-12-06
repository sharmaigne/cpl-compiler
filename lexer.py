from dataclasses import dataclass
from enum import Enum, auto
from typing import TextIO


class TokenType(Enum):
    IOL = auto()
    LOI = auto()
    INT = auto()
    STR = auto()
    INTO = auto()
    IS = auto()
    BEG = auto()
    PRINT = auto()
    ADD = auto()
    SUB = auto()
    MULT = auto()
    DIV = auto()
    MOD = auto()
    NEWLN = auto()
    INT_LIT = auto()
    IDENT = auto()
    EOF = auto()
    ERR_LEX = auto()


@dataclass
class Token:
    """
    A Token holds its type, an optional str `value`, and its starting position
    in `line` and `column`
    """

    name: TokenType
    value: str | int | None
    line: int
    column: int

    def __str__(self) -> str:
        value = f" = {self.value}" if self.value is not None else ""
        name = str(self.name).lstrip("TokenType.")
        return f"<{name}{value} [{self.line},{self.column}]>"


class Lexer:
    KEYWORDS = {
        "IOL": TokenType.IOL,
        "LOI": TokenType.LOI,
        "INT": TokenType.INT,
        "STR": TokenType.STR,
        "INTO": TokenType.INTO,
        "IS": TokenType.IS,
        "BEG": TokenType.BEG,
        "PRINT": TokenType.PRINT,
        "ADD": TokenType.ADD,
        "SUB": TokenType.SUB,
        "MULT": TokenType.MULT,
        "DIV": TokenType.DIV,
        "MOD": TokenType.MOD,
        "NEWLN": TokenType.NEWLN,
    }

    def __init__(self, stream: TextIO) -> None:
        """
        Lexer takes in a `stream` which is used to do buffer reads for
        tokenization.
        """

        self.stream: TextIO = stream
        self.current_char: str = ""
        self.current_column: int = 1
        self.current_line: int = 1
        self.tokens: list[Token] = []

    def _advance(self) -> str:
        """
        Advances the stream.

        Should only be called within `Lexer.tokenize()`.
        """

        self.current_char = self.stream.read(1)

        if self.current_char:
            self.current_column += 1

        return self.current_char

    @classmethod
    def _make_token(cls, value: str, start_line: int, start_column) -> Token:
        """
        Helper method to tag tokens.
        """

        if value in cls.KEYWORDS.keys():
            return Token(
                cls.KEYWORDS[value],
                None,
                start_line,
                start_column,
            )

        if value.isnumeric():
            return Token(
                TokenType.INT_LIT,
                int(value),
                start_line,
                start_column,
            )

        if value.isalnum():
            return Token(
                TokenType.IDENT,
                value,
                start_line,
                start_column,
            )

        return Token(
            TokenType.ERR_LEX,
            value,
            start_line,
            start_column,
        )

    def tokenize(self) -> list[Token]:
        """
        Tokenize the stream and returns the token list, which can be accessed
        again as `Lexer.tokens`.

        Invalidates the stream afterward.
        """

        current_token = ""

        start_column = self.current_column
        start_line = self.current_line

        while True:
            ch = self._advance()

            if not ch:  # EOF case
                if current_token:
                    token = self._make_token(
                        current_token,
                        start_line,
                        start_column,
                    )
                    self.tokens.append(token)

                self.tokens.append(
                    Token(
                        TokenType.EOF,
                        None,
                        self.current_line,
                        self.current_column,
                    )
                )

                break

            if ch.isspace():
                # flush current_token
                if current_token:
                    token = self._make_token(
                        current_token,
                        start_line,
                        start_column,
                    )
                    self.tokens.append(token)
                current_token = ""

                # update coords on new line
                if ch == "\n":
                    self.current_line += 1
                    self.current_column = 1

                start_line = self.current_line
                start_column = self.current_column

                continue

            current_token += ch

        return self.tokens
