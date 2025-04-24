import random
import os, glob, re
import pandas as pd
from datetime import datetime
from math import cos, sin, pi
from PIL import Image, ImageDraw, ImageFont

def sanitize_filename(name: str) -> str:    
    return re.sub(r'[\\/*?:"<>|]', "_", name)

log_dir = "log"
log_file = os.path.join(log_dir, "log.txt")

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(linha)

# Quebra de linha manual
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

def gerar_cardapio_formatado(df_path="uploads/cardapios/arquivo.xlsx"):
    log(">> Iniciando renderização do cardápio formatado")
    largura, cor_fundo, cor_detalhe = 1000, (45, 12, 25), (230, 190, 140)

    #fontes = carregar_fontes()
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

    #altura = calcular_altura(df, y_start, espacamento_vertical)
    qtd_linhas = (min(len(df), 6) + 1) // 2
    altura = y_start + qtd_linhas * espacamento_vertical + 200    

    img = Image.new("RGB", (largura, altura), cor_fundo)
    draw = ImageDraw.Draw(img)

    #inserir_logo(img, largura)
    logos = glob.glob("uploads/logo/*")
    if logos:
        logo = Image.open(logos[0]).resize((150, 150))
        img.paste(logo, ((largura - logo.width) // 2, 40), logo if logo.mode == 'RGBA' else None)    

    #inserir_titulo(draw, largura, fontes['titulo'], cor_detalhe)
    titulo = "CARDÁPIO"
    titulo_w = draw.textlength(titulo, fontes['titulo'])
    draw.text(((largura - titulo_w) // 2, 210), titulo, cor_detalhe, fontes['titulo'])    

    y_max = desenhar_pratos(img, draw, df, largura, largura_img, altura_img, x_start_esq, x_start_dir, y_start, espacamento_vertical, fontes, cor_detalhe)

    espaco_entre_texto_e_borda = 80
    espaco_texto_rodape = 50
    margem_inferior = 40
    altura_final = y_max + espaco_entre_texto_e_borda + espaco_texto_rodape + margem_inferior

    img = img.crop((0, 0, largura, altura_final))
    draw = ImageDraw.Draw(img)
    inserir_rodape(draw, largura, altura_final, fontes['rodape'], cor_detalhe, margem_inferior, espaco_texto_rodape)

    draw.rectangle([40, 40, largura - 40, altura_final - 40], outline=cor_detalhe, width=3)
    draw.rectangle([60, 60, largura - 60, altura_final - 60], outline=cor_detalhe, width=1)

    salvar_imagem(img, "uploads/final", "cardapio_final.png")

def desenhar_pratos(img, draw, df, largura, largura_img, altura_img, x_start_esq, x_start_dir, y_start, espacamento_vertical, fontes, cor_detalhe):
    y_max = 0
    for i, (_, prato) in enumerate(df.iterrows()):
        if i >= 6:
            log(">> Limite de 6 pratos atingido, parando renderização")
            break
        imagem_path = os.path.join("uploads", "geradas", sanitize_filename(prato['nome']) + ".png")
        try:
            imagem_prato = Image.open(imagem_path).resize((largura_img, altura_img))
        except FileNotFoundError:
            log(f"Imagem não encontrada: {imagem_path}")
            continue

        #x_atual = calcular_posicao_x(i, len(df), largura, largura_img, x_start_esq, x_start_dir)
        if i == len(df) - 1 and len(df) % 2 != 0:
            return (largura - largura_img) // 2
        x_atual =  x_start_esq if i % 2 == 0 else x_start_dir        

        y_atual = y_start + (espacamento_vertical * (i // 2))
        img.paste(imagem_prato, (x_atual, y_atual))
        y_texto = y_atual + altura_img + 10
        y_max = desenhar_textos(draw, prato, x_atual, y_texto, largura_img, fontes, cor_detalhe, y_max)
    return y_max

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
    log(f">> Cardápio final salvo em: {caminho}")

if __name__ == "__main__":
    gerar_cardapio() 