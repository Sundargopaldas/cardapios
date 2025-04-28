import os
import json
import requests
import traceback
import pandas as pd
from typing import List
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
from uteis import sanitize_filename, log
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from gerar_cardapio import gerar_cardapio_formatado, criar_template_base
from gpt import gerar_descricao_imagem, gerar_imagem_a_partir_da_descricao

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
    USA_IA_PARA_DESCRICAO = False

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    saved_files = []
    descriptions = {}
    folder_path = "uploads/images"
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        filename_original = file.filename
        log(f"Recebendo imagem: {filename_original}")

        if not filename_original.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            log(f"Arquivo ignorado (formato inválido): {filename_original}")
            continue

        file_path = os.path.join(folder_path, filename_original)

        try:
            contents = await file.read()
            with open(file_path, 'wb') as f:
                f.write(contents)

            log(f"Imagem salva como: {file_path}")
            saved_files.append(filename_original)

            nome_base = os.path.splitext(filename_original)[0]

            public_url = f"https://i.imgur.com/9YFRSkw.jpeg"  # ou localhost no seu caso real

            if USA_IA_PARA_DESCRICAO:
                descricao = await gerar_descricao_imagem(public_url, nome_base)
            else:
                # 🔵 Ler a descrição salva no JSON
                descriptions_path = os.path.join("uploads", "images", "descriptions.json")
                if os.path.exists(descriptions_path):
                    with open(descriptions_path, "r", encoding="utf-8") as f:
                        descriptions_json = json.load(f)
                        descricao = descriptions_json.get(nome_base, "Descrição não disponível.")
                        log(f"🔵 Descrição lida do JSON para {nome_base}: {descricao}")
                else:
                    log(f"⚠️ Descriptions.json não encontrado. Usando descrição padrão para {nome_base}.")
                    descricao = "Descrição não disponível."

            # if USA_IA_PARA_DESCRICAO:
            #     descricao = await gerar_descricao_imagem(public_url, nome_base)
            # else:
            #     descricao = nome_base

            descriptions[nome_base] = descricao

            # 🖼️ Agora gera a imagem usando a descrição:
            await gerar_imagem_a_partir_da_descricao(nome_base, descricao)

        except Exception as e:
            log(f"Erro ao salvar ou processar imagem {filename_original}: {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)

    if not saved_files:
        raise HTTPException(status_code=400, detail="Nenhuma imagem válida foi enviada")

    descriptions_path = os.path.join(folder_path, "descriptions.json")
    with open(descriptions_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=4)
    
    log(f"Descrições salvas em {descriptions_path}")

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
            
            log(f">> Gerando 3 imagens para {nome}")
            response = client.images.generate(
                model=model,
                prompt=prompt,
                n=3, 
                size=size,
                response_format="url"
            )

            for idx, image_data in enumerate(response.data, start=1):
                image_url = image_data.url
                log(f"URL da imagem gerada {idx}: {image_url}")

                image_content = requests.get(image_url).content
                image_name = sanitize_filename(nome) + f"{idx}.png"
                image_path = os.path.join(folder_path, image_name)

                with open(image_path, "wb") as f:
                    f.write(image_content)

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
    log(f"aprovar_layout")

    nomeArquivo = data.get("nomeArquivo")
    if not nomeArquivo:
        raise HTTPException(status_code=400, detail="nomeArquivo não especificado")
    log(f"nomeArquivo {nomeArquivo}")

    if not nomeArquivo.lower().endswith(".png"):
        nomeArquivo += ".png"

    imagem_path = os.path.join("uploads", "final", nomeArquivo)

    output_pdf_path = os.path.join("menus", "cardapio.pdf")
    formato = data.get("formato")

    from pdf import gerar_pdf_simples
    gerar_pdf_simples(imagem_path, output_pdf_path, formato)

    return {"message": "PDF gerado com sucesso", "arquivo_pdf": output_pdf_path}

@app.get("/menus/cardapio.pdf")
async def download_cardapio_pdf():
    log(f"download_cardapio_pdf")
    caminho = os.path.join("menus", "cardapio.pdf")
    log(f"Download solicitado: {caminho}")

    if os.path.exists(caminho):
        return FileResponse(caminho, media_type="application/pdf", filename="cardapio.pdf")
    else:
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 