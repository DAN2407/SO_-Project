import tkinter as tk
from tkinter import ttk, messagebox
import random

class MemoryManager:
    def __init__(self, total_memory=100):
        self.total_memory = total_memory
        self.memory = [None] * total_memory
        self.history = []
        
    def worst_fit(self, process_name, size):
        """Algoritmo de Peor Ajuste"""
        best_start = -1
        best_size = -1
        current_start = -1
        current_size = 0
        
        for i in range(self.total_memory + 1):
            if i < self.total_memory and self.memory[i] is None:
                if current_start == -1:
                    current_start = i
                current_size += 1
            else:
                if current_size >= size and current_size > best_size:
                    best_start = current_start
                    best_size = current_size
                current_start = -1
                current_size = 0
        
        if best_start != -1:
            self.allocate_memory(best_start, process_name, size)
            self.history.append(f"Asignado {process_name} (tamaño {size}) en posición {best_start} - Peor Ajuste (bloque tamaño {best_size})")
            return best_start
        
        self.history.append(f"FALLÓ asignar {process_name} (tamaño {size}) - Sin espacio")
        return -1
    
    def check_free_space(self, start, size):
        if start + size > self.total_memory:
            return False
        return all(self.memory[i] is None for i in range(start, start + size))
    
    def allocate_memory(self, start, process_name, size):
        for i in range(start, start + size):
            self.memory[i] = process_name
    
    def deallocate_memory(self, process_name):
        for i in range(self.total_memory):
            if self.memory[i] == process_name:
                self.memory[i] = None
        self.history.append(f"Liberado proceso {process_name}")
    
    def get_fragmentation(self):
        free_blocks = 0
        in_free_block = False
        
        for cell in self.memory:
            if cell is None and not in_free_block:
                free_blocks += 1
                in_free_block = True
            elif cell is not None:
                in_free_block = False
        
        return free_blocks
    
    def get_largest_free_block(self):
        max_block = 0
        current_block = 0
        
        for cell in self.memory:
            if cell is None:
                current_block += 1
                max_block = max(max_block, current_block)
            else:
                current_block = 0
        
        return max_block

class MemorySimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Algoritmos de Memoria - Windows 98/XP/7")
        self.root.geometry("950x750")
        
        self.memory_manager = MemoryManager(50)
        self.process_counter = 0
        self.current_algorithm = "worst_fit"  # solo Peor Ajuste
        self.current_demo_info = ""  # texto base de la demo (para usar en pause/reanudar)
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Configura la interfaz gráfica integrada"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== FILA SUPERIOR: CONTROLES Y DEMOSTRACIONES =====
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Columna izquierda: Controles básicos
        left_controls = ttk.Frame(top_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Algoritmo
        ttk.Label(left_controls, text="Algoritmo:").grid(row=0, column=0, sticky=tk.W, padx=5)
        # Interfaz fija: solo Peor Ajuste (no editable)
        self.algorithm_var = tk.StringVar(value="Peor Ajuste")
        algorithm_combo = ttk.Combobox(left_controls, textvariable=self.algorithm_var,
                                      values=["Peor Ajuste"], width=15, state="readonly")
        algorithm_combo.grid(row=0, column=1, padx=5)
        
        # Tamaño de proceso
        ttk.Label(left_controls, text="Tamaño:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.size_var = tk.StringVar(value="5")
        size_spin = ttk.Spinbox(left_controls, from_=1, to=20, textvariable=self.size_var, width=5)
        size_spin.grid(row=0, column=3, padx=5)
        
        # Botones de control
        ttk.Button(left_controls, text="Agregar", command=self.add_process).grid(row=0, column=4, padx=2)
        ttk.Button(left_controls, text="Liberar Aleatorio", command=self.free_random).grid(row=0, column=5, padx=2)
        ttk.Button(left_controls, text="Limpiar Todo", command=self.clear_all).grid(row=0, column=6, padx=2)
        
        # Columna derecha: Demostraciones rápidas
        right_demos = ttk.Frame(top_frame)
        right_demos.pack(side=tk.RIGHT, fill=tk.X)
        
        ttk.Label(right_demos, text="Demostraciones Rápidas:").grid(row=0, column=0, padx=5)
        
        # Botones de demostración compactos
        demos = [
            ("Pequeños", self.demo_small_processes),
            ("Grandes", self.demo_large_processes), 
            ("Mezclados", self.demo_mixed_sizes),
            ("Fragmentación", self.demo_fragmentation),
            ("Comparar", self.demo_comparison)
        ]
        
        for i, (name, command) in enumerate(demos):
            ttk.Button(right_demos, text=name, command=command, width=10).grid(row=0, column=i+1, padx=2)
        
        # ===== ÁREA DE INFORMACIÓN =====
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.info_label = ttk.Label(info_frame, text="Estado: Listo - Selecciona una demostración o agrega procesos manualmente", 
                                   font=('Arial', 10), background='#f0f0f0', relief=tk.SUNKEN, padding=5)
        self.info_label.pack(fill=tk.X)
        
        # ===== VISUALIZACIÓN DE MEMORIA =====
        memory_frame = ttk.Frame(main_frame)
        memory_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas para memoria
        self.canvas = tk.Canvas(memory_frame, bg='white', relief=tk.SUNKEN, borderwidth=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ===== FILA INFERIOR: ESTADÍSTICAS Y CONTROLES =====
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=5)
        
        # Estadísticas
        stats_frame = ttk.Frame(bottom_frame)
        stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 9))
        self.stats_label.pack(anchor=tk.W)
        
        # Botón de pausa para demostraciones
        self.demo_control_frame = ttk.Frame(bottom_frame)
        self.demo_control_frame.pack(side=tk.RIGHT)
        
        self.pause_button = ttk.Button(self.demo_control_frame, text="Pausar Demo", 
                                      command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.RIGHT, padx=5)
        
        # ===== ÁREA DE TEXTO: PROCESOS E HISTORIAL =====
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.X, pady=5)
        
        # Procesos activos (izquierda)
        processes_frame = ttk.Frame(text_frame)
        processes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(processes_frame, text="Procesos Activos:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.processes_text = tk.Text(processes_frame, height=4, width=40)
        self.processes_text.pack(fill=tk.X)
        
        # Historial (derecha)
        history_frame = ttk.Frame(text_frame)
        history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(history_frame, text="Historial de Operaciones:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.history_text = tk.Text(history_frame, height=4, width=40)
        self.history_text.pack(fill=tk.X)
        
        # Variables de control de demostración
        self.demo_running = False
        self.demo_paused = False
        self.current_demo_sequence = []
    
    # ========== DEMOSTRACIONES INTEGRADAS ==========
    
    def demo_small_processes(self):
        """Demo: Procesos pequeños"""
        if self.demo_running:
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO: Procesos Pequeños (1-3 unidades)\n"
            "• Objetivo: Mostrar asignación de procesos pequeños\n"
            "• Observa: Fragmentación y eficiencia\n"
            "• Secuencia: 10 procesos pequeños"
        )
        
        sizes = [2, 1, 3, 2, 1, 3, 2, 1, 2, 3]
        self.start_demo_sequence(sizes, "Procesos pequeños")
    
    def demo_large_processes(self):
        """Demo: Procesos grandes"""
        if self.demo_running:
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO: Procesos Grandes (8-12 unidades)\n"
            "• Objetivo: Comparar asignación de procesos grandes\n"
            "• Observa: Cómo Peor Ajuste busca bloques grandes\n"
            "• Secuencia: 5 procesos grandes"
        )
        
        sizes = [10, 8, 12, 9, 11]
        self.start_demo_sequence(sizes, "Procesos grandes")
    
    def demo_mixed_sizes(self):
        """Demo: Mezcla de tamaños"""
        if self.demo_running:
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO: Mezcla de Tamaños\n"
            "• Objetivo: Comportamiento en escenario real\n"
            "• Observa: Estrategias con variedad de tamaños\n"
            "• Secuencia: Procesos pequeños, medianos y grandes"
        )
        
        sizes = [8, 2, 6, 1, 10, 3, 4, 7, 2, 5]
        self.start_demo_sequence(sizes, "Mezcla de tamaños")
    
    def demo_fragmentation(self):
        """Demo: Fragmentación"""
        if self.demo_running:
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO: Generación de Fragmentación\n"
            "• Fase 1: Llenar con procesos pequeños\n"
            "• Fase 2: Liberar estratégicamente\n"
            "• Observa: Cómo se genera y maneja la fragmentación"
        )
        
        # Fase 1: Llenar con pequeños
        sizes = [3, 3, 3, 3, 3, 3, 3, 3]
        self.start_demo_sequence(sizes, "Fragmentación - Fase 1")
        
        # Programar fase 2 (usar mismo intervalo que execute_next_demo_step: 800ms)
        self.root.after(len(sizes) * 800 + 1000, self.demo_fragmentation_phase2)
    
    def demo_fragmentation_phase2(self):
        """Segunda fase de demo de fragmentación"""
        if not self.demo_running:
            return
            
        processes_to_free = ["P2", "P4", "P6"]
        for process in processes_to_free:
            self.memory_manager.deallocate_memory(process)
        
        self.update_display()
        self.show_demo_info(
            "DEMO: Fragmentación - Fase 2\n"
            "• Liberados procesos P2, P4, P6\n"
            "• Ahora hay fragmentación\n"
            "• Prueba asignar un proceso de tamaño 5-6 unidades\n"
            "• Observa cómo cada algoritmo maneja la situación"
        )
        
        # Finalizar demo
        self.root.after(3000, self.end_demo)
    
    def demo_comparison(self):
        """Demo: Comparación"""
        self.clear_all()
        self.show_demo_info(
            "DEMO: Comparación de Algoritmos\n"
            "• Instrucciones:\n"
            "  1. Ejecuta con Siguiente Ajuste\n"  
            "  2. Cambia a Peor Ajuste\n"
            "  3. Compara resultados\n"
            "• Secuencia recomendada: 5, 3, 7, 2, 6, 4"
        )
        self.size_var.set("5")
    
    def show_demo_info(self, text):
        """Muestra información de la demo en el área de información"""
        self.current_demo_info = text
        self.info_label.config(text=text)
    
    def start_demo_sequence(self, sizes, demo_name):
        """Inicia una secuencia de demostración"""
        self.demo_running = True
        self.demo_paused = False
        self.current_demo_sequence = sizes
        self.pause_button.config(state=tk.NORMAL, text="Pausar Demo")
        
        self.memory_manager.history.append(f"=== INICIO DEMO: {demo_name} ===")
        self.execute_next_demo_step(0)
    
    def execute_next_demo_step(self, index):
        """Ejecuta el siguiente paso de la demo"""
        if not self.demo_running or index >= len(self.current_demo_sequence):
            self.end_demo()
            return
        
        if self.demo_paused:
            # Reintentar después de 500ms si está pausado
            self.root.after(500, lambda: self.execute_next_demo_step(index))
            return
        
        size = self.current_demo_sequence[index]
        self.process_counter += 1
        process_name = f"P{self.process_counter}"
        
        # Usar siempre Peor Ajuste
        self.memory_manager.worst_fit(process_name, size)
        
        self.update_display()
        
        # Programar siguiente paso
        self.root.after(800, lambda: self.execute_next_demo_step(index + 1))
    
    def toggle_pause(self):
        """Pausa/reanuda la demo"""
        if self.demo_running:
            self.demo_paused = not self.demo_paused
            self.pause_button.config(text="Reanudar Demo" if self.demo_paused else "Pausar Demo")
            status = "PAUSADA" if self.demo_paused else "EJECUTANDO"
            # Usar el texto base de la demo para evitar acumulación de prefijos
            base = self.current_demo_info if getattr(self, "current_demo_info", "") else self.info_label.cget("text")
            self.info_label.config(text=f"Demo {status} - {base}")
    
    def end_demo(self):
        """Finaliza la demo"""
        self.demo_running = False
        self.demo_paused = False
        self.pause_button.config(state=tk.DISABLED, text="Pausar Demo")
        self.show_demo_info("Demo finalizada. Puedes probar con otro algoritmo o nueva demostración.")
    
    # ========== FUNCIONES BASE ==========
    
    def on_algorithm_change(self, event):
        self.current_algorithm = "next_fit" if self.algorithm_var.get() == "Siguiente Ajuste" else "worst_fit"
        self.update_display()
    
    def add_process(self):
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demostración actual antes de agregar procesos manualmente.")
            return
            
        try:
            size = int(self.size_var.get())
            if size <= 0:
                messagebox.showerror("Error", "El tamaño debe ser mayor a 0")
                return
            
            self.process_counter += 1
            process_name = f"P{self.process_counter}"
            
            # Asignación con Peor Ajuste
            result = self.memory_manager.worst_fit(process_name, size)
            
            if result == -1:
                messagebox.showwarning("Sin memoria", "No hay espacio suficiente")
                self.process_counter -= 1
            else:
                self.update_display()
                
        except ValueError:
            messagebox.showerror("Error", "Tamaño inválido")
    
    def free_random(self):
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demostración actual antes de liberar procesos.")
            return
            
        active_processes = []
        for cell in self.memory_manager.memory:
            if cell is not None and cell not in active_processes:
                active_processes.append(cell)
        
        if active_processes:
            process_to_free = random.choice(active_processes)
            self.memory_manager.deallocate_memory(process_to_free)
            self.update_display()
        else:
            messagebox.showinfo("Info", "No hay procesos activos")
    
    def clear_all(self):
        if self.demo_running:
            self.end_demo()
            
        self.memory_manager = MemoryManager(50)
        self.process_counter = 0
        self.update_display()
        self.show_demo_info("Sistema reiniciado. Selecciona una demostración o agrega procesos manualmente.")
    
    def update_display(self):
        self.canvas.delete("all")
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                 '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        cell_width = max(10, self.canvas.winfo_width() / len(self.memory_manager.memory))
        cell_height = 30
        
        for i, process in enumerate(self.memory_manager.memory):
            x1 = i * cell_width
            y1 = 10
            x2 = (i + 1) * cell_width
            y2 = y1 + cell_height
            
            if process is None:
                color = 'white'
                text = ""
            else:
                process_num = int(process[1:]) if process[1:].isdigit() else 0
                color = colors[process_num % len(colors)]
                text = process
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black')
            if text and cell_width > 15:
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=('Arial', 8))
        
        # Actualizar estadísticas
        algorithm_name = "Peor Ajuste"
        fragmentation = self.memory_manager.get_fragmentation()
        largest_block = self.memory_manager.get_largest_free_block()
        used_memory = sum(1 for cell in self.memory_manager.memory if cell is not None)
        free_memory = len(self.memory_manager.memory) - used_memory
        usage_percentage = (used_memory / len(self.memory_manager.memory)) * 100
        
        total_mem = len(self.memory_manager.memory)
        stats_text = f"{algorithm_name} | Usado: {used_memory}/{total_mem} ({usage_percentage:.1f}%) | "
        stats_text += f"Fragmentación: {fragmentation} bloques | Mayor bloque libre: {largest_block}"
        self.stats_label.config(text=stats_text)
        
        # Actualizar procesos activos
        self.processes_text.delete(1.0, tk.END)
        active_processes = {}
        for cell in self.memory_manager.memory:
            if cell is not None:
                if cell not in active_processes:
                    active_processes[cell] = 0
                active_processes[cell] += 1
        
        for process, size in active_processes.items():
            self.processes_text.insert(tk.END, f"{process}: {size} unidades\n")
        
        # Actualizar historial
        self.history_text.delete(1.0, tk.END)
        for entry in self.memory_manager.history[-8:]:
            self.history_text.insert(tk.END, f"{entry}\n")

def main():
    root = tk.Tk()
    app = MemorySimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()