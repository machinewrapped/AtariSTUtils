import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import struct
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes

class FunctionTableGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Function Table Generator")
        
        # Enable DPI awareness
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass  # Not on Windows or other error
            
        # Get system DPI scaling factor
        scaling = 1
        try:
            scaling = root.winfo_fpixels('1i') / 72  # Get actual DPI/default DPI
        except:
            pass
            
        # Scale font sizes
        default_font_size = int(10 * scaling)
        title_font_size = int(12 * scaling)
        
        # Configure default font
        style = ttk.Style()
        style.configure('.',  font=('TkDefaultFont', default_font_size))
        style.configure('TLabel', padding=int(3 * scaling))
        style.configure('TButton', padding=int(5 * scaling))
        style.configure('TEntry', padding=int(5 * scaling))
        
        # Create main frame with scaled padding
        main_frame = ttk.Frame(root, padding=int(10 * scaling))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create toolbar with scaled padding
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, int(10 * scaling)))
        
        # Create toolbar buttons with scaled padding
        for text, command in [
            ("Load Config", self.load_config),
            ("Save Config", self.save_config),
            ("Generate", self.generate_data),
            ("Save Data", self.save_data)
        ]:
            btn = ttk.Button(toolbar, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=int(2 * scaling))
        
        # Create parameter frame with scaled padding
        param_frame = ttk.LabelFrame(main_frame, text="Parameters", padding=int(5 * scaling))
        param_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, int(5 * scaling)))
        
        # Function selection
        ttk.Label(param_frame, text="Function:").grid(row=0, column=0, sticky=tk.W)
        self.function_var = tk.StringVar(value="SIN")
        self.function_combo = ttk.Combobox(param_frame, textvariable=self.function_var, values=["SIN", "COS"])
        self.function_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=int(2 * scaling))
        
        # Range inputs
        ttk.Label(param_frame, text="Range (degrees):").grid(row=1, column=0, sticky=tk.W)
        range_frame = ttk.Frame(param_frame)
        range_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=int(2 * scaling))
        
        self.range_min_var = tk.StringVar(value="0")
        self.range_max_var = tk.StringVar(value="360")
        ttk.Entry(range_frame, textvariable=self.range_min_var, width=6).pack(side=tk.LEFT, padx=int(2 * scaling))
        ttk.Label(range_frame, text="to").pack(side=tk.LEFT, padx=int(2 * scaling))
        ttk.Entry(range_frame, textvariable=self.range_max_var, width=6).pack(side=tk.LEFT, padx=int(2 * scaling))
        
        # Scale input
        ttk.Label(param_frame, text="Scale:").grid(row=2, column=0, sticky=tk.W)
        self.scale_var = tk.StringVar(value="255")
        ttk.Entry(param_frame, textvariable=self.scale_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=int(2 * scaling))
        
        # Number of entries
        ttk.Label(param_frame, text="Number of entries:").grid(row=3, column=0, sticky=tk.W)
        self.entries_var = tk.StringVar(value="361")
        ttk.Entry(param_frame, textvariable=self.entries_var).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=int(2 * scaling))
        
        # Entry size
        ttk.Label(param_frame, text="Entry size (bits):").grid(row=4, column=0, sticky=tk.W)
        self.size_var = tk.StringVar(value="16")
        size_combo = ttk.Combobox(param_frame, textvariable=self.size_var, values=["8", "16", "32"])
        size_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=int(2 * scaling))
        
        # Create plot frame with scaled padding
        plot_frame = ttk.LabelFrame(main_frame, text="Preview", padding=int(5 * scaling))
        plot_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create matplotlib figure with scaled size and DPI
        plt.style.use('default')
        dpi = 96 * scaling
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configure plot fonts
        plt.rcParams.update({
            'font.size': default_font_size,
            'axes.labelsize': default_font_size,
            'axes.titlesize': title_font_size,
            'xtick.labelsize': default_font_size,
            'ytick.labelsize': default_font_size
        })
        
        self.generated_data = None
        
    def generate_data(self):
        try:
            min_deg = float(self.range_min_var.get())
            max_deg = float(self.range_max_var.get())
            scale = float(self.scale_var.get())
            num_entries = int(self.entries_var.get())
            
            # Generate x values (degrees)
            x = np.linspace(min_deg, max_deg, num_entries)
            
            # Convert degrees to radians
            radians = np.deg2rad(x)
            
            # Generate y values based on selected function
            if self.function_var.get() == "SIN":
                y = np.sin(radians) * scale
            else:  # COS
                y = np.cos(radians) * scale
            
            # Round to integers
            self.generated_data = np.round(y).astype(int)
            
            # Update plot
            self.ax.clear()
            self.ax.plot(x, self.generated_data, linewidth=2)
            self.ax.set_title(f"{self.function_var.get()} Table")
            self.ax.set_xlabel("Degrees")
            self.ax.set_ylabel("Value")
            self.ax.grid(True)
            self.canvas.draw()
            
        except ValueError as e:
            tk.messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def save_data(self):
        if self.generated_data is None:
            tk.messagebox.showwarning("Warning", "No data generated yet!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'wb') as f:
                    size_bits = int(self.size_var.get())
                    
                    if size_bits == 8:
                        fmt = '>B'  # unsigned char
                        data = np.clip(self.generated_data, 0, 255)
                    elif size_bits == 16:
                        fmt = '>h'  # short
                        data = np.clip(self.generated_data, -32768, 32767)
                    else:  # 32
                        fmt = '>l'  # long
                        data = self.generated_data
                    
                    for value in data:
                        f.write(struct.pack(fmt, value))
                        
                tk.messagebox.showinfo("Success", "Data saved successfully!")
                
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def save_config(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".cfg",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        
        if filename:
            config = {
                'function': self.function_var.get(),
                'range_min': self.range_min_var.get(),
                'range_max': self.range_max_var.get(),
                'scale': self.scale_var.get(),
                'entries': self.entries_var.get(),
                'size': self.size_var.get()
            }
            
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=4)
                tk.messagebox.showinfo("Success", "Configuration saved successfully!")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                self.function_var.set(config['function'])
                self.range_min_var.set(config['range_min'])
                self.range_max_var.set(config['range_max'])
                self.scale_var.set(config['scale'])
                self.entries_var.set(config['entries'])
                self.size_var.set(config['size'])
                
                tk.messagebox.showinfo("Success", "Configuration loaded successfully!")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FunctionTableGenerator(root)
    root.mainloop()
