import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod

class ObjetoGrafico(ABC):
    _contador = 0  # Contador estático compartilhado
    
    def __init__(self):
        self._nome = None
        self._gerar_nome()
        
    def _gerar_nome(self):
        ObjetoGrafico._contador += 1
        self._nome = f"{self.prefixo}{ObjetoGrafico._contador}"
    
    @property
    @abstractmethod
    def prefixo(self):
        pass
    
    @property
    def nome(self):
        return self._nome
    
    @property
    @abstractmethod
    def tipo(self):
        pass
    
    @abstractmethod
    def desenhar(self, canvas, transform):
        pass

    @classmethod
    def reset_contador(cls):
        cls._contador = 0


class Ponto(ObjetoGrafico):
    prefixo = "P"
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        super().__init__()
    
    @property
    def tipo(self):
        return "Ponto"
    
    def desenhar(self, canvas, transform):
        vx, vy = transform(self.x, self.y)
        canvas.create_oval(vx-6, vy-6, vx+6, vy+6, 
                         fill="#00ff88", outline="#005533", width=2)


class Linha(ObjetoGrafico):
    prefixo = "L"
    
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        super().__init__()
    
    @property
    def tipo(self):
        return "Linha"
    
    def desenhar(self, canvas, transform):
        vx1, vy1 = transform(self.x1, self.y1)
        vx2, vy2 = transform(self.x2, self.y2)
        canvas.create_line(vx1, vy1, vx2, vy2, 
                         fill="#00aaff", width=3, capstyle=tk.ROUND)


class Poligono(ObjetoGrafico):
    prefixo = "W"
    
    def __init__(self, coordenadas):
        self.coordenadas = coordenadas
        super().__init__()
    
    @property
    def tipo(self):
        return "Polígono"
    
    def desenhar(self, canvas, transform):
        coords = []
        for x, y in self.coordenadas:
            vx, vy = transform(x, y)
            coords.extend([vx, vy])
        if len(self.coordenadas) >= 3:
            x0, y0 = self.coordenadas[0]
            vx0, vy0 = transform(x0, y0)
            coords.extend([vx0, vy0])
        canvas.create_polygon(coords, fill="", outline="#ffaa00", width=2)


