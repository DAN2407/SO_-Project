import tkinter as tk
from tkinter import ttk, messagebox
import random 

class WorstFitMemoryManager:
    def __init__(self):
        self.memory_size = 50  # Tamaño inicial de memoria
        self.memory = [0] * self.memory_size  # 0 = libre, >0 = proceso ocupado
        self.processes = {}  # Diccionario de procesos: {id: tamaño}
        self.next_process_id = 1
        
    def worst_fit(self, process_size):
        """Implementa el algoritmo Peor Ajuste (Worst Fit)"""
        best_start = -1
        best_size = -1
        current_start = -1
        current_size = 0
        
        # Buscar el bloque libre más grande
        for i in range(self.memory_size):
            if self.memory[i] == 0:  # Bloque libre
                if current_start == -1:
                    current_start = i
                current_size += 1
            else:  # Bloque ocupado
                if current_size >= process_size and current_size > best_size:
                    best_start = current_start
                    best_size = current_size
                current_start = -1
                current_size = 0
        
        # Verificar el último bloque
        if current_size >= process_size and current_size > best_size:
            best_start = current_start
            best_size = current_size
        
        return best_start
    
    def allocate_process(self, process_size):
        """Asigna un proceso a la memoria usando Worst Fit"""
        if process_size <= 0:
            messagebox.showerror("Error", "El tamaño del proceso debe ser mayor a 0")
            return False
            
        if process_size > self.memory_size:
            messagebox.showerror("Error", f"El proceso es más grande que la memoria total ({self.memory_size})")
            return False
        
        start_index = self.worst_fit(process_size)
        
        if start_index == -1:
            messagebox.showerror("Error", "No hay espacio suficiente para asignar el proceso")
            return False
        
        # Asignar el proceso
        process_id = self.next_process_id
        self.next_process_id += 1
        
        for i in range(start_index, start_index + process_size):
            self.memory[i] = process_id
        
        self.processes[process_id] = process_size
        return True
    
    def deallocate_process(self, process_id):
        """Libera un proceso de la memoria"""
        if process_id not in self.processes:
            return False
        
        # Liberar la memoria
        for i in range(self.memory_size):
            if self.memory[i] == process_id:
                self.memory[i] = 0
        
        del self.processes[process_id]
        return True
    
    def calculate_fragmentation(self):
        """Calcula la fragmentación externa"""
        free_blocks = []
        current_block = 0
        
        for i in range(self.memory_size):
            if self.memory[i] == 0:
                current_block += 1
            else:
                if current_block > 0:
                    free_blocks.append(current_block)
                    current_block = 0
        
        if current_block > 0:
            free_blocks.append(current_block)
        
        if not free_blocks:
            return 0, 0, 0
        
        total_fragmentation = sum(free_blocks)
        external_fragmentation = len(free_blocks)
        largest_block = max(free_blocks)
        
        return total_fragmentation, external_fragmentation, largest_block

class MemorySimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador Worst Fit - Windows Memory Management")
        self.root.geometry("800x600")
        
        self.manager = WorstFitMemoryManager()
        
        self.setup_gui()
        self.update_display()
    
    def setup_gui(self):
        # Frame de controles
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="ew")
        
        # Control de tamaño de memoria
        ttk.Label(control_frame, text="Tamaño de Memoria (10-100):").grid(row=0, column=0, padx=5)
        self.memory_var = tk.IntVar(value=50)
        memory_scale = ttk.Scale(control_frame, from_=10, to=100, variable=self.memory_var, 
                               orient="horizontal", command=self.update_memory_size)
        memory_scale.grid(row=0, column=1, padx=5)
        
        self.memory_label = ttk.Label(control_frame, text="50")
        self.memory_label.grid(row=0, column=2, padx=5)
        
        # Control de tamaño de proceso
        ttk.Label(control_frame, text="Tamaño Proceso:").grid(row=1, column=0, padx=5)
        self.process_var = tk.IntVar(value=5)
        process_spin = ttk.Spinbox(control_frame, from_=1, to=20, textvariable=self.process_var, width=10)
        process_spin.grid(row=1, column=1, padx=5)
        
        # Botones
        ttk.Button(control_frame, text="Asignar Proceso", 
                  command=self.allocate_process).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Liberar Aleatorio", 
                  command=self.deallocate_random).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Asignar Aleatorio", 
                  command=self.allocate_random).grid(row=2, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Limpiar Memoria", 
                  command=self.clear_memory).grid(row=2, column=3, padx=5, pady=5)
        
        # Frame de visualización de memoria
        memory_frame = ttk.LabelFrame(self.root, text="Visualización de Memoria", padding="10")
        memory_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.canvas = tk.Canvas(memory_frame, height=100, bg="white")
        self.canvas.pack(fill="x", expand=True)
        
        # Frame de información
        info_frame = ttk.LabelFrame(self.root, text="Estadísticas", padding="10")
        info_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.stats_text = tk.Text(info_frame, height=8, width=80)
        self.stats_text.pack(fill="x", expand=True)
        
        # Configurar expansión
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def update_memory_size(self, value):
        """Actualiza el tamaño de memoria cuando se mueve el slider"""
        new_size = int(float(value))
        self.memory_label.config(text=str(new_size))
        
        # Redimensionar memoria manteniendo los procesos existentes
        old_memory = self.manager.memory.copy()
        old_size = self.manager.memory_size
        
        self.manager.memory_size = new_size
        self.manager.memory = [0] * new_size
        
        # Copiar procesos existentes si caben
        process_positions = {}
        # Colocar primero los procesos más grandes para mejorar la recompacción
        sorted_processes = sorted(self.manager.processes.items(), key=lambda it: it[1], reverse=True)
        for process_id, size in sorted_processes:
            start_index = self.manager.worst_fit(size)
            if start_index != -1 and start_index + size <= new_size:
                for i in range(start_index, start_index + size):
                    self.manager.memory[i] = process_id
                process_positions[process_id] = start_index
        
        # Actualizar procesos (eliminar los que no caben)
        self.manager.processes = {pid: size for pid, size in self.manager.processes.items() 
                                if pid in process_positions}
        
        self.update_display()
    
    def allocate_process(self):
        """Asigna un proceso con el tamaño especificado"""
        process_size = self.process_var.get()
        if self.manager.allocate_process(process_size):
            self.update_display()
    
    def allocate_random(self):
        """Asigna un proceso con tamaño aleatorio"""
        process_size = random.randint(1, min(15, self.manager.memory_size // 3))
        self.process_var.set(process_size)
        if self.manager.allocate_process(process_size):
            self.update_display()
    
    def deallocate_random(self):
        """Libera un proceso aleatorio"""
        if self.manager.processes:
            process_id = random.choice(list(self.manager.processes.keys()))
            self.manager.deallocate_process(process_id)
            self.update_display()
        else:
            messagebox.showinfo("Info", "No hay procesos para liberar")
    
    def clear_memory(self):
        """Limpia toda la memoria"""
        self.manager.memory = [0] * self.manager.memory_size
        self.manager.processes = {}
        self.manager.next_process_id = 1
        self.update_display()
    
    def update_display(self):
        """Actualiza la visualización de memoria y estadísticas"""
        self.canvas.delete("all")
        
        # Dibujar memoria
        cell_width = min(20, 780 / self.manager.memory_size)
        x = 10
        
        for i in range(self.manager.memory_size):
            color = "lightgreen" if self.manager.memory[i] == 0 else "lightcoral"
            self.canvas.create_rectangle(x, 10, x + cell_width - 2, 40, 
                                       fill=color, outline="black")
            
            if self.manager.memory[i] != 0:
                self.canvas.create_text(x + cell_width/2, 25, 
                                      text=str(self.manager.memory[i]), font=("Arial", 8))
            
            x += cell_width
        
        # Actualizar estadísticas
        total_frag, ext_frag, largest_block = self.manager.calculate_fragmentation()
        memory_used = sum(self.manager.processes.values())
        memory_free = self.manager.memory_size - memory_used
        
        stats = f"""
ESTADÍSTICAS DEL ALGORITMO PEOR AJUSTE (WORST FIT):
        
Tamaño total de memoria: {self.manager.memory_size} unidades
Memoria utilizada: {memory_used} unidades ({memory_used/self.manager.memory_size*100:.1f}%)
Memoria libre: {memory_free} unidades ({memory_free/self.manager.memory_size*100:.1f}%)
Procesos activos: {len(self.manager.processes)}
Fragmentación total: {total_frag} unidades
Fragmentación externa: {ext_frag} bloques libres
Bloque libre más grande: {largest_block} unidades

CARACTERÍSTICAS DE WORST FIT:
• Busca el bloque libre MÁS GRANDE disponible
• Reduce la fragmentación externa en algunos casos
• Puede dejar bloques grandes sin utiliza
"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

def main():
    root = tk.Tk()
    app = MemorySimulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()