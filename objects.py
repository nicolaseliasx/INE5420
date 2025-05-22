import tkinter as tk
from abc import ABC, abstractmethod
import numpy as np
from enum import Enum
import math

class ObjectType(Enum):
    PONTO = "Ponto"
    LINHA = "Linha"
    POLIGONO = "Polígono"
    CURVA_BEZIER = "Curva Bezier"
    B_SPLINE = "B-Spline"
    PONTO3D = "Ponto3D"
    OBJETO3D = "Objeto3D"

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
    
    def get_coordinates_3d(self, transform):
        coords = []
        for x, y, z in self.coordinates:
            vx, vy = transform(x, y, z)
            coords.extend([vx, vy])
        if len(self.coordinates) >= 3:
            x0, y0, z0 = self.coordinates[0]
            vx0, vy0 = transform(x0, y0, z0)
            coords.extend([vx0, vy0])
        return coords
    
    # def get_coordinates(self, transform):
    #     coords = []
    #     for point in self.coordinates:
    #         if len(point) == 2:  # 2D
    #             x, y = point
    #             vx, vy = transform(x, y)
    #             coords.extend([vx, vy])
    #         elif len(point) == 3:  # 3D
    #             x, y, z = point
    #             vx, vy = transform(x, y, z)
    #             coords.extend([vx, vy])
        
    #     if len(self.coordinates) >= 3:
    #         first_point = self.coordinates[0]
    #         if len(first_point) == 2:
    #             x0, y0 = first_point
    #             vx0, vy0 = transform(x0, y0)
    #         else:
    #             x0, y0, z0 = first_point
    #             vx0, vy0 = transform(x0, y0, z0)
    #         coords.extend([vx0, vy0])
    #     return coords

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


class BSpline(GraphicObject):
    prefix = "B"
    
    def __init__(self, coordinates, color="#00aaff", degree=3):
        super().__init__(coordinates, color)
        self.degree = degree
        self._validate_input()
        self.curve_points = []
        self._compute_entire_curve()
        
    def _validate_input(self):
        if len(self.coordinates) < 4:
            raise ValueError("B-Spline requer pelo menos 4 pontos de controle")
        if len(self.coordinates) < self.degree + 1:
            raise ValueError(f"Grau {self.degree} requer pelo menos {self.degree + 1} pontos")

    def _compute_entire_curve(self):
        """Pré-computa todos os pontos da curva usando Forward Differences"""
        n = len(self.coordinates)
        self.curve_points = []
        
        for i in range(n - self.degree):
            segment = self.coordinates[i:i+self.degree+1]
            self.curve_points.extend(self._compute_segment(segment))
            
        self._remove_duplicate_points()

    def _compute_segment(self, control_points, steps=100):
        """Calcula um segmento da curva com Forward Differences"""
        if len(control_points) != 4:
            return []
            
        coeffs = self._calculate_coefficients(control_points)
        points = []
        
        # Parâmetros de diferença
        delta = 1.0 / steps
        delta2 = delta * delta
        delta3 = delta * delta * delta
        
        # Inicialização para X
        x = coeffs['dx']  # Termo constante dx (d)
        dx = (
            coeffs['cx'] * delta +
            coeffs['bx'] * delta2 +
            coeffs['ax'] * delta3
        )
        d2x = (
            2 * coeffs['bx'] * delta2 +
            6 * coeffs['ax'] * delta3
        )
        d3x = 6 * coeffs['ax'] * delta3
        
        # Inicialização para Y
        y = coeffs['dy']  # Termo constante dy (d)
        dy = (
            coeffs['cy'] * delta +
            coeffs['by'] * delta2 +
            coeffs['ay'] * delta3
        )
        d2y = (
            2 * coeffs['by'] * delta2 +
            6 * coeffs['ay'] * delta3
        )
        d3y = 6 * coeffs['ay'] * delta3
        
        # Geração dos pontos
        for _ in range(steps):
            points.append((x, y))
            x += dx
            dx += d2x
            d2x += d3x
            
            y += dy
            dy += d2y
            d2y += d3y
            
        return points


    def _calculate_coefficients(self, control_points):
        """Calcula os coeficientes para B-Spline cúbica uniforme"""
        p0, p1, p2, p3 = control_points
        
        return {
            # Coeficientes para X
            'ax': (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) / 6,
            'bx': (3*p0[0] - 6*p1[0] + 3*p2[0]) / 6,
            'cx': (-3*p0[0] + 3*p2[0]) / 6,
            'dx': (p0[0] + 4*p1[0] + p2[0]) / 6,
            
            # Coeficientes para Y
            'ay': (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) / 6,
            'by': (3*p0[1] - 6*p1[1] + 3*p2[1]) / 6,
            'cy': (-3*p0[1] + 3*p2[1]) / 6,
            'dy': (p0[1] + 4*p1[1] + p2[1]) / 6
        }

    def _remove_duplicate_points(self):
        """Remove pontos duplicados para suavização"""
        unique_points = []
        prev = None
        for p in self.curve_points:
            if prev is None or abs(p[0]-prev[0]) > 1e-6 or abs(p[1]-prev[1]) > 1e-6:
                unique_points.append(p)
                prev = p
        self.curve_points = unique_points

    @property
    def type(self):
        return "B-Spline"

    def draw(self, canvas, transform):
        if not self.curve_points:
            return
            
        visible_points = []
        for x, y in self.curve_points:
            if self._point_inside_clip_window(x, y):
                tx, ty = transform(x, y)
                visible_points.extend([tx, ty])
        
        if len(visible_points) >= 4:
            canvas.create_line(
                *visible_points,
                fill=self.color,
                width=3,
                smooth=True,
                splinesteps=100
            )

    def _point_inside_clip_window(self, x, y):
        return (self.window["xmin"] <= x <= self.window["xmax"] and
                self.window["ymin"] <= y <= self.window["ymax"])

    def clip(self, clip_window):
        """Clipagem otimizada usando bounding box dos pontos de controle"""
        x_coords = [p[0] for p in self.coordinates]
        y_coords = [p[1] for p in self.coordinates]
        
        self.visible = not (
            max(x_coords) < clip_window["xmin"] or
            min(x_coords) > clip_window["xmax"] or
            max(y_coords) < clip_window["ymin"] or
            min(y_coords) > clip_window["ymax"]
        )
        self.window = clip_window

