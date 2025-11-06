import tkinter as tk
from tkinter import ttk, messagebox
import random

class MemoryManager:
    def __init__(self, total_memory=100):
        self.total_memory = total_memory
        self.memory = [None] * total_memory
        self.history = []

    def _free_blocks(self):
        """Devuelve lista de (start, size) de bloques libres"""
        blocks = []
        start = None
        for i, cell in enumerate(self.memory + [1]):  # sentinel para cerrar bloque al final
            if cell is None:
                if start is None:
                    start = i
            else:
                if start is not None:
                    blocks.append((start, i - start))
                    start = None
        return blocks

    def worst_fit(self, process_name, size):
        blocks = self._free_blocks()
        # Buscar el bloque libre más grande que quepa
        best = max(((s, l) for s, l in blocks if l >= size), key=lambda x: x[1], default=None)
        if best:
            start = best[0]
            self.allocate_memory(start, process_name, size)
            self.history.append(f"Asignado {process_name} (tamaño {size}) en {start} - Peor Ajuste (bloque {best[1]})")
            return start
        self.history.append(f"FALLÓ asignar {process_name} (tamaño {size}) - Sin espacio")
        return -1

    def allocate_memory(self, start, process_name, size):
        for i in range(start, start + size):
            self.memory[i] = process_name

    def deallocate_memory(self, process_name):
        changed = False
        for i, v in enumerate(self.memory):
            if v == process_name:
                self.memory[i] = None
                changed = True
        if changed:
            self.history.append(f"Liberado proceso {process_name}")

    def stats(self):
        used = sum(1 for c in self.memory if c is not None)
        free = self.total_memory - used
        blocks = self._free_blocks()
        fragmentation = len(blocks)
        largest = max((b for _, b in blocks), default=0)
        return used, free, fragmentation, largest

