import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import numpy as np


class GraphicObject(ABC):
    _counter = 0  # Contador estático compartilhado
    
    def __init__(self, coordinates):
        self.coordinates = coordinates
        self._name = None
        self._generate_name()
        
    def _generate_name(self):
        GraphicObject._counter += 1
        self._name = f"{self.prefix}{GraphicObject._counter}"
    
    @property
    @abstractmethod
    def prefix(self):
        pass
    
    @property
    def name(self):
        return self._name
    
    @property
    @abstractmethod
    def type(self):
        pass
    
    @abstractmethod
    def draw(self, canvas, transform):
        pass

    def get_coordinates(self, transform):
        coords = []
        for x, y in self.coordinates:
            vx, vy = transform(x, y)
            coords.extend([vx, vy])
        if len(self.coordinates) >= 3:
            x0, y0 = self.coordinates[0]
            vx0, vy0 = transform(x0, y0)
            coords.extend([vx0, vy0])
        return coords

    @classmethod
    def reset_counter(cls):
        cls._counter = 0


class Point(GraphicObject):
    prefix = "P"
    
    def __init__(self, coordinates):
        super().__init__(coordinates)
    
    @property
    def type(self):
        return "Ponto"
    
    def draw(self, canvas, transform):
        vx, vy = self.get_coordinates(transform)
        canvas.create_oval(vx-6, vy-6, vx+6, vy+6, 
                         fill="#00ff88", outline="#005533", width=2)


class Line(GraphicObject):
    prefix = "L"
    
    def __init__(self, coordinates):
        super().__init__(coordinates)
    
    @property
    def type(self):
        return "Linha"
    
    def draw(self, canvas, transform):
        vx1, vy1, vx2, vy2 = self.get_coordinates(transform)
        canvas.create_line(vx1, vy1, vx2, vy2, 
                         fill="#00aaff", width=3, capstyle=tk.ROUND)


class Polygon(GraphicObject):
    prefix = "W"
    
    def __init__(self, coordinates):
        super().__init__(coordinates)
    
    @property
    def type(self):
        return "Polígono"
    
    def draw(self, canvas, transform):
        coords = self.get_coordinates(transform)
        canvas.create_polygon(coords, fill="", outline="#ffaa00", width=2)


