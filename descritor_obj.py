from objects import GraphicObject, Point, Line, Polygon, Curve2D, BSpline, BezierPatch
from tkinter import messagebox

class DescritorOBJ:
    @staticmethod
    def read_obj(filename):
        """
        Lê arquivo .obj com suporte a vértices 2D/3D, elementos gráficos e retalhos Bézier.
        """
        display_file = []
        vertices = []
        color_map = {}
        fill_map = {}
        elements = []
        bezier_patches = []  
        bezier_counter = 0  # NOVO: Contador para retalhos Bézier

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

                # Processamento de retalhos Bézier (ALTERADO: nomeação)
                elif parts[0] == 'bp':
                    try:
                        points_str = line[3:].replace(' ', '').split(';')
                        control_points = []
                        for row in points_str:
                            row_points = eval(f'[{row}]')
                            control_points.extend([(p[0], p[1], p[2]) for p in row_points])
                        if len(control_points) == 16:
                            bezier_counter += 1  # Incrementa contador
                            name = f"BP{bezier_counter}"  # Gera nome único
                            patch = BezierPatch(control_points)
                            patch._name = name  # Atribui nome ao retalho
                            bezier_patches.append(patch)
                    except Exception as e:
                        print(f"Erro ao ler retalho Bézier: {str(e)}")

                # Processamento de cores
                elif parts[0] == 'c' and len(parts) >= 3:
                    color_map[parts[1]] = parts[2]
                
                # Processamento do preenchimento 
                elif parts[0] == 'fill' and len(parts) >= 3:
                    nome = parts[1]
                    valor = parts[2].lower() == 'true'
                    fill_map[nome] = valor

                # Processamento de elementos gráficos
                elif parts[0] in ['p', 'l', 'f', 'c', 'b']:
                    element_type = parts[0]
                    indices = [int(part.split('/')[0]) for part in parts[1:]]
                    elements.append((element_type, indices))

        # Criação de objetos gráficos 2D (existente)
        max_counter = 0
        for i, (elem_type, indices) in enumerate(elements):
            coords = [vertices[idx-1] for idx in indices]
            
            obj_prefix = {
                'p': 'P',
                'l': 'L',
                'f': 'W',
                'c': 'C',
                'b': 'B'
            }[elem_type]
            obj_number = i + 1
            name = f"{obj_prefix}{obj_number}"
            color = color_map.get(name, "#00aaff")

            if elem_type == 'p' and len(coords) == 1:
                obj = Point([(p[0], p[1]) for p in coords], color)
            elif elem_type == 'l' and len(coords) == 2:
                obj = Line([(p[0], p[1]) for p in coords], color)
            elif elem_type == 'f' and len(coords) >= 3:
                fill = fill_map.get(name, True)
                obj = Polygon([(p[0], p[1]) for p in coords], color, fill)
            elif elem_type == 'c' and len(coords) >= 4 and (len(coords) - 4) % 3 == 0:
                obj = Curve2D([(p[0], p[1]) for p in coords], color)
            elif elem_type == 'b' and len(coords) >= 4:
                obj = BSpline([(p[0], p[1]) for p in coords], color)
            else:
                continue

            obj._name = name
            max_counter = max(max_counter, obj_number)
            display_file.append(obj)

        # ADICIONADO: Adiciona retalhos à display_file
        for patch in bezier_patches:
            display_file.append(patch)

        # Aplica cores a todos os objetos (incluindo retalhos)
        for obj in display_file:
            if obj.name in color_map:
                obj.color = color_map[obj.name]

        GraphicObject._counter = max_counter
        return display_file
    
    @staticmethod
    def write_obj(display_file, filename):
        """
        Escreve arquivo .obj com suporte para objetos 2D, 3D e retalhos Bézier.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Sistema Gráfico - Arquivo OBJ\n")
                f.write("o CenaCompleta\n")

                # Escreve vértices (agora suporta 3D)
                vertex_index = 1
                all_vertices = []
                vertex_map = {}

                for obj in display_file:
                    for coord in obj.coordinates:
                        # Converte para 3D se necessário
                        if len(coord) == 2:
                            coord_3d = (coord[0], coord[1], 0.0)
                        else:
                            coord_3d = coord
                        
                        if coord_3d not in vertex_map:
                            all_vertices.append(coord_3d)
                            vertex_map[coord_3d] = vertex_index
                            vertex_index += 1

                # Escreve vértices 3D
                for x, y, z in all_vertices:
                    f.write(f"v {x:.2f} {y:.2f} {z:.2f}\n")

                # Escreve cores
                for obj in display_file:
                    f.write(f"c {obj.name} {obj.color}\n")

                # Escreve elementos e retalhos
                for obj in display_file:
                    # Retalhos Bézier (novo)
                    if isinstance(obj, BezierPatch):
                        rows = []
                        for i in range(4):
                            row_points = obj.coordinates[i*4 : (i+1)*4]
                            row_str = ",".join([f"({p[0]:.2f},{p[1]:.2f},{p[2]:.2f})" for p in row_points])
                            rows.append(row_str)
                        f.write(f"bp {';'.join(rows)}\n")
                        continue
                    
                    # Objetos 2D existentes
                    indices = []
                    for coord in obj.coordinates:
                        coord_3d = (coord[0], coord[1], 0.0) if len(coord) == 2 else coord
                        indices.append(str(vertex_map[coord_3d]))
                    
                    if isinstance(obj, Point):
                        f.write(f"p {' '.join(indices)}\n")
                    elif isinstance(obj, Line):
                        f.write(f"l {' '.join(indices)}\n")
                    elif isinstance(obj, Polygon):
                        f.write(f"f {' '.join(indices)}\n")
                        f.write(f"fill {obj.name} {str(obj.filled)}\n")
                    elif isinstance(obj, Curve2D):
                        f.write(f"c {' '.join(indices)}\n")
                    elif isinstance(obj, BSpline):
                        f.write(f"b {' '.join(indices)}\n")

                f.write("\n# Fim do arquivo\n")
                return True

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
            return False