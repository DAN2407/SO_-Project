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
        
        # Encontrar el bloque libre más grande
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
            self.history.append(f"✓ Asignado {process_name} (tamaño {size}) en posición {best_start} - Bloque libre usado: {best_size}")
            return best_start
        
        self.history.append(f"✗ FALLÓ asignar {process_name} (tamaño {size}) - Sin espacio suficiente")
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
        self.history.append(f"🗑️ Liberado proceso {process_name}")
    
    def get_fragmentation(self):
        """Calcula fragmentación externa (número de bloques libres)"""
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
        """Encuentra el bloque libre más grande"""
        max_block = 0
        current_block = 0
        
        for cell in self.memory:
            if cell is None:
                current_block += 1
                max_block = max(max_block, current_block)
            else:
                current_block = 0
        
        return max_block
    
    def get_memory_usage(self):
        """Calcula porcentaje de uso de memoria"""
        used = sum(1 for cell in self.memory if cell is not None)
        return (used / self.total_memory) * 100

class MemorySimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador - Algoritmo PEOR AJUSTE")
        self.root.geometry("900x700")
        
        self.memory_manager = MemoryManager(50)
        self.process_counter = 0
        self.demo_running = False
        self.current_demo_sizes = []
        self.current_demo_name = ""
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Configura la interfaz gráfica para Peor Ajuste"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== TÍTULO Y DESCRIPCIÓN =====
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="ALGORITMO DE PEOR AJUSTE", 
                               font=('Arial', 14, 'bold'),
                               foreground='#2E86AB')
        title_label.pack()
        
        desc_label = ttk.Label(title_frame,
                              text="Asigna procesos en el bloque de memoria LIBRE MÁS GRANDE disponible",
                              font=('Arial', 10),
                              foreground='#555555')
        desc_label.pack()
        
        # ===== CONTROLES PRINCIPALES =====
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        # Controles de proceso
        ttk.Label(controls_frame, text="Tamaño del proceso:").grid(row=0, column=0, padx=5)
        self.size_var = tk.StringVar(value="5")
        size_spin = ttk.Spinbox(controls_frame, from_=1, to=20, textvariable=self.size_var, width=8)
        size_spin.grid(row=0, column=1, padx=5)
        
        ttk.Button(controls_frame, text="Agregar Proceso", 
                  command=self.add_process).grid(row=0, column=2, padx=5)
        ttk.Button(controls_frame, text="Liberar Aleatorio", 
                  command=self.free_random).grid(row=0, column=3, padx=5)
        ttk.Button(controls_frame, text="Limpiar Todo", 
                  command=self.clear_all).grid(row=0, column=4, padx=5)
        
        # ===== DEMOSTRACIONES PEOR AJUSTE =====
        demos_frame = ttk.Frame(main_frame)
        demos_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(demos_frame, text="Demostraciones Específicas de PEOR AJUSTE:", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        demo_buttons_frame = ttk.Frame(demos_frame)
        demo_buttons_frame.pack(fill=tk.X, pady=5)
        
        demos = [
            ("Demo 1: Procesos Grandes", self.demo_large_processes),
            ("Demo 2: Fragmentación", self.demo_fragmentation),
            ("Demo 3: Escenario Real", self.demo_real_scenario),
            ("Demo 4: Eficiencia", self.demo_efficiency)
        ]
        
        for i, (name, command) in enumerate(demos):
            ttk.Button(demo_buttons_frame, text=name, command=command).grid(
                row=0, column=i, padx=3, sticky='ew')
            demo_buttons_frame.columnconfigure(i, weight=1)
        
        # ===== BOTÓN DE CONTROL DE DEMO =====
        self.demo_control_frame = ttk.Frame(main_frame)
        self.demo_control_frame.pack(fill=tk.X, pady=5)
        
        self.start_demo_button = ttk.Button(self.demo_control_frame, 
                                          text="Iniciar Demo", 
                                          command=self.start_demo_execution,
                                          state=tk.DISABLED)
        self.start_demo_button.pack()
        
        # ===== VISUALIZACIÓN DE MEMORIA =====
        memory_frame = ttk.Frame(main_frame)
        memory_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = tk.Canvas(memory_frame, bg='white', relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ===== ESTADÍSTICAS =====
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 10, 'bold'))
        self.stats_label.pack(anchor=tk.W)
        
        # ===== INFORMACIÓN Y HISTORIAL =====
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        # Información del algoritmo
        info_left = ttk.Frame(info_frame)
        info_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(info_left, text="Características del PEOR AJUSTE:", 
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        algorithm_info = """• Busca el BLOQUE LIBRE MÁS GRANDE disponible
• Ventaja: Deja bloques grandes disponibles para procesos futuros
• Desventaja: Puede crear más fragmentación con el tiempo
• Usado en: Windows XP y 7 para ciertos tipos de asignación"""
        
        info_text = tk.Text(info_left, height=5, width=45, font=('Arial', 9))
        info_text.pack(fill=tk.X)
        info_text.insert(1.0, algorithm_info)
        info_text.config(state=tk.DISABLED)
        
        # Historial de operaciones
        info_right = ttk.Frame(info_frame)
        info_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(info_right, text="Historial de Operaciones:", 
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.history_text = tk.Text(info_right, height=5, width=50, font=('Arial', 9))
        self.history_text.pack(fill=tk.X)
    
    # ========== DEMOSTRACIONES ESPECÍFICAS PARA PEOR AJUSTE ==========
    
    def demo_large_processes(self):
        """Demo: Procesos grandes - Fortaleza del Peor Ajuste"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demo actual antes de comenzar otra.")
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO 1: FORTALEZA con Procesos Grandes\n\n"
            "El PEOR AJUSTE es ideal para procesos grandes porque:\n"
            "• Siempre busca el bloque MÁS GRANDE disponible\n"
            "• Maximiza la probabilidad de encontrar espacio\n"
            "• Evita dividir bloques grandes innecesariamente\n\n"
            "Secuencia: 4 procesos grandes [12, 15, 10, 8]\n\n"
            "Presiona 'Iniciar Demo' para comenzar..."
        )
        
        self.current_demo_sizes = [12, 15, 10, 8]
        self.current_demo_name = "Procesos grandes - Fortaleza"
        self.start_demo_button.config(state=tk.NORMAL)
    
    def demo_fragmentation(self):
        """Demo: Fragmentación - Debilidad del Peor Ajuste"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demo actual antes de comenzar otra.")
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO 2: DEBILIDAD - Fragmentación\n\n"
            "El PEOR AJUSTE puede crear fragmentación porque:\n"
            "• Usa bloques grandes para procesos pequeños\n"
            "• Deja muchos bloques pequeños inutilizables\n"
            "• Dificulta asignaciones futuras de procesos grandes\n\n"
            "Secuencia: 5 procesos medianos [8, 8, 8, 8, 8]\n\n"
            "Presiona 'Iniciar Demo' para comenzar..."
        )
        
        self.current_demo_sizes = [8, 8, 8, 8, 8]
        self.current_demo_name = "Fragmentación - Debilidad"
        self.start_demo_button.config(state=tk.NORMAL)
    
    def demo_real_scenario(self):
        """Demo: Escenario real de Windows"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demo actual antes de comenzar otra.")
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO 3: Escenario Real - Windows XP/7\n\n"
            "Simulación de uso real en sistemas Windows:\n"
            "• Mezcla de servicios del sistema y aplicaciones\n"
            "• Procesos de diferentes tamaños y prioridades\n"
            "• Comportamiento típico del administrador de memoria\n\n"
            "Secuencia: [3, 6, 2, 8, 4, 5, 3, 7, 2, 6]\n\n"
            "Presiona 'Iniciar Demo' para comenzar..."
        )
        
        self.current_demo_sizes = [3, 6, 2, 8, 4, 5, 3, 7, 2, 6]
        self.current_demo_name = "Escenario real Windows"
        self.start_demo_button.config(state=tk.NORMAL)
    
    def demo_efficiency(self):
        """Demo: Eficiencia en diferentes situaciones"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Termina la demo actual antes de comenzar otra.")
            return
            
        self.clear_all()
        self.show_demo_info(
            "DEMO 4: Análisis de Eficiencia\n\n"
            "Compararemos el rendimiento del PEOR AJUSTE en:\n"
            "• Asignación inicial de procesos\n"
            "• Fragmentación acumulada\n"
            "• Capacidad para procesos grandes\n\n"
            "Secuencia: [10, 5, 8, 3, 12, 4, 6, 7, 2, 9, 3, 5]\n\n"
            "Presiona 'Iniciar Demo' para comenzar..."
        )
        
        self.current_demo_sizes = [10, 5, 8, 3, 12, 4, 6, 7, 2, 9, 3, 5]
        self.current_demo_name = "Análisis de eficiencia"
        self.start_demo_button.config(state=tk.NORMAL)
    
    def show_demo_info(self, text):
        """Muestra información de la demo en el área de estadísticas"""
        self.stats_label.config(text="DEMO CONFIGURADA - Presiona 'Iniciar Demo' para comenzar")
        
        # Mostrar información en el historial
        self.history_text.delete(1.0, tk.END)
        self.history_text.insert(1.0, f"=== CONFIGURACIÓN DE DEMO ===\n{text}")
    
    def start_demo_execution(self):
        """Inicia la ejecución de la demo cuando se presiona el botón"""
        if not self.current_demo_sizes:
            messagebox.showinfo("Error", "No hay demo configurada. Selecciona una demo primero.")
            return
            
        self.demo_running = True
        self.start_demo_button.config(state=tk.DISABLED)
        self.memory_manager.history.append(f"=== INICIO DEMO: {self.current_demo_name} ===")
        self.execute_demo_steps(0)
    
    def execute_demo_steps(self, index):
        """Ejecuta los pasos de la demo"""
        if index >= len(self.current_demo_sizes):
            self.demo_running = False
            self.memory_manager.history.append("=== DEMO COMPLETADA ===")
            self.update_display()
            self.stats_label.config(text="DEMO COMPLETADA - Selecciona otra demo o agrega procesos manualmente")
            return
        
        size = self.current_demo_sizes[index]
        self.process_counter += 1
        process_name = f"P{self.process_counter}"
        
        self.memory_manager.worst_fit(process_name, size)
        self.update_display()
        
        # Actualizar estadísticas durante la demo
        used_memory = sum(1 for cell in self.memory_manager.memory if cell is not None)
        usage_percentage = (used_memory / len(self.memory_manager.memory)) * 100
        self.stats_label.config(text=f"Demo en progreso... ({index + 1}/{len(self.current_demo_sizes)}) - Memoria usada: {usage_percentage:.1f}%")
        
        # Siguiente paso con retardo
        self.root.after(1000, lambda: self.execute_demo_steps(index + 1))
    
    # ========== FUNCIONES PRINCIPALES ==========
    
    def add_process(self):
        """Agrega un proceso usando Peor Ajuste"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Espera a que termine la demo actual.")
            return
            
        try:
            size = int(self.size_var.get())
            if size <= 0:
                messagebox.showerror("Error", "El tamaño debe ser mayor a 0")
                return
            
            self.process_counter += 1
            process_name = f"P{self.process_counter}"
            
            result = self.memory_manager.worst_fit(process_name, size)
            
            if result == -1:
                messagebox.showwarning("Sin memoria", 
                    f"No hay espacio suficiente para el proceso {process_name} (tamaño {size})\n"
                    f"Bloque libre más grande: {self.memory_manager.get_largest_free_block()}")
                self.process_counter -= 1
            else:
                self.update_display()
                
        except ValueError:
            messagebox.showerror("Error", "Tamaño inválido")
    
    def free_random(self):
        """Libera un proceso aleatorio"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Espera a que termine la demo actual.")
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
        """Limpia toda la memoria"""
        if self.demo_running:
            messagebox.showinfo("Demo en curso", "Espera a que termine la demo actual.")
            return
            
        self.memory_manager = MemoryManager(50)
        self.process_counter = 0
        self.demo_running = False
        self.current_demo_sizes = []
        self.current_demo_name = ""
        self.start_demo_button.config(state=tk.DISABLED)
        self.update_display()
        self.stats_label.config(text="Sistema reiniciado - Selecciona una demo o agrega procesos manualmente")
    
    def update_display(self):
        """Actualiza toda la visualización"""
        self.canvas.delete("all")
        
        # Colores para procesos
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                 '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        # Dibujar memoria
        cell_width = max(15, self.canvas.winfo_width() / len(self.memory_manager.memory))
        cell_height = 35
        
        for i, process in enumerate(self.memory_manager.memory):
            x1 = i * cell_width
            y1 = 20
            x2 = (i + 1) * cell_width
            y2 = y1 + cell_height
            
            if process is None:
                color = '#F8F9FA'  # Gris muy claro para espacios libres
                text = ""
                outline = '#DEE2E6'
            else:
                process_num = int(process[1:]) if process[1:].isdigit() else 0
                color = colors[process_num % len(colors)]
                text = process
                outline = '#343A40'
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=1)
            if text and cell_width > 20:
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, 
                                      font=('Arial', 9, 'bold'), fill='#212529')
        
        # Actualizar estadísticas (solo si no hay demo en curso)
        if not self.demo_running:
            fragmentation = self.memory_manager.get_fragmentation()
            largest_block = self.memory_manager.get_largest_free_block()
            used_memory = sum(1 for cell in self.memory_manager.memory if cell is not None)
            usage_percentage = self.memory_manager.get_memory_usage()
            
            stats_text = f"PEOR AJUSTE | Memoria usada: {used_memory}/50 ({usage_percentage:.1f}%) | "
            stats_text += f"Fragmentación: {fragmentation} bloques | Mayor bloque libre: {largest_block}"
            
            # Color según el nivel de fragmentación
            if fragmentation > 8:
                stats_text += " ⚠️ ALTA FRAGMENTACIÓN"
            elif fragmentation > 4:
                stats_text += " ⚠️ Fragmentación moderada"
            
            self.stats_label.config(text=stats_text)
        
        # Actualizar historial
        self.history_text.delete(1.0, tk.END)
        for entry in self.memory_manager.history[-10:]:
            self.history_text.insert(tk.END, f"{entry}\n")
        self.history_text.see(tk.END)

def main():
    root = tk.Tk()
    app = MemorySimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()