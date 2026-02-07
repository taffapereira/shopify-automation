#!/usr/bin/env python3
"""
🛍️ Processador de Produtos Shopify v2
Usa Google Gemini para gerar títulos e descrições profissionais
"""
import sys
import os
import time
import logging
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class ShopifyProcessor:
    """Processa produtos na Shopify usando Google Gemini"""

    # Traduções de categorias
    CATEGORIAS = {
        "earring": "brincos", "brinco": "brincos",
        "necklace": "colares", "colar": "colares", "pendant": "colares",
        "bracelet": "pulseiras", "pulseira": "pulseiras", "bangle": "pulseiras",
        "ring": "aneis", "anel": "aneis",
        "watch": "relogios", "relógio": "relogios",
        "sunglasses": "oculos", "glasses": "oculos", "óculos": "oculos",
        "bag": "bolsas", "handbag": "bolsas", "purse": "bolsas", "tote": "bolsas",
        "wallet": "carteiras", "card holder": "carteiras",
    }

    def __init__(self):
        self.store_url = os.getenv("SHOPIFY_STORE_URL")
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = os.getenv("SHOPIFY_API_VERSION", "2024-01")

        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        # Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=google_key)
        self.gemini = genai.GenerativeModel('gemini-pro')
        logger.info("✅ Google Gemini inicializado")

        # Configurações
        self.markup = float(os.getenv("DEFAULT_MARKUP", "2.5"))
        self.taxa_cambio = 5.5

        logger.info(f"✅ Shopify: {self.store_url}")

    def get_products(self, limit=250) -> List[Dict]:
        """Busca produtos"""
        produtos = []
        url = f"{self.base_url}/products.json?limit={limit}"

        while url:
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                produtos.extend(data.get("products", []))

                link = r.headers.get("Link", "")
                if 'rel="next"' in link:
                    match = re.search(r'<([^>]+)>; rel="next"', link)
                    url = match.group(1) if match else None
                else:
                    url = None
            else:
                break

        return produtos

    def update_product(self, product_id: str, data: Dict) -> bool:
        """Atualiza produto"""
        url = f"{self.base_url}/products/{product_id}.json"
        r = requests.put(url, headers=self.headers, json={"product": data})
        return r.status_code == 200

    def update_variant(self, variant_id: str, price: float, compare_price: float) -> bool:
        """Atualiza variante"""
        url = f"{self.base_url}/variants/{variant_id}.json"
        data = {
            "variant": {
                "id": variant_id,
                "price": f"{price:.2f}",
                "compare_at_price": f"{compare_price:.2f}"
            }
        }
        r = requests.put(url, headers=self.headers, json=data)
        return r.status_code == 200

    def detectar_categoria(self, titulo: str) -> str:
        """Detecta categoria pelo título"""
        titulo_lower = titulo.lower()
        for keyword, cat in self.CATEGORIAS.items():
            if keyword in titulo_lower:
                return cat
        return "acessorios"

    def gerar_titulo_gemini(self, titulo_original: str, categoria: str) -> str:
        """Gera título otimizado com Gemini"""
        prompt = f"""Traduza e otimize este título de produto para uma loja brasileira de acessórios femininos.

TÍTULO ORIGINAL: {titulo_original}
CATEGORIA: {categoria}

REGRAS OBRIGATÓRIAS:
1. Máximo 65 caracteres
2. Em português brasileiro fluente
3. Remova códigos, números de modelo e marcas desconhecidas
4. Comece com emoji relacionado (💎 joias, 👜 bolsas, ⌚ relógios, 👓 óculos, 💍 anéis, 📿 colares, etc)
5. Seja descritivo e atraente
6. Use palavras como: Elegante, Luxo, Fashion, Delicado, Sofisticado

EXEMPLOS:
- "Yhpup 316L Stainless Steel Pearl Double Layer Cuff..." → "💎 Bracelete Duplo com Pérolas Aço Inox Elegante"
- "Designer Handbag High end Genuine Leather Large..." → "👜 Bolsa Grande Couro Legítimo Luxo Feminina"
- "Xuping Jewelry Fashion Crystal Pendant Necklace..." → "📿 Colar Pingente Cristal Fashion Delicado"

RESPONDA APENAS COM O NOVO TÍTULO, nada mais."""

        try:
            response = self.gemini.generate_content(prompt)
            titulo = response.text.strip()
            # Remove aspas se houver
            titulo = titulo.strip('"\'')
            return titulo[:65]
        except Exception as e:
            logger.error(f"Erro Gemini título: {e}")
            return self._titulo_fallback(titulo_original, categoria)

    def _titulo_fallback(self, titulo: str, categoria: str) -> str:
        """Fallback para título sem IA"""
        emojis = {
            "brincos": "✨", "colares": "📿", "pulseiras": "💎",
            "aneis": "💍", "relogios": "⌚", "oculos": "👓",
            "bolsas": "👜", "carteiras": "👛", "acessorios": "🎀"
        }
        emoji = emojis.get(categoria, "✨")

        # Remove marcas e códigos
        titulo = re.sub(r'\b[A-Z]{2,}[a-z]*\b', '', titulo)  # Remove marcas tipo Yhpup
        titulo = re.sub(r'\b\d+\w*\b', '', titulo)  # Remove códigos
        titulo = re.sub(r'\s+', ' ', titulo).strip()

        cat_pt = categoria.replace("aneis", "Anel").replace("brincos", "Brinco").replace("colares", "Colar")
        cat_pt = cat_pt.replace("pulseiras", "Pulseira").replace("bolsas", "Bolsa").replace("relogios", "Relógio")

        return f"{emoji} {cat_pt} {titulo[:45]}".strip()[:65]

    def gerar_descricao_gemini(self, titulo: str, categoria: str) -> str:
        """Gera descrição HTML com Gemini"""
        prompt = f"""Crie uma descrição de produto para e-commerce brasileiro.

PRODUTO: {titulo}
CATEGORIA: {categoria}

ESTRUTURA HTML OBRIGATÓRIA:
<h3>✨ [Título Atrativo]</h3>
<p>[2-3 frases persuasivas sobre o produto]</p>

<h4>🎁 Por que você vai amar:</h4>
<ul>
<li>✅ [Benefício 1]</li>
<li>✅ [Benefício 2]</li>
<li>✅ [Benefício 3]</li>
<li>✅ [Benefício 4]</li>
</ul>

<h4>📦 Detalhes:</h4>
<ul>
<li>Material: [material apropriado]</li>
<li>Estilo: Fashion/Elegante</li>
<li>Ocasião: Casual/Festa/Trabalho</li>
</ul>

<p>🚚 <strong>Frete Grátis</strong> para todo Brasil!</p>
<p>🔒 <strong>Compra 100% Segura</strong></p>
<p>↩️ <strong>7 dias</strong> para troca ou devolução</p>

RESPONDA APENAS COM O HTML."""

        try:
            response = self.gemini.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erro Gemini descrição: {e}")
            return self._descricao_fallback(titulo)

    def _descricao_fallback(self, titulo: str) -> str:
        """Descrição padrão"""
        return f"""
<h3>✨ {titulo}</h3>
<p>Peça exclusiva para mulheres que valorizam estilo e elegância. Design moderno que combina com qualquer ocasião!</p>

<h4>🎁 Por que você vai amar:</h4>
<ul>
<li>✅ Material de alta qualidade</li>
<li>✅ Acabamento premium</li>
<li>✅ Design exclusivo</li>
<li>✅ Perfeito para presente</li>
</ul>

<h4>📦 Detalhes:</h4>
<ul>
<li>Material: Alta qualidade</li>
<li>Estilo: Fashion/Elegante</li>
<li>Ocasião: Versátil</li>
</ul>

<p>🚚 <strong>Frete Grátis</strong> para todo Brasil!</p>
<p>🔒 <strong>Compra 100% Segura</strong></p>
<p>↩️ <strong>7 dias</strong> para troca ou devolução</p>
"""

    def calcular_preco(self, preco_original: float) -> tuple:
        """Calcula preço de venda e compare_at_price"""
        if preco_original < 100:  # Provavelmente em USD
            preco_brl = preco_original * self.taxa_cambio
        else:
            preco_brl = preco_original

        preco_venda = preco_brl * self.markup

        # Arredondamento psicológico
        if preco_venda < 50:
            preco_venda = round(preco_venda / 5) * 5 - 0.10
        elif preco_venda < 200:
            preco_venda = round(preco_venda / 10) * 10 - 0.10
        else:
            preco_venda = round(preco_venda / 50) * 50 - 0.10

        preco_venda = max(preco_venda, 29.90)
        preco_comparacao = round(preco_venda * 1.4, -1) - 0.10  # "De" 40% maior

        return preco_venda, preco_comparacao

    def gerar_tags(self, titulo: str, categoria: str) -> str:
        """Gera tags"""
        tags = [categoria, "feminino", "acessorios", "moda", "twp"]

        titulo_lower = titulo.lower()
        if any(x in titulo_lower for x in ["gold", "dourad", "ouro", "18k"]):
            tags.append("dourado")
        if any(x in titulo_lower for x in ["silver", "prata", "prateado"]):
            tags.append("prata")
        if any(x in titulo_lower for x in ["crystal", "cristal", "zirconia"]):
            tags.append("cristal")
        if any(x in titulo_lower for x in ["pearl", "perola", "pérola"]):
            tags.append("perola")
        if any(x in titulo_lower for x in ["leather", "couro"]):
            tags.append("couro")
        if any(x in titulo_lower for x in ["steel", "aço", "inox"]):
            tags.append("aco-inox")

        return ", ".join(list(set(tags)))

    def processar_produto(self, produto: Dict) -> bool:
        """Processa um produto completo"""
        pid = produto["id"]
        titulo_original = produto.get("title", "")

        print(f"\n📦 [{pid}] {titulo_original[:50]}...")

        # Categoria
        categoria = self.detectar_categoria(titulo_original)
        print(f"   📁 {categoria}")

        # Título
        print(f"   ✏️ Gerando título...")
        novo_titulo = self.gerar_titulo_gemini(titulo_original, categoria)
        print(f"   📝 {novo_titulo}")

        # Descrição
        print(f"   📄 Gerando descrição...")
        descricao = self.gerar_descricao_gemini(novo_titulo, categoria)

        # Preço
        variants = produto.get("variants", [])
        preco_original = float(variants[0].get("price", 0)) if variants else 0
        preco_venda, preco_comp = self.calcular_preco(preco_original)
        print(f"   💰 R$ {preco_original:.2f} → R$ {preco_venda:.2f} (de R$ {preco_comp:.2f})")

        # Tags
        tags = self.gerar_tags(titulo_original, categoria)
        print(f"   🏷️ {tags}")

        # Atualiza produto
        update_data = {
            "title": novo_titulo,
            "body_html": descricao,
            "tags": tags,
            "vendor": "TWP Acessórios",
            "product_type": categoria.capitalize(),
        }

        if self.update_product(pid, update_data):
            # Atualiza preços das variantes
            for v in variants:
                self.update_variant(v["id"], preco_venda, preco_comp)

            print(f"   ✅ Atualizado!")
            return True
        else:
            print(f"   ❌ Erro ao atualizar")
            return False

    def processar_todos(self, limite: int = None):
        """Processa todos os produtos"""
        print("\n" + "="*60)
        print("🛍️ PROCESSANDO PRODUTOS - TWP ACESSÓRIOS")
        print("="*60)

        produtos = self.get_products()
        total = len(produtos)

        if limite:
            produtos = produtos[:limite]

        print(f"\n📦 Total: {total} | Processando: {len(produtos)}")

        ok = 0
        erro = 0

        for i, p in enumerate(produtos, 1):
            print(f"\n[{i}/{len(produtos)}]", end="")
            try:
                if self.processar_produto(p):
                    ok += 1
                else:
                    erro += 1
                time.sleep(1)  # Rate limit
            except Exception as e:
                logger.error(f"Erro: {e}")
                erro += 1

        print("\n" + "="*60)
        print(f"✅ CONCLUÍDO: {ok} atualizados | {erro} erros")
        print("="*60)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", "-l", type=int, help="Limite de produtos")
    parser.add_argument("--listar", action="store_true", help="Apenas listar")
    args = parser.parse_args()

    proc = ShopifyProcessor()

    if args.listar:
        produtos = proc.get_products()
        print(f"\n📦 {len(produtos)} produtos:\n")
        for p in produtos[:20]:
            print(f"  [{p['id']}] {p['title'][:60]}...")
        if len(produtos) > 20:
            print(f"  ... e mais {len(produtos)-20}")
    else:
        proc.processar_todos(args.limite)


if __name__ == "__main__":
    main()


