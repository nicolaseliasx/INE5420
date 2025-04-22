import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from tkinter import filedialog
import numpy as np
import math
from tkinter.colorchooser import askcolor

class GraphicObject(ABC):
    _counter = 0  # Contador estático compartilhado
    
    def __init__(self, coordinates, color="#00aaff"):
        self.coordinates = coordinates
        self.color = color
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
    
    def __init__(self, coordinates, color="#00aaff"):
        super().__init__(coordinates, color)
    
    @property
    def type(self):
        return "Ponto"
    
    def draw(self, canvas, transform):
        vx, vy = self.get_coordinates(transform)
        canvas.create_oval(vx-6, vy-6, vx+6, vy+6, 
                         fill=self.color, outline="#005533", width=2)

class Line(GraphicObject):
    prefix = "L"
    
    def __init__(self, coordinates, color="#00aaff"):
        super().__init__(coordinates, color)
    
    @property
    def type(self):
        return "Linha"
    
    def draw(self, canvas, transform):
        vx1, vy1, vx2, vy2 = self.get_coordinates(transform)
        canvas.create_line(vx1, vy1, vx2, vy2, 
                         fill=self.color, width=3, capstyle=tk.ROUND)

class Polygon(GraphicObject):
    prefix = "W"
    
    def __init__(self, coordinates, color="#ffaa00", filled=False):
        super().__init__(coordinates, color)
        self.filled = filled
    
    @property
    def type(self):
        return "Polígono"
    
    def draw(self, canvas, transform):
        coords = self.get_coordinates(transform)
        canvas.create_polygon(coords, fill=self.color if self.filled else "", outline=self.color, width=2)

class Curve2D(GraphicObject):
    prefix = "C"
    
    def __init__(self, coordinates, color="#00aaff"):
        super().__init__(coordinates, color)
        self.clipped_segments = []
    
    @property
    def type(self):
        return "Curva Bezier"
    
    def draw(self, canvas, transform):
        for segment in self.clipped_segments:
            points = self.compute_bezier_points(segment)
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i+1]
                vx1, vy1 = transform(x1, y1)
                vx2, vy2 = transform(x2, y2)
                canvas.create_line(vx1, vy1, vx2, vy2, 
                                 fill=self.color, width=3, capstyle=tk.ROUND)

    def get_bezier_segments(self):
        segments = []
        n = len(self.coordinates)
        if n < 4:
            return []
        i = 0
        while i + 3 < n:
            segments.append(self.coordinates[i:i+4])
            i += 3
        return segments

    def compute_bezier_points(self, control_points, steps=20):
        points = []
        for t in np.linspace(0, 1, steps):
            x = ( (1-t)**3 * control_points[0][0] +
                  3*(1-t)**2 * t * control_points[1][0] +
                  3*(1-t)*t**2 * control_points[2][0] +
                  t**3 * control_points[3][0] )
            y = ( (1-t)**3 * control_points[0][1] +
                  3*(1-t)**2 * t * control_points[1][1] +
                  3*(1-t)*t**2 * control_points[2][1] +
                  t**3 * control_points[3][1] )
            points.append((x, y))
        return points

    def clip(self, clip_window, max_depth=8):
        self.clipped_segments = []
        segments = self.get_bezier_segments()
        for segment in segments:
            self._clip_segment(segment, clip_window, max_depth)

    def _clip_segment(self, segment, clip_window, depth):
        if depth == 0:
            if self._is_visible(segment, clip_window):
                self.clipped_segments.append(segment)
            return

        if self._is_fully_inside(segment, clip_window):
            self.clipped_segments.append(segment)
            return

        left, right = self._de_casteljau_split(segment)
        self._clip_segment(left, clip_window, depth-1)
        self._clip_segment(right, clip_window, depth-1)

    def _is_fully_inside(self, segment, window):
        xmin, ymin = window["xmin"], window["ymin"]
        xmax, ymax = window["xmax"], window["ymax"]
        for (x, y) in segment:
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                return False
        return True

    def _is_visible(self, segment, window):
        xmin, ymin = window["xmin"], window["ymin"]
        xmax, ymax = window["xmax"], window["ymax"]
        
        for t in np.linspace(0, 1, 10):
            x = ( (1-t)**3 * segment[0][0] +
                  3*(1-t)**2 * t * segment[1][0] +
                  3*(1-t)*t**2 * segment[2][0] +
                  t**3 * segment[3][0] )
            y = ( (1-t)**3 * segment[0][1] +
                  3*(1-t)**2 * t * segment[1][1] +
                  3*(1-t)*t**2 * segment[2][1] +
                  t**3 * segment[3][1] )
            if xmin <= x <= xmax and ymin <= y <= ymax:
                return True
        return False

    def _de_casteljau_split(self, control_points):
        points = [control_points]
        while len(points[-1]) > 1:
            new_points = []
            for i in range(len(points[-1])-1):
                x0, y0 = points[-1][i]
                x1, y1 = points[-1][i+1]
                new_points.append((
                    (x0 + x1)/2,
                    (y0 + y1)/2
                ))
            points.append(new_points)
        
        left = [points[i][0] for i in range(len(points))]
        right = [points[i][-1] for i in reversed(range(len(points)))]
        
        return left, right

