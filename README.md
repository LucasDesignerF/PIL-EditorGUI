<div align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License MIT">
  <img src="https://img.shields.io/github/stars/LucasDesignerF/PIL-EditorGUI?style=for-the-badge" alt="Stars">
  <br><br>
  <h1 style="font-size: 3em; color: #00d4ff;">PIL-EditorGUI</h1>
  <p style="font-size: 1.2em; color: #b0b0b0;">Um editor de imagens simples e poderoso com suporte a múltiplas camadas e exportação para código!</p>
  <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjYwN2R0cWt0NzltOXNydW50MW44Ym52bXRpdnRpeXRobmllN3FpYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/coxQHKASG60HrHtvkt/giphy.gif" alt="GIF Demo" width="400">
</div>

---

## 🚀 Sobre o Projeto

**PIL-EditorGUI** é uma ferramenta desenvolvida por **[LucasFortes](https://github.com/LucasDesignerF)** para criar composições de imagens de forma simples e intuitiva. Com ele, você pode adicionar imagens, formas e textos, manipulá-los com facilidade e exportar seu trabalho em formatos como `.png`, `.jpg`, ou até mesmo códigos em **Python**, **JavaScript** e **Lua**. Perfeito para designers, desenvolvedores e criadores que querem unir arte e código!

### ✨ Recursos Principais
- **Múltiplas Camadas**: Adicione e edite várias imagens com controle de opacidade.
- **Formas e Textos**: Crie retângulos com bordas arredondadas e adicione textos personalizados.
- **Exportação Avançada**: Salve como imagem ou gere código funcional em Python, JS ou Lua.
- **Visualizador Integrado**: Veja suas criações em tempo real com o script `visualizador.py`.

---

## 🛠️ Estrutura do Repositório

```
PIL-EditorGUI/
├── main.py          # O coração do editor
├── visualizador.py  # Visualizador para arquivos exportados
├── img/             # Pasta para imagens dos projetos
├── requirements.txt # Dependências do projeto
└── README.md        # Este arquivo
```

---

## 🎨 Como Usar

### 1. Instalação
Clone o repositório e instale as dependências:

```bash
git clone https://github.com/LucasDesignerF/PIL-EditorGUI.git
cd PIL-EditorGUI
pip install -r requirements.txt
```

> **Nota**: Certifique-se de ter o Python 3.8+ instalado. O `tkinter` vem por padrão, mas em algumas distribuições Linux pode ser necessário instalar separadamente (`sudo apt-get install python3-tk`).

### 2. Usando o Editor (`main.py`)
Execute o editor e comece a criar:

```bash
python main.py
```

- **Carregue imagens** com "Load Image".
- Adicione **formas** e **textos** com os botões correspondentes.
- Ajuste **opacidade**, **cores** e **tamanhos**.
- Salve seu projeto em `.png`, `.jpg`, `.py`, `.js` ou `.lua`.

### 3. Visualizando os Resultados (`visualizador.py`)
Veja seus arquivos exportados em ação:

```bash
python visualizador.py
```

- Selecione um arquivo `.py`, `.js` ou `.lua`.
- As imagens devem estar na pasta `img/` para o visualizador funcionar corretamente.

---

## 📦 Dependências

Contidas em `requirements.txt`:

- **`Pillow>=9.0.0`**: Para manipulação de imagens.
- **`tkinter`**: Biblioteca padrão para a interface gráfica (verifique sua instalação Python).

Instale com:
```bash
pip install -r requirements.txt
```

---

## 🎥 Demonstração

> (Adicione um GIF ou screenshot do seu editor aqui para mostrar como ele funciona! Você pode usar ferramentas como ScreenToGif ou ShareX.)

---

## 🌟 Exemplos de Exportação

### Python (`.py`)
```python
from PIL import Image, ImageDraw
img = Image.new('RGBA', (1700, 1222), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
img_layer_0 = Image.open('img/fundo.png').convert('RGBA')
img_layer_0 = img_layer_0.resize((1700, 1222))
img.paste(img_layer_0, (0, 0), img_layer_0)
img.show()
img.save('output.png')
```

### JavaScript (`.js`)
```javascript
const canvas = document.createElement('canvas');
canvas.width = 1700;
canvas.height = 1222;
const ctx = canvas.getContext('2d');
const img0 = new Image();
img0.src = 'img/fundo.png';
ctx.drawImage(img0, 0, 0, 1700, 1222);
document.body.appendChild(canvas);
```

### Lua (`.lua`) - MTA GUI
```lua
addEventHandler('onClientResourceStart', resourceRoot, function()
    local img_0 = guiCreateStaticImage(0, 0, 1700, 1222, 'fundo.png', false)
end)
```

---

## 🤝 Contribuições

Quer ajudar a tornar o **PIL-EditorGUI** ainda melhor? Sinta-se à vontade para:
1. Fazer um **fork** do repositório.
2. Criar uma **branch** para sua feature (`git checkout -b feature/nova-ideia`).
3. Enviar um **pull request** com suas mudanças.

Reporte bugs ou sugira ideias na aba **[Issues](https://github.com/LucasDesignerF/PIL-EditorGUI/issues)**!

---

## 📜 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 💡 Sobre o Autor

<div align="center">
  <img src="https://avatars.githubusercontent.com/u/123456789?v=4" alt="LucasFortes" width="100" style="border-radius: 50%;">
  <h3>LucasFortes</h3>
  <p>Designer e desenvolvedor apaixonado por criar ferramentas que unem criatividade e tecnologia.</p>
  <a href="https://github.com/LucasDesignerF"><img src="https://img.shields.io/badge/GitHub-Profile-blue?style=flat-square&logo=github" alt="GitHub"></a>
</div>

---

<div align="center">
  <p style="color: #b0b0b0;">Feito com 💙 por LucasFortes | 2025</p>
  <img src="https://img.shields.io/github/last-commit/LucasDesignerF/PIL-EditorGUI?style=for-the-badge" alt="Last Commit">
</div>
```

