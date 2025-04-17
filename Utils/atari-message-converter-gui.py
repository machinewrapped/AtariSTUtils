import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Default character mapping (you may need to adjust this based on the exact character set used)
DEFAULT_CHAR_MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?:-()'\" "
ASCII_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz"

class AtariMessageConverterGUI:
    def __init__(self, master):
        self.master = master
        master.title("Atari ST Message Converter")
        master.geometry("800x600")

        self.char_map = DEFAULT_CHAR_MAP
        self.updating = False  # Flag to prevent recursive updates

        # Create main frame
        main_frame = ttk.Frame(master, padding="3 3 12 12")
        main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(column=0, row=0, sticky=(tk.W, tk.E))
        ttk.Button(buttons_frame, text="Load TXT", command=self.load_txt).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save TXT", command=self.save_txt).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Load MSG", command=self.load_msg).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save MSG", command=self.save_msg).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Load Character Map", command=self.load_char_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save Character Map", command=self.save_char_map).pack(side=tk.LEFT, padx=5)

        # Paned window for text areas
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.grid(column=0, row=1, sticky=(tk.N, tk.W, tk.E, tk.S))

        # Text areas
        self.original_text = tk.Text(paned_window, wrap=tk.NONE, width=80, height=10)
        self.original_text.insert(tk.END, "Original Text")
        paned_window.add(self.original_text, weight=1)

        self.atari_text = tk.Text(paned_window, wrap=tk.NONE, width=80, height=10)
        self.atari_text.insert(tk.END, "Atari Format")
        self.atari_text.configure(state='disabled')  # Set Atari text widget to read-only
        paned_window.add(self.atari_text, weight=1)

        # Character map
        self.char_map_text = tk.Text(main_frame, wrap=tk.WORD, width=80, height=3)
        self.char_map_text.grid(column=0, row=2, sticky=(tk.W, tk.E))
        self.char_map_text.insert(tk.END, self.char_map)

        # Configure weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Scrollbars
        original_scrollbar = ttk.Scrollbar(self.original_text, orient=tk.HORIZONTAL, command=self.original_text.xview)
        original_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.original_text.configure(xscrollcommand=original_scrollbar.set)

        atari_scrollbar = ttk.Scrollbar(self.atari_text, orient=tk.HORIZONTAL, command=self.atari_text.xview)
        atari_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.atari_text.configure(xscrollcommand=atari_scrollbar.set)

        # Bind events
        self.original_text.bind("<KeyRelease>", self.update_atari_text)
        # No need to bind update_original_text since Atari text is read-only
        self.char_map_text.bind("<KeyRelease>", self.update_char_map)

    def load_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.original_text.delete('1.0', tk.END)
                self.original_text.insert(tk.END, content)
            self.update_atari_text()

    def save_txt(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.original_text.get('1.0', tk.END))
            messagebox.showinfo("Success", f"File saved as {file_path}")

    def load_msg(self):
        file_path = filedialog.askopenfilename(filetypes=[("Source files", "*.S;*.MSG")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.atari_text.configure(state='normal')
                self.atari_text.delete('1.0', tk.END)
                self.atari_text.insert(tk.END, content)
                self.atari_text.configure(state='disabled')
            self.update_original_text()

    def save_msg(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".msg", filetypes=[("Source files", "*.S;*.MSG")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.atari_text.get('1.0', tk.END))
            messagebox.showinfo("Success", f"File saved as {file_path}")

    def load_char_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                self.char_map = file.read().strip()
                self.char_map_text.delete('1.0', tk.END)
                self.char_map_text.insert(tk.END, self.char_map)
            self.update_atari_text()

    def save_char_map(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.char_map)
            messagebox.showinfo("Success", f"Character map saved as {file_path}")

    def update_atari_text(self, event=None):
        if self.updating:
            return
        self.updating = True
        ascii_text = self.original_text.get('1.0', tk.END)
        atari_text = self.ascii_to_atari(ascii_text)
        self.atari_text.configure(state='normal')
        self.atari_text.delete('1.0', tk.END)
        self.atari_text.insert(tk.END, atari_text)
        self.atari_text.configure(state='disabled')
        self.updating = False

    def update_original_text(self, event=None):
        if self.updating:
            return
        self.updating = True
        atari_text = self.atari_text.get('1.0', tk.END)
        ascii_text = self.atari_to_ascii(atari_text)
        self.original_text.configure(state='normal')
        self.original_text.delete('1.0', tk.END)
        self.original_text.insert(tk.END, ascii_text)
        self.updating = False

    def update_char_map(self, event=None):
        self.char_map = self.char_map_text.get('1.0', tk.END).strip()
        self.update_atari_text()

    def ascii_to_atari(self, ascii_text):
        atari_lines = []
        for line in ascii_text.split('\n'):
            if len(line) > 0:
                atari_line = ''.join(self._ascii_char_to_atari(char) for char in line)
                atari_lines.append(f'\tdc.b "{atari_line}"')
        return '\n'.join(atari_lines)

    def _ascii_char_to_atari(self, char):
        if char == ' ':
            return ' '
        if char.upper() in self.char_map:
            return chr(self.char_map.index(char.upper()) + ord('A'))
        return '*'

    def atari_to_ascii(self, atari_text):
        ascii_lines = []
        for line in atari_text.split('\n'):
            cleaned_line = line.strip().removeprefix('dc.b "').rstrip('"')
            ascii_line = ''.join(self._atari_char_to_ascii(char) for char in cleaned_line)
            ascii_lines.append(ascii_line)
        return '\n'.join(ascii_lines)

    def _atari_char_to_ascii(self, char):
        if char == ' ':
            return ' '
        char_index = ord(char) - ord('A')
        if 0 <= char_index < len(self.char_map):
            return self.char_map[char_index]
        return '*'

if __name__ == "__main__":
    root = tk.Tk()
    app = AtariMessageConverterGUI(root)
    root.mainloop()
