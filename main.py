import os
import requests
import traceback
import pandas as pd
from typing import List
from pathlib import Path
from pydantic import BaseModel
from uteis import sanitize_filename, log
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from gerar_cardapio import gerar_cardapio_formatado, criar_template_base

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

layout_selecionado = None

@app.post("/upload-cardapio")
async def upload_cardapio(file: UploadFile = File(...)):
    log("Recebido upload de Excel:")

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

        log(f"Arquivo Excel salvo como: {file_name}")
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
        log(f"Recebendo imagem: {filename_original}")

        if not filename_original.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            log(f"Arquivo ignorado (formato inválido): {filename_original}")
            continue

        file_path = os.path.join("uploads/images", filename_original)

        try:
            contents = await file.read()
            with open(file_path, 'wb') as f:
                f.write(contents)

            log(f"Imagem salva como: {file_path}")
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
    log("Recebido upload de logo:")

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

        log(f"Logo salvo como: {file_name}")
        return { "message": "Logo enviada com sucesso", "filename": file_name }

    except Exception as e:
        log("Erro ao salvar o logo:{str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar logo: {str(e)}")

class LayoutRequest(BaseModel):
    file_name: str
    fake: bool
    rapido: bool

def processa_prato(nome: str, descricao: str, preco: float, categoria: str, imagem: str, usa_gpt: bool, modo_full: bool):
    log(f"Prato: {nome} | R${preco:.2f} | Categoria: {categoria} | Imagem: {imagem}")

    prompt = (
        f"Fotografia altamente realista de um prato de comida típico brasileiro chamado \"{nome}\". "
        f"O prato está servido em um prato de porcelana sobre uma mesa de madeira. "
        f"Ele deve conter: {descricao}. "
        "A imagem deve ter iluminação natural suave, foco nítido, textura visível dos ingredientes e fundo desfocado. "
        "Formato de apresentação como em fotos de menus profissionais."
    )

    log(f"Prompt para imagem: {prompt}")

    try:
        folder_path = os.path.join("uploads", "geradas")
        os.makedirs(folder_path, exist_ok=True)

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

            log(f"Modo: GPT ATIVADO | Modelo: {model} | Tamanho: {size}")

            for i in range(1, 4):
                log(f">> Gerando imagem {i} para {nome}")
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size=size,
                    response_format="url"
                )

                image_url = response.data[0].url
                log(f"URL da imagem gerada {i}: {image_url}")

                image_data = requests.get(image_url).content
                image_name = sanitize_filename(nome) + f"{i}.png"
                image_path = os.path.join(folder_path, image_name)

                with open(image_path, "wb") as f:
                    f.write(image_data)

                log(f"Imagem salva em: {image_path}")
        else:
            log("Modo: FAKE | Imagens locais serão usadas se existirem")
            for i in range(1, 4):
                image_name = sanitize_filename(nome) + f"{i}.png"
                image_path = os.path.join(folder_path, image_name)

                if os.path.exists(image_path):
                    log(f"[Modo Simulado] Imagem já existente usada: {image_path}")
                else:
                    log(f"[Modo Simulado] ERRO: Imagem {image_path} não encontrada.")
                    raise FileNotFoundError(f"Imagem não encontrada em modo simulado: {image_path} [processa_prato]")
    except Exception as e:
        log("Erro ao processar imagem:\n" + traceback.format_exc())

@app.post("/generate-layouts")
async def generate_layouts(payload: LayoutRequest):
    try:
        usa_gpt = not payload.fake
        modo_full = not payload.rapido
        file_name = os.path.abspath(payload.file_name)
        log(f"Geração de layout para: {file_name}")
        log(f"Configuração: usa_gpt={usa_gpt}, modo_full={modo_full}")

        if not os.path.exists(file_name):
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {file_name}")

        df = pd.read_excel(file_name)
        items = []

        for i, (_, row) in enumerate(df.iterrows()):
            if i >= 6:
                break 
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

        log("Verificando template base visual")
        criar_template_base()            

        try:
            log("Iniciando renderização visual do cardápio final (gerar_cardapio_formatado)")
            gerar_cardapio_formatado()
            log("Renderização do cardápio final concluída com sucesso")
        except Exception as e:
            log(f"Erro ao chamar gerar_cardapio_formatado(): {str(e)}")

        return {
            "message": "Dados extraídos com sucesso",
            "items": items
        }

    except Exception as e:
        log("Erro ao processar generate_layouts:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erro ao processar generate_layouts.")

@app.get("/cardapio/{nome_arquivo}")
async def obter_cardapio(nome_arquivo: str):
    caminho = os.path.join("uploads", "final", nome_arquivo)
    log(f"obter_cardapio {nome_arquivo}")
    if os.path.exists(caminho):        
        return FileResponse(caminho, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Cardápio não encontrado")

@app.post("/aprovar-layout")
async def aprovar_layout(data: dict = Body(...)):
    log(f"Recebido POST /aprovar-layout com data: {data}")
    layout = data.get("layout")
    if not layout:
        log("❌ Nenhum layout especificado no body.")
        raise HTTPException(status_code=400, detail="Layout não especificado")
    
    log(f"✅ Layout aprovado: {layout}")
    return {"message": "Layout aprovado com sucesso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 