"""
🤖 Cliente Claude AI
Integração com Anthropic Claude para análise de produtos
"""
import os
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class AnaliseIA:
    """Resultado da análise de IA"""
    aprovado: bool
    score: float  # 0-100
    motivo: str
    titulo_otimizado: str
    descricao_seo: str
    tags_sugeridas: list
    preco_sugerido: float
    pontos_venda: list
    riscos: list


class ClaudeClient:
    """Cliente para API do Claude (Anthropic)"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-sonnet-20240229"

        if not self.api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY não configurada")

        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def analisar_produto(self, produto: Dict) -> Optional[AnaliseIA]:
        """
        Analisa um produto usando Claude AI

        Args:
            produto: Dict com dados do produto

        Returns:
            AnaliseIA com resultado ou None em caso de erro
        """
        if not self.client:
            logger.warning("⚠️ Cliente Claude não disponível, usando fallback")
            return self._analise_fallback(produto)

        prompt = self._build_prompt(produto)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text
            return self._parse_response(result_text, produto)

        except Exception as e:
            logger.error(f"❌ Erro na análise Claude: {e}")
            return self._analise_fallback(produto)

    def _build_prompt(self, produto: Dict) -> str:
        """Constrói prompt para análise"""
        return f"""Você é um especialista em dropshipping e e-commerce. Analise este produto para uma loja de acessórios (joias, relógios, óculos, bolsas).

DADOS DO PRODUTO:
- Título: {produto.get('title', 'N/A')}
- Preço: ${produto.get('price', 0):.2f}
- Pedidos: {produto.get('orders', 0)}
- Rating: {produto.get('rating', 0)} ⭐
- Reviews: {produto.get('reviews', 0)}
- Categoria: {produto.get('category', 'N/A')}
- URL: {produto.get('product_url', 'N/A')}

CRITÉRIOS DE AVALIAÇÃO:
1. Potencial de venda no Brasil
2. Saturação de mercado (muito concorrido?)
3. Margem de lucro (markup 2.5x é viável?)
4. Apelo visual/emocional
5. Facilidade de marketing

RESPONDA EXATAMENTE NESTE FORMATO JSON:
{{
    "aprovado": true/false,
    "score": 0-100,
    "motivo": "explicação curta da decisão",
    "titulo_ptbr": "título otimizado em português (max 70 chars)",
    "descricao_seo": "descrição persuasiva com emojis e bullet points em HTML",
    "tags": ["tag1", "tag2", "tag3"],
    "preco_sugerido_brl": 99.90,
    "pontos_venda": ["ponto 1", "ponto 2", "ponto 3"],
    "riscos": ["risco 1", "risco 2"]
}}

Seja criterioso. Aprove apenas produtos com real potencial (score >= 70).
"""

    def _parse_response(self, text: str, produto: Dict) -> AnaliseIA:
        """Parseia resposta do Claude"""
        try:
            # Extrai JSON da resposta
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())

                return AnaliseIA(
                    aprovado=data.get('aprovado', False),
                    score=data.get('score', 0),
                    motivo=data.get('motivo', ''),
                    titulo_otimizado=data.get('titulo_ptbr', produto.get('title', '')),
                    descricao_seo=data.get('descricao_seo', ''),
                    tags_sugeridas=data.get('tags', []),
                    preco_sugerido=data.get('preco_sugerido_brl', 0),
                    pontos_venda=data.get('pontos_venda', []),
                    riscos=data.get('riscos', []),
                )
        except Exception as e:
            logger.error(f"Erro ao parsear resposta: {e}")

        return self._analise_fallback(produto)

    def _analise_fallback(self, produto: Dict) -> AnaliseIA:
        """Análise básica quando IA não está disponível"""
        orders = produto.get('orders', 0)
        rating = produto.get('rating', 0)
        price = produto.get('price', 0)

        # Score simples baseado em métricas
        score = 0
        if orders >= 1000:
            score += 30
        elif orders >= 500:
            score += 20

        if rating >= 4.7:
            score += 30
        elif rating >= 4.5:
            score += 20

        if 5 <= price <= 25:
            score += 20
        elif price <= 30:
            score += 10

        aprovado = score >= 60

        # Preço sugerido (markup 2.5x, convertido para BRL)
        preco_brl = round(price * 2.5 * 5.5, 2)  # USD * markup * taxa

        return AnaliseIA(
            aprovado=aprovado,
            score=score,
            motivo="Análise automática baseada em métricas",
            titulo_otimizado=produto.get('title', '')[:70],
            descricao_seo=f"<p>{produto.get('title', '')}</p>",
            tags_sugeridas=[produto.get('category', 'acessorios')],
            preco_sugerido=preco_brl,
            pontos_venda=["Produto popular", f"{orders} pedidos"],
            riscos=["Análise sem IA - revisar manualmente"],
        )

    def gerar_descricao(self, produto: Dict, analise: AnaliseIA = None) -> str:
        """
        Gera descrição otimizada para o produto

        Args:
            produto: Dados do produto
            analise: Análise prévia (opcional)

        Returns:
            HTML da descrição
        """
        if analise and analise.descricao_seo:
            return analise.descricao_seo

        titulo = produto.get('title', 'Produto')
        categoria = produto.get('category', 'acessórios')

        return f"""
<h3>✨ {titulo}</h3>

<p>Produto de alta qualidade selecionado especialmente para você!</p>

<h4>🎁 Destaques:</h4>
<ul>
<li>✅ Material premium</li>
<li>✅ Acabamento impecável</li>
<li>✅ Design moderno e elegante</li>
<li>✅ Perfeito para presente</li>
</ul>

<h4>📦 Inclui:</h4>
<ul>
<li>1x {categoria.capitalize()}</li>
<li>Embalagem segura</li>
</ul>

<p><strong>🚚 Frete Grátis para todo Brasil!</strong></p>
<p><strong>🔒 Compra 100% Segura</strong></p>
<p><strong>↩️ 7 dias para troca ou devolução</strong></p>
"""


class GoogleAIClient:
    """Cliente alternativo usando Google Gemini"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = "gemini-pro"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def analisar_produto(self, produto: Dict) -> Optional[AnaliseIA]:
        """Análise usando Google Gemini"""
        if not self.api_key:
            return None

        # Implementação similar ao Claude
        # ...
        return None


class OpenAIClient:
    """Cliente alternativo usando OpenAI GPT"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-3.5-turbo"

    def analisar_produto(self, produto: Dict) -> Optional[AnaliseIA]:
        """Análise usando OpenAI"""
        if not self.api_key:
            return None

        # Implementação similar ao Claude
        # ...
        return None

