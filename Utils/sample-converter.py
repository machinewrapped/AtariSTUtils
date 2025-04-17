import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import wave
from pydub import AudioSegment
import numpy as np


class SampleSettingsDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, initial_sample_rate=15650):
        self.sample_rate = initial_sample_rate
        self.signed = False  # Default to unsigned samples
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Sample Rate (Hz):").grid(row=0, column=0, sticky='e')
        self.sample_rate_entry = tk.Entry(master)
        self.sample_rate_entry.insert(0, str(self.sample_rate))
        self.sample_rate_entry.grid(row=0, column=1)

        self.signed_var = tk.BooleanVar(value=self.signed)
        tk.Label(master, text="Sample Signedness:").grid(row=1, column=0, sticky='e')
        self.signed_radio_unsigned = tk.Radiobutton(master, text="Unsigned (0 to 255)", variable=self.signed_var, value=False)
        self.signed_radio_signed = tk.Radiobutton(master, text="Signed (-127 to 128)", variable=self.signed_var, value=True)
        self.signed_radio_signed.grid(row=1, column=1, sticky='w')
        self.signed_radio_unsigned.grid(row=2, column=1, sticky='w')
        return self.sample_rate_entry

    def apply(self):
        try:
            self.sample_rate = int(self.sample_rate_entry.get())
            self.signed = self.signed_var.get()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the sample rate.")
            self.sample_rate = None
            self.signed = None

class AtariSTSoundViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Atari ST Sound Data Viewer")
        self.root.geometry("1600x800")

        self.sample_data = None
        self.sample_rate = 15650  # default sample rate
        self.signed = False  # default to unsigned samples

        self.aggregation_method = tk.StringVar(value="Mean")  # Default aggregation method

        self.create_widgets()

    def create_widgets(self):
        self.fig = Figure(figsize=(16,8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        # Bind resize event
        self.canvas.get_tk_widget().bind("<Configure>", self.on_resize)

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        fileMenu = tk.Menu(menubar)
        menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Load Raw Sample Data", command=self.load_raw_sample_data)
        fileMenu.add_command(label="Save as WAV", command=self.save_as_wav)
        fileMenu.add_separator()
        fileMenu.add_command(label="Load WAV File", command=self.load_wav_file)
        fileMenu.add_command(label="Save as Raw Atari ST", command=self.save_as_raw)
        fileMenu.add_separator()
        fileMenu.add_command(label="Convert Sample Signedness", command=self.convert_sample_signedness)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.root.quit)

        optionsMenu = tk.Menu(menubar)
        menubar.add_cascade(label="Options", menu=optionsMenu)

        # Aggregation Method submenu
        optionsMenu.add_radiobutton(label="Mean", variable=self.aggregation_method, command=self.update_plot)
        optionsMenu.add_radiobutton(label="Max", variable=self.aggregation_method, command=self.update_plot)
        optionsMenu.add_radiobutton(label="RMS", variable=self.aggregation_method, command=self.update_plot)
        optionsMenu.add_radiobutton(label="Absolute Mean", variable=self.aggregation_method, command=self.update_plot)

    def on_resize(self, event):
        self.update_plot()

    def load_raw_sample_data(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                # Open the custom dialog
                dialog = SampleSettingsDialog(self.root, title="Load Raw Sample Data", initial_sample_rate=self.sample_rate)
                if dialog.sample_rate is not None:
                    self.sample_rate = dialog.sample_rate
                    self.signed = dialog.signed
                else:
                    return  # User cancelled or input was invalid

                # Read the data
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                # Decide on signed or unsigned
                if self.signed:
                    dtype = np.int8
                else:
                    dtype = np.uint8
                self.sample_data = np.frombuffer(raw_data, dtype=dtype)

                # Update plot
                self.update_plot()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def load_wav_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav;*.mp3;*.flac")])
        if file_path:
            try:
                # Load audio file using pydub
                audio : AudioSegment = AudioSegment.from_file(file_path)
                
                # Ask for target sample rate
                sr = simpledialog.askinteger("Sample Rate", "Enter target sample rate (Hz):", initialvalue=15650)
                if sr is not None:
                    self.sample_rate = sr
                else:
                    self.sample_rate = 15650  # default

                # Resample audio
                if audio.frame_rate != self.sample_rate:
                    audio = audio.set_frame_rate(self.sample_rate)

                # Check if audio is stereo and needs to be converted to mono
                if audio.channels > 1:
                    # Ask the user if they want to mix down to mono
                    mix_to_mono = messagebox.askyesno("Stereo Audio Detected", "The audio file is stereo. Do you want to mix it down to mono?")
                    if mix_to_mono:
                        audio = audio.set_channels(1)  # Mix down to mono
                    else:
                        audio = audio.split_to_mono()[0]  # Use the first channel

                # Ask for signedness
                signed_answer = messagebox.askyesno("Sample Signedness", "Treat samples as signed?")
                self.signed = signed_answer

                # Export audio to raw data
                raw_data = audio.raw_data
                sample_width = audio.sample_width

                # Convert raw data to numpy array
                data = np.frombuffer(raw_data, dtype=f'int{sample_width * 8}')

                # Since we have ensured audio is mono, no need to handle multiple channels here

                # Normalize data to -1.0 to 1.0
                max_val = float(2 ** (8 * sample_width - 1))
                data = data / max_val

                # Scale to 8-bit range
                data = data * 127  # Scale to -127 to 127

                if not self.signed:
                    data = data + 128  # Shift to 0 to 255

                # Clip and convert to integers
                if self.signed:
                    self.sample_data = np.clip(data, -128, 127).astype(np.int8)
                else:
                    self.sample_data = np.clip(data, 0, 255).astype(np.uint8)

                # Update plot
                self.update_plot()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio file:\n{e}")

    def save_as_wav(self):
        if self.sample_data is None:
            messagebox.showwarning("Warning", "No sample data to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
        if file_path:
            try:
                with wave.open(file_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(1)  # 8-bit samples
                    wav_file.setframerate(self.sample_rate)
                    if self.signed:
                        # Convert signed int8 data to unsigned uint8 by adding 128
                        data = (self.sample_data.astype(np.int16) + 128).astype(np.uint8).tobytes()
                    else:
                        data = self.sample_data.astype(np.uint8).tobytes()
                    wav_file.writeframes(data)
                messagebox.showinfo("Success", "WAV file saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save WAV file:\n{e}")


    def save_as_raw(self):
        if self.sample_data is None:
            messagebox.showwarning("Warning", "No sample data to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".SAM", filetypes=[("Atari ST Raw Files", "*.SAM;*.SPL")])
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    if self.signed:
                        data = self.sample_data.astype(np.int8).tobytes()
                    else:
                        data = self.sample_data.astype(np.uint8).tobytes()
                    f.write(data)
                messagebox.showinfo("Success", "Raw sample data saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save raw data:\n{e}")

    def convert_sample_signedness(self):
        if self.sample_data is None:
            messagebox.showwarning("Warning", "No sample data to convert.")
            return
        
        # Confirm action with the user
        confirm = messagebox.askyesno("Convert Sample Signedness", 
                                      f"Are you sure you want to convert the sample values to {'unsigned' if self.signed else 'signed'}?")

        if not confirm:
            return
        
        try:
            if self.signed:
                # Convert from signed to unsigned
                self.sample_data = (self.sample_data.astype(np.int16) + 128).astype(np.uint8)
                self.signed = False
            else:
                # Convert from unsigned to signed
                self.sample_data = (self.sample_data.astype(np.int16) - 128).astype(np.int8)
                self.signed = True
            
            # Update the plot
            self.update_plot()
            
            # Notify the user
            messagebox.showinfo("Conversion Complete", "Sample signedness has been converted.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert sample signedness:\n{e}")

    def update_plot(self):
        if self.sample_data is None:
            return

        self.ax.clear()

        # Get the width of the canvas in pixels
        canvas_width = self.canvas.get_tk_widget().winfo_width()
        if canvas_width <= 1:
            canvas_width = 800

        data_length = len(self.sample_data)

        if data_length > canvas_width:
            # Number of samples per bin
            bin_size = max(1, data_length // canvas_width)
            # Recalculate the number of bins
            num_bins = data_length // bin_size
            # Ensure we have at least one bin
            if num_bins == 0:
                num_bins = 1
                bin_size = data_length
            # Trim the data to fit into an exact multiple of bin_size
            trimmed_length = bin_size * num_bins
            trimmed_data = self.sample_data[:trimmed_length]
            # Reshape and aggregate
            reshaped_data = trimmed_data.reshape((num_bins, bin_size))
            # Choose aggregation method
            method = self.aggregation_method.get()
            if method == "Mean":
                aggregated_data = reshaped_data.mean(axis=1)
            elif method == "Max":
                aggregated_data = reshaped_data.max(axis=1)
            elif method == "RMS":
                aggregated_data = np.sqrt(np.mean(reshaped_data.astype(np.float64) ** 2, axis=1))
            elif method == "Absolute Mean":
                aggregated_data = np.mean(np.abs(reshaped_data), axis=1)
            else:
                aggregated_data = reshaped_data.mean(axis=1)  # Default to mean
        else:
            # No need to downsample
            aggregated_data = self.sample_data

        # Plot the aggregated data
        self.ax.plot(aggregated_data)
        self.ax.set_xlim(0, len(aggregated_data))
        self.ax.set_ylim(np.min(self.sample_data), np.max(self.sample_data))
        self.ax.set_xlabel("Sample Number")
        self.ax.set_ylabel("Amplitude")
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = AtariSTSoundViewer(root)
    root.mainloop()
