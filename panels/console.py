import tkinter as tk

from lexer import Token, TokenType
from widgets.editable_text import EditableText


class ConsolePanel(tk.Frame):
    bg = "#F2A65A"

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(master=parent, bg=self.bg, *args, **kwargs)

        self.init_console()

    def init_console(self):
        self.console = EditableText(self, bg="black", fg="white")
        self.console.config(state="disabled")
        self.console.pack(expand=True, fill="both")

    def display_tokenization_result(self, tokens: list[Token]):
        error_tokens = [t for t in tokens if t.name == TokenType.ERR_LEX]

        with self.console as console:
            console.insert("end", "Tokenization complete.\n")

            if not error_tokens:
                return

            console.insert("end", "Error lexemes found:\n")

            for token in error_tokens:
                console.insert(f"end", f"{token}\n")

    def display_tokenized_code(self, tokens: list[str]):
        with self.console as console:
            console.insert("end", "\n")

            for line in tokens:
                console.insert("end", f"{line}")

            console.insert("end", "\n")
