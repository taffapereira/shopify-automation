"""
🤖 Gerador de Conteúdo com Google Gemini
Cria títulos, descrições e padroniza opções de produtos
"""
import os
import re
import logging
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    GEMINI_NEW = True
except ImportError:
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        GEMINI_NEW = False
    except ImportError:
        GEMINI_AVAILABLE = False
        GEMINI_NEW = False

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Prompt fixo para o Gemini
GEMINI_SYSTEM_PROMPT = """
Você é um diretor criativo de e-commerce brasileiro especializado em luxo acessível.

CONTEXTO:
- Loja: Shopify de dropshipping internacional
- Público: Mulheres brasileiras, 25-45 anos, classe B/C
- Tom: Sofisticado, clean, minimalista (sem exageros)

MISSÃO: Analisar a imagem do produto e gerar conteúdo padronizado.

═══════════════════════════════════════════
📝 RESPONDA EXATAMENTE NESTE FORMATO JSON:
═══════════════════════════════════════════

{
    "titulo": "Nome do Produto - Característica Única (máx 60 chars, sem emoji)",
    "descricao": "Descrição HTML completa",
    "opcoes_traduzidas": ["Cor1 em PT", "Cor2 em PT"],
    "tags": ["tag1", "tag2", "tag3"],
    "material": "material detectado",
    "ocasioes": ["ocasião1", "ocasião2"]
}

REGRAS PARA TÍTULO:
✅ Sem emojis
✅ Primeira letra de cada palavra maiúscula
✅ Específico e descritivo
❌ Termos genéricos ('incrível', 'maravilhoso')
❌ Mistura de idiomas

REGRAS PARA CORES (opcoes_traduzidas):
- TODAS em português correto
- Remover "color", "in golden", etc
- Usar nomes elegantes:
  * golden brown → Marrom Dourado
  * Black color → Preto
  * Milkshake Branco → Branco Off-White
  * rose gold → Rosé

ESTRUTURA DA DESCRIÇÃO HTML:
<p>[Uma frase sofisticada sobre o produto]</p>

<h4>✨ Por que você vai amar:</h4>
<ul>
<li>✅ [Benefício 1 tangível]</li>
<li>✅ [Benefício 2]</li>
<li>✅ [Benefício 3]</li>
<li>✅ [Benefício 4]</li>
</ul>

<h4>📏 Especificações:</h4>
<ul>
<li>Material: [material]</li>
<li>Estilo: [estilo]</li>
</ul>

<h4>🎁 Perfeito para:</h4>
<ul>
<li>[Ocasião 1]</li>
<li>[Ocasião 2]</li>
</ul>
"""


class GeminiContentGenerator:
    """Gerador de conteúdo usando Google Gemini"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.model = None
        self.client = None

        if self.api_key and GEMINI_AVAILABLE:
            try:
                if GEMINI_NEW:
                    # Nova API google.genai
                    self.client = genai.Client(api_key=self.api_key)
                    self.model = "gemini-2.0-flash"
                else:
                    # API antiga google.generativeai
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Google Gemini inicializado")
            except Exception as e:
                logger.error(f"Erro ao inicializar Gemini: {e}")

    def analyze_product(self, image_data: bytes, raw_options: List[str],
                       titulo_original: str = "") -> Dict:
        """
        Analisa imagem e gera conteúdo padronizado

        Args:
            image_data: Bytes da imagem principal
            raw_options: Lista de cores/tamanhos originais
            titulo_original: Título original do produto

        Returns:
            Dict com titulo, descricao, opcoes_padronizadas, tags
        """
        if not self.model and not self.client:
            return self._fallback_content(raw_options, titulo_original)

        try:
            # Preparar imagem
            img = Image.open(BytesIO(image_data))

            # Montar prompt
            prompt = f"""{GEMINI_SYSTEM_PROMPT}

INFORMAÇÕES DO PRODUTO:
- Título original: {titulo_original}
- Opções de cores originais: {', '.join(raw_options)}