class MemorySimulatorApp:
    DEMO_DELAY = 800

    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Algoritmos de Memoria")
        self.root.minsize(800, 600)
        self.root.bind("<Configure>", self._on_root_configure)

        self.mem_size_var = tk.StringVar(value="50")
        self.size_var = tk.StringVar(value="5")
        self.process_counter = 0

        self.memory_manager = MemoryManager(int(self.mem_size_var.get()))
        self.demo_running = self.demo_paused = False
        self.current_demo_info = ""
        self.current_demo_sequence = []
        self._after_id = None

        self._build_ui()
        self.update_display()

    def _build_ui(self):
        m = ttk.Frame(self.root, padding=8); m.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(m); top.pack(fill=tk.X, pady=4)
        left = ttk.Frame(top); left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(left, text="Algoritmo:").grid(row=0, column=0, sticky=tk.W, padx=4)
        ttk.Combobox(left, values=["Peor Ajuste"], state="readonly", width=15).grid(row=0, column=1, padx=4)
        ttk.Label(left, text="Tamaño:").grid(row=0, column=2, sticky=tk.W, padx=4)
        ttk.Spinbox(left, from_=1, to=500, textvariable=self.size_var, width=6).grid(row=0, column=3, padx=4)
        ttk.Button(left, text="Agregar", command=self.add_process).grid(row=0, column=4, padx=3)
        ttk.Button(left, text="Liberar Aleatorio", command=self.free_random).grid(row=0, column=5, padx=3)
        ttk.Button(left, text="Limpiar Todo", command=self.clear_all).grid(row=0, column=6, padx=3)
        ttk.Label(left, text="Memoria:").grid(row=0, column=7, sticky=tk.W, padx=4)
        ttk.Spinbox(left, from_=10, to=1000, textvariable=self.mem_size_var, width=6).grid(row=0, column=8, padx=4)
        ttk.Button(left, text="Aplicar Tamaño", command=self.set_memory_size).grid(row=0, column=9, padx=3)

        right = ttk.Frame(top); right.pack(side=tk.RIGHT)
        demos = [
            ("Pequeños", [2,1,3,2,1,3,2,1,2,3]),
            ("Grandes", [10,8,12,9,11]),
            ("Mezclados", [8,2,6,1,10,3,4,7,2,5]),
            ("Fragmentación", [3,3,3,3,3,3,3,3]),
        ]
        ttk.Label(right, text="Demos:").grid(row=0, column=0, padx=4)
        for i, (n, seq) in enumerate(demos):
            ttk.Button(right, text=n, width=10, command=lambda s=seq, name=n: self.start_demo_sequence(s, name)).grid(row=0, column=i+1, padx=2)

        self.info_label = ttk.Label(m, text="Listo", background="#f0f0f0", relief=tk.SUNKEN, padding=4)
        self.info_label.pack(fill=tk.X, pady=4)

        mem_frame = ttk.Frame(m); mem_frame.pack(fill=tk.BOTH, expand=True)
        wrap = ttk.Frame(mem_frame); wrap.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(wrap, bg="white", highlightthickness=0)
        self.h_scroll = ttk.Scrollbar(wrap, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set)
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.h_scroll.pack(fill=tk.X, side=tk.BOTTOM)
        self.canvas.bind("<Configure>", lambda e: self.update_display())

        bottom = ttk.Frame(m); bottom.pack(fill=tk.X, pady=4)
        self.stats_label = ttk.Label(bottom, text=""); self.stats_label.pack(side=tk.LEFT, anchor=tk.W)
        self.pause_button = ttk.Button(bottom, text="Pausar Demo", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.RIGHT, padx=4)

        text_frame = ttk.Frame(m); text_frame.pack(fill=tk.X, pady=4)
        pframe = ttk.Frame(text_frame); pframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        ttk.Label(pframe, text="Procesos Activos:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.processes_text = tk.Text(pframe, height=4); self.processes_text.pack(fill=tk.X)
        hframe = ttk.Frame(text_frame); hframe.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4)
        ttk.Label(hframe, text="Historial:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.history_text = tk.Text(hframe, height=4); self.history_text.pack(fill=tk.X)

    def show_demo_info(self, text):
        self.current_demo_info = text
        self.info_label.config(text=text)

    def start_demo_sequence(self, sizes, demo_name):
        if self.demo_running: return
        self.clear_all()
        self.show_demo_info(f"DEMO: {demo_name}")
        self.demo_running = True; self.demo_paused = False
        self.current_demo_sequence = sizes[:]
        self.pause_button.config(state=tk.NORMAL, text="Pausar Demo")
        self.memory_manager.history.append(f"=== INICIO DEMO: {demo_name} ===")
        self._step_demo(0)

    def _step_demo(self, idx):
        if not self.demo_running or idx >= len(self.current_demo_sequence):
            return self.end_demo()
        if self.demo_paused:
            self._after_id = self.root.after(300, lambda: self._step_demo(idx))
            return
        size = self.current_demo_sequence[idx]
        self.process_counter += 1
        name = f"P{self.process_counter}"
        self.memory_manager.worst_fit(name, size)
        self.update_display()
        self._after_id = self.root.after(self.DEMO_DELAY, lambda: self._step_demo(idx + 1))

    def toggle_pause(self):
        if not self.demo_running: return
        self.demo_paused = not self.demo_paused
        self.pause_button.config(text="Reanudar Demo" if self.demo_paused else "Pausar Demo")
        status = "PAUSADA" if self.demo_paused else "EJECUTANDO"
        base = self.current_demo_info or self.info_label.cget("text")
        self.info_label.config(text=f"Demo {status} - {base}")

    def end_demo(self):
        if self._after_id:
            try: self.root.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None
        self.demo_running = self.demo_paused = False
        self.pause_button.config(state=tk.DISABLED, text="Pausar Demo")
        self.show_demo_info("Demo finalizada. Puedes probar otra demo o agregar procesos.")

    def add_process(self):
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demostración antes de agregar procesos.")
            return
        try:
            size = int(self.size_var.get())
            if size <= 0: raise ValueError
        except Exception:
            return messagebox.showerror("Error", "Tamaño inválido")
        self.process_counter += 1
        name = f"P{self.process_counter}"
        if self.memory_manager.worst_fit(name, size) == -1:
            messagebox.showwarning("Sin memoria", "No hay espacio suficiente")
            self.process_counter -= 1
        self.update_display()

    def free_random(self):
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demostración antes de liberar procesos.")
            return
        procs = [c for c in set(self.memory_manager.memory) if c]
        if not procs:
            messagebox.showinfo("Info", "No hay procesos activos")
            return
        self.memory_manager.deallocate_memory(random.choice(procs))
        self.update_display()

    def clear_all(self):
        if self.demo_running:
            self.end_demo()
        try:
            size = int(self.mem_size_var.get())
        except Exception:
            size = 50
        self.memory_manager = MemoryManager(size)
        self.process_counter = 0
        self.update_display()
        self.show_demo_info("Sistema reiniciado.")

    def set_memory_size(self):
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demostración antes de cambiar el tamaño.")
            return
        try:
            size = int(self.mem_size_var.get())
            if size <= 0: raise ValueError
        except Exception:
            return messagebox.showerror("Error", "Tamaño inválido")
        self.memory_manager = MemoryManager(size)
        self.process_counter = 0
        self.update_display()
        self.show_demo_info(f"Tamaño de memoria actualizado a {size}.")

    def update_display(self):
        self.canvas.delete("all")
        colors = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7DC6F','#BB8FCE','#85C1E9']
        min_w = 12
        total = max(1, self.memory_manager.total_memory)
        vw = max(1, self.canvas.winfo_width())
        cell_w = max(min_w, vw / total)
        cell_h = max(18, int(self.canvas.winfo_height() * 0.08))
        total_w = int(cell_w * total)
        self.canvas.config(scrollregion=(0,0,total_w,cell_h+20))
        for i, p in enumerate(self.memory_manager.memory):
            x1, x2 = i*cell_w, (i+1)*cell_w
            y1, y2 = 10, 10+cell_h
            col = 'white' if p is None else colors[(int(p[1:]) if p and p[1:].isdigit() else 0) % len(colors)]
            text = "" if p is None else p
            self.canvas.create_rectangle(x1,y1,x2,y2, fill=col, outline='black')
            if text and cell_w > 15: self.canvas.create_text((x1+x2)/2,(y1+y2)/2, text=text, font=('Arial',8))
        used, free, frag, largest = self.memory_manager.stats()
        stats = f"Peor Ajuste | Usado: {used}/{total} ({(used/total*100):.1f}%) | Fragmentación: {frag} | Mayor: {largest}"
        self.stats_label.config(text=stats)
        self.processes_text.delete(1.0, tk.END)
        counts = {}
        for c in self.memory_manager.memory:
            if c:
                counts[c] = counts.get(c, 0) + 1
        for k, v in counts.items(): self.processes_text.insert(tk.END, f"{k}: {v} unidades\n")
        self.history_text.delete(1.0, tk.END)
        for e in self.memory_manager.history[-12:]: self.history_text.insert(tk.END, e + "\n")

    def _on_root_configure(self, event):
        if event.widget == self.root: self.update_display()

def main():
    root = tk.Tk()
    MemorySimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()