import os
import re
import glob
import requests
import traceback
import pandas as pd
from fastapi import Body
from typing import List
from pathlib import Path
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from fastapi.middleware.cors import CORSMiddleware
from gerar_cardapio import gerar_cardapio_formatado
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request

log_dir = "log"
log_file = os.path.join(log_dir, "log.txt")

if os.path.exists(log_file):
    os.remove(log_file)

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(linha)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Credentials(BaseModel):
    user: str
    password: str

class LayoutRequest(BaseModel):
    file_name: str
    fake: bool
    rapido: bool    

@app.post("/upload-cardapio")
async def upload_cardapio(file: UploadFile = File(...)):
    log(">> Recebido upload de Excel:")

    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser XLS ou XLSX")

    cardapio_dir = "uploads/cardapios"
    os.makedirs(cardapio_dir, exist_ok=True)
    for f in os.listdir(cardapio_dir):
        file_path = os.path.join(cardapio_dir, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    file_extension = Path(file.filename).suffix
    file_name = f"{cardapio_dir}/arquivo{file_extension}"

    try:
        contents = await file.read()
        with open(file_name, 'wb') as f:
            f.write(contents)

        log(f">> Arquivo Excel salvo como: {file_name}")
        return { "message": "Arquivo salvo com sucesso", "filename": file_name }

    except Exception as e:
        log("Erro ao salvar o arquivo Excel:{str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar o arquivo: {str(e)}")

@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    saved_files = []
    for file in files:
        filename_original = file.filename
        log(f">> Recebendo imagem: {filename_original}")

        if not filename_original.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            log(f">> Arquivo ignorado (formato inválido): {filename_original}")
            continue

        file_path = os.path.join("uploads/images", filename_original)

        try:
            contents = await file.read()
            with open(file_path, 'wb') as f:
                f.write(contents)

            log(f">> Imagem salva como: {file_path}")
            saved_files.append(file_path)

        except Exception as e:
            log(f"Erro ao salvar imagem: {filename_original} - {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)

    if not saved_files:
        raise HTTPException(status_code=400, detail="Nenhuma imagem válida foi enviada")

    return {
        "message": f"{len(saved_files)} imagem(ns) enviada(s) com sucesso",
        "files": saved_files
    }

@app.post("/verify")
async def verify_credentials(credentials: Credentials):
    is_valid = credentials.user == "user" and credentials.password == "pass"
    return {"is_valid": is_valid}

@app.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    log(">> Recebido upload de logo:")

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem (PNG, JPG, JPEG ou GIF)")

    logo_dir = "uploads/logo"
    os.makedirs(logo_dir, exist_ok=True)
    for f in os.listdir(logo_dir):
        file_path = os.path.join(logo_dir, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

    file_extension = Path(file.filename).suffix.lower()
    file_name = f"{logo_dir}/logo{file_extension}"

    try:
        contents = await file.read()
        with open(file_name, 'wb') as f:
            f.write(contents)

        log(f">> Logo salvo como: {file_name}")
        return { "message": "Logo enviada com sucesso", "filename": file_name }

    except Exception as e:
        log("Erro ao salvar o logo:{str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar logo: {str(e)}")

def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de pasta"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

class LayoutRequest(BaseModel):
    file_name: str
    fake: bool
    rapido: bool

def processa_prato(nome: str, descricao: str, preco: float, categoria: str, imagem: str, usa_gpt: bool, modo_full: bool):
    log(f">> Prato: {nome} | R${preco:.2f} | Categoria: {categoria} | Imagem: {imagem}")
    prompt = f"Crie uma imagem realista de um prato de comida chamado \"{nome}\". Ele deve conter os seguintes ingredientes: {descricao}."
    log(f">> Prompt para imagem: {prompt}")

    try:
        folder_path = os.path.join("uploads", "geradas")
        os.makedirs(folder_path, exist_ok=True)
        image_name = sanitize_filename(nome) + ".png"
        image_path = os.path.join(folder_path, image_name)

        if usa_gpt:
            from openai import OpenAI
            from dotenv import load_dotenv
            load_dotenv()
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            if modo_full:
                model = "dall-e-3"
                size = "1024x1024"
            else:
                model = "dall-e-2"
                size = "256x256"

            log(f">> Modo: GPT ATIVADO | Modelo: {model} | Tamanho: {size}")

            generation_response = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=size,
                response_format="url"
            )

            image_url = generation_response.data[0].url
            log(f">> URL da imagem gerada: {image_url}")

            image_data = requests.get(image_url).content
            with open(image_path, "wb") as f:
                f.write(image_data)

            log(f">> Imagem salva em: {image_path}")
        else:
            log(">> Modo: FAKE | Imagem local será usada se existir")
            if os.path.exists(image_path):
                log(f">> [Modo Simulado] Imagem já existente usada: {image_path}")
            else:
                log(f">> [Modo Simulado] ERRO: Imagem {image_path} não encontrada.")
                raise FileNotFoundError(f"Imagem não encontrada em modo simulado: {image_path}")
    except Exception as e:
        log("Erro ao processar imagem:\n" + traceback.format_exc())

@app.post("/generate-layouts")
async def generate_layouts(payload: LayoutRequest):
    try:
        usa_gpt = not payload.fake
        modo_full = not payload.rapido
        file_name = os.path.abspath(payload.file_name)
        log(f">> Geração de layout para: {file_name}")
        log(f">> Configuração: usa_gpt={usa_gpt}, modo_full={modo_full}")

        if not os.path.exists(file_name):
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {file_name}")

        df = pd.read_excel(file_name)
        items = []

        for _, row in df.iterrows():
            nome = str(row.get('nome', ''))
            descricao = str(row.get('descricao', ''))
            preco = float(row.get('preco', 0))
            categoria = str(row.get('categoria', ''))
            imagem = str(row.get('imagem', ''))

            processa_prato(nome, descricao, preco, categoria, imagem, usa_gpt, modo_full)

            items.append({
                "nome": nome,
                "descricao": descricao,
                "preco": preco,
                "categoria": categoria,
                "imagem": imagem
            })

        # Geração dos templates visuais com logo
        width, height, header_height = 800, 1200, 200
        logos = glob.glob("uploads/logo/*")
        logo_path = logos[0] if logos else None
        log(f">> {'Com' if logo_path else 'Sem'} logo para templates")

        template_dir = "uploads/templates"
        os.makedirs(template_dir, exist_ok=True)

        for i in range(1, 4):
            template = Image.new('RGB', (width, height), color='#2B3A2B')

            if logo_path:
                try:
                    logo = Image.open(logo_path)
                    logo_ratio = min(header_height / logo.height, (width - 40) / logo.width)
                    new_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
                    logo = logo.resize(new_size, Image.Resampling.LANCZOS)
                    logo_position = ((width - logo.width) // 2, (header_height - logo.height) // 2)
                    template.paste(logo, logo_position, logo if logo.mode == 'RGBA' else None)
                except Exception as e:
                    log(f">> Erro ao aplicar logo: {str(e)}")

            draw = ImageDraw.Draw(template)
            draw.rectangle([(20, 20), (width - 20, height - 20)], outline='#8B7355', width=2)
            file_path = os.path.join(template_dir, f"arquivo{i}.png")
            template.save(file_path, "PNG")
            log(f">> Template gerado: {file_path}")

        # 🔥 CHAMADA FINAL PARA GERAR O CARDÁPIO NO ESTILO DO LUIS CARLOS
        try:
            log(">> Iniciando renderização visual do cardápio final (gerar_cardapio_formatado)")
            gerar_cardapio_formatado()
            log(">> Renderização do cardápio final concluída com sucesso")
        except Exception as e:
            log(f">> Erro ao chamar gerar_cardapio_formatado(): {str(e)}")

        return {
            "message": "Dados extraídos com sucesso",
            "items": items
        }

    except Exception as e:
        log("Erro ao processar generate_layouts:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erro ao processar generate_layouts.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 