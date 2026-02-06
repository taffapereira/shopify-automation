"""
🤖 Cliente Claude AI - Opus 4.5
Análise inteligente de produtos com viralidade e concorrência
"""
import os
import json
import logging
import re
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class AnaliseViralidade:
    score: int = 0
    potencial_tiktok: int = 0
    potencial_instagram: int = 0
    hashtags_sugeridas: List[str] = field(default_factory=list)
    hooks_video: List[str] = field(default_factory=list)
    tendencias_relacionadas: List[str] = field(default_factory=list)


@dataclass
class AnaliseConcorrencia:
    nivel_saturacao: str = "medio"
    estimativa_lojas: int = 0
    diferencial_sugerido: str = ""
    risco_marca_registrada: bool = False
    alertas: List[str] = field(default_factory=list)


@dataclass
class AnaliseIA:
    aprovado: bool = False
    score: float = 0
    motivo: str = ""
    titulo_otimizado: str = ""
    descricao_seo: str = ""
    tags_sugeridas: List[str] = field(default_factory=list)
    preco_sugerido: float = 0.0
    margem_estimada: float = 0.0
    pontos_venda: List[str] = field(default_factory=list)
    publico_alvo: str = ""
    viralidade: Optional[AnaliseViralidade] = None
    concorrencia: Optional[AnaliseConcorrencia] = None
    riscos: List[str] = field(default_factory=list)
    modelo_usado: str = ""
    timestamp: str = ""


class ClaudeClient:
    """Cliente Claude Opus 4.5"""

    MODELOS = {
        "opus": "claude-opus-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "sonnet-3.5": "claude-3-5-sonnet-20241022",
    }

    def __init__(self, modelo: str = "opus"):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = self.MODELOS.get(modelo, self.MODELOS["opus"])
        self.client = None

        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"✅ Claude {modelo} inicializado")

    def analisar_produto(self, produto: Dict) -> AnaliseIA:
        if not self.client:
            return self._fallback(produto)

        prompt = f"""Analise este produto para dropshipping de acessórios no Brasil.

PRODUTO:
- Título: {produto.get('title', 'N/A')}
- Preço: ${produto.get('price', 0):.2f}
- Pedidos: {produto.get('orders', 0)}
- Rating: {produto.get('rating', 0)}⭐
- Categoria: {produto.get('category', 'N/A')}

RESPONDA EM JSON:
{{
    "aprovado": true/false,
    "score": 0-100,
    "motivo": "explicação",
    "titulo_ptbr": "título português max 70 chars",
    "descricao_html": "<h3>✨ Título</h3><p>Descrição</p>",
    "tags": ["tag1", "tag2"],
    "preco_sugerido_brl": 99.90,
    "margem_percentual": 55,
    "pontos_venda": ["ponto1", "ponto2"],
    "publico_alvo": "descrição público",
    "viralidade": {{
        "score": 0-100,
        "potencial_tiktok": 0-100,
        "potencial_instagram": 0-100,
        "hashtags": ["#tag1"],
        "hooks": ["hook1"],
        "tendencias": ["tendencia1"]
    }},
    "concorrencia": {{
        "nivel_saturacao": "baixo/medio/alto",
        "estimativa_lojas": 50,
        "diferencial_sugerido": "como diferenciar",
        "risco_marca": false,
        "alertas": []
    }},
    "riscos": ["risco1"]
}}

Score >= 70 para aprovar."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse(response.content[0].text, produto)
        except Exception as e:
            logger.error(f"Erro Claude: {e}")
            return self._fallback(produto)

    def _parse(self, text: str, produto: Dict) -> AnaliseIA:
        try:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                d = json.loads(match.group())
                v = d.get('viralidade', {})
                c = d.get('concorrencia', {})

                return AnaliseIA(
                    aprovado=d.get('aprovado', False),
                    score=d.get('score', 0),
                    motivo=d.get('motivo', ''),
                    titulo_otimizado=d.get('titulo_ptbr', '')[:70],
                    descricao_seo=d.get('descricao_html', ''),
                    tags_sugeridas=d.get('tags', []),
                    preco_sugerido=d.get('preco_sugerido_brl', 0),
                    margem_estimada=d.get('margem_percentual', 0),
                    pontos_venda=d.get('pontos_venda', []),
                    publico_alvo=d.get('publico_alvo', ''),
                    viralidade=AnaliseViralidade(
                        score=v.get('score', 0),
                        potencial_tiktok=v.get('potencial_tiktok', 0),
                        potencial_instagram=v.get('potencial_instagram', 0),
                        hashtags_sugeridas=v.get('hashtags', []),
                        hooks_video=v.get('hooks', []),
                        tendencias_relacionadas=v.get('tendencias', [])
                    ),
                    concorrencia=AnaliseConcorrencia(
                        nivel_saturacao=c.get('nivel_saturacao', 'medio'),
                        estimativa_lojas=c.get('estimativa_lojas', 0),
                        diferencial_sugerido=c.get('diferencial_sugerido', ''),
                        risco_marca_registrada=c.get('risco_marca', False),
                        alertas=c.get('alertas', [])
                    ),
                    riscos=d.get('riscos', []),
                    modelo_usado=self.model,
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            logger.error(f"Parse error: {e}")
        return self._fallback(produto)

    def _fallback(self, produto: Dict) -> AnaliseIA:
        orders = produto.get('orders', 0)
        rating = produto.get('rating', 0)
        price = produto.get('price', 0)

        score = 0
        if orders >= 1000: score += 30
        elif orders >= 500: score += 20
        if rating >= 4.5: score += 25
        if 5 <= price <= 25: score += 20

        return AnaliseIA(
            aprovado=score >= 60,
            score=score,
            motivo="Análise automática",
            titulo_otimizado=produto.get('title', '')[:70],
            descricao_seo=f"<p>{produto.get('title', '')}</p>",
            tags_sugeridas=['acessorios'],
            preco_sugerido=round(price * 2.5 * 5.5, 2),
            margem_estimada=50,
            pontos_venda=[f'{orders} pedidos'],
            publico_alvo='Mulheres 18-45',
            viralidade=AnaliseViralidade(score=score),
            concorrencia=AnaliseConcorrencia(),
            riscos=['Revisar manualmente'],
            modelo_usado='fallback',
            timestamp=datetime.now().isoformat()
        )

