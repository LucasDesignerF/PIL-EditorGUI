import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import os
import sys
import importlib.util
import re

class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Projetos PIL-EditorGUI")
        self.root.geometry("900x700")
        self.root.configure(bg="#2d2d2d")

        # Frame para botões
        self.button_frame = tk.Frame(self.root, bg="#2d2d2d")
        self.button_frame.pack(pady=10)

        # Botão para carregar o arquivo
        self.load_button = tk.Button(self.button_frame, text="Carregar Código (.py, .js, .lua)", 
                                   command=self.load_and_display, bg="#4a4a4a", fg="white")
        self.load_button.pack(pady=5)

        # Canvas para exibir a imagem
        self.canvas = tk.Canvas(self.root, bg="#3c3f41", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_tk = None  # Para manter a referência da imagem exibida

    def load_and_display(self):
        """Carrega o arquivo e exibe a imagem gerada."""
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo",
            filetypes=[("Code Files", "*.py *.js *.lua"), ("Python Files", "*.py"), 
                       ("JavaScript Files", "*.js"), ("Lua Files", "*.lua")]
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            if ext == ".py":
                self.handle_python(code)
            elif ext == ".js":
                self.handle_javascript(code)
            elif ext == ".lua":
                self.handle_lua(code)
            else:
                raise ValueError("Formato de arquivo não suportado.")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar ou processar o código:\n{str(e)}")

    def handle_python(self, code):
        """Processa e executa código Python."""
        adjusted_code = self.adjust_image_paths(code, "Image.open(")
        temp_file = "temp_script.py"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(adjusted_code)

        spec = importlib.util.spec_from_file_location("temp_module", temp_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_module"] = module
        spec.loader.exec_module(module)

        img = module.img
        self.display_image(img)
        os.remove(temp_file)

    def handle_javascript(self, code):
        """Converte código JavaScript em imagem usando PIL."""
        # Extrai dimensões do canvas
        width_match = re.search(r"canvas\.width\s*=\s*(\d+);", code)
        height_match = re.search(r"canvas\.height\s*=\s*(\d+);", code)
        width = int(width_match.group(1)) if width_match else 800
        height = int(height_match.group(1)) if height_match else 600

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Processa cada drawImage
        draw_calls = re.findall(r"ctx\.drawImage\(img\d+,\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\);", code)
        image_paths = re.findall(r"img\d+\.src\s*=\s*'(.*?)';", code)
        alphas = re.findall(r"ctx\.globalAlpha\s*=\s*([\d.]+);", code)

        for i, (x, y, w, h) in enumerate(draw_calls):
            x, y, w, h = int(x), int(y), int(w), int(h)
            path = image_paths[i] if i < len(image_paths) else ""
            alpha = float(alphas[i]) if i < len(alphas) else 1.0

            if path:
                adjusted_path = f"img/{os.path.basename(path)}"
                layer_img = Image.open(adjusted_path).convert('RGBA')
                layer_img = layer_img.resize((w, h), Image.Resampling.LANCZOS)
                if alpha < 1.0:
                    alpha_channel = layer_img.split()[3]
                    new_alpha = alpha_channel.point(lambda p: int(p * alpha))
                    layer_img.putalpha(new_alpha)
                img.paste(layer_img, (x, y), layer_img)

        self.display_image(img)

    def handle_lua(self, code):
        """Converte código Lua (MTA GUI) em imagem usando PIL."""
        # Tenta estimar as dimensões baseadas nas imagens (não há canvas explícito)
        img_calls = re.findall(r"guiCreateStaticImage\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*'([^']+)',\s*false\)", code)
        alpha_calls = re.findall(r"guiSetAlpha\([^,]+,\s*([\d.]+)\)", code)

        # Calcula dimensões máximas
        max_x, max_y = 0, 0
        for x, y, w, h, _ in img_calls:
            max_x = max(max_x, int(x) + int(w))
            max_y = max(max_y, int(y) + int(h))
        width, height = max_x or 800, max_y or 600

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Processa cada imagem
        for i, (x, y, w, h, path) in enumerate(img_calls):
            x, y, w, h = int(x), int(y), int(w), int(h)
            alpha = float(alpha_calls[i]) if i < len(alpha_calls) else 1.0

            if path and path != ":guieditor/images/rect.png":  # Ignora retângulos genéricos
                adjusted_path = f"img/{path}"
                layer_img = Image.open(adjusted_path).convert('RGBA')
                layer_img = layer_img.resize((w, h), Image.Resampling.LANCZOS)
                if alpha < 1.0:
                    alpha_channel = layer_img.split()[3]
                    new_alpha = alpha_channel.point(lambda p: int(p * alpha))
                    layer_img.putalpha(new_alpha)
                img.paste(layer_img, (x, y), layer_img)

        self.display_image(img)

    def adjust_image_paths(self, code, marker):
        """Ajusta os caminhos absolutos das imagens para 'img/nome_do_arquivo'."""
        lines = code.split('\n')
        adjusted_lines = []
        for line in lines:
            if marker in line and "C:/" in line:
                start_idx = line.find("'") + 1
                end_idx = line.rfind("'")
                full_path = line[start_idx:end_idx]
                file_name = os.path.basename(full_path)
                new_path = f"img/{file_name}"
                adjusted_line = line.replace(full_path, new_path)
                adjusted_lines.append(adjusted_line)
            else:
                adjusted_lines.append(line)
        return '\n'.join(adjusted_lines)

    def display_image(self, img):
        """Exibe a imagem no canvas com redimensionamento proporcional."""
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 850, 650

        img_width, img_height = img.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_img)

        offset_x = (canvas_width - new_width) // 2
        offset_y = (canvas_height - new_height) // 2
        self.canvas.create_image(offset_x, offset_y, image=self.image_tk, anchor=tk.NW)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root)
    root.mainloop()