class GraphicsSystem:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#2d2d2d")
        
        # Configurações iniciais
        self.window = {"xmin": -50, "ymin": -50, "xmax": 50, "ymax": 50}
        self.original_window = self.window.copy()
        self.viewport = {"xmin": 50, "ymin": 50, "xmax": 850, "ymax": 650}
        self.display_file = []
        self.move_step = 0.1
        
        # Configuração do tema
        self.style = ttk.Style()
        self.style.theme_use("alt")
        self._configure_styles()
        
        # Configuração da interface
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Área principal
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_canvas()
        self._create_object_list()
        self._create_controls()
        self._bind_events()


    def _configure_styles(self):
        self.style.configure("TFrame", background="#2d2d2d")
        self.style.configure("TButton",
                             background="#262523",
                             foreground="white",
                             padding=5,
                             font=("Helvetica", 10, "bold"))
        self.style.map("TButton", background=[("active", "#4d4d4d")])
        self.style.configure("TEntry",
                             fieldbackground="#3d3d3d",
                             foreground="white")
        self.style.configure("Treeview",
                             background="#2d2d2d",
                             foreground="white",
                             fieldbackground="#2d2d2d")
        self.style.configure("Treeview.Heading",
                             background="#3d3d3d",
                             foreground="white")
        self.style.configure("DeleteButton.TButton",
                             background="#a60c0c",
                             foreground="white",
                             font=("Helvetica", 10, "bold"),
                             padding=10,
                             width=20)
        self.style.map("DeleteButton.TButton", background=[("active", "#800808")])
        self.style.configure("TSeparator", background="#4d4a49")
        self.style.configure("Title.TLabel", 
                             background="#2d2d2d", 
                             foreground="white", 
                             font=("Helvetica", 12, "bold"))
        self.style.configure("CoordsLabel.TLabel", 
                             background="#2d2d2d", 
                             foreground="white")


    def _create_canvas(self):
        self.canvas_frame = ttk.Frame(self.content_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, 
                              width=600, 
                              height=600,
                              bg="#1a1a1a",
                              highlightthickness=0)
        self.canvas.pack(pady=10, fill=tk.BOTH, expand=True)


    def _create_object_list(self):
        self.list_frame = ttk.Frame(self.content_frame)
        self.list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        self.object_tree = ttk.Treeview(self.list_frame, 
                                    columns=("type", "name"), 
                                    show="headings",
                                    height=25)
        self.object_tree.heading("type", text="Tipo")
        self.object_tree.heading("name", text="Nome")
        self.object_tree.column("type", width=100)
        self.object_tree.column("name", width=80)
        self.object_tree.pack(fill=tk.BOTH, expand=True)
        

    def _create_controls(self):
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self._create_view_controls(control_frame)
        self._create_separator(control_frame)
        self._create_move_controls(control_frame)
        self._create_separator(control_frame)
        self._create_object_controls(control_frame)


    def _create_view_controls(self, parent_frame):
        view_frame = ttk.Frame(parent_frame)
        view_frame.pack(side=tk.LEFT, padx=5)

        view_label = ttk.Label(view_frame, text="Controle de Zoom", style="Title.TLabel")
        view_label.grid(row=0, column=0, pady=5)

        ttk.Button(view_frame, text="+ Zoom", 
                command=lambda: self.zoom_manual(0.9)).grid(row=1, column=0, pady=2)
        ttk.Button(view_frame, text="- Zoom", 
                command=lambda: self.zoom_manual(1.1)).grid(row=2, column=0, pady=2)
        ttk.Button(view_frame, text="Resetar", 
                command=self.reset_view).grid(row=3, column=0, pady=2)


    def _create_move_controls(self, parent_frame):
        move_frame = ttk.Frame(parent_frame)
        move_frame.pack(side=tk.LEFT, padx=5)

        move_label = ttk.Label(move_frame, text="Controle de Movimento", style="Title.TLabel")
        move_label.grid(row=0, column=0, pady=5, columnspan=3)

        move_frame.grid_columnconfigure(0, weight=1)
        move_frame.grid_columnconfigure(1, weight=1)
        move_frame.grid_columnconfigure(2, weight=1)
        move_frame.grid_rowconfigure(1, weight=1)
        move_frame.grid_rowconfigure(2, weight=1)
        move_frame.grid_rowconfigure(3, weight=1)

        ttk.Button(move_frame, text="↑", 
                command=lambda: self.move_window("up")).grid(row=1, column=1, padx=2, pady=2, sticky="nsew")
        ttk.Button(move_frame, text="↓", 
                command=lambda: self.move_window("down")).grid(row=3, column=1, padx=2, pady=2, sticky="nsew")
        ttk.Button(move_frame, text="←", 
                command=lambda: self.move_window("left")).grid(row=2, column=0, padx=2, pady=2, sticky="nsew")
        ttk.Button(move_frame, text="→", 
                command=lambda: self.move_window("right")).grid(row=2, column=2, padx=2, pady=2, sticky="nsew")


    def _create_object_controls(self, parent_frame):
        obj_frame = ttk.Frame(parent_frame)
        obj_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        obj_label = ttk.Label(obj_frame, text="Adicionar Objetos", style="Title.TLabel")
        obj_label.pack(side=tk.TOP, pady=5)

        coords_label = ttk.Label(obj_frame, text="Insira as coordenadas no formato \"(x1, y1), (x2, y2), ...\":", style="CoordsLabel.TLabel")
        coords_label.pack(side=tk.TOP, pady=5)

        self.coord_entry = ttk.Entry(obj_frame, width=40)
        self.coord_entry.pack(side=tk.TOP, padx=5, fill=tk.X, expand=False)

        # Botões de Adição de Objetos (Ponto, Linha, Polígono)
        button_frame = ttk.Frame(obj_frame)
        button_frame.pack(side=tk.TOP, pady=10)

        ttk.Button(button_frame, text="Ponto", 
                command=self.add_point).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Linha", 
                command=self.add_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Polígono", 
                command=self.add_polygon).pack(side=tk.LEFT, padx=2)

        # Botões de limpar
        clear_buttons_frame = ttk.Frame(self.list_frame)
        clear_buttons_frame.pack(side=tk.BOTTOM, pady=10)

        ttk.Button(clear_buttons_frame, text="Apagar Selecionado", 
                command=self.delete_selected, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Limpar Tudo", 
                command=self.clear_canvas, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)


    def _create_separator(self, parent_frame):
        separator = ttk.Separator(parent_frame, orient="vertical")
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)


    def _bind_events(self):
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-2>", lambda e: self.pan(e, "start"))
        self.canvas.bind("<B2-Motion>", lambda e: self.pan(e, "drag"))
        

    def _update_object_list(self):
        self.object_tree.delete(*self.object_tree.get_children())
        for obj in self.display_file:
            self.object_tree.insert("", "end", values=(obj.tipo, obj.nome))


    def move_window(self, direction):
        delta_x = (self.window["xmax"] - self.window["xmin"]) * self.move_step
        delta_y = (self.window["ymax"] - self.window["ymin"]) * self.move_step
        
        if direction == "up":
            self.window["ymin"] += delta_y
            self.window["ymax"] += delta_y
        elif direction == "down":
            self.window["ymin"] -= delta_y
            self.window["ymax"] -= delta_y
        elif direction == "left":
            self.window["xmin"] -= delta_x
            self.window["xmax"] -= delta_x
        elif direction == "right":
            self.window["xmin"] += delta_x
            self.window["xmax"] += delta_x
            
        self.redraw()


    def reset_view(self):
        self.window = self.original_window.copy()
        self.redraw()


    def clear_canvas(self):
        self.display_file = []
        ObjetoGrafico.reset_contador()
        self.coord_entry.delete(0, tk.END)
        self._update_object_list()
        self.redraw()


    def delete_selected(self):
        selected_items = self.object_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.object_tree.item(selected_item, "values")
            selected_name = item_values[1]  # Obtém o nome do objeto
            
            # Procura o objeto pelo nome na display_file
            for i, obj in enumerate(self.display_file):
                if obj.nome == selected_name:
                    del self.display_file[i]
                    self._update_object_list()
                    self.redraw()
                    break


    def viewport_transform(self, x, y):
        window_aspect = (self.window["xmax"] - self.window["xmin"]) / (self.window["ymax"] - self.window["ymin"])
        viewport_aspect = (self.viewport["xmax"] - self.viewport["xmin"]) / (self.viewport["ymax"] - self.viewport["ymin"])
        
        scale = (self.viewport["xmax"] - self.viewport["xmin"]) / (self.window["xmax"] - self.window["xmin"]) if window_aspect > viewport_aspect else (
            self.viewport["ymax"] - self.viewport["ymin"]) / (self.window["ymax"] - self.window["ymin"])
        
        return (
            self.viewport["xmin"] + (x - self.window["xmin"]) * scale,
            self.viewport["ymin"] + (self.window["ymax"] - y) * scale
        )

    def add_point(self):
        coords = self.parse_input()
        if len(coords) == 1:
            ponto = Ponto(*coords[0])
            self.display_file.append(ponto)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Ponto, insira apenas uma coordenada.")

    def add_line(self):
        coords = self.parse_input()
        if len(coords) == 2:
            linha = Linha(*coords[0], *coords[1])
            self.display_file.append(linha)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar uma Linha, insira exatamente duas coordenadas.")

    def add_polygon(self):
        coords = self.parse_input()
        if len(coords) >= 3:
            poligono = Poligono(coords)
            self.display_file.append(poligono)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Polígono, insira pelo menos três coordenadas.")

    def pan(self, event, action):
        if action == "start":
            self.last_pan = (event.x, event.y)
        elif action == "drag":
            dx = (event.x - self.last_pan[0]) * (self.window["xmax"] - self.window["xmin"]) / self.viewport["xmax"]
            dy = (event.y - self.last_pan[1]) * (self.window["ymax"] - self.window["ymin"]) / self.viewport["ymax"]
            
            self.window["xmin"] -= dx
            self.window["xmax"] -= dx
            self.window["ymin"] += dy
            self.window["ymax"] += dy
            
            self.last_pan = (event.x, event.y)
            self.redraw()

    def zoom(self, event):
        factor = 0.9 if event.delta > 0 else 1.1
        mx = self.window["xmin"] + (event.x / self.viewport["xmax"]) * (self.window["xmax"] - self.window["xmin"])
        my = self.window["ymin"] + ((self.viewport["ymax"] - event.y) / self.viewport["ymax"]) * (self.window["ymax"] - self.window["ymin"])
        
        self.window["xmin"] = mx - (mx - self.window["xmin"]) * factor
        self.window["xmax"] = mx + (self.window["xmax"] - mx) * factor
        self.window["ymin"] = my - (my - self.window["ymin"]) * factor
        self.window["ymax"] = my + (self.window["ymax"] - my) * factor
        
        self.redraw()

    def zoom_manual(self, factor):
        cx = (self.window["xmin"] + self.window["xmax"]) / 2
        cy = (self.window["ymin"] + self.window["ymax"]) / 2
        
        self.window["xmin"] = cx - (cx - self.window["xmin"]) * factor
        self.window["xmax"] = cx + (self.window["xmax"] - cx) * factor
        self.window["ymin"] = cy - (cy - self.window["ymin"]) * factor
        self.window["ymax"] = cy + (self.window["ymax"] - cy) * factor
        
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for obj in self.display_file:
            obj.desenhar(self.canvas, self.viewport_transform)

    def parse_input(self):
        try:
            input_str = self.coord_entry.get().strip()
            if input_str:
                return list(eval(f"[{input_str.replace(" ", "").replace(")(", "),(")}]"))
            return []
        except:
            messagebox.showerror("Erro de Entrada", "Coordenadas inválidas! Por favor, insira coordenadas no formato correto.")
            return []

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema Gráfico 2D com Lista de Objetos")
    root.geometry("1200x800")
    app = GraphicsSystem(root)
    root.mainloop()