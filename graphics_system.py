import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import numpy as np
import math
from tkinter.colorchooser import askcolor
from objects import GraphicObject, Point, Line, Polygon, Curve2D, BSpline, Ponto3D, Objeto3D, ObjectType, BezierPatch, BezierSurface
from descritor_obj import DescritorOBJ


class GraphicsSystem:
    CANVAS_WIDTH = 775
    CANVAS_HEIGHT = 383
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

    def __init__(self, root):
        """
        Parte de interface grafica (parte de Tkinter, botoes inputs e etc, parte visual) foi gerada inteiramente por IAs

        DOC IAgen:
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Adapte a interface atual para comportar os requisitos da entrega X 
        (Cola os requisitos da entrega X e o codigo atual da interface (Tkinter))
        """
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
        self.style.configure("ProjButton.TRadiobutton", 
                             background="#2d2d2d", 
                             foreground="white",
                             indicatorcolor="#1a1a1a",
                             font=("bold"))

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
        self._create_projection_controls()
        self._create_separator()
        self._create_move_controls()
        self._create_separator()
        self._create_rotation_controls()
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
    
    def _create_projection_controls(self):
        projection_frame = ttk.Frame(self.control_frame)
        projection_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        projection_label = ttk.Label(projection_frame, text="Tipo de projeção", style="Title.TLabel")
        projection_label.grid(row=0, column=0, pady=5, columnspan=2)

        self.projection_type = tk.StringVar(value="parallel")

        radio_frame = ttk.Frame(projection_frame)
        radio_frame.grid(row=1, column=0, columnspan=2, pady=2)
        ttk.Radiobutton(projection_frame, text="Paralela", variable=self.projection_type, style="ProjButton.TRadiobutton",
                        value="parallel", command=self.toggle_projection_params).grid(row=1, column=0, pady=2)
        ttk.Radiobutton(projection_frame, text="Perspectiva", variable=self.projection_type, style="ProjButton.TRadiobutton",
                        value="perspective", command=self.toggle_projection_params).grid(row=2, column=0, pady=2)
        
        # Frame para os parâmetros de perspectiva (inicialmente oculto)
        self.perspective_frame = ttk.Frame(projection_frame)
        # Este grid é controlado por toggle_projection_params
        
        # Parâmetros da projeção perspectiva
        ttk.Label(self.perspective_frame, text="Distância (d):", style="CoordsLabel.TLabel").grid(row=0, column=0, pady=2, sticky=tk.W)
        self.d_entry = ttk.Entry(self.perspective_frame)
        self.d_entry.insert(0, "200")
        self.d_entry.grid(row=1, column=0, pady=2, sticky=tk.EW)
        
        # Botão Aplicar 'd'
        ttk.Button(self.perspective_frame, text="Aplicar d",
                   command=self.redraw).grid(row=2, column=0, pady=5, sticky=tk.EW)

        # Novos botões para Grande Angular e Teleobjetiva
        ttk.Button(self.perspective_frame, text="Grande Angular (-d)",
                   command=self.apply_wide_angle_effect).grid(row=3, column=0, pady=2, sticky=tk.EW)
        ttk.Button(self.perspective_frame, text="Teleobjetiva (+d)",
                   command=self.apply_telephoto_effect).grid(row=4, column=0, pady=2, sticky=tk.EW)
        
        self.toggle_projection_params() # Chama para configurar a visibilidade inicial

    def toggle_projection_params(self):
        if self.projection_type.get() == "perspective":
            self.perspective_frame.grid(row=3, column=0, pady=5, sticky=tk.EW)
        else:
            self.perspective_frame.grid_forget()
        self.redraw()

    def apply_wide_angle_effect(self):
        try:
            current_d = float(self.d_entry.get())
            # Reduz 'd' para efeito grande angular. Não deixe ser zero ou negativo.
            new_d = max(50, current_d * 0.75) # Exemplo: reduz em 25%, mínimo de 50
            self.d_entry.delete(0, tk.END)
            self.d_entry.insert(0, str(new_d))
            self.redraw()
        except ValueError:
            messagebox.showerror("Erro", "Valor de 'd' inválido.")

    def apply_telephoto_effect(self):
        try:
            current_d = float(self.d_entry.get())
            # Aumenta 'd' para efeito teleobjetiva.
            new_d = current_d * 1.25 # Exemplo: aumenta em 25%
            self.d_entry.delete(0, tk.END)
            self.d_entry.insert(0, str(new_d))
            self.redraw()
        except ValueError:
            messagebox.showerror("Erro", "Valor de 'd' inválido.")

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
        obj_frame.pack(side=tk.LEFT, padx=5)

        obj_label = ttk.Label(obj_frame, text="Adicionar Objetos", style="Title.TLabel")
        obj_label.pack(side=tk.TOP, pady=5)

        button_frame = ttk.Frame(obj_frame)
        button_frame.pack(side=tk.TOP, pady=10)

        ttk.Button(button_frame, text="Adicionar Objetos", 
                command=self.create_add_objects_menu).pack(side=tk.TOP, padx=2, pady=5, fill=tk.X)
        ttk.Button(button_frame, text="Carregar OBJ", 
                 command=self.load_obj).pack(side=tk.TOP, padx=2, pady=5, fill=tk.X)
        ttk.Button(button_frame, text="Salvar OBJ", 
                 command=self.save_obj).pack(side=tk.TOP, padx=2, pady=5, fill=tk.X)

        # Botões de limpar
        clear_buttons_frame = ttk.Frame(self.list_frame)
        clear_buttons_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X, expand=True)

        ttk.Button(clear_buttons_frame, text="Aplicar Transformações", 
                command=self.create_transformations_menu).pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Apagar Selecionado", 
                command=self.delete_selected, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(clear_buttons_frame, text="Limpar Tudo", 
                command=self.clear_canvas, style="DeleteButton.TButton").pack(side=tk.TOP, padx=2, pady=5)
    
    def _create_rotation_controls(self):
        rotation_frame = ttk.Frame(self.control_frame)
        rotation_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Label(rotation_frame, text="Rotação da Window", style="Title.TLabel").pack(side=tk.TOP, padx=2, pady=5)
        ttk.Label(rotation_frame, text="Insira a rotação da windows (em graus):", style="CoordsLabel.TLabel").pack(pady=5)
        
        self.rotation_entry = ttk.Entry(rotation_frame, width=8)
        self.rotation_entry.pack(side=tk.TOP, padx=2, pady=5)
        ttk.Button(rotation_frame, text="Aplicar", 
                 command=self.apply_window_rotation).pack(side=tk.TOP, padx=2, pady=5)

    def create_add_objects_menu(self):
        add_objects_window = tk.Toplevel(self.root)
        add_objects_window.title("Adicionar Objetos")
        notebook = ttk.Notebook(add_objects_window)

        # Abas para objetos 2D
        for obj_type in [ObjectType.PONTO, ObjectType.LINHA, ObjectType.POLIGONO, 
                        ObjectType.CURVA_BEZIER, ObjectType.B_SPLINE]:
            self.create_object_tab(obj_type, notebook)

        # Nova aba para superfícies Bézier
        bezier_tab = ttk.Frame(notebook)
        notebook.add(bezier_tab, text="Retalho Bézier")

        # Frame para os elementos de entrada
        input_frame = ttk.Frame(bezier_tab)
        input_frame.pack(pady=10, fill=tk.X)

        ttk.Label(input_frame, text="16 pontos 3D (4 linhas com 4 pontos separados por ';')", style="CoordsLabel.TLabel").pack(pady=5)
        self.bezier_entry = ttk.Entry(input_frame, width=60)
        self.bezier_entry.pack(pady=5)

        # Frame para botões (cor e adicionar)
        button_frame = ttk.Frame(bezier_tab)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Escolher Cor", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Adicionar Retalho", command=self.add_bezier_patch).pack(side=tk.LEFT, padx=5)

        # Abas para objetos 3D
        self.create_3d_objects_tab(ObjectType.PONTO3D, notebook)
        self.create_3d_objects_tab(ObjectType.OBJETO3D, notebook)

        notebook.pack(expand=True, fill='both')
        add_objects_window.transient(self.root)
        add_objects_window.grab_set()

    def create_object_tab(self, type: ObjectType, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=type.value)

        default_label_text = "Insira as coordenadas no formato \"(x1, y1), (x2, y2), ...\":"

        label_texts = {
            ObjectType.PONTO: "Insira as coordenadas no formato \"(x1, y1)\":",
            ObjectType.LINHA: "Insira as coordenadas no formato \"(x1, y1), (x2, y2)\":"
        }
        ttk.Label(tab, text=label_texts.get(type, default_label_text), style="CoordsLabel.TLabel").pack(pady=5)
        
        if type == ObjectType.LINHA:
            ttk.Label(tab, text="Técnica de Clipagem de Retas:", style="Title.TLabel").pack(pady=(10, 0))
            clip_radio_frame = ttk.Frame(tab)
            clip_radio_frame.pack(pady=5)

            ttk.Radiobutton(clip_radio_frame, text="Cohen-Sutherland", variable=self.line_clip_method, value="CS").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(clip_radio_frame, text="Liang-Barsky", variable=self.line_clip_method, value="LB").pack(side=tk.LEFT, padx=5)
        
        elif type == ObjectType.POLIGONO:
            self.fill_var = tk.BooleanVar()
            fill_checkbox = ttk.Checkbutton(tab, text="Preencher Polígono", variable=self.fill_var)
            fill_checkbox.pack(side=tk.TOP, pady=5)

        coord_entry = ttk.Entry(tab, width=40)
        coord_entry.pack(side=tk.TOP, padx=5, fill=tk.X, expand=False)

        button_frame = ttk.Frame(tab)
        button_frame.pack(side=tk.TOP, pady=10)

        command_dict = {
            ObjectType.LINHA: lambda: self.add_line(coord_entry),
            ObjectType.POLIGONO: lambda: self.add_polygon(coord_entry),
            ObjectType.PONTO: lambda: self.add_point(coord_entry),
            ObjectType.CURVA_BEZIER: lambda: self.add_bezier_curve(coord_entry),
            ObjectType.B_SPLINE: lambda: self.add_bspline(coord_entry)
        }

        ttk.Button(button_frame, text="Escolher Cor", command=self.choose_color).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Adicionar objeto", 
                command=command_dict.get(type)).pack(side=tk.LEFT, padx=2)
    
    def create_3d_objects_tab(self, type: ObjectType, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=type.value)

        if type == ObjectType.PONTO3D:
            ttk.Label(tab, text="Insira as coordenadas no formato \"(x, y, z)\":", style="CoordsLabel.TLabel").pack(pady=5)
            coord_entry = ttk.Entry(tab, width=40)
            coord_entry.pack(side=tk.TOP, padx=5, fill=tk.X, expand=False)

            button_frame = ttk.Frame(tab)
            button_frame.pack(side=tk.TOP, pady=10)

            ttk.Button(button_frame, text="Escolher Cor", command=self.choose_color).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Adicionar Ponto3D", 
                    command=lambda: self.add_ponto3d(coord_entry)).pack(side=tk.LEFT, padx=2)
        
        elif type == ObjectType.OBJETO3D:
            ttk.Label(tab, text="Insira os segmentos no formato \"[((x1,y1,z1), (x2,y2,z2)), ...]\":", style="CoordsLabel.TLabel").pack(pady=5)
            segments_entry = ttk.Entry(tab, width=40)
            segments_entry.pack(side=tk.TOP, padx=5, fill=tk.X, expand=False)

            button_frame = ttk.Frame(tab)
            button_frame.pack(side=tk.TOP, pady=10)

            ttk.Button(button_frame, text="Escolher Cor", command=self.choose_color).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Adicionar Objeto3D", 
                    command=lambda: self.add_objeto3d(segments_entry)).pack(side=tk.LEFT, padx=2)
    
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
        self.canvas.bind("<Configure>", self._on_canvas_resize)
    
    def _on_canvas_resize(self, event):
        new_width = event.width
        new_height = event.height

        self.CANVAS_WIDTH = new_width
        self.CANVAS_HEIGHT = new_height

        self.viewport["xmax"] = new_width - 20
        self.viewport["ymax"] = new_height - 20

        vp_width = self.viewport["xmax"] - self.viewport["xmin"]
        vp_height = self.viewport["ymax"] - self.viewport["ymin"]
        half_width = vp_width / 2
        half_height = vp_height / 2

        self.window["xmin"] = -half_width
        self.window["xmax"] = half_width
        self.window["ymin"] = -half_height
        self.window["ymax"] = half_height

        self.redraw()
        
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

            # Verifica se o objeto é 2D ou 3D
            obj = next((o for o in self.display_file if o.name == selected_name), None)
            is_3d = isinstance(obj, (Ponto3D, Objeto3D))

            # Janela temporária para coletar transformações
            self.temp_transformations = []
            trans_window = tk.Toplevel(self.root)
            trans_window.title("Transformações 3D" if is_3d else "Transformações 2D")

            # Frame principal
            main_frame = ttk.Frame(trans_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Notebook (Abas)
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Frame da lista
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

            # Treeview para listar transformações
            self.transform_list = ttk.Treeview(list_frame, columns=("type", "params"), show="headings", height=5)
            self.transform_list.heading("type", text="Tipo")
            self.transform_list.heading("params", text="Parâmetros")
            self.transform_list.pack(fill=tk.BOTH, expand=True)

            # Botões
            button_frame = ttk.Frame(list_frame)
            button_frame.pack(pady=5)

            ttk.Button(button_frame, text="Adicionar", 
                    command=lambda: self.add_transformation(selected_name, trans_window)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Remover", 
                    command=self.remove_transformation).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Aplicar Tudo", 
                    command=lambda: self.apply_all_transformations(selected_name, trans_window)).pack(side=tk.LEFT, padx=2)

            # Criar abas
            if is_3d:
                self.create_3d_translation_tab()
                self.create_3d_scaling_tab()
                self.create_3d_rotation_tab()
            else:
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
        combined_matrix = np.identity(4)  # Matriz 4x4 para suportar 3D
        for t in self.temp_transformations:
            matrix = self.generate_matrix(t["type"], t["params"], selected_name)
            combined_matrix = combined_matrix @ matrix

        # Aplica a matriz final ao objeto
        for obj in self.display_file:
            if obj.name == selected_name:
                new_coords = []
                
                # Verifica o tipo de objeto
                if isinstance(obj, (Ponto3D, Objeto3D, BezierPatch, BezierSurface)):
                    # Processamento para objetos 3D
                    for coord in obj.coordinates:
                        x, y, z = coord[:3]  # Pega os 3 primeiros valores
                        point = np.array([x, y, z, 1])  # Coordenada homogênea
                        transformed_point = point @ combined_matrix
                        new_coords.append((
                            transformed_point[0], 
                            transformed_point[1], 
                            transformed_point[2]
                        ))
                        
                else:
                    # Processamento para objetos 2D
                    for coord in obj.coordinates:
                        x, y = coord[:2]  # Pega apenas x,y
                        point = np.array([x, y, 0, 1])  # Z=0 para 2D
                        transformed_point = point @ combined_matrix
                        new_coords.append((
                            transformed_point[0], 
                            transformed_point[1]
                        ))
                
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
        
        elif tab_name == "Translação 3D":
            params["dx"] = float(current_tab.children["x_entry"].get())
            params["dy"] = float(current_tab.children["y_entry"].get())
            params["dz"] = float(current_tab.children["z_entry"].get())
        
        elif tab_name == "Escalonamento":
            params["sx"] = float(current_tab.children["sx_entry"].get())
            params["sy"] = float(current_tab.children["sy_entry"].get())
        
        elif tab_name == "Escalonamento 3D":
            params["sx"] = float(current_tab.children["sx_entry"].get())
            params["sy"] = float(current_tab.children["sy_entry"].get())
            params["sz"] = float(current_tab.children["sz_entry"].get())
        
        elif tab_name == "Rotações":
            params["degrees"] = float(current_tab.children["degrees_entry"].get())
            params["pivot_type"] = current_tab.children["pivot_combobox"].get()
            
            if params["pivot_type"] == "Em torno de um ponto arbitrário":
                params["x"] = float(current_tab.children["x_pivot_entry"].get())
                params["y"] = float(current_tab.children["y_pivot_entry"].get())
        
        elif tab_name == "Rotação 3D":
            params["degrees"] = float(current_tab.children["degrees_entry"].get())
            params["axis"] = current_tab.children["axis_combobox"].get()
            params["pivot_type"] = current_tab.children["pivot_combobox"].get()
        
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
            if t["type"] in ["Translação", "Translação 3D"]:
                desc += f"dx={t['params'].get('dx', 0)}, dy={t['params'].get('dy', 0)}"
                if "dz" in t["params"]:
                    desc += f", dz={t['params']['dz']}"
            elif t["type"] in ["Escalonamento", "Escalonamento 3D"]:
                desc += f"sx={t['params'].get('sx', 1)}, sy={t['params'].get('sy', 1)}"
                if "sz" in t["params"]:
                    desc += f", sz={t['params']['sz']}"
            elif t["type"] == "Rotações":
                desc += f"graus={t['params']['degrees']}, pivô={t['params']['pivot_type']}"
            elif t["type"] == "Rotação 3D":
                desc += f"graus={t['params']['degrees']}, eixo={t['params']['axis']}, pivô={t['params']['pivot_type']}"
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

    def get_object_center(self, object_coordinates):
        total_x, total_y = zip(*object_coordinates)
        array_length = len(object_coordinates)
        cx = sum(total_x) / array_length
        cy = sum(total_y) / array_length
        return cx, cy

    def viewport_transform(self, x, y, z=None):
        if z is None:  # Transformação 2D
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
        else:  # Transformação 3D
            """
            Solicitamos a ajuda de IA para aprender a fazer transformações 3D

            DOC IAgen:
            DeepSeek https://chat.deepseek.com

            Prompt usado:
            "Como fazer a transformação de um ponto 3D para uma viewport 2D, considerando rotação e perspectiva?"
            """
            try:
                d = float(self.d_entry.get())
            except ValueError:
                d = 200

            vrp = np.array([
                (self.window["xmin"] + self.window["xmax"]) / 2,  # Centro X
                (self.window["ymin"] + self.window["ymax"]) / 2,  # Centro Y
                0  # Assumindo VRP no plano XY
            ])
            
            # VPN (View Plane Normal) - apontando para o observador
            vpn = np.array([0, 0, 1])
            
            # Vetor View Up (VUP) - orientação "para cima"
            vup = np.array([0, 1, 0])
            
            # Calcula os eixos do sistema de coordenadas da view
            n = vpn / np.linalg.norm(vpn)
            u = np.cross(vup, n)
            u = u / np.linalg.norm(u)
            v = np.cross(n, u)
            
            # Matriz de rotação para alinhar com o sistema de coordenadas da view
            R = np.array([
                [u[0], u[1], u[2], 0],
                [v[0], v[1], v[2], 0],
                [n[0], n[1], n[2], 0],
                [0,    0,    0,    1]
            ])
            
            # Matriz de translação para mover o VRP para a origem
            T = np.array([
                [1, 0, 0, -vrp[0]],
                [0, 1, 0, -vrp[1]],
                [0, 0, 1, -vrp[2]],
                [0, 0, 0, 1]
            ])
            
            # Transformação completa (primeiro translação, depois rotação)
            M = R @ T
            
            # Aplica a transformação ao ponto
            point = np.array([x, y, z, 1])
            transformed = M @ point
            
            if self.projection_type.get() == "parallel":
                # Projeção Paralela Ortogonal - simplesmente descarta a coordenada Z
                x_proj = transformed[0]
                y_proj = transformed[1]
            else:
                # Projeção Perspectiva
                if transformed[2] + d == 0:
                    transformed[2] = -d + 0.0001
                    
                x_proj = (transformed[0] * d) / (transformed[2] + d)
                y_proj = (transformed[1] * d) / (transformed[2] + d)
            
            # Mapeia para a viewport
            window_width = self.window["xmax"] - self.window["xmin"]
            window_height = self.window["ymax"] - self.window["ymin"]
            viewport_width = self.viewport["xmax"] - self.viewport["xmin"]
            viewport_height = self.viewport["ymax"] - self.viewport["ymin"]
            
            scale_x = viewport_width / window_width
            scale_y = viewport_height / window_height
            scale = min(scale_x, scale_y)
            
            vx = self.viewport["xmin"] + (x_proj - self.window["xmin"]) * scale
            vy = self.viewport["ymax"] - (y_proj - self.window["ymin"]) * scale
            
            return (vx, vy)
    
    def generate_matrix_3d(self, trans_type, params, selected_name):
        if trans_type == "Translação 3D":
            dx = params["dx"]
            dy = params["dy"]
            dz = params["dz"]
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [dx, dy, dz, 1]
            ])
        
        elif trans_type == "Escalonamento 3D":
            sx = params["sx"]
            sy = params["sy"]
            sz = params["sz"]
            
            # Encontra o centro do objeto
            obj = next((o for o in self.display_file if o.name == selected_name), None)
            if not obj:
                return np.identity(4)
                
            if isinstance(obj, Ponto3D):
                cx, cy, cz = obj.coordinates[0]
            elif isinstance(obj, Objeto3D):
                # Calcula o centro médio de todos os pontos
                all_points = []
                for segment in obj.segments:
                    all_points.extend(segment)
                cx = sum(p[0] for p in all_points) / len(all_points)
                cy = sum(p[1] for p in all_points) / len(all_points)
                cz = sum(p[2] for p in all_points) / len(all_points)
            
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [-cx, -cy, -cz, 1]
            ]) @ np.array([
                [sx, 0, 0, 0],
                [0, sy, 0, 0],
                [0, 0, sz, 0],
                [0, 0, 0, 1]
            ]) @ np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [cx, cy, cz, 1]
            ])
        
        elif trans_type == "Rotação 3D":
            angle = math.radians(params["degrees"])
            axis = params["axis"]
            pivot_type = params["pivot_type"]
            
            # Determina o ponto de pivô
            if pivot_type == "Em torno da origem":
                cx, cy, cz = 0, 0, 0
            else:
                obj = next((o for o in self.display_file if o.name == selected_name), None)
                if not obj:
                    return np.identity(4)
                    
                if isinstance(obj, Ponto3D):
                    cx, cy, cz = obj.coordinates[0]
                elif isinstance(obj, Objeto3D):
                    all_points = []
                    for segment in obj.segments:
                        all_points.extend(segment)
                    cx = sum(p[0] for p in all_points) / len(all_points)
                    cy = sum(p[1] for p in all_points) / len(all_points)
                    cz = sum(p[2] for p in all_points) / len(all_points)
            
            # Matriz de translação para a origem
            T1 = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [-cx, -cy, -cz, 1]
            ])
            
            # Matriz de rotação
            c = math.cos(angle)
            s = math.sin(angle)
            
            if axis == "X":
                R = np.array([
                    [1, 0, 0, 0],
                    [0, c, s, 0],
                    [0, -s, c, 0],
                    [0, 0, 0, 1]
                ])
            elif axis == "Y":
                R = np.array([
                    [c, 0, -s, 0],
                    [0, 1, 0, 0],
                    [s, 0, c, 0],
                    [0, 0, 0, 1]
                ])
            elif axis == "Z":
                R = np.array([
                    [c, s, 0, 0],
                    [-s, c, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ])
            
            # Matriz de translação de volta
            T2 = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [cx, cy, cz, 1]
            ])
            
            return T1 @ R @ T2
        
        return np.identity(4)

    def create_3d_translation_tab(self):
        translation_tab = ttk.Frame(self.notebook)
        self.notebook.add(translation_tab, text="Translação 3D")
        
        ttk.Label(translation_tab, text="Deslocamento em X:").pack(pady=5)
        x_entry = ttk.Entry(translation_tab, name="x_entry")
        x_entry.pack(pady=5)
        
        ttk.Label(translation_tab, text="Deslocamento em Y:").pack(pady=5)
        y_entry = ttk.Entry(translation_tab, name="y_entry")
        y_entry.pack(pady=5)
        
        ttk.Label(translation_tab, text="Deslocamento em Z:").pack(pady=5)
        z_entry = ttk.Entry(translation_tab, name="z_entry")
        z_entry.pack(pady=5)

    def create_3d_scaling_tab(self):
        scaling_tab = ttk.Frame(self.notebook)
        self.notebook.add(scaling_tab, text="Escalonamento 3D")

        ttk.Label(scaling_tab, text="Fator de Escalonamento em X:").pack(pady=5)
        sx_entry = ttk.Entry(scaling_tab, name="sx_entry")
        sx_entry.pack(pady=5)

        ttk.Label(scaling_tab, text="Fator de Escalonamento em Y:").pack(pady=5)
        sy_entry = ttk.Entry(scaling_tab, name="sy_entry")
        sy_entry.pack(pady=5)

        ttk.Label(scaling_tab, text="Fator de Escalonamento em Z:").pack(pady=5)
        sz_entry = ttk.Entry(scaling_tab, name="sz_entry")
        sz_entry.pack(pady=5)

    def create_3d_rotation_tab(self):
        rotation_tab = ttk.Frame(self.notebook)
        self.notebook.add(rotation_tab, text="Rotação 3D")

        ttk.Label(rotation_tab, text="Graus:").pack(pady=5)
        degrees_entry = ttk.Entry(rotation_tab, name="degrees_entry")
        degrees_entry.pack(pady=5)

        ttk.Label(rotation_tab, text="Eixo de rotação:").pack(pady=5)
        axis_combobox = ttk.Combobox(rotation_tab, values=["X", "Y", "Z"], name="axis_combobox")
        axis_combobox.set("Z")
        axis_combobox.pack(pady=5)

        ttk.Label(rotation_tab, text="Ponto de rotação:").pack(pady=5)
        pivot_combobox = ttk.Combobox(rotation_tab, 
                                    values=["Em torno da origem", "Em torno do centro do objeto"], 
                                    name="pivot_combobox")
        pivot_combobox.set("Em torno do centro do objeto")
        pivot_combobox.pack(pady=5)

    def apply_all_transformations(self, selected_name, window):
        """
        DOC IAgen:
        Usado para entender como aplicar transformações 3D em objetos 3D
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Como posso adaptar minhas transformacoes atuais para comportar objetos 3D? metodo passado como contexto apply_all_transformations
        """
        combined_matrix = np.identity(4)  # Matriz 4x4 para 3D

        # Construir matriz combinada
        for t in self.temp_transformations:
            matrix = self.generate_matrix(t["type"], t["params"], selected_name)
            combined_matrix = combined_matrix @ matrix

        # Aplicar transformação ao objeto selecionado
        for obj in self.display_file:
            if obj.name == selected_name:
                new_coords = []
                
                # Verificar tipo de objeto
                if isinstance(obj, (Ponto3D, Objeto3D, BezierPatch, BezierSurface)):
                    # Processar coordenadas 3D
                    for coord in obj.coordinates:
                        # Garantir que temos pelo menos 3 coordenadas (x,y,z)
                        x = coord[0]
                        y = coord[1] if len(coord) > 1 else 0
                        z = coord[2] if len(coord) > 2 else 0
                        
                        # Aplicar transformação
                        point = np.array([x, y, z, 1])
                        transformed = combined_matrix @ point
                        new_coords.append((transformed[0], transformed[1], transformed[2]))
                        
                else:
                    # Processar coordenadas 2D
                    for coord in obj.coordinates:
                        # Garantir que temos pelo menos 2 coordenadas (x,y)
                        x = coord[0]
                        y = coord[1] if len(coord) > 1 else 0
                        
                        # Aplicar transformação com Z=0
                        point = np.array([x, y, 0, 1])
                        transformed = combined_matrix @ point
                        new_coords.append((transformed[0], transformed[1]))
                
                # Atualizar coordenadas do objeto
                obj.coordinates = new_coords
                break

        self.redraw()
        window.destroy()

    def add_point(self, coords_entry):
        coords = self.parse_input(coords_entry)
        if len(coords) == 1:
            ponto = Point(coords, color=self.selected_color)
            self.display_file.append(ponto)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Ponto, insira apenas uma coordenada.")

    def add_line(self, coords_entry):
        coords = self.parse_input(coords_entry)
        if len(coords) == 2:
            linha = Line(coords, color=self.selected_color)
            self.display_file.append(linha)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar uma Linha, insira exatamente duas coordenadas.")

    def add_polygon(self, coords_entry):
        coords = self.parse_input(coords_entry)
        if len(coords) >= 3:
            poligono = Polygon(coords, color=self.selected_color, filled=self.fill_var.get())
            self.display_file.append(poligono)
            self.fill_var.set(False)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Para adicionar um Polígono, insira pelo menos três coordenadas.")
    
    def add_bezier_curve(self, coords_entry):
        coords = self.parse_input(coords_entry)
        if len(coords) >= 4 and (len(coords) - 4) % 3 == 0:
            curva = Curve2D(coords, color=self.selected_color)
            self.display_file.append(curva)
            self._update_object_list()
            self.redraw()
        else:
            messagebox.showerror("Erro de Entrada", "Uma curva Bézier requer pelo menos 4 pontos de controle, e cada segmento adicional requer 3 pontos.")
    
    def add_bspline(self, coords_entry):
        coords = self.parse_input(coords_entry)
        try:
            bspline = BSpline(coords, color=self.selected_color)
            self.display_file.append(bspline)
            self._update_object_list()
            self.redraw()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar B-Spline:\n{str(e)}")
    
    def add_ponto3d(self, coords_entry):
        coords = eval(coords_entry.get().strip())
        try:
            if len(coords) == 3:
                ponto3d = Ponto3D(coords, color=self.selected_color)
                self.display_file.append(ponto3d)
                self._update_object_list()
                self.redraw()
            else:
                messagebox.showerror("Erro", "Ponto3D requer exatamente 3 coordenadas (x, y, z)")
        except Exception as e:
            messagebox.showerror("Erro", f"Coordenadas inválidas: {str(e)}")
    
    def add_objeto3d(self, segments_entry):
        try:
            segments = eval(segments_entry.get().strip())
            if len(segments) > 0 and all(len(seg) == 2 for seg in segments):
                objeto = Objeto3D(segments, color=self.selected_color)
                self.display_file.append(objeto)
                self._update_object_list()
                self.redraw()
            else:
                messagebox.showerror("Erro", "Objeto3D requer uma lista de segmentos [(p1, p2), ...]")
        except Exception as e:
            messagebox.showerror("Erro", f"Segmentos inválidos: {str(e)}")

    def add_bezier_patch(self):
        """
        Adiciona um retalho bicúbico de Bézier a partir da entrada do usuário.

        DOC IAgen:
        Foi usado IA fazer o parse da entrada do usuario
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Dado essa classe de superficie BezierPatch, como posso fazer o parse de uma entrada do usuario? Colar codigo da classe
        """
        input_str = self.bezier_entry.get().strip()
        try:
            if not input_str:
                raise ValueError("Entrada vazia!")
            
            # Processa linhas e pontos
            rows = input_str.split(';')
            if len(rows) != 4:
                raise ValueError("Deve ter 4 linhas separadas por ';'")
            
            control_points = []
            for row in rows:
                clean_row = row.strip().replace(' ', '').replace('),(', '),(')
                points = eval(f'[{clean_row}]')
                
                if len(points) != 4:
                    raise ValueError(f"Cada linha deve ter 4 pontos. Linha inválida: {row}")
                
                # Converte para tuplas 3D
                for p in points:
                    if len(p) != 3:
                        raise ValueError(f"Ponto deve ser 3D (x,y,z). Ponto inválido: {p}")
                    control_points.append((p[0], p[1], p[2]))
            
            if len(control_points) != 16:
                raise ValueError(f"Total de pontos deve ser 16. Encontrados: {len(control_points)}")
            
            # Cria e adiciona o retalho
            patch = BezierPatch(control_points, self.selected_color)
            self.display_file.append(patch)
            self._update_object_list()
            self.redraw()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Entrada inválida:\n{str(e)}")

    def clip_object(self, obj):
        if isinstance(obj, Point): # Objeto 2D Ponto
            return obj if self.clip_point(obj) else None
        elif isinstance(obj, Line): # Objeto 2D Linha
            return self.clip_line(obj)
        elif isinstance(obj, Polygon): # Objeto 2D Polígono
            return self.clip_polygon(obj)
        elif isinstance(obj, Curve2D):
            obj.clip({
                "xmin": self.window["xmin"], "ymin": self.window["ymin"],
                "xmax": self.window["xmax"], "ymax": self.window["ymax"]
            })
            return obj
        elif isinstance(obj, BSpline):
            obj.clip({
                "xmin": self.window["xmin"], "ymin": self.window["ymin"],
                "xmax": self.window["xmax"], "ymax": self.window["ymax"]
            })
            return obj

        elif isinstance(obj, Ponto3D):
            x, y, z = obj.coordinates[0] 
            projected_coords = self.get_projected_2d_coords(x, y, z)
            if projected_coords:
                # Cria um objeto Ponto 2D temporário para clipping
                # As coordenadas de 'projected_coords' já estão no "espaço da window"
                temp_point_2d = Point([projected_coords], color=obj.color)
                if self.clip_point(temp_point_2d): # clip_point usa self.window
                    # Retorna um novo objeto Point 2D com as coordenadas projetadas
                    # O nome do objeto original é perdido aqui, mas é para desenho.
                    return Point([projected_coords], color=obj.color) 
            return None

        elif isinstance(obj, Objeto3D):
            clipped_2d_lines = []
            for p1_3d, p2_3d in obj.segments:
                # Projeta os dois pontos do segmento 3D para 2D
                p1_2d_proj = self.get_projected_2d_coords(p1_3d[0], p1_3d[1], p1_3d[2])
                p2_2d_proj = self.get_projected_2d_coords(p2_3d[0], p2_3d[1], p2_3d[2])

                if p1_2d_proj and p2_2d_proj: # Se ambos os pontos puderam ser projetados
                    # Cria um objeto Linha 2D temporário com as coordenadas projetadas
                    line_to_clip = Line([p1_2d_proj, p2_2d_proj], color=obj.color)
                    # Aplica o clipping 2D (Cohen-Sutherland ou Liang-Barsky)
                    clipped_line_segment = self.clip_line(line_to_clip) 
                    if clipped_line_segment:
                        clipped_2d_lines.append(clipped_line_segment)
            return clipped_2d_lines # Retorna uma lista de objetos Linha 2D clipados
        elif isinstance(obj, BezierPatch):
            """
            Faz o clipping de um BezierPatch, retornando uma lista de linhas clipadas.

            DOC IAgen:
            Foi usado IA parfa entender como clipar um objeto 3D em 2D e como podemos fazer essa conversão
            DeepSeek https://chat.deepseek.com

            Prompt usado:
            Como funciona o clipping de um objeto 3D para 2D em computação gráfica? Explique como converter e recortar objetos 3D fora da visão do canvas.
            """
            # Similar ao Objeto3D, mas iterando sobre as linhas da malha da superfície
            clipped_patch_lines = []
            resolution = obj.resolution
            # obj.surface_points são os pontos 3D da superfície já calculados
            
            # Projetar todos os pontos da superfície primeiro
            projected_surface_points = []
            for pt3d in obj.surface_points:
                proj_pt = self.get_projected_2d_coords(pt3d[0], pt3d[1], pt3d[2])
                projected_surface_points.append(proj_pt)

            # Linhas na direção U
            for i in range(resolution):
                for j in range(resolution - 1):
                    idx1 = i * resolution + j
                    idx2 = i * resolution + j + 1
                    p1_2d_proj = projected_surface_points[idx1]
                    p2_2d_proj = projected_surface_points[idx2]
                    if p1_2d_proj and p2_2d_proj:
                        line_to_clip = Line([p1_2d_proj, p2_2d_proj], color=obj.color)
                        clipped_segment = self.clip_line(line_to_clip)
                        if clipped_segment:
                            clipped_patch_lines.append(clipped_segment)
            # Linhas na direção V
            for j in range(resolution):
                for i in range(resolution - 1):
                    idx1 = i * resolution + j
                    idx2 = (i + 1) * resolution + j
                    p1_2d_proj = projected_surface_points[idx1]
                    p2_2d_proj = projected_surface_points[idx2]
                    if p1_2d_proj and p2_2d_proj:
                        line_to_clip = Line([p1_2d_proj, p2_2d_proj], color=obj.color)
                        clipped_segment = self.clip_line(line_to_clip)
                        if clipped_segment:
                            clipped_patch_lines.append(clipped_segment)
            return clipped_patch_lines
            
        return None 
    
    def clip_bspline(self, bspline):
        bspline.clip({
            "xmin": self.window["xmin"],
            "ymin": self.window["ymin"],
            "xmax": self.window["xmax"],
            "ymax": self.window["ymax"]
        })
        return bspline
    
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
        self._draw_viewport()

        for obj_original in self.display_file:
            # clip_object agora lida com a projeção 3D para 2D e o clipping 2D subsequente.
            # Para objetos 3D, ele retorna uma lista de primitivas 2D (Lines) ou um Point 2D.
            # Para objetos 2D, ele retorna o objeto 2D clipado ou None.
            drawable_primitives = self.clip_object(obj_original)

            if drawable_primitives:
                if isinstance(drawable_primitives, list): 
                    # Caso de Objeto3D ou BezierPatch, que retornam lista de Linhas 2D
                    for primitive_2d in drawable_primitives:
                        # primitive_2d é um objeto Line (ou Point) com coordenadas já no "espaço da window"
                        # viewport_transform (parte 2D) fará a conversão de window para viewport
                        primitive_2d.draw(self.canvas, self.viewport_transform)
                else: 
                    # Caso de Point, Line, Polygon, Curve2D, BSpline (2D originais ou Ponto3D projetado)
                    # As coordenadas já estão no "espaço da window" (para Ponto3D projetado) ou são originais (para 2D)
                    # viewport_transform (parte 2D) fará a conversão de window para viewport
                    drawable_primitives.draw(self.canvas, self.viewport_transform)

    def parse_input(self, coords_entry):
        try:
            input_str = coords_entry.get().strip()
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
    
    def clip_point_3d(self, point):
        x, y, z = point.coordinates[0]
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

    def world_to_window_local(self, x, y):
        """ Converte coordenadas mundiais para o sistema local da window (considera rotação)"""
        cx = (self.window["xmin"] + self.window["xmax"]) / 2
        cy = (self.window["ymin"] + self.window["ymax"]) / 2
        theta = -self.window["rotation"]
        
        # Translada e rotaciona
        x_rot = (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta) + cx
        y_rot = (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta) + cy
        
        return x_rot, y_rot

    def window_local_to_world(self, x_local, y_local):
        """Converte coordenadas locais da window de volta para o sistema mundial"""
        cx = (self.window["xmin"] + self.window["xmax"]) / 2
        cy = (self.window["ymin"] + self.window["ymax"]) / 2
        theta = self.window["rotation"]
        
        # Rotaciona e translada
        x_world = (x_local - cx) * math.cos(theta) - (y_local - cy) * math.sin(theta) + cx
        y_world = (x_local - cx) * math.sin(theta) + (y_local - cy) * math.cos(theta) + cy
        
        return x_world, y_world

    def clip_line_cohen_sutherland(self, line):
        (x1, y1), (x2, y2) = line.coordinates

        # Converte para coordenadas locais da window
        x1w, y1w = self.world_to_window_local(x1, y1)
        x2w, y2w = self.world_to_window_local(x2, y2)

        code_start = self.compute_out_code(x1w, y1w)
        code_end = self.compute_out_code(x2w, y2w)
        
        while True:
            if not (code_start | code_end):
                # Converte de volta para coordenadas mundiais
                x1f, y1f = self.window_local_to_world(x1w, y1w)
                x2f, y2f = self.window_local_to_world(x2w, y2w)
                return Line([(x1f, y1f), (x2f, y2f)], color=line.color)
            
            elif code_start & code_end:
                return None
            
            else:
                code_out = code_start if code_start else code_end
                
                if code_out & self.TOP:
                    x = x1w + (x2w - x1w) * (self.window["ymax"] - y1w) / (y2w - y1w) if y2w != y1w else x1w
                    y = self.window["ymax"]
                elif code_out & self.BOTTOM:
                    x = x1w + (x2w - x1w) * (self.window["ymin"] - y1w) / (y2w - y1w) if y2w != y1w else x1w
                    y = self.window["ymin"]
                elif code_out & self.RIGHT:
                    y = y1w + (y2w - y1w) * (self.window["xmax"] - x1w) / (x2w - x1w) if x2w != x1w else y1w
                    x = self.window["xmax"]
                elif code_out & self.LEFT:
                    y = y1w + (y2w - y1w) * (self.window["xmin"] - x1w) / (x2w - x1w) if x2w != x1w else y1w
                    x = self.window["xmin"]

                if code_out == code_start:
                    x1w, y1w = x, y
                    code_start = self.compute_out_code(x1w, y1w)
                else:
                    x2w, y2w = x, y
                    code_end = self.compute_out_code(x2w, y2w)

    def clip_line_liang_barsky(self, line):
        (x1, y1), (x2, y2) = line.coordinates

        # Converte para coordenadas locais da window
        x1w, y1w = self.world_to_window_local(x1, y1)
        x2w, y2w = self.world_to_window_local(x2, y2)

        dx = x2w - x1w
        dy = y2w - y1w
        p = [-dx, dx, -dy, dy]
        q = [
            x1w - self.window["xmin"],
            self.window["xmax"] - x1w,
            y1w - self.window["ymin"],
            self.window["ymax"] - y1w
        ]
        
        u1, u2 = 0.0, 1.0
        for i in range(4):
            if p[i] == 0:
                if q[i] < 0:
                    return None
            else:
                u = q[i]/p[i]
                if p[i] < 0:
                    u1 = max(u1, u)
                else:
                    u2 = min(u2, u)

        if u1 > u2:
            return None

        # Calcula pontos clipados em coordenadas locais
        x1c = x1w + u1 * dx
        y1c = y1w + u1 * dy
        x2c = x1w + u2 * dx
        y2c = y1w + u2 * dy

        # Converte de volta para coordenadas mundiais
        x1f, y1f = self.window_local_to_world(x1c, y1c)
        x2f, y2f = self.window_local_to_world(x2c, y2c)

        return Line([(x1f, y1f), (x2f, y2f)], color=line.color)
    
    def get_projected_2d_coords(self, x_world, y_world, z_world):
        """
        Transforma um ponto 3D do mundo para coordenadas 2D no plano de projeção,
        compatíveis com self.window para clipping 2D.
        Retorna (x_proj, y_proj) ou None se a projeção não for possível.

        DOC IAgen:
        Foi usado IA entender como representrar um objeto com cordenadas 3D em 2D no plano de projecao em Python
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Como representrar um objeto com cordenadas 3D em 2D no plano de projecao em Python, demos o contexto do codigo atual antes da implementacao
        """
        try:
            d = float(self.d_entry.get())
            if d <= 1e-6: # d deve ser positivo e não muito pequeno
                # messagebox.showwarning("Aviso", "Distância de projeção 'd' muito pequena ou inválida. Usando valor padrão.")
                d = 200 
        except ValueError:
            d = 200

        # VRP (View Reference Point) - Centro da window, no plano z=0 do mundo
        vrp = np.array([
            (self.window["xmin"] + self.window["xmax"]) / 2,
            (self.window["ymin"] + self.window["ymax"]) / 2,
            0  # Assumindo VRP no plano XY do mundo para simplificar a câmera canônica inicial
        ])
        
        # VPN (View Plane Normal) - Olhando ao longo do eixo Z do mundo
        vpn = np.array([0, 0, 1])
        
        # VUP (View Up Vector) - Eixo Y do mundo como "para cima"
        vup = np.array([0, 1, 0])
        
        # Normalizar VPN
        n = vpn / np.linalg.norm(vpn)
        # Calcular u (eixo x da view)
        u = np.cross(vup, n)
        if np.linalg.norm(u) < 1e-6: # vup e n são colineares
            # Tentar um vup alternativo se o padrão for problemático (ex: olhando reto para cima/baixo)
            if abs(n[1]) > 0.99: # n é próximo de (0, +/-1, 0)
                u = np.cross(np.array([0,0,1]), n) # Usar Z global como up temporário
            else: 
                u = np.cross(np.array([1,0,0]), n) # Usar X global como up temporário

        u = u / np.linalg.norm(u)
        # Calcular v (eixo y da view)
        v = np.cross(n, u)

        # Matriz de Translação para levar VRP à origem
        T_vrp = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [-vrp[0], -vrp[1], -vrp[2], 1]
        ])

        # Matriz de Rotação para alinhar eixos do mundo com eixos da view
        R_view = np.array([
            [u[0], v[0], n[0], 0], # Colunas são os eixos da view no sistema do mundo
            [u[1], v[1], n[1], 0],
            [u[2], v[2], n[2], 0],
            [0,    0,    0,    1]
        ])
  
        R_align = np.array([
            [u[0], v[0], n[0], 0],
            [u[1], v[1], n[1], 0],
            [u[2], v[2], n[2], 0],
            [0,    0,    0,    1]
        ])

        R_matrix_original_style = np.array([
            [u[0], u[1], u[2], 0],
            [v[0], v[1], v[2], 0],
            [n[0], n[1], n[2], 0],
            [0,    0,    0,    1]
        ])
        T_matrix_original_style = np.array([
            [1, 0, 0, -vrp[0]],
            [0, 1, 0, -vrp[1]],
            [0, 0, 1, -vrp[2]],
            [0, 0, 0, 1]
        ])
        M_view_transform_col = R_matrix_original_style @ T_matrix_original_style # Para P_view_col = M @ P_world_col

        point_world_col = np.array([x_world, y_world, z_world, 1]).reshape(4,1)
        transformed_view_col = M_view_transform_col @ point_world_col
        
        x_v, y_v, z_v = transformed_view_col[0,0], transformed_view_col[1,0], transformed_view_col[2,0]

        if self.projection_type.get() == "parallel":
            x_proj = x_v
            y_proj = y_v
        elif self.projection_type.get() == "perspective":
            # COP está em (0,0,-d) no sistema da view, plano de projeção em z_view=0
            denominator = z_v + d 
            if abs(denominator) < 1e-6: # Evita divisão por zero
                return None
            if denominator <= 0: # Ponto está no COP ou atrás dele (inválido para esta projeção)
                 return None

            x_proj = (x_v * d) / denominator
            y_proj = (y_v * d) / denominator
        else:
            return None # Tipo de projeção desconhecido
            
        return x_proj, y_proj

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema Gráfico 2D com Lista de Objetos")
    root.geometry("1020x700")
    app = GraphicsSystem(root)
    root.mainloop()