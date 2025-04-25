import os, glob
import pandas as pd
from math import pi
from uteis import sanitize_filename, log
from PIL import Image, ImageDraw, ImageFont

def quebra_linhas(texto, fonte, max_width, draw):
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = f"{linha_atual} {palavra}".strip()
        largura_teste = draw.textlength(teste, font=fonte)
        if largura_teste <= max_width:
            linha_atual = teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas

def criar_template_base():
    width, height, header_height = 800, 1200, 200
    template_dir = "uploads/templates"
    os.makedirs(template_dir, exist_ok=True)
    template_path = os.path.join(template_dir, "template.png")

    if os.path.exists(template_path):
        from uteis import log
        log(f"Template já existe: {template_path}")
        return

    cor_fundo = (45, 12, 25)
    template = Image.new('RGB', (width, height), cor_fundo)

    logos = glob.glob("uploads/logo/*")
    logo_path = logos[0] if logos else None

    if logo_path:
        try:
            logo = Image.open(logo_path)
            logo_ratio = min(header_height / logo.height, (width - 40) / logo.width)
            new_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
            logo = logo.resize(new_size, Image.Resampling.LANCZOS)
            logo_position = ((width - logo.width) // 2, (header_height - logo.height) // 2)
            template.paste(logo, logo_position, logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            log(f"Erro ao aplicar logo: {str(e)}")

    draw = ImageDraw.Draw(template)
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline='#8B7355', width=2)

    template.save(template_path, "PNG")
    log(f"Template gerado: {template_path}")

def desenhar_pratos_versao(img, draw, df, versao, largura, largura_img, altura_img, x_start_esq, x_start_dir, y_start, espacamento_vertical, fontes, cor_detalhe):
    y_max = 0
    for i, (_, prato) in enumerate(df.iterrows()):
        if i >= 6:
            log("Limite de 6 pratos atingido, parando renderização")
            break

        nome_img = sanitize_filename(prato['nome']) + f"{versao}.png"
        imagem_path = os.path.join("uploads", "geradas", nome_img)

        try:
            imagem_prato = Image.open(imagem_path).resize((largura_img, altura_img))
        except FileNotFoundError:
            log(f"Imagem não encontrada: {imagem_path} [desenhar_pratos_versao]")
            continue

        if i == len(df) - 1 and len(df) % 2 != 0:
            x_atual = (largura - largura_img) // 2
        else:
            x_atual = x_start_esq if i % 2 == 0 else x_start_dir

        y_atual = y_start + (espacamento_vertical * (i // 2))
        img.paste(imagem_prato, (x_atual, y_atual))
        y_texto = y_atual + altura_img + 10
        y_max = desenhar_textos(draw, prato, x_atual, y_texto, largura_img, fontes, cor_detalhe, y_max)
    return y_max

def gerar_cardapio_formatado(df_path="uploads/cardapios/arquivo.xlsx"):
    log("Iniciando renderização dos 3 cardápios")

    for versao in range(1, 4):  # 1, 2, 3
        log(f"Gerando versão {versao} do cardápio")

        largura, cor_fundo, cor_detalhe = 1000, (45, 12, 25), (230, 190, 140)
        fontes = {
            'titulo': ImageFont.truetype("arial.ttf", 48),
            'prato': ImageFont.truetype("arial.ttf", 28),
            'desc': ImageFont.truetype("arial.ttf", 20),
            'preco': ImageFont.truetype("arial.ttf", 24),
            'rodape': ImageFont.truetype("arial.ttf", 36),
        }

        df = pd.read_excel(df_path)
        espacamento_horizontal, largura_img, altura_img = 80, 320, 260
        x_start_esq = (largura - (largura_img * 2 + espacamento_horizontal)) // 2
        x_start_dir = x_start_esq + largura_img + espacamento_horizontal
        y_start, espacamento_vertical = 300, 400

        qtd_linhas = (min(len(df), 6) + 1) // 2
        altura = y_start + qtd_linhas * espacamento_vertical + 200    

        img = Image.new("RGB", (largura, altura), cor_fundo)
        draw = ImageDraw.Draw(img)

        logos = glob.glob("uploads/logo/*")
        if logos:
            logo = Image.open(logos[0]).resize((150, 150))
            img.paste(logo, ((largura - logo.width) // 2, 70), logo if logo.mode == 'RGBA' else None)

        titulo = "CARDÁPIO"
        titulo_w = draw.textlength(titulo, fontes['titulo'])
        draw.text(((largura - titulo_w) // 2, 230), titulo, cor_detalhe, fontes['titulo'])     

        y_max = desenhar_pratos_versao(
            img, draw, df, versao, largura, largura_img, altura_img,
            x_start_esq, x_start_dir, y_start, espacamento_vertical, fontes, cor_detalhe
        )

        espaco_entre_texto_e_borda = 80
        espaco_texto_rodape = 50
        margem_inferior = 40
        altura_final = y_max + espaco_entre_texto_e_borda + espaco_texto_rodape + margem_inferior

        img = img.crop((0, 0, largura, altura_final))
        draw = ImageDraw.Draw(img)

        inserir_rodape(draw, largura, altura_final, fontes['rodape'], cor_detalhe, margem_inferior, espaco_texto_rodape)

        draw.rectangle([40, 40, largura - 40, altura_final - 40], outline=cor_detalhe, width=3)
        draw.rectangle([60, 60, largura - 60, altura_final - 60], outline=cor_detalhe, width=1)

        salvar_imagem(img, "uploads/final", f"cardapio{versao}.png")

def desenhar_textos(draw, prato, x, y_texto, largura_img, fontes, cor_detalhe, y_max):
    nome = prato['nome'].title()
    preco = prato['preco']
    draw.text((x + (largura_img - draw.textlength(nome, fontes['prato'])) // 2, y_texto), nome, "white", fontes['prato'])
    draw.text((x + (largura_img - draw.textlength(f"R$ {preco:.2f}", fontes['preco'])) // 2, y_texto + 35), f"R$ {preco:.2f}", cor_detalhe, fontes['preco'])
    descricao_linhas = quebra_linhas(prato['descricao'], fontes['desc'], largura_img - 10, draw)
    for j, linha in enumerate(descricao_linhas):
        linha_w = draw.textlength(linha, fontes['desc'])
        y_linha = y_texto + 65 + j * 22
        draw.text((x + (largura_img - linha_w) // 2, y_linha), linha, (200, 200, 200), fontes['desc'])
        y_max = max(y_max, y_linha)
    return y_max

def inserir_rodape(draw, largura, altura_final, fonte, cor, margem_inferior=40, deslocamento_extra=15):
    rodape = "Bom Apetite!"
    rodape_w = draw.textlength(rodape, fonte)
    bbox = fonte.getbbox(rodape)
    altura_texto = bbox[3] - bbox[1]
    y_pos = altura_final - margem_inferior - altura_texto - deslocamento_extra
    draw.text(((largura - rodape_w) // 2, y_pos), rodape, cor, font=fonte)

def salvar_imagem(img, diretorio, nome_arquivo):
    os.makedirs(diretorio, exist_ok=True)
    caminho = os.path.join(diretorio, nome_arquivo)
    img.save(caminho)
    log(f"Cardápio final salvo em: {caminho}")
