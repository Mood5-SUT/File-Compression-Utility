import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import heapq
import os
import json
import time
import hashlib
from collections import Counter, defaultdict
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np



class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq



class CompressionAlgorithm:
    def compress(self, input_path, output_path):
        raise NotImplementedError
    
    def decompress(self, input_path, output_path):
        raise NotImplementedError
    
    def get_stats(self):
        raise NotImplementedError



class HuffmanCoding(CompressionAlgorithm):
    def __init__(self):
        self.codes = {}
        self.reverse_mapping = {}
        self.stats = {}
        self.compression_time = 0
        self.decompression_time = 0
    
    def _calculate_parity(self, data):
        """Calculate parity bit for error detection"""
        parity = 0
        for byte in data:
            parity ^= byte
        return parity
    
    def make_frequency_dict(self, text):
        return Counter(text)
    
    def build_heap(self, frequency):
        heap = []
        for char, freq in frequency.items():
            node = Node(char, freq)
            heapq.heappush(heap, node)
        return heap
    
    def merge_nodes(self, heap):
        while len(heap) > 1:
            node1 = heapq.heappop(heap)
            node2 = heapq.heappop(heap)
            merged = Node(freq=node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2
            heapq.heappush(heap, merged)
        return heap[0]
    
    def make_codes_helper(self, root, current_code):
        if root is None:
            return
        if root.char is not None:
            self.codes[root.char] = current_code
            self.reverse_mapping[current_code] = root.char
        self.make_codes_helper(root.left, current_code + "0")
        self.make_codes_helper(root.right, current_code + "1")
    
    def make_codes(self, tree):
        self.codes.clear()
        self.reverse_mapping.clear()
        self.make_codes_helper(tree, "")
    
    def get_encoded_text(self, text):
        return "".join(self.codes[char] for char in text)
    
    def pad_encoded_text(self, encoded_text):
        extra_padding = 8 - len(encoded_text) % 8
        padded_info = "{0:08b}".format(extra_padding)
        encoded_text += "0" * extra_padding
        return padded_info + encoded_text
    
    def get_byte_array(self, padded_text):
        return bytearray(int(padded_text[i:i+8], 2) for i in range(0, len(padded_text), 8))
    
    def compress(self, input_path, output_path=None):
        start_time = time.time()
        
        if output_path is None:
            filename, _ = os.path.splitext(input_path)
            output_path = filename + ".huff"
        
        with open(input_path, "r", encoding="utf-8") as file:
            text = file.read()
        
      
        original_size = os.path.getsize(input_path)
        self.stats['original_size'] = original_size
        self.stats['character_count'] = len(text)
        
     
        freq = self.make_frequency_dict(text)
        heap = self.build_heap(freq)
        tree = self.merge_nodes(heap)
        self.make_codes(tree)
        
        encoded_text = self.get_encoded_text(text)
        padded_text = self.pad_encoded_text(encoded_text)
        byte_array = self.get_byte_array(padded_text)
        
       
        checksum = self._calculate_parity(byte_array)
        file_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        
        
        with open(output_path, "wb") as output:
          
            output.write(b"HUFF")
            
           
            metadata = {
                'original_size': original_size,
                'character_count': len(text),
                'checksum': checksum,
                'file_hash': file_hash,
                'timestamp': datetime.now().isoformat()
            }
            metadata_json = json.dumps(metadata).encode("utf-8")
            output.write(len(metadata_json).to_bytes(4, "big"))
            output.write(metadata_json)
            
           
            freq_json = json.dumps(freq).encode("utf-8")
            output.write(len(freq_json).to_bytes(4, "big"))
            output.write(freq_json)
            
           
            output.write(byte_array)
        
     
        compressed_size = os.path.getsize(output_path)
        self.compression_time = time.time() - start_time
        
        self.stats.update({
            'compressed_size': compressed_size,
            'compression_ratio': (1 - compressed_size / original_size) * 100,
            'compression_time': self.compression_time,
            'output_path': output_path,
            'algorithm': 'Huffman Coding',
            'checksum': checksum,
            'file_hash': file_hash
        })
        
        return output_path
    
    def remove_padding(self, padded_text):
        padded_info = padded_text[:8]
        extra_padding = int(padded_info, 2)
        padded_text = padded_text[8:]
        return padded_text[:-extra_padding]
    
    def decode_text(self, encoded_text):
        current = ""
        decoded = ""
        for bit in encoded_text:
            current += bit
            if current in self.reverse_mapping:
                decoded += self.reverse_mapping[current]
                current = ""
        return decoded
    
    def decompress(self, input_path, output_path=None):
        start_time = time.time()
        
        if output_path is None:
            filename, _ = os.path.splitext(input_path)
            output_path = filename + "_decompressed.txt"
        
        with open(input_path, "rb") as file:
           
            magic = file.read(4)
            if magic != b"HUFF":
                raise ValueError("Not a valid Huffman compressed file")
            
           
            metadata_size = int.from_bytes(file.read(4), "big")
            metadata_json = file.read(metadata_size).decode("utf-8")
            metadata = json.loads(metadata_json)
            
          
            freq_size = int.from_bytes(file.read(4), "big")
            freq_json = file.read(freq_size).decode("utf-8")
            freq = json.loads(freq_json)
            
           
            compressed_data = file.read()
        
      
        checksum = self._calculate_parity(compressed_data)
        if checksum != metadata['checksum']:
            print(f"Warning: Checksum mismatch! Expected {metadata['checksum']}, got {checksum}")
        
    
        heap = self.build_heap(freq)
        tree = self.merge_nodes(heap)
        self.make_codes(tree)
        
       
        bit_string = "".join(bin(byte)[2:].rjust(8, '0') for byte in compressed_data)
        
     
        encoded_text = self.remove_padding(bit_string)
        decompressed = self.decode_text(encoded_text)
        
       
        decompressed_hash = hashlib.md5(decompressed.encode()).hexdigest()[:8]
        if decompressed_hash != metadata['file_hash']:
            print(f"Warning: File hash mismatch!")
        
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(decompressed)
        
        self.decompression_time = time.time() - start_time
        self.stats.update({
            'decompressed_path': output_path,
            'decompression_time': self.decompression_time,
            'verified': decompressed_hash == metadata['file_hash']
        })
        
        return output_path
    
    def get_stats(self):
        return self.stats



class RunLengthEncoding(CompressionAlgorithm):
    def __init__(self):
        self.stats = {}
        self.compression_time = 0
        self.decompression_time = 0
    
    def compress(self, input_path, output_path=None):
        start_time = time.time()
        
        if output_path is None:
            filename, _ = os.path.splitext(input_path)
            output_path = filename + ".rle"
        
        with open(input_path, "r", encoding="utf-8") as file:
            text = file.read()
        
        original_size = os.path.getsize(input_path)
        
       
        compressed = []
        count = 1
        for i in range(1, len(text)):
            if text[i] == text[i-1] and count < 255:
                count += 1
            else:
                compressed.append(f"{count:03d}{text[i-1]}")
                count = 1
        compressed.append(f"{count:03d}{text[-1]}")
        compressed_text = "".join(compressed)
        
       
        metadata = {
            'original_size': original_size,
            'algorithm': 'Run-Length Encoding',
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, "w", encoding="utf-8") as output:
            output.write(json.dumps(metadata) + "\n")
            output.write(compressed_text)
        
        compressed_size = os.path.getsize(output_path)
        self.compression_time = time.time() - start_time
        
        self.stats = {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': (1 - compressed_size / original_size) * 100,
            'compression_time': self.compression_time,
            'output_path': output_path,
            'algorithm': 'Run-Length Encoding'
        }
        
        return output_path
    
    def decompress(self, input_path, output_path=None):
        start_time = time.time()
        
        if output_path is None:
            filename, _ = os.path.splitext(input_path)
            output_path = filename + "_decompressed.txt"
        
        with open(input_path, "r", encoding="utf-8") as file:
            metadata_line = file.readline()
            compressed_text = file.read()
        
   
        decompressed = []
        i = 0
        while i < len(compressed_text):
            count = int(compressed_text[i:i+3])
            char = compressed_text[i+3]
            decompressed.append(char * count)
            i += 4
        
        decompressed_text = "".join(decompressed)
        
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(decompressed_text)
        
        self.decompression_time = time.time() - start_time
        self.stats['decompression_time'] = self.decompression_time
        
        return output_path
    
    def get_stats(self):
        return self.stats



class CompressionManager:
    def __init__(self):
        self.algorithms = {
            'Huffman Coding': HuffmanCoding(),
            'Run-Length Encoding': RunLengthEncoding()
        }
        self.comparison_results = []
    
    def get_algorithm(self, name):
        return self.algorithms.get(name)
    
    def compare_algorithms(self, input_path):
        results = []
        
        for algo_name, algorithm in self.algorithms.items():
            try:
               
                filename, _ = os.path.splitext(input_path)
                output_path = filename + f"_{algo_name.replace(' ', '_').lower()}_temp"
                
                
                algorithm.compress(input_path, output_path)
                stats = algorithm.get_stats()
                
                results.append({
                    'algorithm': algo_name,
                    'original_size': stats['original_size'],
                    'compressed_size': stats['compressed_size'],
                    'compression_ratio': stats['compression_ratio'],
                    'compression_time': stats['compression_time']
                })
                
                
                if os.path.exists(output_path):
                    os.remove(output_path)
                    
            except Exception as e:
                print(f"Error with {algo_name}: {e}")
        
        self.comparison_results = results
        return results



class CompressionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Compression Utility")
        self.root.geometry("1200x800")
        
       
        self.manager = CompressionManager()
        self.current_algorithm = None
        self.current_file = None
        
       
        self.root.configure(bg='#f5f5f5')
      
        self.create_widgets()
        
    def create_widgets(self):
       
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=100)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title = tk.Label(header_frame, text="🔧 File Compression Utility", 
                        font=('Arial', 28, 'bold'), fg='white', bg='#2c3e50')
        title.pack(pady=30)
        
   
        main_container = tk.Frame(self.root, bg='#f5f5f5')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
     
        left_panel = tk.Frame(main_container, bg='#ecf0f1', padx=15, pady=15)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        
     
        right_panel = tk.Frame(main_container, bg='#ecf0f1', padx=15, pady=15)
        right_panel.pack(side='right', fill='both', expand=True)
        
    
        tk.Label(left_panel, text="📁 File Operations", font=('Arial', 14, 'bold'), 
                bg='#ecf0f1').pack(anchor='w', pady=(0, 10))
        
        
        file_frame = tk.Frame(left_panel, bg='#ecf0f1')
        file_frame.pack(fill='x', pady=(0, 20))
        
        self.file_path_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.file_path_var, 
                             font=('Arial', 10), width=30, state='readonly')
        file_entry.pack(side='left', padx=(0, 10), fill='x', expand=True)
        
        browse_btn = tk.Button(file_frame, text="Browse", command=self.browse_file,
                              bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                              padx=15, cursor='hand2')
        browse_btn.pack(side='right')
        
      
        tk.Label(left_panel, text="⚙️ Compression Algorithm", font=('Arial', 14, 'bold'), 
                bg='#ecf0f1').pack(anchor='w', pady=(0, 10))
        
        self.algo_var = tk.StringVar(value="Huffman Coding")
        algo_menu = ttk.Combobox(left_panel, textvariable=self.algo_var, 
                                values=list(self.manager.algorithms.keys()),
                                state='readonly', font=('Arial', 10))
        algo_menu.pack(fill='x', pady=(0, 20))
        
        # Action buttons
        btn_frame = tk.Frame(left_panel, bg='#ecf0f1')
        btn_frame.pack(fill='x', pady=(0, 20))
        
        self.compress_btn = tk.Button(btn_frame, text="🔽 Compress", command=self.compress_file,
                                     bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                                     padx=20, pady=8, cursor='hand2', state='disabled')
        self.compress_btn.pack(fill='x', pady=(0, 10))
        
        self.decompress_btn = tk.Button(btn_frame, text="🔼 Decompress", command=self.decompress_file,
                                       bg='#e67e22', fg='white', font=('Arial', 11, 'bold'),
                                       padx=20, pady=8, cursor='hand2', state='disabled')
        self.decompress_btn.pack(fill='x', pady=(0, 10))
        
        self.compare_btn = tk.Button(btn_frame, text="📊 Compare Algorithms", command=self.compare_algorithms,
                                    bg='#9b59b6', fg='white', font=('Arial', 11, 'bold'),
                                    padx=20, pady=8, cursor='hand2', state='disabled')
        self.compare_btn.pack(fill='x')
        
    
        self.progress = ttk.Progressbar(left_panel, mode='indeterminate', length=200)
        self.progress.pack(fill='x', pady=20)
        
       
        tk.Label(left_panel, text="📈 Quick Stats", font=('Arial', 14, 'bold'), 
                bg='#ecf0f1').pack(anchor='w', pady=(0, 10))
        
        self.stats_summary = tk.Text(left_panel, height=8, width=30, font=('Courier', 9),
                                    bg='#f8f9fa', relief='flat')
        self.stats_summary.pack(fill='both', expand=True)
        
      
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True)
        
        
        stats_tab = tk.Frame(notebook, bg='white')
        notebook.add(stats_tab, text="📊 Detailed Statistics")
        
        self.detailed_stats = scrolledtext.ScrolledText(stats_tab, height=15, 
                                                       font=('Courier', 10), wrap='word')
        self.detailed_stats.pack(fill='both', expand=True, padx=10, pady=10)
        
      
        codes_tab = tk.Frame(notebook, bg='white')
        notebook.add(codes_tab, text="🔤 Huffman Codes")
        
        columns = ('Character', 'ASCII', 'Frequency', 'Code')
        self.code_tree = ttk.Treeview(codes_tab, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.code_tree.heading(col, text=col)
            self.code_tree.column(col, width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(codes_tab, orient='vertical', command=self.code_tree.yview)
        self.code_tree.configure(yscrollcommand=scrollbar.set)
        
        self.code_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=10)
        
        
        compare_tab = tk.Frame(notebook, bg='white')
        notebook.add(compare_tab, text="⚖️ Algorithm Comparison")
        
        compare_frame = tk.Frame(compare_tab, bg='white')
        compare_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.comparison_text = scrolledtext.ScrolledText(compare_frame, height=10,
                                                        font=('Courier', 10), wrap='word')
        self.comparison_text.pack(fill='both', expand=True)
        
       
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, compare_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, pady=(10, 0))
        
        
        error_tab = tk.Frame(notebook, bg='white')
        notebook.add(error_tab, text="🔍 Error Detection")
        
        self.error_text = scrolledtext.ScrolledText(error_tab, height=15,
                                                   font=('Courier', 10), wrap='word')
        self.error_text.pack(fill='both', expand=True, padx=10, pady=10)
        
       
        self.status_bar = tk.Label(self.root, text="Ready", bg='#2c3e50', fg='white',
                                  font=('Arial', 10), anchor='w', padx=10)
        self.status_bar.pack(side='bottom', fill='x')
    
    def browse_file(self):
        filetypes = [
            ('Text files', '*.txt'),
            ('Huffman compressed', '*.huff'),
            ('RLE compressed', '*.rle'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.current_file = filename
            self.file_path_var.set(filename)
            self.update_button_states(filename)
            self.clear_displays()
            self.update_status(f"Selected: {os.path.basename(filename)}")
            self.show_file_info(filename)
    
    def update_button_states(self, filename):
        is_compressed = filename.lower().endswith(('.huff', '.rle'))
        is_text = filename.lower().endswith('.txt')
        
        self.compress_btn.config(state='normal' if is_text else 'disabled')
        self.decompress_btn.config(state='normal' if is_compressed else 'disabled')
        self.compare_btn.config(state='normal' if is_text else 'disabled')
    
    def clear_displays(self):
        self.detailed_stats.delete(1.0, tk.END)
        self.stats_summary.delete(1.0, tk.END)
        self.comparison_text.delete(1.0, tk.END)
        self.error_text.delete(1.0, tk.END)
        for item in self.code_tree.get_children():
            self.code_tree.delete(item)
    
    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.update()
    
    def show_progress(self, show=True):
        if show:
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress['value'] = 0
    
    def show_file_info(self, filepath):
        try:
            size = os.path.getsize(filepath)
            info = f"File: {os.path.basename(filepath)}\n"
            info += f"Size: {size:,} bytes\n"
            info += f"Path: {filepath}\n"
            
            if filepath.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                info += f"Characters: {len(content):,}\n"
                info += f"Lines: {content.count(chr(10)) + 1}\n"
            
            self.stats_summary.delete(1.0, tk.END)
            self.stats_summary.insert(1.0, info)
        except Exception as e:
            print(f"Error reading file info: {e}")
    
    def compress_file(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select a file first!")
            return
        
        def compress_thread():
            self.show_progress(True)
            self.update_status(f"Compressing with {self.algo_var.get()}...")
            
            try:
                algorithm = self.manager.get_algorithm(self.algo_var.get())
                output_path = algorithm.compress(self.current_file)
                stats = algorithm.get_stats()
                
                self.root.after(0, lambda: self.update_ui_after_compress(stats, algorithm))
                
                messagebox.showinfo("Success", 
                                  f"File compressed successfully!\n"
                                  f"Saved to: {os.path.basename(output_path)}\n"
                                  f"Compression ratio: {stats['compression_ratio']:.2f}%")
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Compression failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.show_progress(False))
                self.root.after(0, lambda: self.update_status("Ready"))
        
        threading.Thread(target=compress_thread, daemon=True).start()
    
    def update_ui_after_compress(self, stats, algorithm):
       
        details = f"=== COMPRESSION STATISTICS ===\n\n"
        details += f"Algorithm: {stats.get('algorithm', 'N/A')}\n"
        details += f"Original file size: {stats.get('original_size', 0):,} bytes\n"
        details += f"Compressed file size: {stats.get('compressed_size', 0):,} bytes\n"
        details += f"Compression ratio: {stats.get('compression_ratio', 0):.2f}%\n"
        details += f"Space saved: {(stats.get('original_size', 0) - stats.get('compressed_size', 0)):,} bytes\n"
        details += f"Compression time: {stats.get('compression_time', 0):.3f} seconds\n"
        details += f"Output file: {os.path.basename(stats.get('output_path', ''))}\n"
        
        if 'checksum' in stats:
            details += f"Checksum: {stats.get('checksum', 'N/A')}\n"
            details += f"File hash: {stats.get('file_hash', 'N/A')}\n"
        
        self.detailed_stats.delete(1.0, tk.END)
        self.detailed_stats.insert(1.0, details)
        
      
        summary = f"Size: {stats.get('compressed_size', 0):,}B\n"
        summary += f"Ratio: {stats.get('compression_ratio', 0):.1f}%\n"
        summary += f"Time: {stats.get('compression_time', 0):.2f}s\n"
        if 'checksum' in stats:
            summary += f"✓ Error detection\n"
        
        self.stats_summary.delete(1.0, tk.END)
        self.stats_summary.insert(1.0, summary)
        
       
        if isinstance(algorithm, HuffmanCoding):
            self.update_huffman_codes(algorithm)
            
            
            error_info = f"=== ERROR DETECTION INFO ===\n\n"
            error_info += f"Algorithm used: Parity bit check\n"
            error_info += f"Checksum value: {stats.get('checksum', 'N/A')}\n"
            error_info += f"File hash (MD5 first 8 chars): {stats.get('file_hash', 'N/A')}\n"
            error_info += f"\nParity bit calculation:\n"
            error_info += f"  - XOR of all bytes in compressed data\n"
            error_info += f"  - Single-bit error detection\n"
            error_info += f"  - Quick validation during decompression\n"
            
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(1.0, error_info)
    
    def update_huffman_codes(self, huffman_algo):
        
        for item in self.code_tree.get_children():
            self.code_tree.delete(item)
        
       
        with open(self.current_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        freq = Counter(text)
        sorted_codes = sorted(huffman_algo.codes.items(), 
                             key=lambda x: freq.get(x[0], 0), 
                             reverse=True)
        
        for char, code in sorted_codes[:100]:  # Show top 100
            char_display = repr(chr(char) if isinstance(char, int) else char)[1:-1]
            ascii_val = ord(char) if not isinstance(char, int) else char
            freq_val = freq.get(char, 0)
            self.code_tree.insert('', 'end', values=(char_display, ascii_val, freq_val, code))
    
    def decompress_file(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select a file first!")
            return
        
        def decompress_thread():
            self.show_progress(True)
            self.update_status("Decompressing...")
            
            try:
                # Detect algorithm from file extension
                if self.current_file.endswith('.huff'):
                    algorithm = HuffmanCoding()
                elif self.current_file.endswith('.rle'):
                    algorithm = RunLengthEncoding()
                else:
                    messagebox.showerror("Error", "Unknown file format!")
                    return
                
                output_path = algorithm.decompress(self.current_file)
                stats = algorithm.get_stats()
                
                self.root.after(0, lambda: self.update_ui_after_decompress(stats))
                
                messagebox.showinfo("Success", 
                                  f"File decompressed successfully!\n"
                                  f"Saved to: {os.path.basename(output_path)}\n"
                                  f"Decompression time: {stats.get('decompression_time', 0):.3f} seconds")
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Decompression failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.show_progress(False))
                self.root.after(0, lambda: self.update_status("Ready"))
        
        threading.Thread(target=decompress_thread, daemon=True).start()
    
    def update_ui_after_decompress(self, stats):
        details = f"=== DECOMPRESSION STATISTICS ===\n\n"
        details += f"Input file: {os.path.basename(self.current_file)}\n"
        details += f"Output file: {os.path.basename(stats.get('decompressed_path', ''))}\n"
        details += f"Decompression time: {stats.get('decompression_time', 0):.3f} seconds\n"
        
        if 'verified' in stats:
            status = "✓ VERIFIED" if stats['verified'] else "✗ VERIFICATION FAILED"
            details += f"Integrity check: {status}\n"
        
        self.detailed_stats.delete(1.0, tk.END)
        self.detailed_stats.insert(1.0, details)
    
    def compare_algorithms(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select a file first!")
            return
        
        def compare_thread():
            self.show_progress(True)
            self.update_status("Comparing algorithms...")
            
            try:
                results = self.manager.compare_algorithms(self.current_file)
                
                self.root.after(0, lambda: self.update_comparison_ui(results))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Comparison failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.show_progress(False))
                self.root.after(0, lambda: self.update_status("Ready"))
        
        threading.Thread(target=compare_thread, daemon=True).start()
    
    def update_comparison_ui(self, results):
       
        comparison_text = "=== ALGORITHM COMPARISON ===\n\n"
        
        for result in results:
            comparison_text += f"Algorithm: {result['algorithm']}\n"
            comparison_text += f"  Original size: {result['original_size']:,} bytes\n"
            comparison_text += f"  Compressed size: {result['compressed_size']:,} bytes\n"
            comparison_text += f"  Compression ratio: {result['compression_ratio']:.2f}%\n"
            comparison_text += f"  Compression time: {result['compression_time']:.3f} seconds\n"
            comparison_text += "-" * 40 + "\n"
        
        
        if results:
            best_ratio = max(results, key=lambda x: x['compression_ratio'])
            best_time = min(results, key=lambda x: x['compression_time'])
            
            comparison_text += f"\n📊 SUMMARY:\n"
            comparison_text += f"Best compression ratio: {best_ratio['algorithm']} ({best_ratio['compression_ratio']:.2f}%)\n"
            comparison_text += f"Fastest compression: {best_time['algorithm']} ({best_time['compression_time']:.3f}s)\n"
        
        self.comparison_text.delete(1.0, tk.END)
        self.comparison_text.insert(1.0, comparison_text)
        
       
        self.update_comparison_chart(results)
    
    def update_comparison_chart(self, results):
        self.ax.clear()
        
        if not results:
            return
        
        algorithms = [r['algorithm'] for r in results]
        ratios = [r['compression_ratio'] for r in results]
        times = [r['compression_time'] for r in results]
        
        x = np.arange(len(algorithms))
        width = 0.35
        
       
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        
        bars1 = ax1.bar(x, ratios, width, color=['#27ae60', '#3498db'])
        ax1.set_xlabel('Algorithm')
        ax1.set_ylabel('Compression Ratio (%)')
        ax1.set_title('Compression Efficiency')
        ax1.set_xticks(x)
        ax1.set_xticklabels(algorithms, rotation=15)
        
       
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        
        bars2 = ax2.bar(x, times, width, color=['#e67e22', '#9b59b6'])
        ax2.set_xlabel('Algorithm')
        ax2.set_ylabel('Time (seconds)')
        ax2.set_title('Compression Speed')
        ax2.set_xticks(x)
        ax2.set_xticklabels(algorithms, rotation=15)
        
        
        for bar in bars2:
            height = bar.get_height()
            ax2.annotate(f'{height:.3f}s',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        plt.tight_layout()
        
       
        self.canvas.figure = fig
        self.canvas.draw()


def main():
    root = tk.Tk()
    app = CompressionGUI(root)


    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()