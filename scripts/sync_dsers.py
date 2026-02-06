#!/usr/bin/env python3
"""
🔄 Sincronização DSers → Shopify
Adiciona produtos aprovados ao DSers e sincroniza com Shopify

USO:
    python scripts/sync_dsers.py                    # Todos aprovados pendentes
    python scripts/sync_dsers.py --url URL          # Produto específico
    python scripts/sync_dsers.py --arquivo CSV      # De arquivo CSV
"""
import os
import sys
import csv
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dsers.automation import DSersAutomation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def carregar_produtos_aprovados() -> list:
    """Carrega produtos aprovados do CSV"""
    arquivo = DATA_DIR / "products_approved.csv"

    if not arquivo.exists():
        logger.warning("Arquivo products_approved.csv não encontrado")
        return []

    with open(arquivo, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    parser = argparse.ArgumentParser(description="Sincronização DSers")
    parser.add_argument("--url", "-u", help="URL específica do AliExpress")
    parser.add_argument("--arquivo", "-a", help="Arquivo CSV com produtos")
    parser.add_argument("--limite", "-l", type=int, default=10, help="Limite de produtos")
    parser.add_argument("--headless", action="store_true", help="Modo headless (sem interface)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🔄 SINCRONIZAÇÃO DSERS → SHOPIFY")
    print("="*60)

    dsers = DSersAutomation(headless=args.headless)

    try:
        # Login
        if not dsers.login():
            logger.error("❌ Falha no login do DSers")
            return

        if args.url:
            # Adicionar URL específica
            logger.info(f"📦 Adicionando: {args.url[:50]}...")
            if dsers.adicionar_produto_por_url(args.url):
                dsers.push_to_shopify()
                logger.info("✅ Produto adicionado e sincronizado!")
            else:
                logger.error("❌ Falha ao adicionar produto")

        elif args.arquivo:
            # Carregar de arquivo
            with open(args.arquivo, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                produtos = list(reader)[:args.limite]

            stats = dsers.adicionar_e_sincronizar(produtos)
            logger.info(f"📊 Resultado: {stats}")

        else:
            # Carregar aprovados
            produtos = carregar_produtos_aprovados()[:args.limite]

            if not produtos:
                logger.warning("Nenhum produto aprovado para sincronizar")
                return

            logger.info(f"📦 {len(produtos)} produtos para sincronizar")
            stats = dsers.adicionar_e_sincronizar(produtos)

            print("\n" + "="*60)
            print("✅ SINCRONIZAÇÃO CONCLUÍDA!")
            print("="*60)
            print(f"📦 Total: {stats['total']}")
            print(f"✅ Adicionados: {stats['adicionados']}")
            print(f"❌ Falhas: {stats['falhas']}")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Sincronização interrompida")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise
    finally:
        dsers.close()


if __name__ == "__main__":
    main()

