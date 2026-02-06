"""
Serviço de Coleções
Cria e gerencia coleções automáticas (smart collections) baseadas em tags
"""
import os
from typing import Dict, Any, List, Optional

try:
    from ..shopify.client import ShopifyClient
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shopify.client import ShopifyClient


class CollectionService:
    """Serviço para gerenciar coleções da loja"""

    def __init__(self):
        self.client = ShopifyClient()

    def create_tag_collection(self, title: str, tag: str, sort_order: str = "best-selling") -> Dict[str, Any]:
        """
        Cria coleção inteligente baseada em tag

        Args:
            title: Nome da coleção
            tag: Tag que os produtos devem ter
            sort_order: Ordenação (best-selling, created-desc, price-asc, etc)
        """
        data = {
            "title": title,
            "rules": [
                {
                    "column": "tag",
                    "relation": "equals",
                    "condition": tag
                }
            ],
            "sort_order": sort_order,
            "published": True
        }
        return self.client.create_smart_collection(data)

    def create_price_collection(
        self,
        title: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Cria coleção baseada em faixa de preço

        Args:
            title: Nome da coleção
            min_price: Preço mínimo (opcional)
            max_price: Preço máximo (opcional)
        """
        rules = []

        if min_price is not None:
            rules.append({
                "column": "variant_price",
                "relation": "greater_than",
                "condition": str(min_price)
            })

        if max_price is not None:
            rules.append({
                "column": "variant_price",
                "relation": "less_than",
                "condition": str(max_price)
            })

        if not rules:
            raise ValueError("Defina pelo menos min_price ou max_price")

        data = {
            "title": title,
            "rules": rules,
            "disjunctive": False,  # AND entre regras
            "sort_order": "best-selling",
            "published": True
        }
        return self.client.create_smart_collection(data)

    def create_vendor_collection(self, vendor: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Cria coleção por fornecedor/marca"""
        data = {
            "title": title or f"Produtos {vendor}",
            "rules": [
                {
                    "column": "vendor",
                    "relation": "equals",
                    "condition": vendor
                }
            ],
            "sort_order": "best-selling",
            "published": True
        }
        return self.client.create_smart_collection(data)

    def create_type_collection(self, product_type: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Cria coleção por tipo de produto"""
        data = {
            "title": title or product_type,
            "rules": [
                {
                    "column": "type",
                    "relation": "equals",
                    "condition": product_type
                }
            ],
            "sort_order": "best-selling",
            "published": True
        }
        return self.client.create_smart_collection(data)

    def setup_default_collections(self) -> List[Dict[str, Any]]:
        """
        Cria coleções padrão para a loja
        Retorna lista de resultados (sucesso/erro)
        """
        collections_config = [
            # Coleções por preço
            {"type": "tag", "title": "💰 Ofertas até R$50", "tag": "price:budget"},
            {"type": "tag", "title": "⭐ Produtos Premium", "tag": "price:premium"},

            # Coleções por status
            {"type": "tag", "title": "🆕 Novidades", "tag": "status:new"},
            {"type": "tag", "title": "🔥 Mais Vendidos", "tag": "best-seller"},
            {"type": "tag", "title": "🎁 Promoções", "tag": "promo"},

            # Coleções por faixa de preço
            {"type": "price", "title": "Até R$30", "max_price": 30},
            {"type": "price", "title": "R$30 - R$70", "min_price": 30, "max_price": 70},
            {"type": "price", "title": "Acima de R$70", "min_price": 70},
        ]

        results = []

        for config in collections_config:
            try:
                if config["type"] == "tag":
                    result = self.create_tag_collection(config["title"], config["tag"])
                elif config["type"] == "price":
                    result = self.create_price_collection(
                        config["title"],
                        config.get("min_price"),
                        config.get("max_price")
                    )
                else:
                    continue

                results.append({
                    "success": True,
                    "title": config["title"],
                    "id": result.get("smart_collection", {}).get("id")
                })
                print(f"✅ Criada: {config['title']}")

            except Exception as e:
                error_msg = str(e)
                # Ignora erro de coleção já existente
                if "already exists" in error_msg.lower() or "422" in error_msg:
                    results.append({
                        "success": True,
                        "title": config["title"],
                        "note": "Já existia"
                    })
                    print(f"⚠️  Já existe: {config['title']}")
                else:
                    results.append({
                        "success": False,
                        "title": config["title"],
                        "error": error_msg
                    })
                    print(f"❌ Erro: {config['title']} - {error_msg}")

        return results

    def list_collections(self) -> Dict[str, Any]:
        """Lista todas as coleções inteligentes"""
        return self.client.get_smart_collections()

    def delete_collection(self, collection_id: int) -> None:
        """Deleta uma coleção"""
        self.client.delete_smart_collection(collection_id)
        print(f"🗑️  Coleção {collection_id} deletada")

    def get_collections_summary(self) -> List[Dict[str, Any]]:
        """Retorna resumo das coleções existentes"""
        result = self.list_collections()
        collections = result.get("smart_collections", [])

        summary = []
        for col in collections:
            summary.append({
                "id": col["id"],
                "title": col["title"],
                "rules_count": len(col.get("rules", [])),
                "published": col.get("published_at") is not None
            })

        return summary


# Teste direto
if __name__ == "__main__":
    service = CollectionService()

    print("=== Coleções Existentes ===")
    summary = service.get_collections_summary()

    if summary:
        for col in summary:
            status = "✅" if col["published"] else "📝"
            print(f"{status} {col['title']} (ID: {col['id']})")
    else:
        print("Nenhuma coleção encontrada")

