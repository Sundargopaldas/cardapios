from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.utils import ImageReader
from PIL import Image
import os

def gerar_pdf_simples(imagem_path, output_pdf_path, formato):
    try:
        if not os.path.exists(imagem_path):
            raise FileNotFoundError(f"Imagem não encontrada: {imagem_path}")

        # Escolhe o tamanho da página conforme o formato
        if formato == "a4":
            page_size = A4
        elif formato == "a5":
            page_size = A5
        else:
            # Padrão: A4
            page_size = A4

        largura_pt, altura_pt = page_size  # valores já em pontos (pt)
        
        img = Image.open(imagem_path)
        img_ratio = img.width / img.height
        page_ratio = largura_pt / altura_pt

        # Decide o tamanho da imagem dentro da página
        if img_ratio > page_ratio:
            # Imagem mais larga que a página
            new_width = largura_pt
            new_height = largura_pt / img_ratio
        else:
            # Imagem mais alta que a página
            new_height = altura_pt
            new_width = altura_pt * img_ratio

        x = (largura_pt - new_width) / 2
        y = (altura_pt - new_height) / 2

        c = canvas.Canvas(output_pdf_path, pagesize=page_size)

        c.drawImage(ImageReader(img), x, y, width=new_width, height=new_height)
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        c.save()

        print(f"✅ PDF gerado com sucesso: {output_pdf_path}")
        return output_pdf_path

    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        raise
