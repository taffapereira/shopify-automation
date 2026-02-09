import os
import base64
import requests
import logging
from anthropic import Anthropic
import json

logger = logging.getLogger(__name__)

class LuxuryVisionFilter:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Prompt focado em estética de luxo e limpeza visual
        self.system_prompt = """
        Você é um curador de arte e joias de luxo para uma marca high-end.
        Sua função é filtrar imagens de produtos (joias) vindas de fornecedores.
        
        CRITÉRIOS DE REPROVAÇÃO (FATAL):
        1. Marcas d'água chinesas ou logotipos de terceiros visíveis (ex: texto sobrepondo a peça).
        2. Mãos ou partes do corpo com aparência descuidada/suja.
        3. Fundo extremamente poluído, bagunçado ou com objetos aleatórios domésticos.
        4. Montagens coladas toscas ou textos promocionais ("SALE", "HOT", etc).
        5. Imagem pixelada ou de baixíssima resolução.
        
        CRITÉRIOS DE APROVAÇÃO (LUXO):
        1. Fundo limpo (branco, preto, mármore, seda, ou lifestyle elegante).
        2. Foco nítido na peça.
        3. Iluminação que valorize o brilho do metal/pedra.
        4. Fotos "lifestyle" (uso real) são bem-vindas se forem estéticas.
        
        Responda APENAS com um JSON neste formato:
        {
            "decision": "APPROVED" | "REJECTED",
            "reason": "breve motivo",
            "score": 0-10 (onde 10 é foto de capa de revista)
        }
        """

    def _get_base64_image(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao baixar imagem {url}: {e}")
        return None

    def analyze_images(self, image_urls, max_check=3):
        """
        Analisa as primeiras X imagens do produto para decidir se vale a pena importar.
        Retorna: True (Aprovado) ou False (Reprovado)
        """
        logger.info(f"🔍 Analisando {len(image_urls)} imagens com AI Vision...")
        
        # Pega apenas as primeiras imagens (geralmente as principais) para economizar tokens
        images_payload = []
        
        count = 0
        for url in image_urls:
            if count >= max_check:
                break
                
            b64_img = self._get_base64_image(url)
            if b64_img:
                images_payload.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg", # Assumindo jpeg/png, Claude lida bem
                        "data": b64_img
                    }
                })
                count += 1
        
        if not images_payload:
            return False # Sem imagens válidas

        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229", # Modelo forte de visão
                max_tokens=300,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Avalie estas imagens de produto para o catálogo de luxo:"},
                            *images_payload
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            logger.info(f"🤖 Análise AI: {response_text}")
            
            # Parsing simples do JSON na resposta
            if '"decision": "APPROVED"' in response_text or '"decision":"APPROVED"' in response_text:
                return True
            return False

        except Exception as e:
            logger.error(f"Erro na API do Claude Vision: {e}")
            # Fallback: Se a IA falhar, aprova para não travar o fluxo (ou reprova se preferir segurança)
            return True 
