import os
import requests
from dotenv import load_dotenv
from uteis import sanitize_filename, log

async def gerar_imagem_a_partir_da_descricao(nome_prato: str, descricao: str, nivel: float = 1.0):
    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY não configurada no ambiente")

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = gerar_prompt_para_imagem(descricao, nivel)
        log(f"Prompt para gerar imagem de {nome_prato}: {prompt}")

        endpoint_image = "https://api.openai.com/v1/images/generations"

        payload_img = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response_img = requests.post(endpoint_image, headers=headers, json=payload_img)

        if response_img.status_code != 200:
            log(f"Erro ao gerar imagem do prato {nome_prato}: {response_img.text}")
            return

        img_url = response_img.json()["data"][0]["url"]

        # Salvar a imagem
        img_data = requests.get(img_url).content
        filename = sanitize_filename(nome_prato) + ".png"
        folder_path = os.path.join("uploads", "geradas")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'wb') as f:
            f.write(img_data)

        log(f"Imagem gerada e salva como: {file_path}")

    except Exception as e:
        log(f"Erro inesperado em gerar_imagem_a_partir_da_descricao para {nome_prato}:\n{traceback.format_exc()}")

def gerar_prompt_para_imagem(descricao: str, nivel: float = 1.0) -> str:
    if nivel <= 1:
        # Normal: apenas reusar a descrição
        return f"Fotografia realista de um prato de comida: {descricao}. Fundo neutro, iluminação natural."
    else:
        # Melhorado: adicionar qualidade extra
        return (
            f"Fotografia ultra detalhada de alta qualidade de um prato de comida. "
            f"Descrição visual: {descricao}. "
            f"A imagem deve ter realce nas cores, texturas aprimoradas, iluminação profissional, e pequenos detalhes visíveis. "
            f"Fundo artístico e leve desfoque no fundo. "
            f"Qualidade de imagem melhorada em {int((nivel - 1) * 100)}%."
        )

async def gerar_descricao_imagem(url_imagem: str, nome_prato: str):
    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY não configurada no ambiente")

        endpoint_chat = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        LIMITE_MIN_CARACTERES_DESCRICAO = 50
        LIMITE_MAX_CARACTERES_DESCRICAO = 100
        MAX_TOKENS_GPT = LIMITE_MAX_CARACTERES_DESCRICAO * 2

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Descreva o prato desta imagem de forma objetiva, com no mínimo {LIMITE_MIN_CARACTERES_DESCRICAO} "
                                f"e no máximo {LIMITE_MAX_CARACTERES_DESCRICAO} caracteres. "
                                "Priorize aspectos visuais como: cor, textura, tamanho, brilho, cozimento e frescor. "
                                "Indique também a posição aproximada dos elementos (ex: esquerda, centro, direita, topo, base). "
                                "Mencione ingredientes identificáveis como tomate, arroz, carne, feijão, cebola, etc. "
                                "Não use frases genéricas como 'Esta imagem mostra...'. Vá direto ao ponto."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": url_imagem
                            }
                        }
                    ]
                }
            ],
            "max_tokens": MAX_TOKENS_GPT
        }

        response = requests.post(endpoint_chat, headers=headers, json=payload)

        if response.status_code != 200:
            log(f"Erro ao chamar OpenAI Vision API: {response.text}")
            return "Descrição não disponível."

        data = response.json()
        descricao = data["choices"][0]["message"]["content"].strip()

        log(f"Descrição retornada para {nome_prato}: {descricao}")

        return descricao

    except Exception as e:
        log(f"Erro inesperado em gerar_descricao_imagem: {str(e)}")
        return "Descrição não disponível."