####################### Objetos 3D #######################

class Ponto3D(GraphicObject):
    prefix = "P3D"
    
    def __init__(self, coordinates, color="#00aaff"):
        if len(coordinates) != 3:
            raise ValueError("Ponto3D requer coordenadas (x, y, z)")
        super().__init__([coordinates], color)
    
    @property
    def type(self):
        return "Ponto3D"
    
    def draw(self, canvas, transform):
        vx, vy = self.get_coordinates_3d(transform)
        canvas.create_oval(vx-6, vy-6, vx+6, vy+6, 
                         fill=self.color, outline="#005533", width=2)

class Objeto3D(GraphicObject):
    prefix = "O3D"
    
    def __init__(self, segments, color="#00aaff"):
        self.segments = segments  # Lista de segmentos [(p1, p2), ...] onde p1 e p2 são tuplas (x,y,z)
        # Extrai todas as coordenadas únicas para a lista de coordenadas
        all_points = []
        for p1, p2 in segments:
            all_points.extend([p1, p2])
        # Remove duplicatas mantendo a ordem
        unique_points = []
        seen = set()
        for point in all_points:
            if point not in seen:
                seen.add(point)
                unique_points.append(point)
        super().__init__(unique_points, color)
    
    @property
    def type(self):
        return "Objeto3D"
    
    def draw(self, canvas, transform):
        for p1, p2 in self.segments:
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx1, vy1 = transform(x1, y1, z1)
            vx2, vy2 = transform(x2, y2, z2)
            canvas.create_line(vx1, vy1, vx2, vy2, 
                             fill=self.color, width=2, capstyle=tk.ROUND)

###