class DescritorOBJ:
    @staticmethod
    def read_obj(filename):
        display_file = []
        vertices = []
        color_map = {}  # Mapeia nomes de objetos para cores
        fill_map = {}  # Mapeia nome do polígono para saber se é preenchido ou não
        elements = []    # Lista de elementos (p, l, f) com seus nomes
        current_name = None

        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if not parts:
                    continue

                # Processamento de vértices
                if parts[0] == 'v':
                    x, y = map(float, parts[1:3])
                    vertices.append((x, y))

                # Processamento de cores
                elif parts[0] == 'c' and len(parts) >= 3:
                    color_map[parts[1]] = parts[2]
                
                # Processamento do preenchimento do polígono
                elif parts[0] == 'fill' and len(parts) >= 3:
                    nome = parts[1]
                    valor = parts[2].lower() == 'true'
                    fill_map[nome] = valor

                # Processamento de elementos gráficos
                elif parts[0] in ['p', 'l', 'f']:
                    element_type = parts[0]
                    indices = [int(part.split('/')[0]) for part in parts[1:]]
                    elements.append((element_type, indices))

        # Criar objetos gráficos
        max_counter = 0
        for i, (elem_type, indices) in enumerate(elements):
            # Obter coordenadas reais (índices são 1-based)
            coords = [vertices[idx-1] for idx in indices]
            
            # Gerar nome sequencial (P1, L2, W3, W4, etc)
            obj_prefix = {
                'p': 'P',
                'l': 'L',
                'f': 'W'
            }[elem_type]
            obj_number = i + 1
            name = f"{obj_prefix}{obj_number}"
            
            # Criar objeto com a cor correspondente
            color = color_map.get(name, "#00aaff")

            if elem_type == 'p' and len(coords) == 1:
                obj = Point(coords, color)
            elif elem_type == 'l' and len(coords) == 2:
                obj = Line(coords, color)
            elif elem_type == 'f' and len(coords) >= 3:
                fill = fill_map.get(name, True)
                obj = Polygon(coords, color, fill)
            else:
                continue  # Ignora elementos inválidos

            # Atualizar nome e contador
            obj._name = name
            max_counter = max(max_counter, obj_number)
            display_file.append(obj)

        # Atualizar contador global de objetos
        GraphicObject._counter = max_counter

        return display_file
    
    @staticmethod
    def write_obj(display_file, filename):
        try:
            if not display_file:
                raise ValueError("Não há objetos para salvar")

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Sistema Gráfico - Arquivo OBJ\n")
                f.write("o CenaCompleta\n")  # Um único objeto para toda a cena

                # Escreve todos os vértices primeiro
                vertex_index = 1
                all_vertices = []  # Armazena todos os vértices em ordem
                vertex_map = {}    # Evita vértices duplicados

                for obj in display_file:
                    for coord in obj.coordinates:
                        if coord not in vertex_map:
                            all_vertices.append(coord)
                            vertex_map[coord] = vertex_index
                            vertex_index += 1

                # Escreve vértices no arquivo
                for x, y in all_vertices:
                    f.write(f"v {x:.2f} {y:.2f} 0.0\n")

                # Escreve cores personalizadas (formato extendido)
                for obj in display_file:
                    f.write(f"c {obj.name} {obj.color}\n")

                # Escreve elementos (pontos, linhas, polígonos)
                for obj in display_file:
                    # Obtém índices dos vértices do objeto
                    indices = [str(vertex_map[coord]) for coord in obj.coordinates]
                    
                    if isinstance(obj, Point):
                        f.write(f"p {' '.join(indices)}\n")
                    elif isinstance(obj, Line):
                        f.write(f"l {' '.join(indices)}\n")
                    elif isinstance(obj, Polygon):
                        f.write(f"f {' '.join(indices)}\n")
                        f.write(f"fill {obj.name} {str(obj.filled)}\n")
                    else:
                        raise TypeError(f"Tipo inválido: {type(obj)}")

                f.write("\n# Fim do arquivo\n")
                return True

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
            return False

