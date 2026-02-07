#!/usr/bin/env python3
"""
🛍️ Processador de Produtos Shopify
Edita produtos já importados: títulos, descrições, preços, imagens, tags
"""
import sys
import os
import time
import logging
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ProdutoProcessado:
    """Dados do produto processado"""
    id: str
    titulo_original: str
    titulo_novo: str
    descricao_html: str
    preco_original: float
    preco_novo: float
    tags: List[str]
    colecao: str


class ShopifyProductProcessor:
    """Processa produtos na Shopify: edita títulos, descrições, preços, etc"""

    def __init__(self):
        self.store_url = os.getenv("SHOPIFY_STORE_URL")
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = os.getenv("SHOPIFY_API_VERSION", "2024-01")

        if not self.store_url or not self.access_token:
            raise ValueError("SHOPIFY_STORE_URL e SHOPIFY_ACCESS_TOKEN são obrigatórios no .env")

        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        # IA para gerar conteúdo (tenta OpenAI/DeepSeek primeiro, depois Gemini)
        self.ai_client = None
        self.ai_type = None

        # Tenta OpenAI/DeepSeek
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                self.ai_client = openai.OpenAI(api_key=openai_key)
                self.ai_type = "openai"
                logger.info("✅ OpenAI inicializado para geração de conteúdo")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao inicializar OpenAI: {e}")

        # Fallback: Google Gemini
        if not self.ai_client:
            google_key = os.getenv("GOOGLE_API_KEY")
            if google_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=google_key)
                    self.ai_client = genai.GenerativeModel('gemini-pro')
                    self.ai_type = "gemini"
                    logger.info("✅ Google Gemini inicializado para geração de conteúdo")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao inicializar Gemini: {e}")

        if not self.ai_client:
            logger.warning("⚠️ Nenhuma API de IA disponível - usando templates básicos")

        # Configurações de preço
        self.markup = float(os.getenv("DEFAULT_MARKUP", "2.5"))
        self.taxa_cambio = 5.5  # USD para BRL

        logger.info(f"✅ Shopify conectada: {self.store_url}")

    def get_all_products(self) -> List[Dict]:
        """Busca todos os produtos da loja"""
        produtos = []
        url = f"{self.base_url}/products.json?limit=250"

        while url:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                produtos.extend(data.get("products", []))

                # Paginação
                link_header = response.headers.get("Link", "")
                if 'rel="next"' in link_header:
                    match = re.search(r'<([^>]+)>; rel="next"', link_header)
                    url = match.group(1) if match else None
                else:
                    url = None
            else:
                logger.error(f"Erro ao buscar produtos: {response.status_code}")
                break

        return produtos

    def get_product(self, product_id: str) -> Optional[Dict]:
        """Busca um produto específico"""
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json().get("product")
        return None

    def update_product(self, product_id: str, data: Dict) -> bool:
        """Atualiza um produto"""
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.put(url, headers=self.headers, json={"product": data})

        if response.status_code == 200:
            return True
        else:
            logger.error(f"Erro ao atualizar produto {product_id}: {response.text}")
            return False

    def gerar_titulo_otimizado(self, titulo_original: str, categoria: str = "") -> str:
        """Gera título otimizado em português"""
        if self.claude:
            prompt = f"""Crie um título de produto para e-commerce brasileiro.

TÍTULO ORIGINAL (em inglês): {titulo_original}
CATEGORIA: {categoria or "acessórios femininos"}

REGRAS:
- Máximo 70 caracteres
- Em português brasileiro
- Sem marca registrada
- Atrativo e descritivo
- Pode usar emojis no início (1 apenas)

RESPONDA APENAS com o título, nada mais."""

            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text.strip()[:70]
            except Exception as e:
                logger.error(f"Erro Claude: {e}")

        # Fallback: tradução básica
        return self._traduzir_titulo_basico(titulo_original)

    def _traduzir_titulo_basico(self, titulo: str) -> str:
        """Tradução básica de título"""
        traducoes = {
            "earrings": "Brincos",
            "necklace": "Colar",
            "bracelet": "Pulseira",
            "ring": "Anel",
            "watch": "Relógio",
            "bag": "Bolsa",
            "sunglasses": "Óculos de Sol",
            "jewelry": "Joia",
            "women": "Feminino",
            "fashion": "Fashion",
            "elegant": "Elegante",
            "vintage": "Vintage",
            "gold": "Dourado",
            "silver": "Prateado",
            "crystal": "Cristal",
            "pearl": "Pérola",
        }

        resultado = titulo
        for en, pt in traducoes.items():
            resultado = re.sub(en, pt, resultado, flags=re.IGNORECASE)

        return resultado[:70]

    def gerar_descricao_html(self, produto: Dict) -> str:
        """Gera descrição HTML persuasiva"""
        titulo = produto.get("title", "Produto")

        if self.claude:
            prompt = f"""Crie uma descrição de produto para e-commerce brasileiro.

PRODUTO: {titulo}

ESTRUTURA OBRIGATÓRIA (use HTML):
1. <h3> com título atrativo e emoji
2. <p> com descrição persuasiva (2-3 frases)
3. <h4>🎁 Por que você vai amar:</h4> seguido de <ul> com 4 benefícios
4. <h4>📦 Especificações:</h4> seguido de <ul> com detalhes
5. <p> com garantias: frete grátis, compra segura, 7 dias troca

Use emojis ✨🎁💎✅🚚🔒

RESPONDA APENAS com o HTML, sem explicações."""

            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text.strip()
            except Exception as e:
                logger.error(f"Erro Claude: {e}")

        # Fallback: template básico
        return self._template_descricao(titulo)

    def _template_descricao(self, titulo: str) -> str:
        """Template básico de descrição"""
        return f"""
<h3>✨ {titulo}</h3>

<p>Peça exclusiva selecionada especialmente para você! Design moderno e elegante que combina com qualquer ocasião.</p>

<h4>🎁 Por que você vai amar:</h4>
<ul>
<li>✅ Material de alta qualidade</li>
<li>✅ Acabamento premium</li>
<li>✅ Design exclusivo e elegante</li>
<li>✅ Perfeito para presente</li>
</ul>

<h4>📦 Especificações:</h4>
<ul>
<li>Material: Liga metálica de alta qualidade</li>
<li>Acabamento: Polido</li>
<li>Estilo: Fashion/Casual</li>
</ul>

<p><strong>🚚 Frete Grátis</strong> para todo Brasil!</p>
<p><strong>🔒 Compra 100% Segura</strong></p>
<p><strong>↩️ 7 dias</strong> para troca ou devolução</p>
"""

    def calcular_preco(self, preco_original: float) -> float:
        """Calcula preço de venda com markup"""
        # Converte para BRL se necessário
        if preco_original < 50:  # Provavelmente em USD
            preco_brl = preco_original * self.taxa_cambio
        else:
            preco_brl = preco_original

        # Aplica markup
        preco_final = preco_brl * self.markup

        # Arredondamento psicológico
        if preco_final < 50:
            preco_final = round(preco_final / 5) * 5 - 0.10
        elif preco_final < 100:
            preco_final = round(preco_final / 10) * 10 - 0.10
        else:
            preco_final = round(preco_final / 10) * 10 - 0.10

        return max(preco_final, 29.90)

    def detectar_categoria(self, titulo: str) -> str:
        """Detecta categoria pelo título"""
        titulo_lower = titulo.lower()

        categorias = {
            "brincos": ["earring", "brinco", "ear"],
            "colares": ["necklace", "colar", "pendant", "chain"],
            "pulseiras": ["bracelet", "pulseira", "bangle"],
            "aneis": ["ring", "anel"],
            "relogios": ["watch", "relógio", "relogio"],
            "oculos": ["sunglasses", "glasses", "óculos", "oculos"],
            "bolsas": ["bag", "bolsa", "purse", "handbag"],
        }

        for categoria, keywords in categorias.items():
            for kw in keywords:
                if kw in titulo_lower:
                    return categoria

        return "acessorios"

    def gerar_tags(self, titulo: str, categoria: str) -> List[str]:
        """Gera tags para o produto"""
        tags = [categoria, "feminino", "acessorios", "moda"]

        # Tags baseadas no título
        titulo_lower = titulo.lower()

        if any(x in titulo_lower for x in ["gold", "dourad", "ouro"]):
            tags.append("dourado")
        if any(x in titulo_lower for x in ["silver", "prata", "prateado"]):
            tags.append("prateado")
        if any(x in titulo_lower for x in ["crystal", "cristal"]):
            tags.append("cristal")
        if any(x in titulo_lower for x in ["pearl", "perola", "pérola"]):
            tags.append("perola")
        if any(x in titulo_lower for x in ["vintage", "retro"]):
            tags.append("vintage")
        if any(x in titulo_lower for x in ["elegant", "elegante"]):
            tags.append("elegante")

        return list(set(tags))

    def processar_produto(self, produto: Dict) -> Optional[ProdutoProcessado]:
        """Processa um produto: gera novo título, descrição, preço, tags"""
        product_id = produto.get("id")
        titulo_original = produto.get("title", "")

        # Pega preço da primeira variante
        variants = produto.get("variants", [])
        preco_original = float(variants[0].get("price", 0)) if variants else 0

        print(f"\n📦 Processando: {titulo_original[:50]}...")

        # Detecta categoria
        categoria = self.detectar_categoria(titulo_original)
        print(f"   📁 Categoria: {categoria}")

        # Gera novo título
        print(f"   ✏️ Gerando título...")
        titulo_novo = self.gerar_titulo_otimizado(titulo_original, categoria)
        print(f"   📝 Novo título: {titulo_novo}")

        # Gera descrição
        print(f"   📄 Gerando descrição...")
        descricao = self.gerar_descricao_html(produto)

        # Calcula preço
        preco_novo = self.calcular_preco(preco_original)
        print(f"   💰 Preço: R$ {preco_original:.2f} → R$ {preco_novo:.2f}")

        # Gera tags
        tags = self.gerar_tags(titulo_original, categoria)
        print(f"   🏷️ Tags: {', '.join(tags)}")

        return ProdutoProcessado(
            id=str(product_id),
            titulo_original=titulo_original,
            titulo_novo=titulo_novo,
            descricao_html=descricao,
            preco_original=preco_original,
            preco_novo=preco_novo,
            tags=tags,
            colecao=categoria
        )

    def aplicar_alteracoes(self, processado: ProdutoProcessado) -> bool:
        """Aplica alterações ao produto na Shopify"""
        print(f"   🔄 Aplicando alterações...")

        # Dados para atualização
        update_data = {
            "title": processado.titulo_novo,
            "body_html": processado.descricao_html,
            "tags": ", ".join(processado.tags),
            "vendor": "TWP Acessórios",
            "product_type": processado.colecao.capitalize(),
        }

        # Atualiza produto
        if self.update_product(processado.id, update_data):
            # Atualiza preço das variantes
            produto = self.get_product(processado.id)
            if produto:
                for variant in produto.get("variants", []):
                    variant_id = variant.get("id")
                    self._update_variant_price(processado.id, variant_id, processado.preco_novo)

            print(f"   ✅ Produto atualizado!")
            return True
        else:
            print(f"   ❌ Erro ao atualizar")
            return False

    def _update_variant_price(self, product_id: str, variant_id: str, price: float):
        """Atualiza preço de uma variante"""
        url = f"{self.base_url}/variants/{variant_id}.json"
        data = {
            "variant": {
                "id": variant_id,
                "price": f"{price:.2f}",
                "compare_at_price": f"{price * 1.3:.2f}"  # Preço "de" 30% maior
            }
        }
        requests.put(url, headers=self.headers, json=data)

    def processar_todos_produtos(self, apenas_novos: bool = True):
        """Processa todos os produtos da loja"""
        print("\n" + "="*60)
        print("🛍️ PROCESSANDO PRODUTOS DA SHOPIFY")
        print("="*60)

        produtos = self.get_all_products()
        print(f"\n📦 Total de produtos: {len(produtos)}")

        if not produtos:
            print("⚠️ Nenhum produto encontrado")
            return

        processados = 0
        erros = 0

        for produto in produtos:
            # Pula produtos já processados (verificar por tag ou vendor)
            if apenas_novos:
                tags = produto.get("tags", "")
                vendor = produto.get("vendor", "")
                if "processado" in tags.lower() or vendor == "TWP Acessórios":
                    continue

            try:
                resultado = self.processar_produto(produto)
                if resultado:
                    if self.aplicar_alteracoes(resultado):
                        processados += 1
                    else:
                        erros += 1

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"Erro ao processar produto: {e}")
                erros += 1

        print("\n" + "="*60)
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"   📦 Processados: {processados}")
        print(f"   ❌ Erros: {erros}")
        print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Processador de Produtos Shopify")
    parser.add_argument("--todos", "-t", action="store_true", help="Processa todos (inclusive já processados)")
    parser.add_argument("--produto", "-p", type=str, help="ID de produto específico")
    parser.add_argument("--listar", "-l", action="store_true", help="Apenas listar produtos")

    args = parser.parse_args()

    processor = ShopifyProductProcessor()

    if args.listar:
        produtos = processor.get_all_products()
        print(f"\n📦 {len(produtos)} produtos na loja:\n")
        for p in produtos:
            print(f"  [{p['id']}] {p['title'][:50]}...")

    elif args.produto:
        produto = processor.get_product(args.produto)
        if produto:
            resultado = processor.processar_produto(produto)
            if resultado:
                processor.aplicar_alteracoes(resultado)
        else:
            print(f"❌ Produto {args.produto} não encontrado")

    else:
        processor.processar_todos_produtos(apenas_novos=not args.todos)


if __name__ == "__main__":
    main()


