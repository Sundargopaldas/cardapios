from flask import Flask, request, jsonify, send_file, send_from_directory, make_response
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import uuid
import pandas as pd
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

app = Flask(__name__, static_folder='.')
CORS(app)

# Diretórios para armazenar arquivos
UPLOAD_FOLDER = 'uploads'
LAYOUTS_FOLDER = 'layouts'
IMAGES_FOLDER = 'geradas'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(LAYOUTS_FOLDER):
    os.makedirs(LAYOUTS_FOLDER)
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

# Configuração para upload de arquivos
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LAYOUTS_FOLDER'] = LAYOUTS_FOLDER

def get_cardapio_dimensions(custom_dimensions=None):
    try:
        if custom_dimensions and isinstance(custom_dimensions, dict):
            width = int(custom_dimensions.get('width', 800))
            height = int(custom_dimensions.get('height', 1200))
            print(f"Usando dimensões personalizadas: {width}x{height}")
        else:
            # Dimensões padrão
            width = 800
            height = 1200
            print(f"Usando dimensões padrão: {width}x{height}")
        
        # Garantir dimensões mínimas
        width = max(width, 400)
        height = max(height, 600)
        
        return width, height
    except Exception as e:
        print(f"Erro ao processar dimensões: {e}")
        # Retornar dimensões padrão em caso de erro
        return 800, 1200

def get_dish_image(dish_name):
    print(f"Buscando imagem para o prato: {dish_name}")
    
    # Mapeamento de nomes de pratos para arquivos de imagem
    image_mapping = {
        'À la minute': 'alaminuta.png',
        'Omelete': 'Omelete.png',
        'Picanha na Chapa': 'Picanha na Chapa.png',
        'Filé de Peixe à Milanesa': 'Filé de Peixe à Milanesa.png',
        'Estrogonofe de Frango': 'Estrogonofe de Frango.png',
        'Salada': 'salada.png',
        'Bife Acebolado': 'bife acebolado.png'
    }
    
    try:
        if dish_name in image_mapping:
            image_path = os.path.join('geradas', image_mapping[dish_name])
            print(f"Caminho da imagem: {image_path}")
            
            # Verificar se o arquivo existe
            if os.path.exists(image_path):
                print(f"Imagem encontrada: {image_path}")
                return Image.open(image_path)
            else:
                print(f"Imagem não encontrada: {image_path}")
                
                # Tentar encontrar em caminhos alternativos
                alternative_paths = [
                    os.path.join('.', 'geradas', image_mapping[dish_name]),
                    os.path.join('public', 'geradas', image_mapping[dish_name]),
                    os.path.join('static', 'geradas', image_mapping[dish_name])
                ]
                
                for path in alternative_paths:
                    print(f"Tentando caminho alternativo: {path}")
                    if os.path.exists(path):
                        print(f"Imagem encontrada em caminho alternativo: {path}")
                        return Image.open(path)
        
        print(f"Nenhuma imagem encontrada para o prato: {dish_name}")
        return None
    except Exception as e:
        print(f"Erro ao carregar imagem para {dish_name}: {str(e)}")
        return None

def draw_border(draw, width, height, color, border_width=20, corner_size=40):
    # Desenha as bordas
    draw.rectangle([(0, 0), (width-1, height-1)], outline=color, width=border_width)
    
    # Desenha os cantos decorativos
    # Superior esquerdo
    draw.line([(corner_size, border_width), (border_width, border_width), (border_width, corner_size)], fill=color, width=border_width)
    # Superior direito
    draw.line([(width-corner_size, border_width), (width-border_width, border_width), (width-border_width, corner_size)], fill=color, width=border_width)
    # Inferior esquerdo
    draw.line([(border_width, height-corner_size), (border_width, height-border_width), (corner_size, height-border_width)], fill=color, width=border_width)
    # Inferior direito
    draw.line([(width-border_width, height-corner_size), (width-border_width, height-border_width), (width-corner_size, height-border_width)], fill=color, width=border_width)

