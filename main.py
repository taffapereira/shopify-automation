#!/usr/bin/env python3
"""
🤖 Bot Drop - Automação Shopify
Sistema de automação para dropshipping com DSers + Shopify

Comandos:
    python main.py test         - Testa conexão com a loja
    python main.py health       - Gera relatório de saúde
    python main.py collections  - Cria coleções padrão
    python main.py enrich       - Enriquece produtos (tags, SEO)
    python main.py enrich --product-id 123 --cost 10  - Enriquece produto específico
    python main.py stats        - Mostra estatísticas rápidas
"""
import argparse
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.shopify.client import ShopifyClient
from src.enrichment.service import EnrichmentService
from src.collections.service import CollectionService
from src.health.checker import HealthChecker


def cmd_test():
    """Testa conexão com a loja"""
    print("🔌 Testando conexão com Shopify...\n")

    client = ShopifyClient()

    try:
        shop = client.get_shop()
        shop_info = shop.get("shop", {})

        print("✅ Conexão OK!\n")
        print(f"🏪 Loja: {shop_info.get('name')}")
        print(f"📧 Email: {shop_info.get('email')}")
        print(f"🌐 Domínio: {shop_info.get('domain')}")
        print(f"💱 Moeda: {shop_info.get('currency')}")
        print(f"🌍 País: {shop_info.get('country_name')}")

        # Conta produtos
        product_count = client.get_product_count()
        print(f"\n📦 Total de produtos: {product_count}")

        # Mostra alguns produtos
        if product_count > 0:
            products = client.get_products(limit=3)
            print("\n📋 Últimos produtos:")
            for p in products.get("products", []):
                print(f"   - {p['title'][:50]}")

        return True

    except Exception as e:
        print(f"❌ Falha na conexão: {e}")
        return False


def cmd_health():
    """Gera relatório de saúde"""
    print("🏥 Gerando relatório de saúde...\n")

    checker = HealthChecker()
    report = checker.generate_report(save_to_file=True)

    print(report)


def cmd_collections():
    """Cria coleções padrão"""
    print("📁 Criando coleções automáticas...\n")

    service = CollectionService()

    # Mostra coleções existentes
    print("=== Coleções existentes ===")
    existing = service.get_collections_summary()
    if existing:
        for col in existing:
            print(f"   ✓ {col['title']}")
    else:
        print("   Nenhuma coleção encontrada")

    print("\n=== Criando coleções padrão ===")
    results = service.setup_default_collections()

    print(f"\n✅ Processo concluído!")
    success = sum(1 for r in results if r["success"])
    print(f"   {success}/{len(results)} coleções criadas/existentes")


def cmd_enrich(product_id=None, cost=None, shipping=0):
    """Enriquece produtos"""
    service = EnrichmentService()

    if product_id:
        print(f"🔄 Enriquecendo produto {product_id}...\n")
        try:
            result = service.enrich_product(product_id, cost, shipping)
            print(f"✅ Produto enriquecido com sucesso!")

            # Mostra detalhes
            product = result.get("product", {})
            print(f"\n📦 {product.get('title')}")
            print(f"🏷️  Tags: {product.get('tags')}")

            variants = product.get("variants", [])
            if variants:
                print(f"💰 Preço: ${variants[0].get('price')}")

        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print("🔄 Enriquecendo todos os produtos novos...\n")
        results = service.enrich_all_new_products()

        success = sum(1 for r in results if r["status"] == "success")
        print(f"\n✅ Processo concluído!")
        print(f"   {success}/{len(results)} produtos enriquecidos")


def cmd_stats():
    """Mostra estatísticas rápidas"""
    print("📊 Estatísticas da Loja\n")

    checker = HealthChecker()
    stats = checker.get_quick_stats()

    if stats["status"] == "online":
        print(f"🏪 Loja: {stats['shop_name']}")
        print(f"📧 Email: {stats['shop_email']}")
        print(f"📦 Produtos: {stats['total_products']}")

        if stats.get("recent_products"):
            print(f"\n📋 Produtos recentes:")
            for title in stats["recent_products"]:
                print(f"   - {title[:50]}")
    else:
        print(f"❌ Erro: {stats['error']}")


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Bot Drop - Automação Shopify",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py test                              Testa conexão
  python main.py health                            Relatório de saúde
  python main.py collections                       Cria coleções
  python main.py enrich                            Enriquece todos os produtos
  python main.py enrich --product-id 123 --cost 10 Enriquece produto específico
  python main.py stats                             Estatísticas rápidas
        """
    )

    parser.add_argument(
        "command",
        choices=["test", "health", "collections", "enrich", "stats"],
        help="Comando a executar"
    )
    parser.add_argument(
        "--product-id",
        type=int,
        help="ID do produto (para enrich)"
    )
    parser.add_argument(
        "--cost",
        type=float,
        help="Custo do produto em USD (para cálculo de preço)"
    )
    parser.add_argument(
        "--shipping",
        type=float,
        default=0,
        help="Custo de frete em USD (padrão: 0)"
    )

    args = parser.parse_args()

    print("\n" + "="*50)
    print("🤖 Bot Drop - Automação Shopify")
    print("="*50 + "\n")

    if args.command == "test":
        cmd_test()

    elif args.command == "health":
        cmd_health()

    elif args.command == "collections":
        cmd_collections()

    elif args.command == "enrich":
        cmd_enrich(args.product_id, args.cost, args.shipping)

    elif args.command == "stats":
        cmd_stats()

    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()