Analise a imagem e retorne APENAS o JSON, sem texto adicional.
"""

            # Gerar resposta
            if self.client:
                # Nova API google.genai
                img_bytes = BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes.seek(0)

                # Criar conteúdo multimodal
                contents = [
                    prompt,
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": __import__('base64').b64encode(img_bytes.getvalue()).decode()
                        }
                    }
                ]

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents
                )
                text = response.text
            else:
                # API antiga
                response = self.model.generate_content([prompt, img])
                text = response.text

            # Parsear JSON
            content = self._parse_response(text)
            return content

        except Exception as e:
            logger.error(f"Erro no Gemini: {e}")
            return self._fallback_content(raw_options, titulo_original)

    def _parse_response(self, text: str) -> Dict:
        """Extrai JSON da resposta do Gemini"""
        import json

        # Tentar extrair JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    'titulo': data.get('titulo', ''),
                    'descricao': data.get('descricao', ''),
                    'opcoes_padronizadas': data.get('opcoes_traduzidas', []),
                    'tags': data.get('tags', []),
                    'material': data.get('material', ''),
                    'ocasioes': data.get('ocasioes', [])
                }
            except json.JSONDecodeError:
                pass

        return self._fallback_content([], "")

    def _fallback_content(self, raw_options: List[str], titulo: str) -> Dict:
        """Conteúdo fallback quando Gemini falha"""
        # Traduzir opções manualmente
        traducoes = {
            'black': 'Preto', 'white': 'Branco', 'red': 'Vermelho',
            'blue': 'Azul', 'green': 'Verde', 'pink': 'Rosa',
            'gold': 'Dourado', 'silver': 'Prata', 'brown': 'Marrom',
            'beige': 'Bege', 'grey': 'Cinza', 'gray': 'Cinza',
            'purple': 'Roxo', 'orange': 'Laranja', 'yellow': 'Amarelo',
            'navy': 'Azul Marinho', 'wine': 'Vinho', 'cream': 'Creme',
            'khaki': 'Cáqui', 'coffee': 'Café', 'caramel': 'Caramelo',
            'rose': 'Rosé', 'champagne': 'Champanhe', 'ivory': 'Marfim',
        }

        opcoes_pt = []
        for opt in raw_options:
            opt_lower = opt.lower().strip()
            # Remover "color", "in golden", etc
            opt_clean = re.sub(r'\s*(color|in\s+golden|in\s+silver)\s*', '', opt_lower, flags=re.I)

            # Traduzir
            for en, pt in traducoes.items():
                if en in opt_clean:
                    opt_clean = opt_clean.replace(en, pt)

            opcoes_pt.append(opt_clean.title())

        return {
            'titulo': titulo[:60] if titulo else 'Produto Fashion',
            'descricao': self._gerar_descricao_padrao(),
            'opcoes_padronizadas': opcoes_pt,
            'tags': ['fashion', 'feminino', 'elegante'],
            'material': '',
            'ocasioes': ['Uso diário', 'Eventos casuais']
        }

    def _gerar_descricao_padrao(self) -> str:
        """Gera descrição HTML padrão"""
        return """
<p>Peça selecionada especialmente para mulheres que valorizam estilo e elegância.</p>

<h4>✨ Por que você vai amar:</h4>
<ul>
<li>✅ Material de alta qualidade</li>
<li>✅ Design moderno e sofisticado</li>
<li>✅ Acabamento premium</li>
<li>✅ Versátil para diversas ocasiões</li>
</ul>

<h4>🎁 Perfeito para:</h4>
<ul>
<li>Uso diário</li>
<li>Eventos casuais</li>
<li>Presente especial</li>
</ul>
"""

    def traduzir_opcoes(self, opcoes: List[str]) -> List[str]:
        """Traduz lista de opções para português"""
        return self._fallback_content(opcoes, "")['opcoes_padronizadas']

