import tkinter as tk
from tkinter import filedialog, ttk
import struct
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Mapping of register numbers to descriptions
REGISTER_DESCRIPTIONS = {
    0: 'Channel A Fine Tune',
    1: 'Channel A Coarse Tune',
    2: 'Channel B Fine Tune',
    3: 'Channel B Coarse Tune',
    4: 'Channel C Fine Tune',
    5: 'Channel C Coarse Tune',
    6: 'Noise Period',
    7: 'Mixer Control',
    8: 'Channel A Volume',
    9: 'Channel B Volume',
    10: 'Channel C Volume',
    11: 'Envelope Period Fine',
    12: 'Envelope Period Coarse',
    13: 'Envelope Shape/Cycle',
    14: 'I/O Port A',
    15: 'I/O Port B',
}

class SampleTableViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sample Table Viewer")
        self.geometry("1200x750")
        self.entries = []
        self.original_entries = []
        self.register_values = []
        self.num_channels = 2  # Default to 2 channels
        self.create_widgets()

    def create_widgets(self):
        # Create a frame for the table
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create columns based on number of channels
        self.create_table_columns()

        # Add a scrollbar to the table
        scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a frame for the graph
        self.graph_frame = tk.Frame(self)
        self.graph_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Create control frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

        # Create the scale controls
        scale_label = tk.Label(self.control_frame, text="Scale Volume:")
        scale_label.pack(side=tk.LEFT, padx=5)
        self.scale_entry = tk.Entry(self.control_frame, width=10)
        self.scale_entry.pack(side=tk.LEFT, padx=5)
        self.scale_entry.bind("<Return>", lambda event: self.apply_scale())

        # Create a menu with separate options for 2 and 3 channel tables
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        
        # Load submenu
        filemenu.add_command(label="Load 2-Channel Table", command=lambda: self.load_sample_table(2))
        filemenu.add_command(label="Load 3-Channel Table", command=lambda: self.load_sample_table(3))
        filemenu.add_separator()
        
        # Save options
        filemenu.add_command(label="Save Sample Table", command=self.save_sample_table_as_binary)
        filemenu.add_separator()
        filemenu.add_command(label="Load from Text", command=self.load_sample_table_from_text)
        filemenu.add_command(label="Save as Text", command=self.save_sample_table_as_text)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def create_table_columns(self):
        # Remove existing tree if it exists
        if hasattr(self, 'tree'):
            self.tree.destroy()

        # Create columns based on number of channels
        columns = ['Index']
        for i in range(self.num_channels):
            columns.extend([f'Reg{i+1}', f'Val{i+1}'])

        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_sample_table(self, num_channels):
        file_path = filedialog.askopenfilename(
            title=f"Select {num_channels}-Channel Sample Table", 
            filetypes=[("Binary Files", "*.TAB;*.DAT;*.BIN")]
        )
        if file_path:
            self.num_channels = num_channels
            
            with open(file_path, 'rb') as f:
                data = f.read()

            self.parse_sample_table(data, num_channels)

            # Recreate table with new number of columns
            self.create_table_columns()
            self.populate_table()
            self.plot_graph()

            # Keep a copy of the original entries
            self.original_entries = self.entries.copy()

    def save_sample_table_as_binary(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".TAB",
            filetypes=[("Binary Files", "*.TAB;*.DAT;*.BIN")]
        )
        if file_path:
            with open(file_path, 'wb') as f:
                for entry in self.entries:
                    # Write each channel's data
                    for i in range(self.num_channels if self.num_channels == 2 else 4):
                        if i < self.num_channels or (self.num_channels == 3 and i < 3):
                            reg_num = entry[f'reg{i+1}_num']
                            reg_val = entry[f'reg{i+1}_val']
                            f.write(struct.pack('>BB', reg_num, reg_val))
                        else:
                            # Write padding bytes for 3-channel format
                            f.write(struct.pack('>BB', 0, 0))

    def save_sample_table_as_text(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if file_path:
            with open(file_path, 'w') as f:
                # Write header
                header = ['index']
                for i in range(self.num_channels):
                    header.extend([f'reg{i+1}', f'val{i+1}'])
                f.write(','.join(header) + '\n')
                
                # Write data
                for entry in self.entries:
                    values = [str(entry['index'])]
                    for i in range(self.num_channels):
                        values.extend([
                            str(entry[f'reg{i+1}_num']),
                            f"{entry[f'reg{i+1}_val']:02X}"
                        ])
                    f.write(','.join(values) + '\n')

    def load_sample_table_from_text(self):
        file_path = filedialog.askopenfilename(
            title="Select Sample Table",
            filetypes=[("Text Files", "*.txt")]
        )
        if file_path:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            header = lines[0].strip().split(',')
            self.num_channels = (len(header) - 1) // 2  # Subtract 1 for index column, divide by 2 for reg/val pairs
            
            self.create_table_columns()
            self.entries = []
            
            for line in lines[1:]:  # Skip header
                parts = line.strip().split(',')
                if len(parts) == (self.num_channels * 2) + 1:
                    entry = {'index': int(parts[0])}
                    for i in range(self.num_channels):
                        reg_num = int(parts[i*2 + 1])
                        reg_val = int(parts[i*2 + 2], 16)
                        entry[f'reg{i+1}_num'] = reg_num
                        entry[f'reg{i+1}_val'] = reg_val
                        entry[f'raw_bytes{i+1}'] = f'{reg_num:02X}{reg_val:02X}'
                    self.entries.append(entry)
            
            self.original_entries = self.entries.copy()
            self.populate_table()
            self.plot_graph()

    def parse_sample_table(self, data, num_channels):
        self.entries.clear()
        num_entries = 256
        bytes_per_entry = len(data) // num_entries
        bytes_per_channel = 4 if bytes_per_entry == num_channels * 4 else 2 if bytes_per_entry > num_channels else 1
        self.register_values = [{} for _ in range(num_entries)]

        for i in range(num_entries):
            offset = i * bytes_per_entry
            entry = data[offset:offset + bytes_per_entry]
            if len(entry) < bytes_per_entry:
                break

            entry_dict = {'index': i}

            for j in range(num_channels):
                if bytes_per_channel == 4:
                    # Each channel has 4 bytes: register (8 bits) and value (8 bits)
                    channel_data = struct.unpack('>HH', entry[j*4:(j+1)*4])
                    reg_num = (channel_data[0] >> 8) & 0x0F     # Lower 4 bits for register number
                    reg_val = (channel_data[1] >> 8)            # 8 bits for value
                    
                    entry_dict[f'reg{j+1}_num'] = reg_num
                    entry_dict[f'reg{j+1}_val'] = reg_val
                    entry_dict[f'raw_bytes{j+1}'] = f'{channel_data[0]:04X}{channel_data[1]:04X}'
                    
                    # Store register values
                    self.register_values[i][reg_num] = reg_val
                elif bytes_per_channel == 2:
                    # Each channel has 2 bytes: register (8 bits) and value (8 bits)
                    channel_data = struct.unpack('>BB', entry[j*2:(j+1)*2])
                    reg_num = channel_data[0] & 0x0F  # Lower 4 bits for register number
                    reg_val = channel_data[1]  # 8 bits for value
                    
                    entry_dict[f'reg{j+1}_num'] = reg_num
                    entry_dict[f'reg{j+1}_val'] = reg_val
                    entry_dict[f'raw_bytes{j+1}'] = f'{channel_data[0]:02X}{channel_data[1]:02X}'
                    
                    # Store register values
                    self.register_values[i][reg_num] = reg_val
                else:
                    # Each channel just has a value, register numbers are implicit (let's say 8 and 9)
                    channel_data = struct.unpack('>B', entry[j:j+1])
                    reg_num = 8 + j
                    reg_val = channel_data[0]
                    entry_dict[f'reg{j+1}_num'] = reg_num
                    entry_dict[f'reg{j+1}_val'] = reg_val
                    entry_dict[f'raw_bytes{j+1}'] = f'{reg_val:02X}'

                    # Store register values
                    self.register_values[i][reg_num] = reg_val

            self.entries.append(entry_dict)

    def populate_table(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for entry in self.entries:
            values = [entry['index']]
            for i in range(self.num_channels):
                values.extend([
                    f"{entry[f'reg{i+1}_num']} ({REGISTER_DESCRIPTIONS.get(entry[f'reg{i+1}_num'], 'Unknown')})",
                    f"{entry[f'reg{i+1}_val']:02X}"
                ])
            self.tree.insert('', tk.END, values=values)

    def apply_scale(self):
        try:
            scale_factor = float(self.scale_entry.get())
            self.scale_volume(scale_factor)

            self.rebuild_sample_table()
            self.populate_table()
            self.plot_graph()

        except ValueError:
            tk.messagebox.showerror("Error", "Invalid scale factor (must be between 0 and 1)")

    def scale_volume(self, scale_factor):
        if scale_factor <= 0 or scale_factor > 1:
            raise ValueError("Scale factor must be between 0 and 1")
        
        # Clear scaled entries and calculate new indices based on scale factor
        scaled_entries = []
        num_entries = len(self.original_entries)

        for i in range(num_entries):
            scaled_index = int(i * scale_factor)
            if scaled_index < num_entries:
                scaled_entries.append(self.original_entries[scaled_index])

        self.entries = scaled_entries

    def plot_graph(self):
        # Clear existing graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(self.register_values))
        colors = plt.cm.get_cmap('tab20', 16)
        for reg_num in range(16):
            values = []
            last_value = np.nan
            for reg_vals in self.register_values:
                val = reg_vals.get(reg_num, last_value)
                values.append(val)
                if not np.isnan(val):
                    last_value = val

            if not all(np.isnan(values)):
                ax.plot(x, values, label=f"Reg {reg_num}: {REGISTER_DESCRIPTIONS.get(reg_num, 'Unknown')}", color=colors(reg_num))

        ax.set_xlabel('Sample Index')
        ax.set_ylabel('Register Value')
        ax.legend(loc='upper right', fontsize='small', ncol=2)
        ax.grid(True)
        fig.tight_layout()

        # Ensure the graph occupies the top and expands
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = SampleTableViewer()
    app.mainloop()
