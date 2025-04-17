import struct
import tkinter as tk
from tkinter import filedialog, ttk

def debug_tos_relocation_gui():
    # Global storage for file data
    file_data = {
        'header': None,
        'relocation_entries': None,
    }

    def load_file():
        # Open file selector
        file_path = filedialog.askopenfilename(title="Select TOS File")
        if not file_path:
            print("No file selected.")
            return

        file_label.config(text=f"Current file: {file_path}")
        process_file(file_path)

    def save_file():
        # Check if there's data to save
        if not file_data['header'] or not file_data['relocation_entries']:
            print("No data to save.")
            return

        # Open file dialog to select the save location
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            print("No file selected for saving.")
            return

        # Get the header and relocation entries from the dictionary
        header_rows = file_data['header']
        relocation_entries = file_data['relocation_entries']

        # Open the file and write the header and relocation entries
        with open(file_path, 'w') as f:
            # Write the headers
            f.write("TOS File Header Information:\n")
            for row in header_rows:
                f.write(f"{row[0]:<25}: {row[1]}\n")

            f.write("\nRelocation Entries:\n")
            f.write(f"{'Index':<8}{'Byte Value':<15}{'Current Address':<20}{'Original Value':<20}{'Relocated Value':<20}{'Error':<25}\n")
            f.write("="*100 + "\n")

            # Write the relocation entries
            for entry in relocation_entries:
                f.write(f"{entry['index']:<8}{entry['byte_value']:<15}{entry['current_address']:<20}{entry['original_value']:<20}{entry['relocated_value']:<20}{entry['error']:<25}\n")

        print(f"File saved to {file_path}")

    def process_file(file_path):
        # Read the TOS file
        with open(file_path, 'rb') as f:
            tos_data = f.read()

        # Unpack the TOS header
        header_fmt = '>H4L2H'
        header_size = struct.calcsize(header_fmt)
        if len(tos_data) < header_size:
            print("File too short to contain a valid header.")
            return
        header = tos_data[:header_size]
        unpacked_header = struct.unpack(header_fmt, header)
        magic_number = unpacked_header[0]
        text_length = unpacked_header[1]
        data_length = unpacked_header[2]
        bss_length = unpacked_header[3]
        symbol_table_length = unpacked_header[4]
        flag = unpacked_header[5]
        reserved = unpacked_header[6]

        # Verify the magic number
        if magic_number != 0x601a:
            print("Invalid magic number. Not a valid TOS file.")
            return

        # Compute the total program length
        total_length = text_length + data_length + symbol_table_length

        # Program start address in file
        program_start_offset = 0x1c
        program_end_offset = program_start_offset + total_length
        if len(tos_data) < program_end_offset:
            print("File too short. Incomplete data.")
            return

        # Assume base address is 0x10000
        base_address = 0x10000
        program_start = base_address + program_start_offset
        text_end = program_start + text_length
        data_end = text_end + data_length
        relocation_start = base_address + program_end_offset        

        # Get the relocation table
        relocation_table_offset = program_end_offset
        relocation_table = tos_data[relocation_table_offset:]
        relocation_table_index = 0

        # Read the offset to the first relocatable address
        if len(relocation_table) < 4:
            print("Relocation table too short.")
            return
        first_offset_bytes = relocation_table[:4]
        first_offset = struct.unpack('>L', first_offset_bytes)[0]
        relocation_table_index += 4

        # Initialize current relocation address
        current_reloc_address = base_address + first_offset
        reloc_file_offset = program_start_offset + (current_reloc_address - base_address)

        # Check if the relocation address is valid
        text_data_end_offset = program_start_offset + text_length + data_length
        if reloc_file_offset + 4 > text_data_end_offset:
            print(f"Error: Relocation address 0x{current_reloc_address:08x} is beyond text + data sections.")
            return

        # Read the original value
        original_value_bytes = tos_data[reloc_file_offset:reloc_file_offset+4]
        original_value = struct.unpack('>L', original_value_bytes)[0]
        relocated_value = original_value + base_address

        # Prepare relocation entries list
        relocation_entries = []

        # Add the first relocation entry
        relocation_entries.append({
            'index': 0,
            'byte_value': f"0x{first_offset:08x}",
            'current_address': f"0x{current_reloc_address:08x}",
            'original_value': f"0x{original_value:08x}",
            'relocated_value': f"0x{relocated_value:08x}",
            'error': ''
        })

        # Process the relocation table
        while relocation_table_index < len(relocation_table):
            byte_value = relocation_table[relocation_table_index]

            if byte_value == 0:
                # End of relocation table
                break
            elif byte_value == 1:
                # Jump 254 bytes
                current_reloc_address += 254
            else:
                current_reloc_address += byte_value
                error_message = ''
                # Check 16-bit alignment
                if current_reloc_address % 2 != 0:
                    error_message = f"Address 0x{current_reloc_address:08x} not 16-bit aligned."
                else:
                    # Compute file offset
                    reloc_file_offset = program_start_offset + (current_reloc_address - base_address)
                    if reloc_file_offset + 4 > text_data_end_offset:
                        error_message = f"Address 0x{current_reloc_address:08x} beyond text + data."
                    else:
                        # Read original value
                        original_value_bytes = tos_data[reloc_file_offset:reloc_file_offset+4]
                        original_value = struct.unpack('>L', original_value_bytes)[0]
                        relocated_value = original_value + base_address
                # Add to entries list
                relocation_entries.append({
                    'index': relocation_table_index,
                    'byte_value': f"{byte_value} (0x{byte_value:02x})",
                    'current_address': f"0x{current_reloc_address:08x}",
                    'original_value': f"0x{original_value:08x}" if not error_message else '',
                    'relocated_value': f"0x{relocated_value:08x}" if not error_message else '',
                    'error': error_message
                })

            # Move to next byte in relocation table
            relocation_table_index += 1

        # Clear the Treeview
        for item in tree.get_children():
            tree.delete(item)

        # Insert data into Treeview
        for entry in relocation_entries:
            tree.insert('', 'end', values=(
                entry['index'],
                entry['byte_value'],
                entry['current_address'],
                entry['original_value'],
                entry['relocated_value'],
                entry['error']
            ))

        # Update header information
        header_rows = [
            [f"Magic number: 0x{magic_number:04x}", f"Symbol table length: {symbol_table_length} bytes", f"Flag: 0x{flag:04x}", f"Reserved: 0x{reserved:04x}"],
            [f"Text length: {text_length} bytes", f"Data length: {data_length} bytes", f"BSS length: {bss_length} bytes"],
            [f"Program Start: 0x{program_start:08x}", f"Text End: 0x{text_end:08x}", f"Data End: 0x{data_end:08x}"],
            [f"Relocation Table: 0x{relocation_start:08x}", f"Entries: {len(relocation_entries)}", f"Errors: {len([entry for entry in relocation_entries if entry['error']])}"]
        ]

        # Clear old header info and update
        for widget in header_frame.winfo_children():
            widget.destroy()

        for row in header_rows:
            row_frame = tk.Frame(header_frame)
            row_frame.pack()
            for label_text in row:
                label = tk.Label(row_frame, text=label_text, padx=10)
                label.pack(fill='x', side='left', expand=True)

        # Store the header information
        file_data['header'] = [
            ["Magic number", f"0x{magic_number:04x}"],
            ["Text length", f"{text_length} bytes"],
            ["Data length", f"{data_length} bytes"],
            ["BSS length", f"{bss_length} bytes"],
            ["Symbol table length", f"{symbol_table_length} bytes"],
            ["Flag", f"0x{flag:04x}"],
            ["Reserved", f"0x{reserved:04x}"],
            ["Program Start", f"0x{program_start:08x}"],
            ["Text End", f"0x{text_end:08x}"],
            ["Data End", f"0x{data_end:08x}"],
            ["Relocation Table Start", f"0x{relocation_start:08x}"],
            ["Relocation Entries", f"{len(relocation_entries)}"],
            ["Errors", f"{len([entry for entry in relocation_entries if entry['error']])}"]
        ]

        # Store the relocation entries
        file_data['relocation_entries'] = relocation_entries

    # Create GUI window
    gui_root = tk.Tk()
    gui_root.title("TOS Relocation Debugger")

    # Top Frame for filename and Load button
    top_frame = tk.Frame(gui_root)
    top_frame.pack(pady=10)

    # Filename label
    file_label = tk.Label(top_frame, text="No file loaded")
    file_label.pack(side='left', padx=10)

    # Load button
    load_button = tk.Button(top_frame, text="Load", command=load_file)
    load_button.pack(side='left', padx=10)

    # Save button
    save_button = tk.Button(top_frame, text="Save", command=save_file)
    save_button.pack(side='left', padx=10)

    # Header Frame
    header_frame = tk.Frame(gui_root)
    header_frame.pack(pady=10)

    # Relocation Entries Frame
    entries_frame = tk.Frame(gui_root)
    entries_frame.pack(fill='both', expand=True)

    # Scrollbar
    scrollbar = tk.Scrollbar(entries_frame)
    scrollbar.pack(side='right', fill='y')

    # Treeview for relocation entries
    columns = ('index', 'byte_value', 'current_address', 'original_value', 'relocated_value', 'error')
    tree = ttk.Treeview(entries_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
    tree.pack(fill='both', expand=True)
    scrollbar.config(command=tree.yview)

    # Define headings
    tree.heading('index', text='Index')
    tree.heading('byte_value', text='Byte Value')
    tree.heading('current_address', text='Current Address')
    tree.heading('original_value', text='Original Value')
    tree.heading('relocated_value', text='Relocated Value')
    tree.heading('error', text='Error')

    # Define column widths
    tree.column('index', width=50, anchor='e')
    tree.column('byte_value', width=100, anchor='e')
    tree.column('current_address', width=150, anchor='e')
    tree.column('original_value', width=150, anchor='e')
    tree.column('relocated_value', width=150, anchor='e')
    tree.column('error', width=250, anchor='w')

    load_file()

    gui_root.mainloop()

# Call the function to execute
debug_tos_relocation_gui()