def create_menu_image(items, custom_dimensions=None):
    try:
        # Obter dimensões do cardápio
        width, height = get_cardapio_dimensions(custom_dimensions)
        print(f"Criando menu com dimensões: {width}x{height}")

        # Criar imagem com fundo branco
        menu_image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(menu_image)

        # Calcular proporções baseadas nas dimensões
        border_width = int(width * 0.02)  # 2% da largura
        title_font_size = int(width * 0.06)  # 6% da largura
        item_name_font_size = int(width * 0.04)  # 4% da largura
        desc_font_size = int(width * 0.03)  # 3% da largura
        price_font_size = int(width * 0.035)  # 3.5% da largura

        try:
            # Carregar fontes com tamanhos proporcionais
            title_font = ImageFont.truetype("arial.ttf", title_font_size)
            item_name_font = ImageFont.truetype("arial.ttf", item_name_font_size)
            desc_font = ImageFont.truetype("arial.ttf", desc_font_size)
            price_font = ImageFont.truetype("arial.ttf", price_font_size)
        except Exception as e:
            print(f"Erro ao carregar fontes: {e}")
            # Fallback para fonte padrão
            title_font = ImageFont.load_default()
            item_name_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            price_font = ImageFont.load_default()

        # Desenhar borda
        draw.rectangle([(0, 0), (width-1, height-1)], outline='black', width=border_width)

        # Desenhar título
        title_text = "CARDÁPIO"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, height * 0.05), title_text, font=title_font, fill='black')

        # Calcular área disponível para itens
        items_start_y = height * 0.15
        items_end_y = height * 0.95
        available_height = items_end_y - items_start_y
        item_height = available_height / len(items)

        # Desenhar itens do menu
        for i, item in enumerate(items):
            y_position = items_start_y + (i * item_height)
            
            # Nome do item
            draw.text((width * 0.1, y_position), 
                     item['nome'], 
                     font=item_name_font, 
                     fill='black')
            
            # Descrição
            draw.text((width * 0.1, y_position + item_height * 0.3), 
                     item['descricao'], 
                     font=desc_font, 
                     fill='black')
            
            # Preço
            price_text = f"R$ {item['preco']:.2f}"
            price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            price_width = price_bbox[2] - price_bbox[0]
            price_x = width * 0.9 - price_width
            draw.text((price_x, y_position), 
                     price_text, 
                     font=price_font, 
                     fill='black')

        return menu_image

    except Exception as e:
        print(f"Erro ao criar imagem do menu: {e}")
        raise

@app.route('/')
def home():
    return send_file('inicio.html')

@app.route('/<path:filename>')
def serve_static(filename):
    try:
        if filename == 'favicon.ico':
            return send_from_directory('.', filename, mimetype='image/vnd.microsoft.icon')
        return send_file(filename)
    except Exception as e:
        print(f"Erro ao servir arquivo {filename}: {str(e)}")
        return jsonify({'error': f'Arquivo não encontrado: {filename}'}), 404

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-cardapio', methods=['POST'])
def upload_cardapio():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    return jsonify({
        'message': 'Cardápio recebido com sucesso',
        'filename': filename
    })

@app.route('/upload-images', methods=['POST'])
def upload_images():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    return jsonify({'message': 'Imagens recebidas com sucesso'})

@app.route('/upload-logo', methods=['POST'])
def upload_logo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    return jsonify({'message': 'Logo recebida com sucesso'})

