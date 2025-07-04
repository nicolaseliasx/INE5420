from objects import BSplineSurface, GraphicObject, Point, Line, Polygon, Curve2D, BSpline, BezierPatch, Objeto3D, Ponto3D, BezierSurface
from tkinter import messagebox

class DescritorOBJ:
    @staticmethod
    def read_obj(filename):
        """
        Lê arquivo .obj com suporte a todos os objetos gráficos 2D/3D

        DOC IAgen:
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Leia um arquivo .obj com suporte para objetos gráficos 2D e 3D, incluindo retalhos Bézier. 
        Copiamos um exemplo de arquivo .obj e adaptaamos para funcionar na nossa necessidade
        """
        display_file = []
        vertices = []
        color_map = {}
        fill_map = {}
        elements = []
        bezier_patches = []
        objects_3d = []
        surfaces = []
        current_patches = []

        GraphicObject.reset_counter()

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
                    if len(parts[1:]) == 2:
                        x, y = map(float, parts[1:3])
                        vertices.append((x, y, 0.0))
                    elif len(parts[1:]) == 3:
                        x, y, z = map(float, parts[1:4])
                        vertices.append((x, y, z))

                # Processamento de retalhos Bézier
                elif parts[0] == 'bp':
                    try:
                        points_str = line[3:].replace(' ', '').split(';')
                        control_points = []
                        for row in points_str:
                            row_points = eval(f'[{row}]')
                            control_points.extend([(p[0], p[1], p[2]) for p in row_points])
                        if len(control_points) == 16:
                            patch = BezierPatch(control_points)
                            bezier_patches.append(patch)
                    except Exception as e:
                        print(f"Erro ao ler retalho Bézier: {str(e)}")

                # Processamento de cores
                elif parts[0] == 'c' and len(parts) >= 3:
                    color_map[parts[1]] = parts[2]

                # Processamento de preenchimento
                elif parts[0] == 'fill' and len(parts) >= 3:
                    fill_map[parts[1]] = parts[2].lower() == 'true'

                # Processamento de pontos 3D
                elif parts[0] == 'p3d':
                    try:
                        indices = [int(p.split('/')[0]) for p in parts[1:]]
                        if len(indices) != 1:
                            continue
                        vertex = vertices[indices[0]-1]
                        obj = Ponto3D([vertex], "#00aaff")
                        display_file.append(obj)
                    except Exception as e:
                        print(f"Erro lendo Ponto3D: {str(e)}")

                # Processamento de objetos 3D
                elif parts[0] == 'obj3d':
                    try:
                        indices = [int(p.split('/')[0]) for p in parts[1:]]
                        if len(indices) % 2 != 0:
                            continue
                        segments = []
                        for i in range(0, len(indices), 2):
                            v1 = vertices[indices[i]-1]
                            v2 = vertices[indices[i+1]-1]
                            segments.append((v1, v2))
                        obj = Objeto3D(segments, "#00aaff")
                        display_file.append(obj)
                    except Exception as e:
                        print(f"Erro lendo Objeto3D: {str(e)}")

                # Processamento de superfícies Bézier
                elif parts[0] == 'bs':
                    try:
                        patch_names = parts[1:]
                        patches = [p for p in bezier_patches if p.name in patch_names]
                        if patches:
                            surface = BezierSurface(patches, "#00aaff")
                            surfaces.append(surface)
                    except Exception as e:
                        print(f"Erro lendo BezierSurface: {str(e)}")

                # Processamento de elementos gráficos 2D
                elif parts[0] in ['p', 'l', 'f', 'c', 'b']:
                    elements.append((parts[0], [int(p.split('/')[0]) for p in parts[1:]]))

                elif parts[0] == 'bspm':
                    try:
                        # O restante da linha é a string da matriz
                        matrix_str = " ".join(parts[1:])
                        rows_str = matrix_str.split(';')
                        control_matrix = []
                        for row_str in rows_str:
                            if not row_str.strip(): continue
                            # Usamos eval para parsear a string formatada
                            points_in_row = list(eval(f"[{row_str}]"))
                            control_matrix.append(points_in_row)
                        
                        if control_matrix:
                            # Cria um objeto temporário que será colorido depois
                            # A cor padrão será sobrescrita se uma diretiva 'c' for encontrada
                            bspline_surface = BSplineSurface(control_matrix, "#00aaff") 
                            display_file.append(bspline_surface)

                    except Exception as e:
                        print(f"Erro ao ler superfície B-Spline (bspm): {str(e)}")

        # Processar elementos 2D
        max_counter = 0
        for i, (elem_type, indices) in enumerate(elements):
            coords = [vertices[idx-1] for idx in indices]
            obj = None
            color = "#00aaff"
            name = ""

            try:
                if elem_type == 'p' and len(coords) == 1:
                    obj = Point([(p[0], p[1]) for p in coords], color)
                elif elem_type == 'l' and len(coords) == 2:
                    obj = Line([(p[0], p[1]) for p in coords], color)
                elif elem_type == 'f' and len(coords) >= 3:
                    obj = Polygon([(p[0], p[1]) for p in coords], color, False)
                elif elem_type == 'c' and len(coords) >= 4:
                    obj = Curve2D([(p[0], p[1]) for p in coords], color)
                elif elem_type == 'b' and len(coords) >= 4:
                    obj = BSpline([(p[0], p[1]) for p in coords], color)

                if obj:
                    max_counter = max(max_counter, GraphicObject._counter)
                    display_file.append(obj)
            except Exception as e:
                print(f"Erro processando elemento {elem_type}: {str(e)}")

        # Adicionar objetos 3D ao display file
        display_file.extend(bezier_patches)
        display_file.extend(surfaces)
        display_file.extend(objects_3d)

        # Aplicar cores e preenchimento
        for obj in display_file:
            if obj.name in color_map:
                obj.color = color_map[obj.name]
            if isinstance(obj, Polygon) and obj.name in fill_map:
                obj.filled = fill_map[obj.name]

        GraphicObject._counter = max_counter
        return display_file
    
    @staticmethod
    def write_obj(display_file, filename):
        """
        DOC IAgen:
        DeepSeek https://chat.deepseek.com

        Prompt usado:
        Escreva um arquivo .obj com suporte a tudo que o read faz e gere um arquivo que consiga ser interpretado no read_obj. 
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Sistema Gráfico - Arquivo OBJ\n")
                f.write("o CenaCompleta\n\n")

                # Fase 1: Coleta de todos os vértices únicos
                vertex_map = {}
                counter = 1
                all_vertices = []

                # Função para adicionar vértices 3D
                def add_vertex(p):
                    nonlocal counter
                    if p not in vertex_map:
                        all_vertices.append(p)
                        vertex_map[p] = counter
                        counter += 1

                # Coleta vértices de todos os objetos
                for obj in display_file:
                    if isinstance(obj, Ponto3D):
                        p = obj.coordinates[0]
                        add_vertex(p)
                    
                    elif isinstance(obj, Objeto3D):
                        for p1, p2 in obj.segments:
                            add_vertex(p1)
                            add_vertex(p2)
                    
                    elif isinstance(obj, BezierPatch):
                        for p in obj.coordinates:
                            add_vertex(p)
                    
                    elif isinstance(obj, (Point, Line, Polygon, Curve2D, BSpline)):
                        for coord in obj.coordinates:
                            p = (coord[0], coord[1], 0.0)
                            add_vertex(p)

                # Escreve vértices
                f.write("# Vértices\n")
                for x, y, z in all_vertices:
                    f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
                f.write("\n")

                # Fase 2: Escreve definições de cores
                f.write("# Definições de cores\n")
                for obj in display_file:
                    if hasattr(obj, 'color'):
                        f.write(f"c {obj.name} {obj.color}\n")
                f.write("\n")

                # Fase 3: Escreve elementos gráficos
                f.write("# Elementos gráficos\n")
                for obj in display_file:
                    # Ponto3D
                    if isinstance(obj, Ponto3D):
                        p = obj.coordinates[0]
                        idx = vertex_map[p]
                        f.write(f"p3d {idx}\n")
                    
                    # Objeto3D
                    elif isinstance(obj, Objeto3D):
                        indices = []
                        for p1, p2 in obj.segments:
                            indices.append(str(vertex_map[p1]))
                            indices.append(str(vertex_map[p2]))
                        f.write(f"obj3d {' '.join(indices)}\n")
                    
                    # BezierPatch
                    elif isinstance(obj, BezierPatch):
                        # Organiza pontos em 4x4
                        points = []
                        for i in range(4):
                            row = obj.coordinates[i*4 : (i+1)*4]
                            row_str = ",".join(
                                [f"({p[0]:.4f},{p[1]:.4f},{p[2]:.4f})" 
                                for p in row]
                            )
                            points.append(row_str)
                        f.write(f"bp {';'.join(points)}\n")
                    
                    # BezierSurface
                    elif isinstance(obj, BezierSurface):
                        patch_names = [p.name for p in obj.patches]
                        f.write(f"bs {' '.join(patch_names)}\n")
                    
                    # Polígono 2D
                    elif isinstance(obj, Polygon):
                        indices = []
                        for coord in obj.coordinates:
                            p = (coord[0], coord[1], 0.0)
                            indices.append(str(vertex_map[p]))
                        f.write(f"f {' '.join(indices)}\n")
                        f.write(f"fill {obj.name} {str(obj.filled).lower()}\n")
                    
                    # Curva Bezier 2D
                    elif isinstance(obj, Curve2D):
                        indices = []
                        for coord in obj.coordinates:
                            p = (coord[0], coord[1], 0.0)
                            indices.append(str(vertex_map[p]))
                        f.write(f"c {' '.join(indices)}\n")
                    
                    # B-Spline 2D
                    elif isinstance(obj, BSpline):
                        indices = []
                        for coord in obj.coordinates:
                            p = (coord[0], coord[1], 0.0)
                            indices.append(str(vertex_map[p]))
                        f.write(f"b {' '.join(indices)}\n")
                    
                    # Linha 2D
                    elif isinstance(obj, Line):
                        indices = []
                        for coord in obj.coordinates:
                            p = (coord[0], coord[1], 0.0)
                            indices.append(str(vertex_map[p]))
                        f.write(f"l {' '.join(indices)}\n")
                    
                    # Ponto 2D
                    elif isinstance(obj, Point):
                        p = (obj.coordinates[0][0], obj.coordinates[0][1], 0.0)
                        idx = vertex_map[p]
                        f.write(f"p {idx}\n")

                    elif isinstance(obj, BSplineSurface):
                        f.write(f"# Definição da Superfície B-Spline: {obj.name}\n")
                        
                        rows, cols, _ = obj.control_matrix.shape
                        matrix_str_rows = []
                        for i in range(rows):
                            row_points = obj.control_matrix[i]
                            row_str = ",".join([f"({p[0]:.4f},{p[1]:.4f},{p[2]:.4f})" for p in row_points])
                            matrix_str_rows.append(row_str)

                        matrix_full_str = ";".join(matrix_str_rows)
                        f.write(f"bspm {matrix_full_str}\n")
                        f.write(f"c {obj.name} {obj.color}\n\n")

                f.write("\n# Fim do arquivo\n")
                return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
            return False