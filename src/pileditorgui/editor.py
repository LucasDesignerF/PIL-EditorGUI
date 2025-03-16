# PIL-EditorGUI - Editor de Imagens Simples
# Versão: 1.9.4
# Data: 16 de Março de 2025
# Autor: LucasFortes
# Descrição: Editor básico para adicionar múltiplas imagens base, criar/redimensionar formas e adicionar texto sobre elas, com salvamento em imagem e código preservando nomes de arquivos.
# Notas de Versão:
# - 1.9: Corrigido Ctrl + Z, adicionado suporte a múltiplas imagens, texto criado já selecionado.
# - 1.9.1: Corrigido TypeError ao redimensionar com mouse, garantindo valores inteiros.
# - 1.9.2: Corrigido desalinhamento dos handles, voltando à lógica de renderização da 1.8 com suporte a múltiplas camadas.
# - 1.9.3: Adicionado salvamento em .png, .jpg, JavaScript, Python e .lua.
# - 1.9.4: Preserva nomes reais dos arquivos de imagem nos códigos exportados.

import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import logging
import copy
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

#############################
#### Classe ImageLayer ####
#############################

class ImageLayer:
    """Classe para camadas de imagem com posição, opacidade e nome do arquivo."""
    def __init__(self, image, file_path, x=0, y=0, opacity=100):
        self.image = image
        self.file_path = file_path  # Armazena o caminho original do arquivo
        self.x = x
        self.y = y
        self.opacity = opacity
        self.width, self.height = image.size

    def draw(self, draw, scale=1.0):
        """Desenha a imagem na camada com escala aplicada."""
        img = self.image.copy()
        if self.opacity < 100:
            alpha = img.split()[3]
            new_alpha = alpha.point(lambda p: int(p * self.opacity / 100))
            img.putalpha(new_alpha)
        scaled_img = img.resize((int(self.width * scale), int(self.height * scale)), Image.Resampling.LANCZOS)
        draw._image.paste(scaled_img, (int(self.x * scale), int(self.y * scale)), scaled_img)

    def resize(self, width, height):
        """Redimensiona a imagem."""
        self.width = max(10, int(width))
        self.height = max(10, int(height))
        self.image = self.image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        logger.info(f"Imagem redimensionada para {self.width}x{self.height}")

    def set_opacity(self, opacity):
        self.opacity = max(0, min(100, opacity))
        logger.info(f"Opacidade da imagem ajustada para {self.opacity}")

    def get_bounding_box(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

#############################
#### Classe Shape ####
#############################

class Shape:
    """Classe para formas geométricas com personalização."""
    def __init__(self, x, y, width=100, height=100, fill="blue", opacity=100, outline_width=1, corner_radius=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fill = fill
        self.opacity = opacity
        self.outline_width = outline_width
        self.corner_radius = corner_radius

    def draw(self, draw):
        """Desenha a forma (retângulo) na imagem com personalizações."""
        if self.fill.startswith('#'):
            fill_rgb = tuple(int(self.fill[i:i+2], 16) for i in (1, 3, 5))
        else:
            fill_rgb = (0, 0, 255)
        fill_rgba = fill_rgb + (int(self.opacity * 255 / 100),)

        if self.corner_radius > 0:
            draw.rounded_rectangle(
                [self.x, self.y, self.x + self.width, self.y + self.height],
                radius=self.corner_radius,
                fill=fill_rgba,
                outline="black" if self.outline_width > 0 else None,
                width=self.outline_width
            )
        else:
            draw.rectangle(
                [self.x, self.y, self.x + self.width, self.y + self.height],
                fill=fill_rgba,
                outline="black" if self.outline_width > 0 else None,
                width=self.outline_width
            )

    def resize(self, width, height):
        """Redimensiona a forma."""
        self.width = max(10, int(width))
        self.height = max(10, int(height))
        logger.info(f"Forma redimensionada para {self.width}x{self.height}")

    def set_opacity(self, opacity):
        self.opacity = max(0, min(100, opacity))
        logger.info(f"Opacidade ajustada para {self.opacity}")

    def set_corner_radius(self, radius):
        self.corner_radius = max(0, min(100, radius))
        logger.info(f"Raio das bordas ajustado para {self.corner_radius}")

    def set_outline_width(self, width):
        self.outline_width = max(0, min(100, width))
        logger.info(f"Espessura do contorno ajustada para {self.outline_width}")

    def set_fill(self, color):
        self.fill = color
        logger.info(f"Cor ajustada para {self.fill}")

    def get_bounding_box(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

#############################
#### Classe TextShape ####
#############################

class TextShape:
    """Classe para textos com personalização."""
    def __init__(self, x, y, text, font_path=None, font_size=20, fill="black", opacity=100):
        self.x = x
        self.y = y
        self.text = text
        self.font_path = font_path
        self.font_size = font_size
        self.fill = fill
        self.opacity = opacity
        self.width, self.height = self.get_text_size()

    def get_font(self, size=None):
        """Retorna o objeto ImageFont baseado no caminho e tamanho."""
        try:
            if self.font_path:
                return ImageFont.truetype(self.font_path, size or self.font_size)
            return ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Erro ao carregar fonte {self.font_path}: {e}, usando padrão")
            return ImageFont.load_default()

    def get_text_size(self):
        """Calcula o tamanho aproximado do texto com buffer para seleção."""
        font = self.get_font()
        dummy_img = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), self.text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        buffer = max(10, self.font_size // 2)
        return (width + buffer, height + buffer)

    def draw(self, draw, scale=1.0):
        """Desenha o texto na imagem com escala aplicada."""
        fill_rgb = tuple(int(self.fill[i:i+2], 16) for i in (1, 3, 5)) if self.fill.startswith('#') else (0, 0, 0)
        fill_rgba = fill_rgb + (int(self.opacity * 255 / 100),)
        font = self.get_font(int(self.font_size * scale))
        draw.text((self.x, self.y), self.text, font=font, fill=fill_rgba)

    def resize(self, size):
        """Redimensiona o tamanho da fonte do texto."""
        self.font_size = max(5, int(size))
        self.width, self.height = self.get_text_size()
        logger.info(f"Tamanho do texto ajustado para {self.font_size}")

    def set_opacity(self, opacity):
        self.opacity = max(0, min(100, opacity))
        logger.info(f"Opacidade ajustada para {self.opacity}")

    def set_fill(self, color):
        self.fill = color
        logger.info(f"Cor ajustada para {self.fill}")

    def set_font(self, font_path, font_size):
        self.font_path = font_path
        self.font_size = int(font_size)
        self.width, self.height = self.get_text_size()
        logger.info(f"Fonte ajustada para {font_path}, tamanho {self.font_size}")

    def get_bounding_box(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

#############################
#### Classe Editor ####
#############################

class Editor:
    """Classe principal do editor simplificado."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PIL-EditorGUI Simples")
        self.root.geometry("800x600")
        self.root.configure(bg="#2d2d2d")

        self.canvas = tk.Canvas(self.root, width=600, height=600, bg="#3c3f41", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.images = []  # Lista de camadas de imagens
        self.shapes = []  # Lista de formas, textos e imagens
        self.selected_shape = None
        self.is_dragging = False
        self.resize_handle = None
        self.last_x = 0
        self.last_y = 0
        self.display_image = None

        self.history = []
        self.save_state()

        self.sidebar = tk.Frame(self.root, bg="#2d2d2d", width=200)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(self.sidebar, text="Load Image", command=self.load_image, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Add Shape", command=self.add_shape, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Add Text", command=self.add_text, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Color", command=self.set_color, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Opacity", command=self.set_opacity, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Corner Radius", command=self.set_corner_radius, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Outline Width", command=self.set_outline_width, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Transparency", command=self.set_transparency, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Set Font", command=self.set_font, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)
        tk.Button(self.sidebar, text="Save Project", command=self.save_project, bg="#4a4a4a", fg="white").pack(pady=5, padx=10)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Up>", self.move_up)
        self.root.bind("<Down>", self.move_down)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<plus>", self.increase_size)
        self.root.bind("<minus>", self.decrease_size)
        self.root.bind("<Control-z>", self.undo)

        self.update_canvas()
        logger.info("Editor inicializado")

    def save_state(self):
        """Salva o estado atual no histórico."""
        state = {
            'images': [copy.deepcopy(img) for img in self.images],
            'shapes': [copy.deepcopy(shape) for shape in self.shapes],
            'selected_shape_index': self.shapes.index(self.selected_shape) if self.selected_shape in self.shapes else None
        }
        self.history.append(state)
        if len(self.history) > 10:
            self.history.pop(0)
        logger.debug("Estado salvo no histórico")

    def undo(self, event):
        """Desfaz a última ação."""
        logger.debug("Tentativa de desfazer ação")
        if len(self.history) > 1:
            self.history.pop()
            previous_state = self.history[-1]
            self.images = [copy.deepcopy(img) for img in previous_state['images']]
            self.shapes = [copy.deepcopy(shape) for shape in previous_state['shapes']]
            self.selected_shape = self.shapes[previous_state['selected_shape_index']] if previous_state['selected_shape_index'] is not None else None
            self.update_canvas()
            logger.info("Última ação desfeita")
        else:
            logger.info("Nenhum estado anterior para desfazer")

    def move_up(self, event):
        """Move o item selecionado para cima."""
        if self.selected_shape:
            self.selected_shape.y -= 5
            self.save_state()
            self.update_canvas()
            logger.info("Item movido para cima")

    def move_down(self, event):
        """Move o item selecionado para baixo."""
        if self.selected_shape:
            self.selected_shape.y += 5
            self.save_state()
            self.update_canvas()
            logger.info("Item movido para baixo")

    def move_left(self, event):
        """Move o item selecionado para a esquerda."""
        if self.selected_shape:
            self.selected_shape.x -= 5
            self.save_state()
            self.update_canvas()
            logger.info("Item movido para a esquerda")

    def move_right(self, event):
        """Move o item selecionado para a direita."""
        if self.selected_shape:
            self.selected_shape.x += 5
            self.save_state()
            self.update_canvas()
            logger.info("Item movido para a direita")

    def increase_size(self, event):
        """Aumenta o tamanho do item selecionado."""
        if self.selected_shape:
            if isinstance(self.selected_shape, Shape):
                self.selected_shape.resize(self.selected_shape.width + 10, self.selected_shape.height + 10)
            elif isinstance(self.selected_shape, TextShape):
                self.selected_shape.resize(self.selected_shape.font_size + 5)
            elif isinstance(self.selected_shape, ImageLayer):
                self.selected_shape.resize(self.selected_shape.width + 10, self.selected_shape.height + 10)
            self.save_state()
            self.update_canvas()
            logger.info("Tamanho aumentado")

    def decrease_size(self, event):
        """Diminui o tamanho do item selecionado."""
        if self.selected_shape:
            if isinstance(self.selected_shape, Shape):
                self.selected_shape.resize(self.selected_shape.width - 10, self.selected_shape.height - 10)
            elif isinstance(self.selected_shape, TextShape):
                self.selected_shape.resize(self.selected_shape.font_size - 5)
            elif isinstance(self.selected_shape, ImageLayer):
                self.selected_shape.resize(self.selected_shape.width - 10, self.selected_shape.height - 10)
            self.save_state()
            self.update_canvas()
            logger.info("Tamanho diminuído")

    def load_image(self):
        """Carrega uma imagem como uma nova camada."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            img = Image.open(file_path).convert("RGBA")
            image_layer = ImageLayer(img, file_path, x=0, y=0, opacity=100)  # Passa o file_path para ImageLayer
            self.images.append(image_layer)
            self.shapes.append(image_layer)
            self.selected_shape = image_layer
            self.save_state()
            self.update_canvas()
            logger.info(f"Imagem carregada: {file_path}")

    def add_shape(self):
        """Adiciona uma forma ao canvas."""
        if self.images:
            shape = Shape(50, 50, 100, 100, fill="#0000FF", opacity=100, outline_width=1, corner_radius=0)
            self.shapes.append(shape)
            self.selected_shape = shape
            self.save_state()
            self.update_canvas()
            logger.info("Forma adicionada")

    def add_text(self):
        """Adiciona texto ao canvas com fonte padrão, já selecionado."""
        if self.images:
            text = simpledialog.askstring("Texto", "Digite o texto:")
            if text:
                text_shape = TextShape(50, 50, text, font_path=None, font_size=20, fill="#000000", opacity=100)
                self.shapes.append(text_shape)
                self.selected_shape = text_shape
                self.save_state()
                self.update_canvas()
                logger.info(f"Texto adicionado: {text}")

    def set_color(self):
        """Define a cor do item selecionado."""
        if self.selected_shape and isinstance(self.selected_shape, (Shape, TextShape)):
            color = colorchooser.askcolor(title="Escolha a cor")[1]
            if color:
                self.selected_shape.set_fill(color)
                self.save_state()
                self.update_canvas()

    def set_opacity(self):
        """Define a opacidade do item selecionado."""
        if self.selected_shape:
            opacity = simpledialog.askinteger("Opacidade", "Digite a opacidade (0-100):", minvalue=0, maxvalue=100)
            if opacity is not None:
                self.selected_shape.set_opacity(opacity)
                self.save_state()
                self.update_canvas()

    def set_corner_radius(self):
        """Define o raio das bordas da forma selecionada."""
        if self.selected_shape and isinstance(self.selected_shape, Shape):
            radius = simpledialog.askinteger("Raio das Bordas", "Digite o raio (0-100):", minvalue=0, maxvalue=100)
            if radius is not None:
                self.selected_shape.set_corner_radius(radius)
                self.save_state()
                self.update_canvas()

    def set_outline_width(self):
        """Define a espessura do contorno da forma selecionada."""
        if self.selected_shape and isinstance(self.selected_shape, Shape):
            width = simpledialog.askinteger("Espessura do Contorno", "Digite a espessura (0-100):", minvalue=0, maxvalue=100)
            if width is not None:
                self.selected_shape.set_outline_width(width)
                self.save_state()
                self.update_canvas()

    def set_transparency(self):
        """Define a transparência do item selecionado ou da última imagem."""
        transparency = simpledialog.askinteger("Transparência", "Digite a transparência (0-100):", minvalue=0, maxvalue=100)
        if transparency is not None:
            if self.selected_shape:
                self.selected_shape.set_opacity(transparency)
                logger.info(f"Transparência do item ajustada para {transparency}")
            elif self.images:
                self.images[-1].set_opacity(transparency)
                logger.info(f"Transparência da última imagem ajustada para {transparency}")
            self.save_state()
            self.update_canvas()

    def set_font(self):
        """Carrega uma fonte .otf ou .ttf para o texto selecionado."""
        if self.selected_shape and isinstance(self.selected_shape, TextShape):
            font_dialog = tk.Toplevel(self.root)
            font_dialog.title("Escolher Fonte")
            font_dialog.geometry("300x200")

            tk.Label(font_dialog, text="Selecione um arquivo de fonte (.otf/.ttf):").pack(pady=5)
            font_path_var = tk.StringVar()

            def browse_font():
                font_path = filedialog.askopenfilename(filetypes=[("Font files", "*.otf *.ttf")])
                if font_path:
                    font_path_var.set(font_path)

            tk.Button(font_dialog, text="Procurar", command=browse_font).pack(pady=5)
            tk.Entry(font_dialog, textvariable=font_path_var, width=30).pack(pady=5)

            size_var = tk.IntVar(value=self.selected_shape.font_size)
            tk.Label(font_dialog, text="Tamanho:").pack(pady=5)
            tk.Entry(font_dialog, textvariable=size_var).pack(pady=5)

            def apply_font():
                font_path = font_path_var.get()
                if font_path:
                    try:
                        ImageFont.truetype(font_path, size_var.get())
                        self.selected_shape.set_font(font_path, size_var.get())
                        self.save_state()
                        self.update_canvas()
                        font_dialog.destroy()
                    except Exception as e:
                        logger.error(f"Erro ao carregar fonte: {e}")
                        tk.messagebox.showerror("Erro", "Fonte inválida ou não suportada.")
                else:
                    self.selected_shape.set_font(None, size_var.get())
                    self.save_state()
                    self.update_canvas()
                    font_dialog.destroy()

            tk.Button(font_dialog, text="Aplicar", command=apply_font).pack(pady=10)

    def save_project(self):
        """Salva o projeto em formato de imagem ou código, preservando nomes reais das imagens."""
        if not self.images:
            messagebox.showwarning("Aviso", "Nenhuma imagem carregada para salvar.")
            return

        filetypes = [
            ("PNG Image", "*.png"),
            ("JPEG Image", "*.jpg"),
            ("JavaScript Code", "*.js"),
            ("Python Code", "*.py"),
            ("Lua Code", "*.lua")
        ]
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=filetypes,
            title="Salvar Projeto"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()

        # Gera a imagem composta para salvamento
        max_width = max(img.width for img in self.images)
        max_height = max(img.height for img in self.images)
        base_layer = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        base_draw = ImageDraw.Draw(base_layer)
        for img_layer in self.images:
            img = img_layer.image.copy()
            if img_layer.opacity < 100:
                alpha = img.split()[3]
                new_alpha = alpha.point(lambda p: int(p * img_layer.opacity / 100))
                img.putalpha(new_alpha)
            x = int(img_layer.x)
            y = int(img_layer.y)
            base_layer.paste(img, (x, y), img)

        shape_layer = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape_layer)
        for shape in self.shapes:
            if isinstance(shape, Shape):
                shape.draw(draw)
            elif isinstance(shape, TextShape):
                shape.draw(draw, scale=1.0)

        final_img = Image.alpha_composite(base_layer, shape_layer)

        if ext in [".png", ".jpg"]:
            # Salva como imagem
            if ext == ".jpg":
                final_img = final_img.convert("RGB")  # Remove canal alfa para JPG
            final_img.save(file_path)
            logger.info(f"Projeto salvo como imagem: {file_path}")
        elif ext == ".js":
            # Salva como JavaScript (Canvas API)
            js_code = "const canvas = document.createElement('canvas');\n"
            js_code += f"canvas.width = {max_width};\ncanvas.height = {max_height};\n"
            js_code += "const ctx = canvas.getContext('2d');\n\n"
            for i, img_layer in enumerate(self.images):
                js_code += f"// Imagem {i}: {img_layer.file_path}\n"
                js_code += f"const img{i} = new Image();\n"
                js_code += f"img{i}.src = '{img_layer.file_path}';\n"
                js_code += f"ctx.globalAlpha = {img_layer.opacity / 100};\n"
                js_code += f"ctx.drawImage(img{i}, {int(img_layer.x)}, {int(img_layer.y)}, {img_layer.width}, {img_layer.height});\n"
            js_code += "ctx.globalAlpha = 1.0;\n\n"
            for i, shape in enumerate(self.shapes):
                if isinstance(shape, Shape):
                    js_code += f"// Forma {i}\n"
                    js_code += f"ctx.fillStyle = '{shape.fill}';\n"
                    js_code += f"ctx.globalAlpha = {shape.opacity / 100};\n"
                    if shape.corner_radius > 0:
                        js_code += f"ctx.beginPath();\n"
                        js_code += f"ctx.moveTo({int(shape.x + shape.corner_radius)}, {int(shape.y)});\n"
                        js_code += f"ctx.arcTo({int(shape.x + shape.width)}, {int(shape.y)}, {int(shape.x + shape.width)}, {int(shape.y + shape.height)}, {shape.corner_radius});\n"
                        js_code += f"ctx.arcTo({int(shape.x + shape.width)}, {int(shape.y + shape.height)}, {int(shape.x)}, {int(shape.y + shape.height)}, {shape.corner_radius});\n"
                        js_code += f"ctx.arcTo({int(shape.x)}, {int(shape.y + shape.height)}, {int(shape.x)}, {int(shape.y)}, {shape.corner_radius});\n"
                        js_code += f"ctx.arcTo({int(shape.x)}, {int(shape.y)}, {int(shape.x + shape.width)}, {int(shape.y)}, {shape.corner_radius});\n"
                        js_code += f"ctx.closePath();\nctx.fill();\n"
                    else:
                        js_code += f"ctx.fillRect({int(shape.x)}, {int(shape.y)}, {shape.width}, {shape.height});\n"
                    if shape.outline_width > 0:
                        js_code += f"ctx.strokeStyle = 'black';\n"
                        js_code += f"ctx.lineWidth = {shape.outline_width};\n"
                        js_code += f"ctx.strokeRect({int(shape.x)}, {int(shape.y)}, {shape.width}, {shape.height});\n"
                elif isinstance(shape, TextShape):
                    js_code += f"// Texto {i}\n"
                    js_code += f"ctx.fillStyle = '{shape.fill}';\n"
                    js_code += f"ctx.globalAlpha = {shape.opacity / 100};\n"
                    js_code += f"ctx.font = '{shape.font_size}px Arial'; // Substitua pela fonte real\n"
                    js_code += f"ctx.fillText('{shape.text}', {int(shape.x)}, {int(shape.y + shape.font_size)});\n"
            js_code += "\ndocument.body.appendChild(canvas);"
            with open(file_path, "w") as f:
                f.write(js_code)
            logger.info(f"Projeto salvo como JavaScript: {file_path}")
        elif ext == ".py":
            # Salva como Python (PIL)
            py_code = "from PIL import Image, ImageDraw\n\n"
            py_code += f"img = Image.new('RGBA', ({max_width}, {max_height}), (0, 0, 0, 0))\n"
            py_code += "draw = ImageDraw.Draw(img)\n\n"
            for i, img_layer in enumerate(self.images):
                py_code += f"# Imagem {i}: {img_layer.file_path}\n"
                py_code += f"img_layer_{i} = Image.open('{img_layer.file_path}').convert('RGBA')\n"
                py_code += f"img_layer_{i} = img_layer_{i}.resize(({img_layer.width}, {img_layer.height}))\n"
                py_code += f"if {img_layer.opacity} < 100:\n"
                py_code += f"    alpha = img_layer_{i}.split()[3]\n"
                py_code += f"    new_alpha = alpha.point(lambda p: int(p * {img_layer.opacity} / 100))\n"
                py_code += f"    img_layer_{i}.putalpha(new_alpha)\n"
                py_code += f"img.paste(img_layer_{i}, ({int(img_layer.x)}, {int(img_layer.y)}), img_layer_{i})\n"
            for i, shape in enumerate(self.shapes):
                if isinstance(shape, Shape):
                    py_code += f"# Forma {i}\n"
                    py_code += f"draw.rectangle([{int(shape.x)}, {int(shape.y)}, {int(shape.x + shape.width)}, {int(shape.y + shape.height)}], "
                    py_code += f"fill='{shape.fill}' + '{int(shape.opacity * 255 / 100):02x}', "
                    py_code += f"outline='black' if {shape.outline_width} > 0 else None, width={shape.outline_width})\n"
                elif isinstance(shape, TextShape):
                    py_code += f"# Texto {i}\n"
                    py_code += f"draw.text(({int(shape.x)}, {int(shape.y)}), '{shape.text}', "
                    py_code += f"fill='{shape.fill}' + '{int(shape.opacity * 255 / 100):02x}', font=None)  # Substitua pela fonte real\n"
            py_code += "\nimg.show()\nimg.save('output.png')"
            with open(file_path, "w") as f:
                f.write(py_code)
            logger.info(f"Projeto salvo como Python: {file_path}")
        elif ext == ".lua":
            # Salva como Lua (MTA GUI)
            lua_code = "-- Script MTA GUI\n"
            lua_code += "addEventHandler('onClientResourceStart', resourceRoot, function()\n"
            lua_code += "    local screenW, screenH = guiGetScreenSize()\n"
            for i, img_layer in enumerate(self.images):
                # Usa apenas o nome do arquivo para MTA (sem caminho completo)
                file_name = os.path.basename(img_layer.file_path)
                lua_code += f"    -- Imagem {i}: {img_layer.file_path}\n"
                lua_code += f"    local img_{i} = guiCreateStaticImage({int(img_layer.x)}, {int(img_layer.y)}, {img_layer.width}, {img_layer.height}, '{file_name}', false)\n"
                lua_code += f"    guiSetAlpha(img_{i}, {img_layer.opacity / 100})\n"
            for i, shape in enumerate(self.shapes):
                if isinstance(shape, Shape):
                    lua_code += f"    -- Forma {i}\n"
                    lua_code += f"    local rect_{i} = guiCreateStaticImage({int(shape.x)}, {int(shape.y)}, {shape.width}, {shape.height}, ':guieditor/images/rect.png', false)\n"
                    lua_code += f"    guiSetProperty(rect_{i}, 'ImageColours', 'tl:{shape.fill[1:]}FF tr:{shape.fill[1:]}FF bl:{shape.fill[1:]}FF br:{shape.fill[1:]}FF')\n"
                    lua_code += f"    guiSetAlpha(rect_{i}, {shape.opacity / 100})\n"
                elif isinstance(shape, TextShape):
                    lua_code += f"    -- Texto {i}\n"
                    lua_code += f"    local label_{i} = guiCreateLabel({int(shape.x)}, {int(shape.y)}, {shape.width}, {shape.height}, '{shape.text}', false)\n"
                    lua_code += f"    guiLabelSetColor(label_{i}, {int(shape.fill[1:3], 16)}, {int(shape.fill[3:5], 16)}, {int(shape.fill[5:7], 16)})\n"
                    lua_code += f"    guiSetAlpha(label_{i}, {shape.opacity / 100})\n"
            lua_code += "end)"
            with open(file_path, "w") as f:
                f.write(lua_code)
            logger.info(f"Projeto salvo como Lua: {file_path}")

    def update_canvas(self):
        """Atualiza a renderização do canvas."""
        self.canvas.delete("all")
        if not self.images:
            self.canvas.create_text(300, 300, text="Carregue uma imagem", fill="white", font=("Arial", 14))
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        max_width = max(img.width for img in self.images)
        max_height = max(img.height for img in self.images)
        scale = min(canvas_width / max_width, canvas_height / max_height)
        new_width = int(max_width * scale)
        new_height = int(max_height * scale)

        # Camada base composta por todas as imagens
        base_layer = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        base_draw = ImageDraw.Draw(base_layer)
        for img_layer in self.images:
            img = img_layer.image.copy()
            if img_layer.opacity < 100:
                alpha = img.split()[3]
                new_alpha = alpha.point(lambda p: int(p * img_layer.opacity / 100))
                img.putalpha(new_alpha)
            scaled_img = img.resize((int(img_layer.width * scale), int(img_layer.height * scale)), Image.Resampling.LANCZOS)
            base_layer.paste(scaled_img, (int(img_layer.x * scale), int(img_layer.y * scale)), scaled_img)

        # Camada de formas e textos
        shape_layer = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape_layer)
        for shape in self.shapes:
            if isinstance(shape, Shape):
                scaled_x = int(shape.x * scale)
                scaled_y = int(shape.y * scale)
                scaled_width = int(shape.width * scale)
                scaled_height = int(shape.height * scale)
                scaled_radius = int(shape.corner_radius * scale)
                fill_rgb = tuple(int(shape.fill[i:i+2], 16) for i in (1, 3, 5)) if shape.fill.startswith('#') else (0, 0, 255)
                fill_rgba = fill_rgb + (int(shape.opacity * 255 / 100),)
                if scaled_radius > 0:
                    draw.rounded_rectangle(
                        [scaled_x, scaled_y, scaled_x + scaled_width, scaled_y + scaled_height],
                        radius=scaled_radius,
                        fill=fill_rgba,
                        outline="black" if shape.outline_width > 0 else None,
                        width=int(shape.outline_width * scale)
                    )
                else:
                    draw.rectangle(
                        [scaled_x, scaled_y, scaled_x + scaled_width, scaled_y + scaled_height],
                        fill=fill_rgba,
                        outline="black" if shape.outline_width > 0 else None,
                        width=int(shape.outline_width * scale)
                    )
            elif isinstance(shape, TextShape):
                shape.draw(draw, scale)

        # Composição final
        final_img = Image.alpha_composite(base_layer, shape_layer)
        self.display_image = ImageTk.PhotoImage(final_img)
        offset_x = (canvas_width - new_width) // 2
        offset_y = (canvas_height - new_height) // 2
        self.canvas.create_image(offset_x, offset_y, image=self.display_image, anchor=tk.NW)

        # Desenha handles para o item selecionado
        if self.selected_shape:
            bbox = self.selected_shape.get_bounding_box()
            scaled_bbox = (
                int(bbox[0] * scale) + offset_x,
                int(bbox[1] * scale) + offset_y,
                int(bbox[2] * scale) + offset_x,
                int(bbox[3] * scale) + offset_y
            )
            self.canvas.create_rectangle(scaled_bbox, outline="yellow", dash=(4, 4), tags="selection")
            if isinstance(self.selected_shape, (Shape, ImageLayer)):
                handles = [
                    (scaled_bbox[2], scaled_bbox[3]),  # bottom_right
                    (scaled_bbox[0], scaled_bbox[3]),  # bottom_left
                    (scaled_bbox[2], scaled_bbox[1]),  # top_right
                    (scaled_bbox[0], scaled_bbox[1])   # top_left
                ]
                for x, y in handles:
                    self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="white", tags="handle")

        logger.debug("Canvas atualizado")

    def on_mouse_press(self, event):
        """Seleciona um item ou inicia redimensionamento/movimento."""
        self.selected_shape = None
        if not self.images:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        max_width = max(img.width for img in self.images)
        max_height = max(img.height for img in self.images)
        scale = min(canvas_width / max_width, canvas_height / max_height)
        offset_x = (canvas_width - int(max_width * scale)) // 2
        offset_y = (canvas_height - int(max_height * scale)) // 2
        x_orig = (event.x - offset_x) / scale if offset_x <= event.x <= offset_x + int(max_width * scale) else -1
        y_orig = (event.y - offset_y) / scale if offset_y <= event.y <= offset_y + int(max_height * scale) else -1

        for shape in reversed(self.shapes):
            bbox = shape.get_bounding_box()
            logger.debug(f"Verificando {shape.__class__.__name__} em {bbox} contra clique em ({x_orig}, {y_orig})")
            if bbox[0] <= x_orig <= bbox[2] and bbox[1] <= y_orig <= bbox[3]:
                self.selected_shape = shape
                logger.info(f"{shape.__class__.__name__} selecionado")
                break

        if self.selected_shape:
            if isinstance(self.selected_shape, (Shape, ImageLayer)):
                self.check_resize_handle(x_orig, y_orig)
                self.is_dragging = not self.resize_handle
            else:  # TextShape
                self.is_dragging = True
            self.last_x, self.last_y = x_orig, y_orig
        self.update_canvas()

    def check_resize_handle(self, x, y):
        """Verifica se o clique foi em um handle de redimensionamento."""
        self.resize_handle = None
        if not self.selected_shape or not isinstance(self.selected_shape, (Shape, ImageLayer)):
            return
        bbox = self.selected_shape.get_bounding_box()
        handles = {
            "bottom_right": (bbox[2], bbox[3]),
            "bottom_left": (bbox[0], bbox[3]),
            "top_right": (bbox[2], bbox[1]),
            "top_left": (bbox[0], bbox[1])
        }
        for handle, pos in handles.items():
            if abs(pos[0] - x) < 10 and abs(pos[1] - y) < 10:
                self.resize_handle = handle
                logger.debug(f"Handle selecionado: {handle}")
                return

    def on_mouse_drag(self, event):
        """Move ou redimensiona o item selecionado."""
        if not self.selected_shape or not self.images:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        max_width = max(img.width for img in self.images)
        max_height = max(img.height for img in self.images)
        scale = min(canvas_width / max_width, canvas_height / max_height)
        offset_x = (canvas_width - int(max_width * scale)) // 2
        offset_y = (canvas_height - int(max_height * scale)) // 2
        x_orig = (event.x - offset_x) / scale if offset_x <= event.x <= offset_x + int(max_width * scale) else self.last_x
        y_orig = (event.y - offset_y) / scale if offset_y <= event.y <= offset_y + int(max_height * scale) else self.last_y
        dx = x_orig - self.last_x
        dy = y_orig - self.last_y

        if self.resize_handle and isinstance(self.selected_shape, (Shape, ImageLayer)):
            bbox = self.selected_shape.get_bounding_box()
            if "right" in self.resize_handle:
                width = x_orig - bbox[0]
            else:
                width = bbox[2] - bbox[0]
            if "bottom" in self.resize_handle:
                height = y_orig - bbox[1]
            else:
                height = bbox[3] - bbox[1]
            self.selected_shape.resize(int(width), int(height))
        elif self.is_dragging:
            self.selected_shape.x += dx
            self.selected_shape.y += dy
        self.last_x, self.last_y = x_orig, y_orig
        self.save_state()
        self.update_canvas()

    def on_mouse_release(self, event):
        """Finaliza o movimento ou redimensionamento."""
        self.is_dragging = False
        self.resize_handle = None
        self.update_canvas()

    def on_resize(self, event):
        """Ajusta o canvas ao redimensionar a janela."""
        self.update_canvas()

    def run(self):
        """Inicia o loop principal."""
        self.root.mainloop()

#############################
#### Execução Principal ####
#############################

if __name__ == "__main__":
    logger.info("Iniciando PIL-EditorGUI Simples")
    app = Editor()
    app.run()