class BezierPatch(GraphicObject):
    prefix = "BP"
    
    def __init__(self, control_points, color="#00aaff", resolution=20):
        """
        Representa um retalho bicúbico de Bézier com 16 pontos de controle.
        
        Args:
            control_points (list): 16 pontos 3D em ordem de matriz 4x4
            color (str): Cor da malha
            resolution (int): Número de divisões para cálculo da superfície
        """
        if len(control_points) != 16:
            raise ValueError("Deve haver 16 pontos de controle (4x4)")
        super().__init__(control_points, color)
        self.resolution = resolution
        self.surface_points = []
        self._compute_surface_points()
    
    @property
    def type(self):
        return "Retalho Bézier"
    
    def _compute_surface_points(self):
        """Calcula os pontos da superfície usando funções de base de Bézier bicúbicas."""
        self.surface_points = []
        for u in np.linspace(0, 1, self.resolution):
            for v in np.linspace(0, 1, self.resolution):
                point = self._evaluate_bezier(u, v)
                self.surface_points.append(point)
    
    def _evaluate_bezier(self, u, v):
        """Avalia a superfície nos parâmetros u e v usando combinação linear."""
        B = [(1 - u)**3, 
             3 * u * (1 - u)**2, 
             3 * u**2 * (1 - u), 
             u**3]
        Bv = [(1 - v)**3, 
              3 * v * (1 - v)**2, 
              3 * v**2 * (1 - v), 
              v**3]
        
        x, y, z = 0, 0, 0
        for i in range(4):
            for j in range(4):
                weight = B[i] * Bv[j]
                px, py, pz = self.coordinates[i*4 + j]
                x += px * weight
                y += py * weight
                z += pz * weight
        return (x, y, z)
    
    def draw(self, canvas, transform):
        """Desenha a superfície como uma malha de linhas projetadas com clipping."""
        projected = [transform(x, y, z) for (x, y, z) in self.surface_points]
        
        # Clipping window (viewport coordinates)
        xmin = 20
        ymin = 20
        xmax = canvas.winfo_width() - 20
        ymax = canvas.winfo_height() - 20
        
        # Função para clipar linhas
        def clip_line(x1, y1, x2, y2):
            INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
            def compute_code(x, y):
                code = INSIDE
                if x < xmin:
                    code |= LEFT
                elif x > xmax:
                    code |= RIGHT
                if y < ymin:
                    code |= BOTTOM
                elif y > ymax:
                    code |= TOP
                return code
            
            code1 = compute_code(x1, y1)
            code2 = compute_code(x2, y2)
            accept = False

            while True:
                if not (code1 | code2):
                    accept = True
                    break
                elif code1 & code2:
                    break
                else:
                    x = 0.0
                    y = 0.0
                    code_out = code1 if code1 else code2
                    
                    if code_out & TOP:
                        x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                        y = ymax
                    elif code_out & BOTTOM:
                        x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                        y = ymin
                    elif code_out & RIGHT:
                        y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                        x = xmax
                    elif code_out & LEFT:
                        y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                        x = xmin

                    if code_out == code1:
                        x1, y1 = x, y
                        code1 = compute_code(x1, y1)
                    else:
                        x2, y2 = x, y
                        code2 = compute_code(x2, y2)
            
            if accept:
                return (x1, y1, x2, y2)
            else:
                return None
        
        # Desenha linhas na direção u com clipping
        for i in range(self.resolution):
            for j in range(self.resolution - 1):
                idx = i * self.resolution + j
                x1, y1 = projected[idx]
                x2, y2 = projected[idx + 1]
                clipped = clip_line(x1, y1, x2, y2)
                if clipped:
                    canvas.create_line(clipped[0], clipped[1], clipped[2], clipped[3], 
                                    fill=self.color, width=1)
        
        # Desenha linhas na direção v com clipping
        for j in range(self.resolution):
            for i in range(self.resolution - 1):
                idx = i * self.resolution + j
                idx_next = (i + 1) * self.resolution + j
                x1, y1 = projected[idx]
                x2, y2 = projected[idx_next]
                clipped = clip_line(x1, y1, x2, y2)
                if clipped:
                    canvas.create_line(clipped[0], clipped[1], clipped[2], clipped[3], 
                                    fill=self.color, width=1)

class BezierSurface(GraphicObject):
    prefix = "BS"
    
    def __init__(self, patches, color="#00aaff"):
        """
        Representa uma superfície composta por múltiplos retalhos.
        
        Args:
            patches (list): Lista de objetos BezierPatch
        """
        super().__init__([], color)
        self.patches = patches
    
    @property
    def type(self):
        return "Superfície Bézier"
    
    def draw(self, canvas, transform):
        """Desenha todos os retalhos da superfície."""
        for patch in self.patches:
            patch.draw(canvas, transform)