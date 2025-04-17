import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk
import os

class AtariSTGraphicsEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Atari ST Graphics Editor")

        # Toolbar
        toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        open_btn = tk.Button(toolbar, text="Open File", command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=2, pady=2)
        save_bmp_btn = tk.Button(toolbar, text="Save BMP", command=self.save_bmp)
        save_bmp_btn.pack(side=tk.LEFT, padx=2, pady=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Main content frame
        main_frame = tk.Frame(root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Parameters Section
        params_frame = tk.Frame(main_frame)
        params_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(params_frame, text="Parameters").pack()
        self.param_h = self.create_param_entry(params_frame, "H (Lines):")
        self.param_h.insert(0, '16')
        self.param_h.bind('<FocusOut>', lambda event: self.update_image())
        self.param_h.bind('<Return>', lambda event: self.update_image())
        
        self.param_w = self.create_param_entry(params_frame, "W (8-pixel blocks):")
        self.param_w.insert(0, '2')
        self.param_w.bind('<FocusOut>', lambda event: self.update_image())
        self.param_w.bind('<Return>', lambda event: self.update_image())
        
        self.param_b = self.create_param_entry(params_frame, "B (Bitplanes):")
        self.param_b.insert(0, '1')
        self.param_b.bind('<FocusOut>', lambda event: self.update_b_param())
        self.param_b.bind('<Return>', lambda event: self.update_b_param())
        
        self.param_n = self.create_param_entry(params_frame, "N (Items):", state='readonly')
        
        self.param_display_scale = self.create_param_entry(params_frame, "Display Scale:")
        self.param_display_scale.insert(0, '4')
        self.param_display_scale.bind('<FocusOut>', lambda event: self.update_image())
        self.param_display_scale.bind('<Return>', lambda event: self.update_image())
      
        self.palette_cols = ["$000", "$333", "$555", "$777", "$100", "$300", "$500", "$700", "$110", "$330", "$550", "$770", "$101", "$303", "$505", "$707"]

        # Store params_frame for later use
        self.params_frame = params_frame

        # Create Palette Frame
        self.create_palette_frame()

        # Right side frame for image and palette text
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Image Display Section
        self.image_frame = tk.Frame(right_frame, bd=2, relief=tk.SUNKEN)
        self.image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.image_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', lambda event: self.update_image())

        # Palette Text Input/Output
        self.palette_text = scrolledtext.ScrolledText(right_frame, height=2)
        self.palette_text.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)
        self.palette_text.bind('<FocusOut>', lambda event: self.update_palette_from_text())
        self.palette_text.bind('<Return>', lambda event: self.update_palette_from_text())

        # Placeholder for image
        self.image = None

        # Initial update of palette text
        self.update_palette_text()

    def create_param_entry(self, parent, label_text, state='normal'):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        label = tk.Label(frame, text=label_text, width=15, anchor='w')
        label.pack(side=tk.LEFT)
        entry = tk.Entry(frame, state=state)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        return entry

    def get_int(self, param):
        value = param.get()
        return int(value) if value.isdigit() else 0  # or your preferred default value

    def update_b_param(self):
        self.update_palette_entries()
        self.update_image()

    def create_palette_frame(self):
        # Palette Section
        self.palette_frame = tk.Frame(self.params_frame)
        self.palette_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(self.palette_frame, text="Palette (Hex Values)").pack()

        self.palette_entries = []
        bitplanes = self.get_int(self.param_b)
        if bitplanes > 0:
            bitplanes = min(bitplanes, 4)
            max_colors = min(2 ** bitplanes, 16)
            for i in range(max_colors):
                color = self.palette_cols[i]
                entry = self.create_param_entry(self.palette_frame, f"Color {i}:")
                entry.insert(0, color)
                entry.bind('<KeyRelease>', lambda event, idx=i: self.update_palette(idx))
                self.palette_entries.append(entry)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if file_path:
            if os.path.splitext(file_path)[1].lower() in ['.bmp', '.img']:
                tk.messagebox.showinfo("Not Supported", "Loading source images is not supported yet.")
                return

            if os.path.splitext(file_path)[1].lower() == '.inf':
                file_path = self.load_from_inf(file_path)
            
            self.load_image(file_path)
            self.update_image()

    def load_from_inf(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                key, value = line.strip().split('=')
                if key == 'file':
                    file_path = value
                    break
        return file_path

    def load_image(self, file_path):
        self.file_path = file_path
        self.data = None

        try:
            # Load image data from file
            with open(self.file_path, 'rb') as f:
                self.data = f.read()

            file_size = os.path.getsize(file_path)

            self.load_inf()

            h = self.get_int(self.param_h)
            w = self.get_int(self.param_w)
            b = self.get_int(self.param_b)

            if h > 0 and w > 0 and b > 0:
                n = file_size // (h * w * b)
                self.update_property(self.param_n, n, readonly=True)
      
        except ValueError:
            print("Please enter valid values for H, W, and B.")

    def update_palette_entries(self):
        # Destroy existing palette frame
        self.palette_frame.destroy()
        # Recreate palette frame
        self.create_palette_frame()
        # Update palette text
        self.update_palette_text()

    def update_palette(self, index):
        new_color = self.palette_entries[index].get()
        if len(new_color) == 4 and new_color.startswith('$'):
            self.palette_cols[index] = new_color
            self.update_image()
            self.update_palette_text()

    def get_palette_color(self, index):
        palcol = self.palette_cols[index]
        if palcol.startswith("$") and palcol[1:].isdigit() and len(palcol) == 4:
            r = int(palcol[1], 16) & 0b111
            g = int(palcol[2], 16) & 0b111
            b = int(palcol[3], 16) & 0b111
            # Scale 3-bit color to 8-bit range (0-255)
            return (r * 36, g * 36, b * 36)

        print(f"Invalid palette color {palcol} at index {index} ")
        return (0, 0, 0)
    
    def update_property(self, property, value, readonly=False):
        property.config(state='normal')
        property.delete(0, tk.END)
        property.insert(0, value)
        if readonly:
            property.config(state='readonly')

    def update_image(self):
        if hasattr(self, 'data') and self.param_h.get() and self.param_w.get() and self.param_b.get():
            try:
                file_size = len(self.data)
                h = self.get_int(self.param_h)
                w = self.get_int(self.param_w)  # 8-pixel blocks
                bpp = self.get_int(self.param_b)

                if h > 0 and w > 0 and bpp > 0:
                    bpp = min(bpp, 4)  # Limit to 4 bitplanes
                    bpcol = bpp  # Bytes per column (8 pixels)
                    w = max(1, min(w, file_size // bpcol))

                    bpline = w * bpcol  # Bytes per line
                    h = max(1, min(h, file_size // bpline))

                    self.update_property(self.param_b, bpp, readonly=False)
                    self.update_property(self.param_w, w, readonly=False)
                    self.update_property(self.param_h, h, readonly=False)

                    bpitem = h * bpline
                    n = max(1, file_size // bpitem)

                    self.update_property(self.param_n, n, readonly=True)

                    palette = [self.get_palette_color(i) for i in range(2**bpp)]

                    display_scale = int(self.param_display_scale.get()) if self.param_display_scale.get().isdigit() else 4
                    canvas_width = self.canvas.winfo_width()
                    items_per_row = max(canvas_width // (w * 8 * display_scale), 1)
                    num_rows = (n + items_per_row - 1) // items_per_row

                    # Convert bitplane data to an image
                    width, height = w * 8 * items_per_row, h * num_rows
                    self.image = Image.new('RGB', (width, height))
                    pixels = self.image.load()

                    bpword = bpcol * 2

                    for item in range(n):
                        for line in range(h):
                            for col in range(w):
                                word_index = (item * bpitem) + (line * bpline) + ((col // 2) * bpword)
                                byte_index = word_index + (col & 1)
                                for bit in range(8):
                                    color_index = 0
                                    for plane in range(bpp):
                                        plane_offset = byte_index + (plane * (2 if w > 1 else 1))
                                        if plane_offset >= file_size:
                                            print("Too many bitplanes.")
                                            break

                                        byte = self.data[plane_offset]
                                        bit_value = (byte >> (7 - bit)) & 1
                                        color_index |= (bit_value << plane)

                                    color = palette[color_index]
                                    x = (col * 8) + bit
                                    row = item // items_per_row
                                    col_offset = item % items_per_row
                                    x = (col_offset * w * 8) + (col * 8) + bit
                                    y = (row * h) + line
                                    pixels[x, y] = color

                    self.display_image()
                    self.save_inf()

            except ValueError:
                print("Please enter valid values for H, W, and B.")

    def display_image(self):
        if self.image:
            # Resize image to fit the canvas dimensions
            display_scale = int(self.param_display_scale.get()) if self.param_display_scale.get().isdigit() else 4
            canvas_width = self.image.width * display_scale
            canvas_height = self.image.height * display_scale

            if canvas_width == 0 or canvas_height == 0:
                return

            resized_image = self.image.resize((canvas_width, canvas_height), Image.NEAREST)
            # Convert image for Tkinter
            tk_image = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
            # Keep a reference to avoid garbage collection
            self.canvas.image = tk_image

    def save_inf(self):
        if hasattr(self, 'file_path'):
            inf_path = os.path.splitext(self.file_path)[0] + '.INF'

            h = self.get_int(self.param_h)
            w = self.get_int(self.param_w)
            b = self.get_int(self.param_b)
            scale = self.get_int(self.param_display_scale)

            if h and w and b and scale:
                with open(inf_path, 'w') as f:
                    f.write(f"file={self.file_path}\n")
                    f.write(f"h={h}\n")
                    f.write(f"w={w}\n")
                    f.write(f"b={b}\n")
                    f.write(f"scale={scale}\n")
                    for i, color in enumerate(self.palette_cols[:2**b]):
                        f.write(f"color{i}={color}\n")

    def load_inf(self):
        if hasattr(self, 'file_path'):
            inf_path = os.path.splitext(self.file_path)[0] + '.INF'
            if os.path.exists(inf_path):
                with open(inf_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        key, value = line.strip().split('=')
                        if key == 'file':
                            if value != self.file_path:
                                print(f"INF file does not match the loaded file: {value}")
                        elif key == 'h':
                            self.param_h.delete(0, tk.END)
                            self.param_h.insert(0, value)
                        elif key == 'w':
                            self.param_w.delete(0, tk.END)
                            self.param_w.insert(0, value)
                        elif key == 'b':
                            self.param_b.delete(0, tk.END)
                            self.param_b.insert(0, value)
                            self.update_palette_entries()
                        elif key == 'scale':
                            self.param_display_scale.delete(0, tk.END)
                            self.param_display_scale.insert(0, value)
                        elif key.startswith('color'):
                            index = int(key[5:])
                            if index < len(self.palette_cols):
                                self.palette_cols[index] = value
                                if index < len(self.palette_entries):
                                    self.palette_entries[index].delete(0, tk.END)
                                    self.palette_entries[index].insert(0, value)
                self.update_palette_text()

    def save_bmp(self):
        if self.image and hasattr(self, 'file_path'):
            bmp_path = os.path.splitext(self.file_path)[0] + '.BMP'
            # Create a new indexed image with the same dimensions as the original
            bmp_image = Image.new('P', self.image.size)
            pixels = bmp_image.load()
            original_pixels = self.image.load()

            bpp = self.get_int(self.param_b)

            # Copy pixel data from the original image to the indexed image
            for y in range(self.image.height):
                for x in range(self.image.width):
                    # Find the closest color in the palette
                    color = original_pixels[x, y]
                    color_index = 0
                    for i, palette_color in enumerate(self.palette_cols[:2**bpp]):
                        if self.get_palette_color(i) == color:
                            color_index = i
                            break
                    pixels[x, y] = color_index

            # Set up a 16-color palette
            bmp_palette = []
            for i in range(16):
                if i < len(self.palette_cols):
                    bmp_palette.extend(self.get_palette_color(i))
                else:
                    bmp_palette.extend([0, 0, 0])  # Fill remaining colors with black

            bmp_image.putpalette(bmp_palette)
            bmp_image.save(bmp_path, format='BMP')

    def update_palette_text(self):
        bpp = self.get_int(self.param_b)
        if bpp > 0 and bpp <= 4:
            palette_str = "dc.w " + ",".join(self.palette_cols[:2**bpp])
            self.palette_text.delete('1.0', tk.END)
            self.palette_text.insert(tk.END, palette_str)

    def update_palette_from_text(self, event=None):
        try:
            text_content = self.palette_text.get('1.0', tk.END).strip()
            if text_content.startswith("dc.w "):
                text_content = text_content[5:]  # Remove "dc.w " prefix
            colors = text_content.split(',')
            for i, color in enumerate(colors):
                if i < len(self.palette_cols):
                    color = color.strip()
                    if len(color) == 4 and color.startswith('$'):
                        self.palette_cols[i] = color
                        if i < len(self.palette_entries):
                            self.palette_entries[i].delete(0, tk.END)
                            self.palette_entries[i].insert(0, color)

            self.update_image()

        except Exception as e:
            print(f"Error updating palette from text: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AtariSTGraphicsEditor(root)
    root.mainloop()