class GraphicsSystem:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#2d2d2d")
        self.root.wm_minsize(1020, 680)
        
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
                              bg="#1a1a1a",
                              highlightthickness=0)
        self.canvas.pack(pady=10, fill=tk.BOTH, expand=True)


    def _create_object_list(self):
        self.list_frame = ttk.Frame(self.content_frame)
        self.list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        self.object_tree = ttk.Treeview(self.list_frame,
                                        columns=("type", "name"),
                                        show="headings")
        self.object_tree.heading("type", text="Tipo")
        self.object_tree.heading("name", text="Nome")
        self.object_tree.column("type", width=100)
        self.object_tree.column("name", width=80)
        self.object_tree.pack(fill=tk.BOTH, expand=True)


    def _create_controls(self):
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self._create_view_controls()
        self._create_separator()
        self._create_move_controls()
        self._create_separator()
        self._create_object_controls()
    

    def _create_view_controls(self):
        view_frame = ttk.Frame(self.control_frame)
        view_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        view_label = ttk.Label(view_frame, text="Controle de Zoom", style="Title.TLabel")
        view_label.grid(row=0, column=0, pady=5)

        ttk.Button(view_frame, text="+ Zoom", 
                command=lambda: self.zoom_manual(0.9)).grid(row=1, column=0, pady=2)
        ttk.Button(view_frame, text="- Zoom", 
                command=lambda: self.zoom_manual(1.1)).grid(row=2, column=0, pady=2)
        ttk.Button(view_frame, text="Resetar", 
                command=self.reset_view).grid(row=3, column=0, pady=2)


    def _create_move_controls(self):
        move_frame = ttk.Frame(self.control_frame)
        move_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

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


    def _create_object_controls(self):
        obj_frame = ttk.Frame(self.control_frame)
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

        ttk.Button(clear_buttons_frame, text="Aplicar Transformações", 
                command=self.open_transformations_menu).pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Apagar Selecionado", 
                command=self.delete_selected, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Limpar Tudo", 
                command=self.clear_canvas, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)


    def _create_separator(self):
        separator = ttk.Separator(self.control_frame, orient="vertical")
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)


    def _bind_events(self):
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-2>", lambda e: self.pan(e, "start"))
        self.canvas.bind("<B2-Motion>", lambda e: self.pan(e, "drag"))
        

    def _update_object_list(self):
        self.object_tree.delete(*self.object_tree.get_children())
        for obj in self.display_file:
            self.object_tree.insert("", "end", values=(obj.type, obj.name))


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
        GraphicObject.reset_counter()
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
                if obj.name == selected_name:
                    del self.display_file[i]
                    self._update_object_list()
                    self.redraw()
                    break
    
    def open_transformations_menu(self):
        selected_items = self.object_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.object_tree.item(selected_item, "values")
            selected_name = item_values[1]

            # Janela de transformações
            trans_window = tk.Toplevel(self.root)
            trans_window.title("Transformações 2D")
            
            # Translação
            ttk.Label(trans_window, text="Translação", style="Title.TLabel").pack(pady=10)
            
            ttk.Label(trans_window, text="Deslocamento em X:").pack(pady=5)
            x_entry_translation = ttk.Entry(trans_window)
            x_entry_translation.pack(pady=5)
            
            ttk.Label(trans_window, text="Deslocamento em Y:").pack(pady=5)
            y_entry_translation = ttk.Entry(trans_window)
            y_entry_translation.pack(pady=5)

            ttk.Button(trans_window, text="Aplicar Translação", command=lambda: self.apply_translation(selected_name, x_entry_translation.get(), y_entry_translation.get())).pack(pady=10)

            # Escalonamento
            ttk.Label(trans_window, text="Escalonamento", style="Title.TLabel").pack(pady=10)
            
            ttk.Label(trans_window, text="Deslocamento em X:").pack(pady=5)
            x_entry_scaling = ttk.Entry(trans_window)
            x_entry_scaling.pack(pady=5)
            
            ttk.Label(trans_window, text="Deslocamento em Y:").pack(pady=5)
            y_entry_scaling = ttk.Entry(trans_window)
            y_entry_scaling.pack(pady=5)

            ttk.Button(trans_window, text="Aplicar Escalonamento", command=lambda: self.apply_scaling(selected_name, x_entry_scaling.get(), y_entry_scaling.get())).pack(pady=10)
            
        else:
            messagebox.showwarning("Nenhum objeto selecionado", "Por favor, selecione um objeto para aplicar as transformações.")
        
    def apply_translation(self, selected_name, x_str, y_str):
        try:
            dx = float(x_str)
            dy = float(y_str)
            
            for i, obj in enumerate(self.display_file):
                if obj.name == selected_name:
                    new_coordinates = []
                    for x, y in obj.coordinates:
                        new_x = x + dx
                        new_y = y + dy

                        new_coordinates.append((new_x, new_y))
                    obj.coordinates = new_coordinates
                    self.redraw()
                    break

        except ValueError:
            messagebox.showerror("Erro de Entrada", "Por favor, insira valores válidos para X e Y.")

    
    def apply_scaling(self, selected_name, x_str, y_str):
        try:
            sx = float(x_str)
            sy = float(y_str)
            
            for i, obj in enumerate(self.display_file):
                if obj.name == selected_name:
                    cx, cy = self.get_object_center(obj.coordinates)

                    new_coordinates = []
                    for x, y in obj.coordinates:
                        matrix1 = np.array([[x, y, 1]])
                        matrix2 = np.array([[1, 0, 0], [0, 1, 0], [-cx, -cy, 1]])
                        matrix3 = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]])
                        matrix4 = np.array([[1, 0, 0], [0, 1, 0], [cx, cy, 1]])
                        matrix  = matrix1 @ matrix2 @ matrix3 @ matrix4

                        new_x = matrix[0,0]
                        new_y = matrix[0,1]

                        new_coordinates.append((new_x, new_y))
                    obj.coordinates = new_coordinates
                    self.redraw()
                    break

        except ValueError:
            messagebox.showerror("Erro de Entrada", "Por favor, insira valores válidos para X e Y.")

    
    def get_object_center(self, object_coordinates):
        total_x, total_y = zip(*object_coordinates)
        array_length = len(object_coordinates)

        cx = sum(total_x) / array_length
        cy = sum(total_y) / array_length
        
        return cx, cy


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
            ponto = Point(coords)
            self.display_file.append(ponto)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Ponto, insira apenas uma coordenada.")

    def add_line(self):
        coords = self.parse_input()
        if len(coords) == 2:
            linha = Line(coords)
            self.display_file.append(linha)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar uma Linha, insira exatamente duas coordenadas.")

    def add_polygon(self):
        coords = self.parse_input()
        if len(coords) >= 3:
            poligono = Polygon(coords)
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
            obj.draw(self.canvas, self.viewport_transform)

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
    root.geometry("1020x680")
    app = GraphicsSystem(root)
    root.mainloop()