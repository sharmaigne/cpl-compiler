import tkinter as tk
from tkinter import ttk


class OutputPanel(tk.Frame):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(master=parent, *args, **kwargs)
        self.configure(bg="white")
        self.pack(expand=True, fill="both")

        self.init_style()
        self.init_header()
        self.init_table()

    def init_style(self):
        """Configures the custom style for the Treeview."""
        style = ttk.Style()

        # Use 'clam' theme if available, as it allows for better color customization
        # compared to the default Windows/Mac themes.
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # 1. Configure the Body (Rows)
        style.configure(
            "VariableTable.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",  # The empty space area
            rowheight=25,
            font=("Arial", 10),
        )

        # 2. Configure the Header
        style.configure(
            "VariableTable.Treeview.Heading",
            background="#F2A65A",  # Matches your ConsolePanel orange
            foreground="black",
            font=("Arial", 10, "bold"),
            relief="flat",
        )

        # 3. Add a slight hover effect to the header
        style.map(
            "VariableTable.Treeview.Heading", background=[("active", "#E09545")]
        )

        # 4. Remove the blue selection highlight (since it's read-only)
        style.map(
            "VariableTable.Treeview",
            background=[("selected", "white")],
            foreground=[("selected", "black")],
        )

    def init_header(self):
        # We can remove the separate Label header since the Treeview
        # now has a styled header, but keeping a main title is fine too.
        # Let's style it to match.
        self.header = tk.Label(
            self,
            text="Variable Table",
            bg="#2F5F9E",  # Matches App Background (Blue)
            fg="white",
            font=("Arial", 10, "bold"),
            pady=5,
        )
        self.header.pack(fill="x")

    def init_table(self):
        columns = ("name", "type")

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            selectmode="none",
            style="VariableTable.Treeview",  # <--- Apply the custom style
        )

        self.tree.heading("name", text="Variable Name")
        self.tree.heading("type", text="Data Type")

        self.tree.column("name", width=150, anchor="center")
        self.tree.column("type", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")

    def display_variables(self, symbol_table: dict):
        """
        Populates the table with data from the Parser's symbol table.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not symbol_table:
            return

        for var_name, var_type in symbol_table.items():
            type_str = (
                var_type.name if hasattr(var_type, "name") else str(var_type)
            )
            self.tree.insert("", "end", values=(var_name, type_str))
