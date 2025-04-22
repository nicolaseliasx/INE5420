# Sistema Gráfico 2D com Window e Viewport

Um sistema básico para visualização de objetos 2D (pontos, linhas e polígonos) com funcionalidades de navegação (panning e zoom).

## Pré-requisitos

- Python 3.8+
- Gerenciador de pacotes Poetry ([Instalação](#instalação-do-poetry))
- **Dependências de sistema** (Linux):

  ```bash
  # Ubuntu/Debian
  sudo apt install python3-tk

  # Arch
  sudo pacman -S tk
  ```

1. Instale o Poetry

```
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone o repositório e instale dependências

```
git clone
cd sistema-grafico
poetry install
```

3. Como executar:

```
poetry run python graphics_system.py
```

Examples:

```
(10,10) # Ponto único
(-20,-30), (40,50) # Linha
(0,0), (30,0), (15,25) # Triângulo
(3, 0), (1.5, 2.6), (-1.5, 2.6), (-3, 0), (-1.5, -2.6), (1.5, -2.6) # Hexagono
(-200, -200), (-100, 300), (300, -100), (400, 400) # Curva
```
