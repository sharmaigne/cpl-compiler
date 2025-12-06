import io
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import simpledialog as sd

from evaluator import Evaluator
from lexer import Lexer
from panels.console import ConsolePanel
from panels.editor import EditorPanel
from panels.output import OutputPanel
from syntax.parser import Parser


class App(tk.Tk):
    DEFAULT_FILENAME: str = "program.iol"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.update_title("New file")
        self.geometry("900x560")

        self.init_menubar()

        self.init_background()
        self.init_left_separator()
        self.init_output_panel()

        self.init_editor_panel()
        self.init_console_panel()

        self.cleanup()

    def update_title(self, new_title):
        """Update the title while maintaining IOL suffix"""
        self.wm_title(f"{new_title} | IOL")

    def init_menubar(self):
        self.option_add("*tearOff", tk.FALSE)
        self.menubar = AppMenu(self)
        self["menu"] = self.menubar

    def init_background(self):
        self.background = tk.PanedWindow(
            self,
            bg="#2F5F9E",
            bd=6,
            relief="flat",
            orient=tk.HORIZONTAL,
            handlesize=2,
        )

        self.background.pack(fill="both", expand=True, padx=8, pady=8)

    def init_left_separator(self):
        """Separates the editor and console vertically."""
        self.left_separator = tk.PanedWindow(
            self.background,
            background="#000000",
            orient=tk.VERTICAL,
            handlesize=2,
        )
        self.background.add(self.left_separator)

    def init_output_panel(self):
        self.output_panel = OutputPanel(self.background)
        self.background.add(self.output_panel)

    def init_console_panel(self):
        """Only call after self.init_left_separator()"""
        self.console_panel = ConsolePanel(self.left_separator)
        self.left_separator.add(self.console_panel)

    def init_editor_panel(self):
        """Only call after self.init_left_separator()"""
        self.editor_panel = EditorPanel(self.left_separator)
        self.left_separator.add(
            self.editor_panel, height=self.winfo_vrootheight() * 3 / 5
        )

    def cleanup(self):
        """
        Run for new file. Clean up previous set state.
        """
        self.file_path = None
        self.file_name = self.DEFAULT_FILENAME
        self.update_title("New file")
        self.editor_panel.editor.delete("1.0", "end")
        with self.console_panel.console as console:
            console.delete("1.0", "end")

        self.is_tokenized = False

    def file_new(self):
        self.cleanup()

    def file_open(self):
        file = fd.askopenfile(
            title="Open File",
            filetypes=[("Integer Oriented Language files", "*.iol")],
        )

        if not file:
            return

        self.cleanup()
        with file as f:
            self.file_path = f.name  # Store full path
            self.file_name = self.file_path.split("/")[-1]
            self.update_title(self.file_name)

            content = f.readlines()
            self.editor_panel.editor.insert("1.0", "".join(content))

    def compile_tokenize(self):
        stream = io.StringIO(self.editor_panel.editor.get("1.0", "end").strip())
        lexer = Lexer(stream)

        lexer.tokenize()

        # write into .tkn file
        with open(f"{self.file_name.rstrip('.iol')}.tkn", "w") as f:
            f.writelines("\n".join(map(str, lexer.tokens)))

        self.is_tokenized = True

        # write results into console
        self.console_panel.display_tokenization_result(lexer.tokens)

    def display_tokenized(self):
        if not self.is_tokenized:
            with self.console_panel.console as console:
                console.insert("end", "No tokenized code found.\n")

            return

        with open(f"{self.file_name.rstrip('.iol')}.tkn", "r") as f:
            lines = f.readlines()

        self.console_panel.display_tokenized_code(lines)

    def file_save(self):
        content = self.editor_panel.editor.get("1.0", "end").strip()

        if self.file_path:
            with open(self.file_path, "w") as f:
                f.write(content)
        else:
            file = fd.asksaveasfile(
                title="Save",
                filetypes=[("Integer Oriented Language files", "*.iol")],
                defaultextension=".iol",
                initialfile=self.file_name,
            )

            if not file:
                return

            self.file_path = file.name
            self.file_name = self.file_path.split("/")[-1]

            with file as f:
                f.write(content)

            self.update_title(self.file_name)

    def file_save_as(self):
        content = self.editor_panel.editor.get("1.0", "end").strip()

        file = fd.asksaveasfile(
            title="Save As",
            filetypes=[("Integer Oriented Language files", "*.iol")],
            defaultextension=".iol",
            initialfile=(
                self.file_name if self.file_path is None else self.file_name
            ),
        )

        if not file:
            return

        self.file_path = file.name
        self.file_name = self.file_path.split("/")[-1]

        with file as f:
            f.write(content)

        self.update_title(self.file_name)

    def append_output(self, text):
        """Callback for the Evaluator to print to the ConsolePanel."""
        # Using the context manager pattern from console.py
        with self.console_panel.console as console:
            console.insert("end", f"{text}")
            console.see("end")

    def request_input(self, prompt_text):
        """Callback for the Evaluator to get input via Popup."""
        return sd.askstring("Program Input", prompt_text, parent=self)

    def execute_code(self):
        """Full pipeline: Lex -> Parse -> Eval"""

        # 1. Clear previous output
        # (Adjust this based on your OutputPanel implementation)
        if hasattr(self.output_panel, "text_area"):
            self.output_panel.text_area.delete("1.0", "end")

        # 2. Get Source Code
        code_content = self.editor_panel.editor.get("1.0", "end").strip()
        if not code_content:
            return

        try:
            # 3. LEXER
            stream = io.StringIO(code_content)
            lexer = Lexer(stream)
            lexer.tokenize()

            # 4. PARSER
            token_stream_str = "\n".join(map(str, lexer.tokens))
            parser_input = io.StringIO(token_stream_str)

            parser = Parser(parser_input)
            ast = parser.parse()

            if parser.errors:
                # Print errors to console panel
                with self.console_panel.console as console:
                    console.delete("1.0", "end")
                    console.insert("end", "Compilation Errors:\n")
                    for err in parser.errors:
                        console.insert("end", f"{err}\n")
                return

            # 5. EVALUATOR
            # Pass the GUI methods as callbacks
            evaluator = Evaluator(
                ast, on_print=self.append_output, on_input=self.request_input
            )

            self.append_output("--- Program Execution Start ---\n\n")
            evaluator.evaluate()
            self.append_output("\n\n--- Program Execution End ---")

        except Exception as e:
            self.append_output(f"\nRuntime Error: {str(e)}")


class AppMenu(tk.Menu):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        self.init_file_menu()
        self.init_compile_menu()
        self.init_execute_menu()

    def init_file_menu(self):
        menu_file = tk.Menu(self)

        menu_file.add_command(label="New File", command=self.parent.file_new)
        menu_file.add_command(label="Open File", command=self.parent.file_open)
        menu_file.add_command(label="Save", command=self.parent.file_save)
        menu_file.add_command(label="Save As", command=self.parent.file_save_as)

        self.add_cascade(menu=menu_file, label="File")

    def init_compile_menu(self):
        menu_compile = tk.Menu(self)

        menu_compile.add_command(
            label="Tokenize",
            command=self.parent.compile_tokenize,
        )

        menu_compile.add_command(
            label="Show tokenized code",
            command=self.parent.display_tokenized,
        )
        self.add_cascade(menu=menu_compile, label="Compile")

    def init_execute_menu(self):
        menu_execute = tk.Menu(self)

        menu_execute.add_command(
            label="Run Program", command=self.parent.execute_code
        )

        self.add_cascade(menu=menu_execute, label="Execute")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
