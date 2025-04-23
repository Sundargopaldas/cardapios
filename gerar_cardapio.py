import random
import os, glob, re
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from math import cos, sin, pi

def sanitize_filename(name: str) -> str:    
    return re.sub(r'[\\/*?:"<>|]', "_", name)

log_dir = "log"
log_file = os.path.join(log_dir, "log.txt")

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(linha)

def gerar_cardapio_formatado(df_path="uploads/cardapios/arquivo.xlsx"):
    log(">> Iniciando renderização do cardápio formatado")

    from PIL import Image, ImageDraw, ImageFont
    import pandas as pd
    import os

    # Configurações básicas
    largura, altura = 1000, 1800
    cor_fundo = (45, 12, 25)  # Vinho escuro
    cor_detalhe = (230, 190, 140)

    # Criar imagem base
    img = Image.new("RGB", (largura, altura), cor_fundo)
    draw = ImageDraw.Draw(img)

    # Fonte
    fonte_titulo = ImageFont.truetype("arial.ttf", 48)
    fonte_prato = ImageFont.truetype("arial.ttf", 28)
    fonte_desc = ImageFont.truetype("arial.ttf", 20)
    fonte_preco = ImageFont.truetype("arial.ttf", 24)
    fonte_rodape = ImageFont.truetype("arial.ttf", 36)

    # Inserir logo (se existir)
    logos = glob.glob("uploads/logo/*")
    if logos:
        logo = Image.open(logos[0]).resize((150, 150))
        img.paste(logo, ((largura - logo.width) // 2, 40), logo if logo.mode == 'RGBA' else None)

    # Título centralizado
    titulo = "CARDÁPIO"
    titulo_w = draw.textlength(titulo, fonte_titulo)
    draw.text(((largura - titulo_w) // 2, 210), titulo, cor_detalhe, fonte_titulo)

    # Carregar dados do Excel
    df = pd.read_excel(df_path)

    espacamento_horizontal = 80
    largura_img = 320

    x_start_esq = (largura - (largura_img * 2 + espacamento_horizontal)) // 2
    x_start_dir = x_start_esq + largura_img + espacamento_horizontal

    y_start = 300
    espacamento_vertical = 400
    largura_img, altura_img = 320, 260

    for i, (_, prato) in enumerate(df.iterrows()):
        nome = prato['nome'].title()
        descricao = prato['descricao']
        preco = prato['preco']
        
        imagem_path = os.path.join("uploads", "geradas", sanitize_filename(prato['nome']) + ".png")
        #imagem_nome = prato['imagem']

        #imagem_path = os.path.join("uploads", "geradas", sanitize_filename(str(prato['nome'])) + ".png")
        #imagem_path = os.path.join("uploads", "geradas", sanitize_filename(imagem_nome.replace(' ', '_')))
        #imagem_path = os.path.join("uploads", "geradas", imagem_nome)
        #image_path = os.path.join("uploads", "geradas", sanitize_filename(str(row.get("imagem", ""))))
        #imagem_path = os.path.join("uploads", "geradas", sanitize_filename(str(prato.get("imagem", ""))))

        try:
            imagem_prato = Image.open(imagem_path).resize((largura_img, altura_img))
        except FileNotFoundError:
            log(f"Imagem não encontrada: {imagem_path}")
            continue

        # Alternância de colunas
        if i % 2 == 0:
            x_atual = x_start_esq
        else:
            x_atual = x_start_dir

        y_atual = y_start + (espacamento_vertical * (i // 2))

        # Inserir imagem
        img.paste(imagem_prato, (x_atual, y_atual))

        # Inserir textos centralizados abaixo da imagem
        y_texto = y_atual + altura_img + 10
        nome_w = draw.textlength(nome, fonte_prato)
        preco_w = draw.textlength(f"R$ {preco:.2f}", fonte_preco)
        descricao_w = draw.textlength(descricao, fonte_desc)

        draw.text((x_atual + (largura_img - nome_w) // 2, y_texto), nome, "white", fonte_prato)
        draw.text((x_atual + (largura_img - preco_w) // 2, y_texto + 35), f"R$ {preco:.2f}", cor_detalhe, fonte_preco)
        draw.text((x_atual + (largura_img - descricao_w) // 2, y_texto + 65), descricao, (200, 200, 200), fonte_desc)

    # Rodapé centralizado
    rodape = "Bom Apetite!"
    rodape_w = draw.textlength(rodape, fonte_rodape)
    draw.text(((largura - rodape_w) // 2, altura - 80), rodape, cor_detalhe, fonte_rodape)

    # Moldura dupla decorativa
    margem_externa, margem_interna = 40, 60
    draw.rectangle([margem_externa, margem_externa, largura - margem_externa, altura - margem_externa], outline=cor_detalhe, width=3)
    draw.rectangle([margem_interna, margem_interna, largura - margem_interna, altura - margem_interna], outline=cor_detalhe, width=1)

    output_dir = "uploads/final"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cardapio_final.png")
    #output_path = "uploads/geradas/cardapio_final.png"

    img.save(output_path)
    log(f">> Cardápio final salvo em: {output_path}")

if __name__ == "__main__":
    gerar_cardapio() 