@app.route('/generate-layouts', methods=['POST'])
def generate_layouts():
    try:
        data = request.get_json()
        dimensoes = data.get('dimensoes', None)
        print(f"Dimensões recebidas para layouts: {dimensoes}")
        
        # Diferentes conjuntos de itens para cada cardápio
        menu_sets = [
            # Cardápio 1 - Pratos Tradicionais
            [
                {"nome": "À la minute", "descricao": "Carne, arroz, feijão e ovo", "preco": 20.00},
                {"nome": "Bife Acebolado", "descricao": "Bife com cebolas caramelizadas, arroz e feijão", "preco": 22.00},
                {"nome": "Omelete", "descricao": "Ovos, queijo, presunto e temperos", "preco": 15.00},
                {"nome": "Filé de Peixe à Milanesa", "descricao": "Peixe empanado com arroz e legumes", "preco": 35.00},
                {"nome": "Estrogonofe de Frango", "descricao": "Frango em molho cremoso com arroz e batata palha", "preco": 25.00},
                {"nome": "Picanha na Chapa", "descricao": "Picanha grelhada com arroz e farofa", "preco": 45.00}
            ]
        ]
        
        layouts = []
        
        # Limpar diretório de layouts existentes
        for file in os.listdir(app.config['LAYOUTS_FOLDER']):
            file_path = os.path.join(app.config['LAYOUTS_FOLDER'], file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Erro ao deletar {file_path}: {e}")
        
        # Gera layout com as dimensões especificadas
        try:
            # Cria uma imagem para o layout usando as dimensões personalizadas
            menu_image = create_menu_image(menu_sets[0], dimensoes)
            
            # Salva a imagem
            filename = "cardapio_layout_1.png"
            filepath = os.path.join(app.config['LAYOUTS_FOLDER'], filename)
            menu_image.save(filepath)
            print(f"Layout salvo em: {filepath}")
            
            # Verificar dimensões da imagem salva
            with Image.open(filepath) as img:
                print(f"Dimensões reais da imagem gerada: {img.size}")
            
            layouts.append({
                'id': 1,
                'name': 'Layout 1',
                'filename': filename
            })
            
            return jsonify({
                'message': 'Layout gerado com sucesso',
                'layouts': layouts,
                'dimensoes_usadas': dimensoes
            })
            
        except Exception as e:
            print(f"Erro ao gerar layout: {str(e)}")
            return jsonify({'error': f'Erro ao gerar layout: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Erro ao processar requisição: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download-layout/<filename>', methods=['GET'])
def download_layout(filename):
    try:
        return send_file(
            os.path.join(app.config['LAYOUTS_FOLDER'], filename),
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/salvar-tamanho', methods=['POST'])
def salvar_tamanho():
    try:
        dimensoes = request.json
        
        # Validar dimensões
        if not isinstance(dimensoes, dict) or 'largura' not in dimensoes or 'altura' not in dimensoes:
            return jsonify({'error': 'Formato de dimensões inválido'}), 400
        
        try:
            # Converter para float para validar
            largura = float(dimensoes['largura'])
            altura = float(dimensoes['altura'])
            
            # Validar valores mínimos
            if largura < 132 or altura < 185:  # Mínimo em mm
                return jsonify({'error': 'Dimensões muito pequenas'}), 400
            
            # Validar valores máximos
            if largura > 1000 or altura > 1500:  # Máximo em mm
                return jsonify({'error': 'Dimensões muito grandes'}), 400
                
        except ValueError:
            return jsonify({'error': 'Valores de dimensão inválidos'}), 400
        
        response = make_response(jsonify({
            'message': 'Tamanho salvo com sucesso',
            'dimensoes': {
                'largura': largura,
                'altura': altura
            }
        }))
        
        # Salvar no cookie
        response.set_cookie('tamanhoCardapio', json.dumps({
            'largura': largura,
            'altura': altura
        }))
        
        return response
    except Exception as e:
        print(f"Erro ao salvar tamanho: {str(e)}")
        return jsonify({'error': str(e)}), 400

def wrap_text(c, text, width):
    """Função auxiliar para quebrar texto em linhas"""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = c.stringWidth(word + " ", "Helvetica", 14)
        if current_width + word_width <= width:
            current_line.append(word)
            current_width += word_width
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines

@app.route('/menus/<path:filename>')
def download_menu(filename):
    try:
        return send_from_directory('public/menus', filename, as_attachment=True)
    except Exception as e:
        print(f"Erro ao baixar arquivo {filename}: {str(e)}")
        return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        items = data.get('items', [])
        dimensoes = data.get('dimensoes', None)
        
        print("Itens recebidos para gerar PDF:", items)
        print("Dimensões recebidas para PDF:", dimensoes)
        
        # Criar diretório se não existir
        if not os.path.exists('public/menus'):
            os.makedirs('public/menus')
        
        filename = f"cardapio_{uuid.uuid4()}.pdf"
        output_path = os.path.join('public', 'menus', filename)
        
        # Obter dimensões personalizadas
        width_px, height_px = get_cardapio_dimensions(dimensoes)
        # Converter pixels para pontos (72 DPI para PDF)
        width_pt = width_px * 72 / 96  # Converter de 96 DPI (pixel) para 72 DPI (pontos)
        height_pt = height_px * 72 / 96
        
        print(f"Gerando PDF com dimensões: {width_pt}x{height_pt} pontos")
        
        # Criar PDF com dimensões personalizadas
        c = canvas.Canvas(output_path, pagesize=(width_pt, height_pt))
        
        # Fundo vinho escuro
        c.setFillColor(colors.Color(0.15, 0, 0.05))
        c.rect(0, 0, width_pt, height_pt, fill=1)
        
        # Borda dourada mais fina
        c.setStrokeColor(colors.gold)
        c.setLineWidth(1)
        margin = width_pt * 0.05  # 5% de margem
        c.rect(margin, margin, width_pt - 2*margin, height_pt - 2*margin, stroke=1)
        
        # Título menor e mais alto
        title_size = width_pt * 0.04  # Tamanho proporcional à largura
        c.setFont("Helvetica-Bold", title_size)
        c.setFillColor(colors.gold)
        title = "La Cuisine"
        title_width = c.stringWidth(title, "Helvetica-Bold", title_size)
        c.drawString((width_pt - title_width)/2, height_pt - margin - title_size, title)
        
        # Subtítulo menor
        subtitle_size = title_size * 0.5
        c.setFont("Helvetica", subtitle_size)
        subtitle = "Gastronomia Refinada"
        subtitle_width = c.stringWidth(subtitle, "Helvetica", subtitle_size)
        c.drawString((width_pt - subtitle_width)/2, height_pt - margin - title_size - subtitle_size - 10, subtitle)
        
        # Menu título mais compacto
        menu_title_size = title_size * 0.8
        c.setFont("Helvetica-Bold", menu_title_size)
        menu_title = "MENU"
        menu_width = c.stringWidth(menu_title, "Helvetica-Bold", menu_title_size)
        c.drawString((width_pt - menu_width)/2, height_pt - margin - title_size - subtitle_size - menu_title_size - 30, menu_title)
        
        # Configurações para layout mais compacto
        start_y = height_pt - margin - title_size - subtitle_size - menu_title_size - 60
        image_width = width_pt * 0.3  # 30% da largura
        image_height = image_width * 0.7  # Proporção 7:10
        col_width = width_pt/2 - margin
        
        # Posições das colunas mais próximas
        col_x = [margin * 1.5, width_pt/2 + margin/2]
        
        # Organizar itens em 2 colunas
        for i, item in enumerate(items):
            col = i % 2
            row = i // 2
            x = col_x[col]
            y = start_y - (row * (image_height + 80))  # Espaçamento vertical ajustado
            
            # Adicionar imagem do prato
            try:
                img = get_dish_image(item['nome'])
                if img:
                    # Converter PIL Image para bytes
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Desenhar imagem no PDF
                    c.drawImage(ImageReader(img_buffer), x, y - image_height, width=image_width, height=image_height)
            except Exception as e:
                print(f"Erro ao adicionar imagem para {item['nome']}: {str(e)}")
            
            # Nome do prato abaixo da imagem
            nome_size = title_size * 0.3
            c.setFont("Helvetica-Bold", nome_size)
            c.setFillColor(colors.gold)
            nome_width = c.stringWidth(item['nome'], "Helvetica-Bold", nome_size)
            c.drawString(x + (image_width - nome_width)/2, y - image_height - nome_size - 5, item['nome'])
            
            # Descrição abaixo do nome
            desc_size = nome_size * 0.8
            c.setFont("Helvetica", desc_size)
            c.setFillColor(colors.white)
            desc_lines = wrap_text(c, item['descricao'], image_width * 0.9)
            for idx, line in enumerate(desc_lines):
                desc_width = c.stringWidth(line, "Helvetica", desc_size)
                c.drawString(x + (image_width - desc_width)/2, 
                           y - image_height - nome_size - desc_size - 15 - (idx * desc_size * 1.2), 
                           line)
            
            # Preço por último
            preco_size = nome_size * 1.2
            c.setFont("Helvetica-Bold", preco_size)
            c.setFillColor(colors.gold)
            preco = f"R$ {item['preco']:.2f}"
            preco_width = c.stringWidth(preco, "Helvetica-Bold", preco_size)
            c.drawString(x + (image_width - preco_width)/2, 
                        y - image_height - nome_size - desc_size * (len(desc_lines) + 1) - 25, 
                        preco)
        
        # Bom Apetite mais discreto
        footer_size = title_size * 0.4
        c.setFont("Helvetica", footer_size)
        c.setFillColor(colors.gold)
        footer = "Bom Apetite!"
        footer_width = c.stringWidth(footer, "Helvetica", footer_size)
        c.drawString((width_pt - footer_width)/2, margin * 2, footer)
        
        c.save()
        print(f"PDF gerado com sucesso: {output_path}")
        
        # Retornar a URL completa do PDF
        pdf_url = f'http://localhost:8001/public/menus/{filename}'
        return jsonify({
            'success': True,
            'pdfUrl': pdf_url
        })
    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar o PDF: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(port=8001, debug=True) 