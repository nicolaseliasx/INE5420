class DescritorOBJ:
    @staticmethod
    def read_obj(filename):
        display_file = []
        vertices = []
        color_map = {}  # Mapeia nomes de objetos para cores
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
                obj = Polygon(coords, color)
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
                    else:
                        raise TypeError(f"Tipo inválido: {type(obj)}")

                f.write("\n# Fim do arquivo\n")
                return True

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")
            return False