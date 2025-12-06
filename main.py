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

        # state
        self.ast = None
        self.tokens = []
        self.is_dirty = True  # True if code has changed since last compile
        self.last_compile_success = False

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
        self.editor_panel.editor.bind("<KeyRelease>", self.on_code_modified)

    def on_code_modified(self, event=None):
        """Called whenever the user types in the editor."""
        # Ignore navigation keys to prevent false positives
        if event and event.keysym in [
            "Up",
            "Down",
            "Left",
            "Right",
            "Control_L",
        ]:
            return

        self.is_dirty = True
        self.last_compile_success = False
        self.ast = None

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
        self.is_dirty = True
        self.last_compile_success = False
        self.ast = None
        self.tokens = []

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

        self.is_dirty = True

    def compile_code(self):
        """
        Performs Lexical Analysis and Parsing.
        Updates the console with success or error messages.
        """
        # 1. Reset Console
        with self.console_panel.console as console:
            console.delete("1.0", "end")

        # 2. Get content
        content = self.editor_panel.editor.get("1.0", "end").strip()
        if not content:
            with self.console_panel.console as console:
                console.insert("end", "Error: Source code is empty.\n")
            return

        # 3. LEXICAL ANALYSIS
        stream = io.StringIO(content)
        lexer = Lexer(stream)
        lexer.tokenize()

        self.tokens = lexer.tokens  # Store for display

        base_name = self.file_name
        if base_name.endswith(".iol"):
            base_name = base_name[:-4]  # Remove last 4 chars (.iol)

        # Save .tkn file
        with open(f"{base_name}.tkn", "w") as f:
            f.writelines("\n".join(map(str, lexer.tokens)))

        # 4. PARSING
        token_stream_str = "\n".join(map(str, lexer.tokens))
        parser_input = io.StringIO(token_stream_str)
        parser = Parser(parser_input)

        self.ast = parser.parse()

        # 5. RESULT DISPLAY & STATE UPDATES
        with self.console_panel.console as console:
            if parser.errors:
                self.last_compile_success = False
                self.is_dirty = True

                console.insert("end", "Compile Unsuccessful. Errors found:\n\n")
                for err in parser.errors:
                    console.insert("end", f"{err}\n")
            else:
                self.last_compile_success = True
                self.is_dirty = False  # Code is now clean
                self.output_panel.display_variables(parser.symbol_table)

                console.insert(
                    "end",
                    f"Analysis successful.\n{self.file_name} compiled with no errors found.\n",
                )

    def display_tokenized(self):
        """Displays the tokens from the last compilation."""
        # Check memory instead of file
        if not self.tokens:
            with self.console_panel.console as console:
                console.insert(
                    "end",
                    "\n[System] No tokenized code found. Please Compile first.\n",
                )
            return

        formatted_tokens = [f"{str(token)}\n" for token in self.tokens]

        self.console_panel.display_tokenized_code(formatted_tokens)

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
        """Executes the Evaluator using the AST generated by compile_code."""

        # --- ADD THESE GUARD CLAUSES ---
        with self.console_panel.console as console:
            if self.is_dirty:
                console.insert(
                    "end",
                    "\n[System] Error: Source code has been modified. Please Compile first.\n",
                )
                return

            if not self.last_compile_success or not self.ast:
                console.insert(
                    "end",
                    "\n[System] Error: Compilation failed or not performed. Please fix errors and Compile first.\n",
                )
                return
        # -------------------------------

        if hasattr(self.output_panel, "text_area"):
            self.output_panel.text_area.delete("1.0", "end")

        try:
            # --- UPDATE: Use self.ast instead of re-parsing ---
            evaluator = Evaluator(
                self.ast,
                on_print=self.append_output,
                on_input=self.request_input,
            )

            self.append_output("\n--- Program Execution Start ---\n")
            evaluator.evaluate()
            self.append_output("\n--- Program Execution End ---\n")

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
            label="Compile Code",
            command=self.parent.compile_code,
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
