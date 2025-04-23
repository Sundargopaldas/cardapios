import random
import os, glob, re
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from math import cos, sin, pi

def sanitize_filename(name: str) -> str:    
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def gerar_cardapio_formatado():
    width, height = 1000, 1800
    prato_width, prato_height = 320, 260
    spacing_x, spacing_y = 60, 320
    logo_max_height = 150
    accent_color = (230, 190, 140)
    background_color = (45, 12, 25)

    df = pd.read_excel("uploads/cardapios/arquivo.xlsx")

    cardapio = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(cardapio)

    # Gradiente elaborado
    for y in range(height):
        r = int(45 + (y / height) * 15)
        g = int(12 + (y / height) * 8)
        b = int(25 + (y / height) * 10)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Textura sutil
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            if (x + y) % 8 == 0:
                draw.point((x, y), fill=(50, 15, 30))

    try:
        fonte_header = ImageFont.truetype("arial.ttf", 48)
        fonte_nome = ImageFont.truetype("arial.ttf", 28)
        fonte_preco = ImageFont.truetype("arial.ttf", 26)
        fonte_desc = ImageFont.truetype("arial.ttf", 22)
    except:
        fonte_header = fonte_nome = fonte_preco = fonte_desc = ImageFont.load_default()

    # Inserir logo se existir
    logos = glob.glob("uploads/logo/*")
    if logos:
        logo = Image.open(logos[0])
        ratio = logo_max_height / logo.height
        logo = logo.resize((int(logo.width * ratio), logo_max_height), Image.LANCZOS)
        cardapio.paste(logo, ((width - logo.width) // 2, 40), logo if logo.mode == 'RGBA' else None)

    # Título centralizado
    titulo = "CARDÁPIO"
    titulo_x = width // 2
    draw.text((titulo_x, 220), titulo, fill=accent_color, font=fonte_header, anchor="mm")

    # Moldura ornamentada externa e interna
    margin = 40
    inner_margin = 60
    draw.rectangle([margin, margin, width-margin, height-margin], outline=accent_color, width=2)
    draw.rectangle([inner_margin, inner_margin, width-inner_margin, height-inner_margin], outline=accent_color, width=1)

    # Renderização dos pratos
    start_y = 300
    pratos_por_linha = 2
    prato_idx = 0

    for idx, row in df.iterrows():
        col = prato_idx % pratos_por_linha
        linha = prato_idx // pratos_por_linha

        x = 100 + col * (prato_width + spacing_x)
        y = start_y + linha * spacing_y

        nome, preco, descricao = row['nome'], row['preco'], row['descricao']
        imagem_nome = sanitize_filename(nome) + ".png"
        imagem_path = os.path.join("uploads/geradas", imagem_nome)

        if os.path.exists(imagem_path):
            img = Image.open(imagem_path).resize((prato_width, prato_height), Image.LANCZOS)
            cardapio.paste(img, (x, y))

        texto_y = y + prato_height + 5
        draw.text((x, texto_y), nome, fill="white", font=fonte_nome)
        draw.text((x, texto_y + 30), f"R$ {preco:.2f}", fill=accent_color, font=fonte_preco)
        draw.text((x, texto_y + 60), descricao, fill="lightgray", font=fonte_desc)

        prato_idx += 1

    # Rodapé decorativo
    footer_text = "Bom Apetite!"
    footer_font = ImageFont.truetype("arial.ttf", 32) if fonte_header else ImageFont.load_default()
    footer_width = draw.textlength(footer_text, font=footer_font)
    draw.text(((width-footer_width)//2, height-80), footer_text, accent_color, footer_font)

    os.makedirs("uploads/final", exist_ok=True)
    cardapio.save("uploads/final/cardapio_formatado.png")

def draw_ornate_frame(draw, x, y, width, height, color):
    # Desenha cantos ornamentados
    corner_size = 30
    line_width = 2
    
    # Função auxiliar para desenhar curvas decorativas
    def draw_corner(x, y, angles):
        for i in range(0, 20, 2):
            angle1 = angles[0] + (angles[1] - angles[0]) * (i / 20)
            angle2 = angles[0] + (angles[1] - angles[0]) * ((i + 1) / 20)
            x1 = x + corner_size * cos(angle1)
            y1 = y + corner_size * sin(angle1)
            x2 = x + corner_size * cos(angle2)
            y2 = y + corner_size * sin(angle2)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=line_width)
    
    # Desenha os cantos
    draw_corner(x + corner_size, y + corner_size, (pi, 3*pi/2))  # Superior esquerdo
    draw_corner(x + width - corner_size, y + corner_size, (3*pi/2, 2*pi))  # Superior direito
    draw_corner(x + corner_size, y + height - corner_size, (pi/2, pi))  # Inferior esquerdo
    draw_corner(x + width - corner_size, y + height - corner_size, (0, pi/2))  # Inferior direito
    
    # Desenha as linhas conectoras
    draw.line([(x + corner_size, y), (x + width - corner_size, y)], fill=color, width=line_width)  # Superior
    draw.line([(x + corner_size, y + height), (x + width - corner_size, y + height)], fill=color, width=line_width)  # Inferior
    draw.line([(x, y + corner_size), (x, y + height - corner_size)], fill=color, width=line_width)  # Esquerda
    draw.line([(x + width, y + corner_size), (x + width, y + height - corner_size)], fill=color, width=line_width)  # Direita

def draw_decorative_divider(draw, x, y, width, color):
    # Desenha divisor decorativo
    line_width = 2
    pattern_width = 20
    
    # Linha central
    draw.line([(x, y), (x + width, y)], fill=color, width=line_width)
    
    # Padrões decorativos ao longo da linha
    for i in range(0, width, pattern_width * 2):
        # Desenha pequenos diamantes
        points = [
            (x + i, y - 5),
            (x + i + 5, y),
            (x + i, y + 5),
            (x + i - 5, y)
        ]
        draw.polygon(points, outline=color)

def draw_fork(draw, x, y, size, color, angle=0):
    # Desenha um garfo estilizado
    handle_width = size // 8
    teeth_length = size * 0.6
    handle_length = size * 0.4
    
    # Base do garfo
    draw.rectangle([x - handle_width//2, y, x + handle_width//2, y + size], fill=color)
    
    # Dentes do garfo
    tooth_width = handle_width // 2
    for i in [-2, 0, 2]:
        draw.rectangle([x + i*tooth_width, y, x + i*tooth_width + tooth_width, y + teeth_length], fill=color)

def draw_knife(draw, x, y, size, color, angle=0):
    # Desenha uma faca estilizada
    handle_width = size // 8
    blade_length = size * 0.6
    handle_length = size * 0.4
    
    # Lâmina
    points = [
        (x - handle_width//2, y),
        (x + handle_width//2, y),
        (x + handle_width//2, y + blade_length),
        (x, y + size),
        (x - handle_width//2, y + blade_length),
    ]
    draw.polygon(points, fill=color)

def draw_plate(draw, x, y, size, color):
    # Desenha um prato estilizado
    outer_radius = size // 2
    inner_radius = int(size * 0.4)
    
    # Círculo externo
    draw.ellipse([x - outer_radius, y - outer_radius, x + outer_radius, y + outer_radius], outline=color, width=2)
    # Círculo interno
    draw.ellipse([x - inner_radius, y - inner_radius, x + inner_radius, y + inner_radius], outline=color, width=2)

def draw_salt_shaker(draw, x, y, size, color):
    # Desenha um saleiro estilizado
    width = size // 3
    height = size // 1.5
    
    # Corpo do saleiro
    draw.rectangle([x - width//2, y + size//6, x + width//2, y + height], outline=color, width=2)
    # Tampa
    draw.ellipse([x - width//2, y, x + width//2, y + size//3], outline=color, width=2)
    # Pontos (sal)
    for i in range(3):
        for j in range(2):
            dot_x = x - width//4 + (i * width//2)
            dot_y = y + height - (j * width//2) - width//4
            draw.ellipse([dot_x-1, dot_y-1, dot_x+1, dot_y+1], fill=color)

def create_restaurant_logo(width, height, background_color, accent_color):
    # Criar uma imagem para a logo
    logo = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(logo)
    
    try:
        # Fonte para o nome do restaurante
        font_name = ImageFont.truetype("arial.ttf", 60)
        font_slogan = ImageFont.truetype("arial.ttf", 24)
    except:
        font_name = ImageFont.load_default()
        font_slogan = ImageFont.load_default()
    
    # Nome do restaurante
    restaurant_name = "La Cuisine"
    name_width = draw.textlength(restaurant_name, font=font_name)
    name_x = (width - name_width) // 2
    
    # Desenhar o nome com sombra
    draw.text((name_x + 2, 20 + 2), restaurant_name, font=font_name, fill=(30, 30, 30))
    draw.text((name_x, 20), restaurant_name, font=font_name, fill=accent_color)
    
    # Slogan
    slogan = "Gastronomia Refinada"
    slogan_width = draw.textlength(slogan, font=font_slogan)
    slogan_x = (width - slogan_width) // 2
    draw.text((slogan_x, 90), slogan, font=font_slogan, fill=(220, 220, 220))
    
    # Elementos decorativos
    line_y = 75
    line_length = 200
    line_start = (width - line_length) // 2
    line_end = line_start + line_length
    
    # Linha decorativa com espessura variável
    for i in range(3):
        draw.line([(line_start, line_y + i), (line_end, line_y + i)], 
                 fill=accent_color)
    
    return logo

def draw_elegant_utensils(draw, x, y, size, color):
    # Desenha talheres mais elegantes
    
    # Garfo
    fork_width = size // 6
    teeth_length = size * 0.7
    handle_length = size * 0.3
    
    # Base do garfo com curva elegante
    points = [
        (x - fork_width, y),
        (x + fork_width, y),
        (x + fork_width//2, y + handle_length),
        (x, y + size),
        (x - fork_width//2, y + handle_length)
    ]
    draw.polygon(points, fill=color)
    
    # Dentes do garfo com curvas
    tooth_spacing = fork_width // 2
    for i in [-2, -1, 1, 2]:
        draw.line([(x + i*tooth_spacing, y), 
                  (x + i*tooth_spacing, y + teeth_length)],
                 fill=color, width=2)

def add_glow_effect(draw, x, y, size, color, intensity=0.3):
    # Adiciona um efeito de brilho sutil
    for i in range(3, 0, -1):
        alpha = int(255 * intensity * (i/3))
        glow_color = (*color[:3], alpha)
        draw.ellipse([x-size*i, y-size*i, x+size*i, y+size*i], 
                    fill=glow_color)

def draw_corner_ornaments(draw, x, y, size, color):
    # Desenha elementos decorativos nos cantos
    # Padrão de folhas estilizadas
    leaf_size = size // 2
    for angle in [0, 90, 180, 270]:
        # Base da folha
        points = [
            (x, y),
            (x + leaf_size * cos(angle * pi/180), y + leaf_size * sin(angle * pi/180)),
            (x + leaf_size * cos((angle + 45) * pi/180), y + leaf_size * sin((angle + 45) * pi/180))
        ]
        draw.polygon(points, outline=color, width=2)

def add_texture_background(draw, width, height, color, density=0.1):
    # Adiciona uma textura sutil ao fundo
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if random.random() < density:
                alpha = random.randint(10, 30)
                draw.point((x, y), fill=(*color[:3], alpha))

def add_text_shadow(draw, text, position, font, color, shadow_color, offset=2):
    # Adiciona sombra suave ao texto
    x, y = position
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text(position, text, font=font, fill=color)

def wrap_text(text, font, max_width, draw):
    # Função para quebrar o texto em múltiplas linhas
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def gerar_cardapio():
    # Carregar a imagem modelo
    modelo_path = "Imagem do WhatsApp de 2025-04-22 à(s) 01.14.55_6aaab00f.jpg"
    modelo = Image.open(modelo_path)
    
    # Definir tamanho das imagens dos pratos
    prato_width = 320
    prato_height = 260
    
    # Configurações de layout
    spacing_x = 60
    
    # Carregar os dados do Excel
    df = pd.read_excel("Pasta1.xlsx")
    
    # Configurações de fonte
    try:
        fonte_menu = ImageFont.truetype("arial.ttf", 72)
        fonte_titulo = ImageFont.truetype("arial.ttf", 28)
        fonte_texto = ImageFont.truetype("arial.ttf", 22)
        fonte_preco = ImageFont.truetype("arial.ttf", 26)
        fonte_footer = ImageFont.truetype("arial.ttf", 36)
    except:
        fonte_menu = ImageFont.load_default()
        fonte_titulo = ImageFont.load_default()
        fonte_texto = ImageFont.load_default()
        fonte_preco = ImageFont.load_default()
        fonte_footer = ImageFont.load_default()
    
    # Criar uma imagem
    width = 1000
    height = 1800  # Reduzindo a altura para 3 pares de imagens
    background_color = (45, 12, 25)  # Vinho escuro
    accent_color = (230, 190, 140)  # Dourado rosado
    secondary_color = (180, 150, 120)  # Dourado mais suave
    
    cardapio = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(cardapio)
    
    # Criar gradiente mais elaborado
    for y in range(height):
        r = int(45 + (y / height) * 15)
        g = int(12 + (y / height) * 8)
        b = int(25 + (y / height) * 10)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Adicionar textura sutil
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            if (x + y) % 8 == 0:
                draw.point((x, y), fill=(50, 15, 30))
    
    # Criar e adicionar logo
    logo = create_restaurant_logo(width, 150, background_color, accent_color)
    cardapio.paste(logo, (0, 30))
    
    # Desenhar molduras ornamentadas
    margin = 40
    draw_ornate_frame(draw, margin, margin, width - 2*margin, height - 2*margin, accent_color)
    
    inner_margin = 60
    draw_ornate_frame(draw, inner_margin, inner_margin, width - 2*inner_margin, height - 2*inner_margin, secondary_color)
    
    # Adicionar título "MENU" com elementos decorativos
    menu_text = "MENU"
    menu_width = draw.textlength(menu_text, font=fonte_menu)
    menu_x = (width - menu_width) // 2
    menu_y = 200  # Ajustado para ficar abaixo da logo
    
    # Sombra do texto com múltiplas camadas
    for offset in range(1, 4):
        draw.text((menu_x + offset, menu_y + offset), menu_text, font=fonte_menu, fill=(60, 20, 35))
    draw.text((menu_x, menu_y), menu_text, font=fonte_menu, fill=accent_color)
    
    # Adicionar talheres elegantes
    icon_size = 80
    icon_spacing = 150
    
    # Lado esquerdo
    draw_elegant_utensils(draw, menu_x - icon_spacing, menu_y + 30, icon_size, accent_color)
    
    # Lado direito
    draw_elegant_utensils(draw, menu_x + menu_width + icon_spacing, menu_y + 30, icon_size, accent_color)
    
    # Adicionar ornamentos nos cantos da moldura principal
    corner_size = 40
    draw_corner_ornaments(draw, margin, margin, corner_size, accent_color)
    draw_corner_ornaments(draw, width - margin, margin, corner_size, accent_color)
    draw_corner_ornaments(draw, margin, height - margin, corner_size, accent_color)
    draw_corner_ornaments(draw, width - margin, height - margin, corner_size, accent_color)
    
    # Calcular espaço disponível para as imagens
    menu_bottom = menu_y + 100  # Posição abaixo do título MENU
    footer_top = height - 150  # Posição acima da linha decorativa inferior
    available_height = footer_top - menu_bottom
    
    # Calcular espaçamento entre os pares de imagens
    total_image_height = prato_height + 150  # Altura da imagem + espaço para texto
    total_spacing = available_height - (3 * total_image_height)  # Espaço total disponível menos o espaço das imagens
    spacing_between = total_spacing // 4  # Dividir o espaço restante em 4 partes (3 espaços entre 3 pares)
    
    # Posições Y para cada par de imagens
    y_positions = []
    current_y = menu_bottom + spacing_between
    for _ in range(3):
        y_positions.append(current_y)
        current_y += total_image_height + spacing_between
    
    # Calcular posições para as 6 imagens (3 pares) centralizadas
    total_width = (prato_width * 2) + spacing_x
    x_start = (width - total_width) // 2
    
    # Redimensionar e adicionar as imagens
    modelo_resized = modelo.resize((prato_width, prato_height))
    
    # Adicionar imagens e textos para cada posição
    for y_pos in y_positions:
        # Primeira imagem e texto
        x1 = x_start
        cardapio.paste(modelo_resized, (x1, y_pos))
        
        if len(df) > 0:
            row = df.iloc[0]
            nome = str(row.get('nome', ''))
            descricao = str(row.get('descricao', ''))
            preco = float(row.get('preco', 0))
            
            text_y = y_pos + prato_height + 20
            
            # Adicionar textos com estilo elaborado
            nome_width = draw.textlength(nome, font=fonte_titulo)
            desc_lines = wrap_text(descricao, fonte_texto, prato_width - 20, draw)
            preco_text = f"R$ {preco:.2f}"
            preco_width = draw.textlength(preco_text, font=fonte_preco)
            
            # Nome com decoração
            nome_x = x1 + (prato_width - nome_width) // 2
            draw.text((nome_x, text_y), nome, font=fonte_titulo, fill=(255, 255, 255))
            draw.line([(nome_x - 10, text_y + 35), (nome_x + nome_width + 10, text_y + 35)],
                     fill=accent_color, width=2)
            
            # Descrição com quebra de linha
            for i, line in enumerate(desc_lines):
                line_width = draw.textlength(line, font=fonte_texto)
                desc_x = x1 + (prato_width - line_width) // 2
                draw.text((desc_x, text_y + 45 + (i * 25)), line, font=fonte_texto, fill=(220, 220, 220))
            
            # Preço com destaque
            preco_x = x1 + (prato_width - preco_width) // 2
            draw.text((preco_x, text_y + 85), preco_text, font=fonte_preco, fill=accent_color)
            
            # Adicionar sombras suaves nos textos
            shadow_color = (60, 20, 35)
            add_text_shadow(draw, nome, (nome_x, text_y), fonte_titulo, (255, 255, 255), shadow_color)
            for i, line in enumerate(desc_lines):
                line_width = draw.textlength(line, font=fonte_texto)
                desc_x = x1 + (prato_width - line_width) // 2
                add_text_shadow(draw, line, (desc_x, text_y + 45 + (i * 25)), fonte_texto, (220, 220, 220), shadow_color)
            add_text_shadow(draw, preco_text, (preco_x, text_y + 85), fonte_preco, accent_color, shadow_color)
        
        # Segunda imagem e texto
        x2 = x1 + prato_width + spacing_x
        cardapio.paste(modelo_resized, (x2, y_pos))
        
        if len(df) > 0:
            # Repetir os mesmos textos para a segunda imagem
            text_y = y_pos + prato_height + 20
            
            nome_x = x2 + (prato_width - nome_width) // 2
            draw.text((nome_x, text_y), nome, font=fonte_titulo, fill=(255, 255, 255))
            draw.line([(nome_x - 10, text_y + 35), (nome_x + nome_width + 10, text_y + 35)],
                     fill=accent_color, width=2)
            
            # Descrição com quebra de linha
            desc_lines = wrap_text(descricao, fonte_texto, prato_width - 20, draw)
            for i, line in enumerate(desc_lines):
                line_width = draw.textlength(line, font=fonte_texto)
                desc_x = x2 + (prato_width - line_width) // 2
                draw.text((desc_x, text_y + 45 + (i * 25)), line, font=fonte_texto, fill=(220, 220, 220))
            
            preco_x = x2 + (prato_width - preco_width) // 2
            draw.text((preco_x, text_y + 85), preco_text, font=fonte_preco, fill=accent_color)
            
            # Adicionar sombras suaves nos textos
            add_text_shadow(draw, nome, (nome_x, text_y), fonte_titulo, (255, 255, 255), shadow_color)
            for i, line in enumerate(desc_lines):
                line_width = draw.textlength(line, font=fonte_texto)
                desc_x = x2 + (prato_width - line_width) // 2
                add_text_shadow(draw, line, (desc_x, text_y + 45 + (i * 25)), fonte_texto, (220, 220, 220), shadow_color)
            add_text_shadow(draw, preco_text, (preco_x, text_y + 85), fonte_preco, accent_color, shadow_color)
    
    # Adicionar rodapé elaborado
    footer_y = height - 150
    footer_text = "Bom Apetite!"
    footer_width = draw.textlength(footer_text, font=fonte_footer)
    footer_x = (width - footer_width) // 2
    
    # Elementos decorativos do rodapé - centralizados
    divider_width = 400
    divider_x = (width - divider_width) // 2
    
    # Linha decorativa superior
    draw_decorative_divider(draw, divider_x, footer_y - 20, divider_width, accent_color)
    
    # Texto do rodapé com efeito elaborado
    for offset in range(1, 3):
        draw.text((footer_x + offset, footer_y + 40 + offset), footer_text,
                 font=fonte_footer, fill=(60, 20, 35))
    draw.text((footer_x, footer_y + 40), footer_text, font=fonte_footer, fill=accent_color)
    
    # Linha decorativa inferior
    draw_decorative_divider(draw, divider_x, footer_y + 100, divider_width, accent_color)
    
    # Adicionar sombra ao texto do rodapé
    add_text_shadow(draw, footer_text, (footer_x, footer_y + 40), fonte_footer, accent_color, shadow_color)
    
    # Salvar a imagem
    cardapio.save("cardapio_1.png")
    print("Cardápio gerado com sucesso!")

if __name__ == "__main__":
    gerar_cardapio() 