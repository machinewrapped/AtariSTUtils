import os
import tkinter as tk
from tkinter import ttk

class OpcodeApp(tk.Tk):
    def __init__(self, filename):
        super().__init__()
        self.title("68000 Opcode Cycle Counts")
        self.geometry("1600x840")

        # Frame for filter and table
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        # Filter Entry
        filter_label = ttk.Label(frame, text="Filter by Opcode or cycle count:")
        filter_label.pack(side=tk.TOP, anchor="w")
        self.filter_entry = ttk.Entry(frame)
        self.filter_entry.pack(side=tk.TOP, fill=tk.X)
        self.filter_entry.bind("<KeyRelease>", self.filter_data)

        # Scrollable Frame for Table
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Set bigger font for Treeview
        style = ttk.Style()
        style.configure("Treeview", font=("Courier New", 12))  # Adjust font size here
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))  # Header font size

        self.tree = ttk.Treeview(table_frame, columns=[], show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Make columns resizable with the window
        self.tree.bind("<Configure>", self.adjust_column_widths)

        # Parse the file
        self.opcode_data = self.parse_file(filename)
        self.original_data = self.opcode_data.copy()
        self.display_data(self.opcode_data)

    def parse_file(self, filename):
        with open(filename, "r") as f:
            lines = f.readlines()

        # Find the position of the ":" to determine where the opcode column ends
        header = lines[0]
        colon_index = header.index(":") if ":" in header else len(header)  # Safe fallback if no ":"

        # Parse the rest of the header to find addressing modes (ignore the colon itself)
        columns = []
        prev_char = ' '
        start_idx = colon_index + 1  # Start after the colon for the rest of the columns
        for i, char in enumerate(header[start_idx:], start=start_idx):
            if prev_char == ' ' and char != ' ':
                start_idx = i
            elif prev_char != ' ' and char == ' ':
                columns.append((header[start_idx:i].strip(), start_idx, i))
            prev_char = char

        columns.append((header[start_idx:].strip(), start_idx, len(header)))  # Add last column
        self.tree.config(columns=["Opcode"] + [c[0] for c in columns])
        self.tree.heading("Opcode", text="Opcode")
        self.tree.column("Opcode", anchor=tk.W)  # Left-align the opcode column
        for col in columns:
            self.tree.heading(col[0], text=col[0])
            self.tree.column(col[0], anchor=tk.CENTER)  # Center-align addressing mode columns

        opcode_data = []
        # Process each row of data
        for line in lines[1:]:
            opcode = line[:colon_index].strip()  # Extract the opcode name up to the ":"
            # distinct_opcodes = opcode.split('/')  # Split distinct opcodes
            distinct_opcodes = [opcode]

            for distinct_opcode in distinct_opcodes:  # Handle distinct opcodes correctly
                row = [distinct_opcode.strip()]
                for _, start, end in columns:
                    row.append(line[start:end].strip())  # Extract cycle counts
                opcode_data.append(row)

        # Sort the data by opcode
        opcode_data.sort(key=lambda x: x[0])

        return opcode_data

    def display_data(self, data):
        # Clear previous data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert new data
        for row in data:
            self.tree.insert("", "end", values=row)

    def filter_data(self, event=None):
        filter_text = self.filter_entry.get().strip().lower()
        if filter_text == "":
            self.display_data(self.original_data)
        else:
            # if the filter is a number, check if any column except the first exactly matches the number
            # if the filter is not a number, check if the filter is in the opcode name
            if filter_text.isdigit():
                filtered_data = [row for row in self.original_data if any(filter_text == col for col in row[1:])]
            else:
                filtered_data = [row for row in self.original_data if filter_text in row[0].lower()]
            
            self.display_data(filtered_data)

    def adjust_column_widths(self, event=None):
        """Dynamically adjust column widths based on window size."""
        total_width = self.tree.winfo_width()
        column_count = len(self.tree["columns"])
        if column_count > 0:
            column_count = column_count + 1 
            column_width = int(total_width // column_count)
            self.tree.column("Opcode", width=column_width*2)

            for col in self.tree["columns"][1:]:
                self.tree.column(col, width=column_width)

# Usage
if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "68000 Cycle Count.txt")
    app = OpcodeApp(path)
    app.mainloop()