class GraphicsSystem:
    CANVAS_WIDTH = 775
    CANVAS_HEIGHT = 383
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#2d2d2d")
        self.root.wm_minsize(1020, 700)
        self.selected_color = "#00aaff"  # Cor padrão
        
        # Configurações iniciais
        self.viewport = {"xmin": 20, "ymin": 20, "xmax": self.CANVAS_WIDTH - 20, "ymax": self.CANVAS_HEIGHT - 20}

        vp_width = self.viewport["xmax"] - self.viewport["xmin"]
        vp_height = self.viewport["ymax"] - self.viewport["ymin"]
        half_width = vp_width / 2
        half_height = vp_height / 2

        self.window = {
            "xmin": -half_width,
            "ymin": -half_height,
            "xmax": half_width,
            "ymax": half_height,
            "rotation": 0
        }
        self.original_window = self.window.copy()

        self.display_file = []
        self.move_step = 0.1
        self.temp_transformations = []  # Lista temporária para transformações
        self.line_clip_method = tk.StringVar(value="CS")
        
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
        self._draw_viewport()
        self._create_object_list()
        self._create_controls()
        self._bind_events()

        # Adicionar elementos de interface para rotação
        self._create_rotation_controls()
        self._create_file_controls()

    def _create_rotation_controls(self):
        rotation_frame = ttk.Frame(self.control_frame)
        rotation_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Label(rotation_frame, text="Rotação Window", style="Title.TLabel").grid(row=0, column=0, pady=5)
        
        self.rotation_entry = ttk.Entry(rotation_frame, width=8)
        self.rotation_entry.grid(row=1, column=0, padx=2)
        ttk.Button(rotation_frame, text="Aplicar", 
                 command=self.apply_window_rotation).grid(row=1, column=1, padx=2)

    def _create_file_controls(self):
        file_frame = ttk.Frame(self.control_frame)
        file_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(file_frame, text="Salvar OBJ", 
                 command=self.save_obj).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Carregar OBJ", 
                 command=self.load_obj).pack(side=tk.LEFT, padx=2)
        
    def apply_window_rotation(self):
        try:
            angle = float(self.rotation_entry.get())
            self.window["rotation"] = math.radians(angle)
            self.redraw()
        except ValueError:
            messagebox.showerror("Erro", "Ângulo inválido")

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
    
    def _draw_viewport(self):
        self.canvas.create_rectangle(
            self.viewport["xmin"], self.viewport["ymin"],
            self.viewport["xmax"], self.viewport["ymax"],
            outline="white", dash=(4, 2))

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

        self.fill_var = tk.BooleanVar()
        fill_checkbox = ttk.Checkbutton(obj_frame, text="Preencher Polígono", variable=self.fill_var)
        fill_checkbox.pack(side=tk.TOP, pady=5)

        ttk.Label(obj_frame, text="Técnica de Clipagem de Retas:", style="Title.TLabel").pack(pady=(10, 0))
        clip_radio_frame = ttk.Frame(obj_frame)
        clip_radio_frame.pack(pady=5)

        ttk.Radiobutton(clip_radio_frame, text="Cohen-Sutherland", variable=self.line_clip_method, value="CS").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(clip_radio_frame, text="Liang-Barsky", variable=self.line_clip_method, value="LB").pack(side=tk.LEFT, padx=5)

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
                command=self.create_transformations_menu).pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Apagar Selecionado", 
                command=self.delete_selected, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Limpar Tudo", 
                command=self.clear_canvas, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
        
        ttk.Button(button_frame, text="Escolher Cor", command=self.choose_color).pack(side=tk.LEFT, padx=2)

        ttk.Button(button_frame, text="Curva Bezier", 
         command=self.add_bezier_curve).pack(side=tk.LEFT, padx=2)

    def choose_color(self):
        color = askcolor()[1]
        if color:
            self.selected_color = color

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
        # Calcular deltas considerando rotação
        theta = self.window["rotation"]
        delta = {
            'up': (0, 1),
            'down': (0, -1),
            'left': (-1, 0),
            'right': (1, 0)
        }[direction]
        
        dx = delta[0] * (self.window["xmax"] - self.window["xmin"]) * self.move_step
        dy = delta[1] * (self.window["ymax"] - self.window["ymin"]) * self.move_step
        
        # Rotacionar o vetor de movimento
        dx_rot = dx * math.cos(theta) - dy * math.sin(theta)
        dy_rot = dx * math.sin(theta) + dy * math.cos(theta)
        
        self.window["xmin"] += dx_rot
        self.window["xmax"] += dx_rot
        self.window["ymin"] += dy_rot
        self.window["ymax"] += dy_rot
        self.redraw()

    def add_bezier_curve(self):
        coords = self.parse_input()
        if len(coords) >= 4 and (len(coords) - 4) % 3 == 0:
            curva = Curve2D(coords, color=self.selected_color)
            self.display_file.append(curva)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Uma curva Bézier requer pelo menos 4 pontos de controle, e cada segmento adicional requer 3 pontos.")

    def save_obj(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".obj",
            filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")]
        )
        if filename:  # Verifica se o usuário não cancelou
            try:
                DescritorOBJ.write_obj(self.display_file, filename)
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
        else:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")

    def load_obj(self):
        filename = filedialog.askopenfilename(filetypes=[("OBJ files", "*.obj")])
        if filename:
            try:
                self.display_file = DescritorOBJ.read_obj(filename)
                self._update_object_list()
                self.redraw()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")

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

    def create_transformations_menu(self):
        selected_items = self.object_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.object_tree.item(selected_item, "values")
            selected_name = item_values[1]

            # Janela temporária para coletar transformações
            self.temp_transformations = []  # Lista temporária para esta sessão
            trans_window = tk.Toplevel(self.root)
            trans_window.title("Transformações 2D")

            # Frame principal para organizar abas e lista
            main_frame = ttk.Frame(trans_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Notebook (Abas) à esquerda
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Frame da lista à direita
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

            # Treeview para listar transformações
            self.transform_list = ttk.Treeview(list_frame, columns=("type", "params"), show="headings", height=5)
            self.transform_list.heading("type", text="Tipo")
            self.transform_list.heading("params", text="Parâmetros")
            self.transform_list.pack(fill=tk.BOTH, expand=True)

            # Botões abaixo da lista
            button_frame = ttk.Frame(list_frame)
            button_frame.pack(pady=5)

            ttk.Button(button_frame, text="Adicionar", 
                    command=lambda: self.add_transformation(selected_name, trans_window)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Remover", 
                    command=self.remove_transformation).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Aplicar Tudo", 
                    command=lambda: self.apply_all_transformations(selected_name, trans_window)).pack(side=tk.LEFT, padx=2)

            # Criar abas de transformações
            self.create_translation_tab()
            self.create_scaling_tab()
            self.create_rotation_tab()

    def add_transformation(self, selected_name, window):
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        params = self.get_params_from_tab(current_tab)
        if params:
            self.temp_transformations.append({"type": current_tab, "params": params})
            self.update_transform_list()

    def apply_all_transformations(self, selected_name, window):
        combined_matrix = np.identity(3)
        for t in self.temp_transformations:
            matrix = self.generate_matrix(t["type"], t["params"], selected_name)
            combined_matrix = combined_matrix @ matrix

        # Aplica a matriz final ao objeto
        for obj in self.display_file:
            if obj.name == selected_name:
                new_coords = []
                for x, y in obj.coordinates:
                    point = np.array([x, y, 1])
                    transformed_point = point @ combined_matrix
                    new_coords.append((transformed_point[0], transformed_point[1]))
                obj.coordinates = new_coords
                self.redraw()
                break
        window.destroy()

    def get_params_from_tab(self, tab_name):
        params = {}
        current_tab = self.notebook.nametowidget(self.notebook.select())
        
        if tab_name == "Translação":
            params["dx"] = float(current_tab.children["x_entry"].get())
            params["dy"] = float(current_tab.children["y_entry"].get())
        
        elif tab_name == "Escalonamento":
            params["sx"] = float(current_tab.children["sx_entry"].get())
            params["sy"] = float(current_tab.children["sy_entry"].get())
        
        elif tab_name == "Rotações":
            params["degrees"] = float(current_tab.children["degrees_entry"].get())
            params["pivot_type"] = current_tab.children["pivot_combobox"].get()
            
            if params["pivot_type"] == "Em torno de um ponto arbitrário":
                params["x"] = float(current_tab.children["x_pivot_entry"].get())
                params["y"] = float(current_tab.children["y_pivot_entry"].get())
        
        return params

    def generate_matrix(self, trans_type, params, selected_name):
        if trans_type == "Translação":
            dx = params["dx"]
            dy = params["dy"]
            return np.array([
                [1, 0, 0],
                [0, 1, 0],
                [dx, dy, 1]
            ])
        elif trans_type == "Escalonamento":
            sx = params["sx"]
            sy = params["sy"]
            for obj in self.display_file:
                if obj.name == selected_name:
                    cx, cy = self.get_object_center(obj.coordinates)
                    break
            return np.array([
                [1, 0, 0],
                [0, 1, 0],
                [-cx, -cy, 1]
            ]) @ np.array([
                [sx, 0, 0],
                [0, sy, 0],
                [0, 0, 1]
            ]) @ np.array([
                [1, 0, 0],
                [0, 1, 0],
                [cx, cy, 1]
            ])
        elif trans_type == "Rotações":
            degrees = math.radians(params["degrees"])
            pivot_type = params["pivot_type"]
            if pivot_type == "Em torno da origem":
                cx, cy = 0.0, 0.0
            elif pivot_type == "Em torno do centro do objeto":
                for obj in self.display_file:
                    if obj.name == selected_name:
                        cx, cy = self.get_object_center(obj.coordinates)
                        break
            else:
                cx = params["x"]
                cy = params["y"]
            return np.array([
                [1, 0, 0],
                [0, 1, 0],
                [-cx, -cy, 1]
            ]) @ np.array([
                [math.cos(degrees), -math.sin(degrees), 0],
                [math.sin(degrees), math.cos(degrees), 0],
                [0, 0, 1]
            ]) @ np.array([
                [1, 0, 0],
                [0, 1, 0],
                [cx, cy, 1]
            ])
        else:
            return np.identity(3)

    def update_transform_list(self):
        self.transform_list.delete(*self.transform_list.get_children())
        for t in self.temp_transformations:
            desc = f"{t['type']}: "
            if t["type"] == "Translação":
                desc += f"dx={t['params']['dx']}, dy={t['params']['dy']}"
            elif t["type"] == "Escalonamento":
                desc += f"sx={t['params']['sx']}, sy={t['params']['sy']}"
            elif t["type"] == "Rotações":
                desc += f"graus={t['params']['degrees']}, pivô={t['params']['pivot_type']}"
            self.transform_list.insert("", "end", values=(t["type"], desc))

    def remove_transformation(self):
        selected = self.transform_list.selection()
        if selected:
            index = self.transform_list.index(selected[0])
            del self.temp_transformations[index]
            self.update_transform_list()

    def create_translation_tab(self):
        translation_tab = ttk.Frame(self.notebook)
        self.notebook.add(translation_tab, text="Translação")
        
        ttk.Label(translation_tab, text="Deslocamento em X:").pack(pady=5)
        x_entry = ttk.Entry(translation_tab, name="x_entry")
        x_entry.pack(pady=5)
        
        ttk.Label(translation_tab, text="Deslocamento em Y:").pack(pady=5)
        y_entry = ttk.Entry(translation_tab, name="y_entry")
        y_entry.pack(pady=5)

    def create_scaling_tab(self):
        scaling_tab = ttk.Frame(self.notebook)
        self.notebook.add(scaling_tab, text="Escalonamento")

        ttk.Label(scaling_tab, text="Fator de Escalonamento em X:").pack(pady=5)
        sx_entry = ttk.Entry(scaling_tab, name="sx_entry")
        sx_entry.pack(pady=5)

        ttk.Label(scaling_tab, text="Fator de Escalonamento em Y:").pack(pady=5)
        sy_entry = ttk.Entry(scaling_tab, name="sy_entry")
        sy_entry.pack(pady=5)

    def create_rotation_tab(self):
        rotation_tab = ttk.Frame(self.notebook)
        self.notebook.add(rotation_tab, text="Rotações")

        ttk.Label(rotation_tab, text="Graus:").pack(pady=5)
        degrees_entry = ttk.Entry(rotation_tab, name="degrees_entry")
        degrees_entry.pack(pady=5)

        ttk.Label(rotation_tab, text="Selecione o ponto de rotação:").pack(pady=5)
        
        pivot_combobox = ttk.Combobox(rotation_tab, values=["Em torno da origem", "Em torno do centro do objeto", "Em torno de um ponto arbitrário"], name="pivot_combobox")
        pivot_combobox.set("Em torno da origem")
        pivot_combobox.pack(pady=5)

        point_label_x = ttk.Label(rotation_tab, text="Ponto X:")
        x_pivot_entry = ttk.Entry(rotation_tab, name="x_pivot_entry")
        point_label_y = ttk.Label(rotation_tab, text="Ponto Y:")
        y_pivot_entry = ttk.Entry(rotation_tab, name="y_pivot_entry")

        def update_point_entry(event):
            if pivot_combobox.get() == "Em torno de um ponto arbitrário":
                point_label_x.pack(pady=5)
                x_pivot_entry.pack(pady=5)
                point_label_y.pack(pady=5)
                y_pivot_entry.pack(pady=5)
            else:
                point_label_x.pack_forget()
                x_pivot_entry.pack_forget()
                point_label_y.pack_forget()
                y_pivot_entry.pack_forget()

        pivot_combobox.bind("<<ComboboxSelected>>", update_point_entry)
        update_point_entry(None)

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
                        matrix = (
                            np.array([[1, 0, 0], [0, 1, 0], [-cx, -cy, 1]]) @
                            np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]]) @
                            np.array([[1, 0, 0], [0, 1, 0], [cx, cy, 1]])
                        )
                        transformed = np.array([x, y, 1]) @ matrix
                        new_coordinates.append((transformed[0], transformed[1]))
                    obj.coordinates = new_coordinates
                    self.redraw()
                    break
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Por favor, insira valores válidos para X e Y.")

    def apply_rotation_around_point(self, selected_name, degrees_str, x_str, y_str):
        try:
            degrees = math.radians(float(degrees_str))
            dx = float(x_str)
            dy = float(y_str)

            for i, obj in enumerate(self.display_file):
                if obj.name == selected_name:
                    new_coordinates = []
                    for x, y in obj.coordinates:
                        matrix = (
                            np.array([[1, 0, 0], [0, 1, 0], [-dx, -dy, 1]]) @
                            np.array([[math.cos(degrees), -math.sin(degrees), 0], 
                                      [math.sin(degrees), math.cos(degrees), 0], 
                                      [0, 0, 1]]) @
                            np.array([[1, 0, 0], [0, 1, 0], [dx, dy, 1]])
                        )
                        transformed = np.array([x, y, 1]) @ matrix
                        new_coordinates.append((transformed[0], transformed[1]))
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
        # Calcular centro da window
        cx = (self.window["xmin"] + self.window["xmax"]) / 2
        cy = (self.window["ymin"] + self.window["ymax"]) / 2
        
        # Aplicar rotação inversa
        theta = -self.window["rotation"]
        x_rot = (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta) + cx
        y_rot = (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta) + cy
        
        # Mapear para viewport
        window_width = self.window["xmax"] - self.window["xmin"]
        window_height = self.window["ymax"] - self.window["ymin"]
        viewport_width = self.viewport["xmax"] - self.viewport["xmin"]
        viewport_height = self.viewport["ymax"] - self.viewport["ymin"]
        
        scale_x = viewport_width / window_width
        scale_y = viewport_height / window_height
        scale = min(scale_x, scale_y)
        
        vx = self.viewport["xmin"] + (x_rot - self.window["xmin"]) * scale
        vy = self.viewport["ymax"] - (y_rot - self.window["ymin"]) * scale
        
        return (vx, vy)

    def add_point(self):
        coords = self.parse_input()
        if len(coords) == 1:
            ponto = Point(coords, color=self.selected_color)
            self.display_file.append(ponto)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Ponto, insira apenas uma coordenada.")

    def add_line(self):
        coords = self.parse_input()
        if len(coords) == 2:
            linha = Line(coords, color=self.selected_color)
            self.display_file.append(linha)
            self.coord_entry.delete(0, tk.END)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar uma Linha, insira exatamente duas coordenadas.")

    def add_polygon(self):
        coords = self.parse_input()
        if len(coords) >= 3:
            poligono = Polygon(coords, color=self.selected_color, filled=self.fill_var.get())
            self.display_file.append(poligono)
            self.coord_entry.delete(0, tk.END)
            self.fill_var.set(False)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Polígono, insira pelo menos três coordenadas.")

    def clip_object(self, obj):
        if isinstance(obj, Point):
            return obj if self.clip_point(obj) else None
        elif isinstance(obj, Line):
            return self.clip_line(obj)
        elif isinstance(obj, Polygon):
            return self.clip_polygon(obj)
        elif isinstance(obj, Curve2D):
            return self.clip_curve(obj)
        return None
    
    def clip_curve(self, curve):
        curve.clip({
            "xmin": self.window["xmin"],
            "ymin": self.window["ymin"],
            "xmax": self.window["xmax"],
            "ymax": self.window["ymax"]
        })
        return curve

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
            clipped = self.clip_object(obj)
            if clipped:
                clipped.draw(self.canvas, self.viewport_transform)
        self._draw_viewport()

    def parse_input(self):
        try:
            input_str = self.coord_entry.get().strip()
            if input_str:
                return list(eval(f"[{input_str.replace(' ', '').replace(')(', '),(')}]"))
            return []
        except:
            messagebox.showerror("Erro de Entrada", "Coordenadas inválidas! Por favor, insira coordenadas no formato correto.")
            return []
    
    def clip_point(self, point):
        x, y = point.coordinates[0]
        return (self.window["xmin"] <= x <= self.window["xmax"] and
                self.window["ymin"] <= y <= self.window["ymax"])

    def clip_line(self, line):
        if self.line_clip_method.get() == "CS":
            return self.clip_line_cohen_sutherland(line)
        else:
            return self.clip_line_liang_barsky(line)
    
    # Clipagem de polígonos usando o algoritmo Sutherland-Hodgeman
    def clip_polygon(self, polygon):
        def is_inside_left(point): return point[0] >= self.window["xmin"]
        def is_inside_right(point): return point[0] <= self.window["xmax"]
        def is_inside_bottom(point): return point[1] >= self.window["ymin"]
        def is_inside_top(point): return point[1] <= self.window["ymax"]

        # Aplica a clipagem do polígono contra uma única borda da window
        def clip_edge(vertices, edge):
            clipped_vertices = []

            for i in range(len(vertices)):
                current = vertices[i]
                prev = vertices[i - 1]

                current_inside = edge(current)
                previous_inside = edge(prev)

                if current_inside:
                    if not previous_inside:
                        clipped_vertices.append(compute_intersection(prev, current, edge))
                    clipped_vertices.append(current)
                elif previous_inside:
                    clipped_vertices.append(compute_intersection(prev, current, edge))
            return clipped_vertices

        # Calcula o ponto de interseção entre uma aresta do polígono e uma borda da window
        def compute_intersection(p1, p2, boundary_check):
            x1, y1 = p1
            x2, y2 = p2
            if x1 == x2:
                m = float("inf")
            else:
                m = (y2 - y1) / (x2 - x1)
            
            if boundary_check == is_inside_left:
                x = self.window["xmin"]
                y = m * (x - x1) + y1
            elif boundary_check == is_inside_right:
                x = self.window["xmax"]
                y = m * (x - x1) + y1
            elif boundary_check == is_inside_bottom:
                y = self.window["ymin"]
                x = x1 + (y - y1) / m
            elif boundary_check == is_inside_top:
                y = self.window["ymax"]
                x = x1 + (y - y1) / m
            return (x, y)

        # Aplica o algoritmo em todas as bordas da window
        clipped_vertices = polygon.coordinates
        for edge in [is_inside_left, is_inside_right, is_inside_bottom, is_inside_top]:
            clipped_vertices = clip_edge(clipped_vertices, edge)
            if not clipped_vertices:
                return None
        return Polygon(clipped_vertices, polygon.color, polygon.filled)

    def compute_out_code(self, x, y):
        code = self.INSIDE
        if x < self.window["xmin"]:
            code |= self.LEFT
        elif x > self.window["xmax"]:
            code |= self.RIGHT

        if y < self.window["ymin"]:
            code |= self.BOTTOM
        elif y > self.window["ymax"]:
            code |= self.TOP
        return code

    def clip_line_cohen_sutherland(self, line):
        (x1, y1), (x2, y2) = line.coordinates

        code_start = self.compute_out_code(x1, y1)
        code_end = self.compute_out_code(x2, y2)
        
        while True:
            # Caso trivial: completamente dentro
            if not (code_start | code_end):
                return Line([(x1, y1), (x2, y2)])
            
            # Caso trivial: completamente fora
            elif code_start & code_end:
                return None
            
            # Caso parcial: calcula interseção
            else:
                code_out = code_start if code_start else code_end
                if code_out & self.TOP:
                    x = (x1 + (x2 - x1) * (self.window["ymax"] - y1) / (y2 - y1)) if y2 != y1 else x1
                    y = self.window["ymax"]
                elif code_out & self.BOTTOM:
                    x = (x1 + (x2 - x1) * (self.window["ymin"] - y1) / (y2 - y1)) if y2 != y1 else x1
                    y = self.window["ymin"]
                elif code_out & self.RIGHT:
                    y = (y1 + (y2 - y1) * (self.window["xmax"] - x1) / (x2 - x1)) if x2 != x1 else y1
                    x = self.window["xmax"]
                elif code_out & self.LEFT:
                    y = (y1 + (y2 - y1) * (self.window["xmin"] - x1) / (x2 - x1)) if x2 != x1 else y1
                    x = self.window["xmin"]
                
                if code_out == code_start:
                    x1, y1 = x, y
                    code_start = self.compute_out_code(x1, y1)
                else:
                    x2, y2 = x, y
                    code_end = self.compute_out_code(x2, y2)
    
    def clip_line_liang_barsky(self, line):
        (x1, y1), (x2, y2) = line.coordinates

        dx = x2 - x1
        dy = y2 - y1
        p = [-dx, dx, -dy, dy]
        q = [x1 - self.window["xmin"],
            self.window["xmax"] - x1,
            y1 - self.window["ymin"],
            self.window["ymax"] - y1]
        
        u1, u2 = 0.0, 1.0
        for pi, qi in zip(p, q):
            if pi == 0:
                if qi < 0:
                    return None
            else:
                u = qi / pi
                if pi < 0:
                    u1 = max(u1, u)
                else:
                    u2 = min(u2, u)
        if u1 > u2:
            return None

        x1 = x1 + u1 * dx
        y1 = y1 + u1 * dy
        x2 = x1 + u2 * dx
        y2 = y1 + u2 * dy
        return Line([(x1, y1), (x2, y2)])

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema Gráfico 2D com Lista de Objetos")
    root.geometry("1020x700")
    app = GraphicsSystem(root)
    root.mainloop()