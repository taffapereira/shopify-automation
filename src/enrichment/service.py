"""
Serviço de Enriquecimento de Produtos
Adiciona tags, SEO, calcula preços e padroniza produtos importados via DSers
"""
import re
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Importação relativa para quando usado como módulo
try:
    from ..shopify.client import ShopifyClient
except ImportError:
    # Importação absoluta para testes diretos
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shopify.client import ShopifyClient

load_dotenv()


class EnrichmentService:
    """Serviço para enriquecer produtos após importação do DSers"""

    def __init__(self):
        self.client = ShopifyClient()
        self.default_markup = float(os.getenv("DEFAULT_MARKUP", 2.5))
        self.default_shipping = float(os.getenv("DEFAULT_SHIPPING_COST", 5.0))

        # Tabela de markup por faixa de custo
        self.markup_table = [
            (5, 4.5),      # custo até $5 = 4.5x
            (15, 3.5),     # custo até $15 = 3.5x
            (30, 2.75),    # custo até $30 = 2.75x
            (50, 2.25),    # custo até $50 = 2.25x
            (float('inf'), 1.9)  # acima = 1.9x
        ]

    def calculate_price(self, cost: float, shipping: float = None) -> float:
        """
        Calcula preço de venda baseado no custo
        Fórmula: (custo + frete) × markup + arredondamento
        """
        if shipping is None:
            shipping = self.default_shipping

        total_cost = cost + shipping

        # Encontra markup adequado
        for threshold, markup in self.markup_table:
            if total_cost <= threshold:
                price = total_cost * markup
                return self._round_price(price)

        return self._round_price(total_cost * 1.9)

    def _round_price(self, price: float) -> float:
        """Arredonda preço para valor psicológico"""
        if price < 20:
            return round(price) - 0.01  # Ex: 14.99
        elif price < 50:
            return (round(price / 5) * 5) - 0.10  # Ex: 34.90
        elif price < 100:
            return (round(price / 10) * 10) - 0.10  # Ex: 79.90
        else:
            return (round(price / 10) * 10) - 0.10  # Ex: 149.90

    def generate_tags(self, product: dict) -> List[str]:
        """Gera tags padronizadas para o produto"""
        tags = []
        title = product.get("title", "").lower()
        vendor = product.get("vendor", "")
        product_type = product.get("product_type", "")

        # Tag de marca/vendor
        if vendor:
            clean_vendor = vendor.lower().replace(" ", "-").replace(".", "")
            tags.append(f"brand:{clean_vendor}")

        # Tag de categoria
        if product_type:
            clean_type = product_type.lower().replace(" ", "-")
            tags.append(f"cat:{clean_type}")

        # Tags de preço
        variants = product.get("variants", [])
        if variants:
            try:
                price = float(variants[0].get("price", 0))
                if price < 25:
                    tags.append("price:budget")
                elif price < 50:
                    tags.append("price:mid")
                elif price < 100:
                    tags.append("price:premium")
                else:
                    tags.append("price:luxury")
            except (ValueError, TypeError):
                pass

        # Tag de origem
        tags.append("source:dsers")

        # Tag de status (para revisão)
        tags.append("status:needs-review")

        return tags

    def generate_seo_title(self, title: str, max_length: int = 70) -> str:
        """Gera título SEO otimizado"""
        # Remove caracteres especiais excessivos
        clean = re.sub(r'\s+', ' ', title).strip()
        clean = re.sub(r'[^\w\s\-\,\.\&]', '', clean)

        if len(clean) <= max_length:
            return clean

        # Corta no último espaço antes do limite
        truncated = clean[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length // 2:
            truncated = truncated[:last_space]

        return truncated + "..."

    def generate_seo_description(self, product: dict, max_length: int = 160) -> str:
        """Gera meta description SEO"""
        title = product.get("title", "")
        product_type = product.get("product_type", "produto")

        # Template básico
        description = f"Compre {title}. {product_type.capitalize()} de alta qualidade com entrega garantida. Satisfação garantida ou seu dinheiro de volta!"

        return description[:max_length]

    def enrich_product(self, product_id: int, cost: Optional[float] = None, shipping: float = None) -> Dict[str, Any]:
        """
        Enriquece um produto com tags, SEO e preço

        Args:
            product_id: ID do produto na Shopify
            cost: Custo do produto (para cálculo de preço)
            shipping: Custo de frete estimado
        """
        # Busca produto atual
        result = self.client.get_product(product_id)
        product = result.get("product", {})

        if not product:
            raise ValueError(f"Produto {product_id} não encontrado")

        update_data = {}

        # === TAGS ===
        existing_tags = product.get("tags", "").split(", ") if product.get("tags") else []
        new_tags = self.generate_tags(product)
        all_tags = list(set([t for t in existing_tags if t] + new_tags))
        update_data["tags"] = ", ".join(all_tags)

        # === SEO ===
        update_data["metafields_global_title_tag"] = self.generate_seo_title(product.get("title", ""))
        update_data["metafields_global_description_tag"] = self.generate_seo_description(product)

        # === PREÇO (se custo fornecido) ===
        if cost is not None:
            new_price = self.calculate_price(cost, shipping or self.default_shipping)
            variants = product.get("variants", [])
            if variants:
                update_data["variants"] = [
                    {"id": v["id"], "price": str(new_price)} for v in variants
                ]
                print(f"   💰 Preço calculado: ${new_price:.2f} (custo: ${cost}, markup aplicado)")

        # Atualiza produto
        result = self.client.update_product(product_id, update_data)

        return result

    def enrich_all_new_products(self) -> List[Dict[str, Any]]:
        """Enriquece todos os produtos marcados como 'needs-review'"""
        products = self.client.get_products(limit=250)
        results = []

        for product in products.get("products", []):
            tags = product.get("tags", "")

            # Pula produtos já processados
            if "status:processed" in tags:
                continue

            # Processa produtos novos ou que precisam revisão
            if not tags or "source:dsers" not in tags or "status:needs-review" in tags:
                try:
                    print(f"🔄 Enriquecendo: {product['title'][:50]}...")
                    self.enrich_product(product["id"])

                    # Marca como processado
                    self._mark_as_processed(product["id"])

                    results.append({
                        "id": product["id"],
                        "title": product["title"],
                        "status": "success"
                    })
                    print(f"   ✅ Concluído!")
                except Exception as e:
                    results.append({
                        "id": product["id"],
                        "title": product["title"],
                        "status": "error",
                        "error": str(e)
                    })
                    print(f"   ❌ Erro: {e}")

        return results

    def _mark_as_processed(self, product_id: int):
        """Marca produto como processado (remove needs-review, adiciona processed)"""
        result = self.client.get_product(product_id)
        product = result.get("product", {})

        tags = product.get("tags", "").split(", ")
        tags = [t for t in tags if t and t != "status:needs-review"]
        tags.append("status:processed")

        self.client.update_product(product_id, {"tags": ", ".join(tags)})


# Teste direto
if __name__ == "__main__":
    service = EnrichmentService()

    # Teste de cálculo de preço
    print("=== Teste de Precificação ===")
    test_costs = [3, 8, 15, 25, 40, 60]
    for cost in test_costs:
        price = service.calculate_price(cost, 5)
        margin = ((price - cost - 5) / price) * 100
        print(f"Custo: ${cost} + $5 frete → Preço: ${price:.2f} (margem: {margin:.1f}%)")

