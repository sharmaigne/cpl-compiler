import io
import tkinter as tk
from tkinter import filedialog as fd

from lexer import Lexer
from panels.console import ConsolePanel
from panels.editor import EditorPanel
from panels.output import OutputPanel


class App(tk.Tk):
    DEFAULT_FILENAME: str = "program.iol"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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

        self.file_name = self.DEFAULT_FILENAME
        self.update_title("New file")
        self.editor_panel.editor.delete("1.0", "end")

        self.is_tokenized = False

    def file_new(self):
        self.cleanup()

    def file_open(self):
        file = fd.askopenfile(
            title="Open File",
            filetypes=[("Integer Oriented Language files", "*.iol")],
        )

        # No file selected
        if not file:
            return

        self.cleanup()
        with file as f:
            self.file_name = f.name.split("/")[-1]
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
                console.insert("end", "No tokenized code found.")

            return

        with open(f"{self.file_name.rstrip('.iol')}.tkn", "r") as f:
            lines = f.readlines()

        self.console_panel.display_tokenized_code(lines)


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

        # TODO: add execute commands

        self.add_cascade(menu=menu_execute, label="Execute")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
