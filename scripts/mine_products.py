#!/usr/bin/env python3
"""
🔍 Script de Mineração de Produtos
Busca produtos no AliExpress, analisa com IA e salva aprovados

USO:
    python scripts/mine_products.py --categoria jewelry --quantidade 20
    python scripts/mine_products.py --todas --quantidade 10
    python scripts/mine_products.py --analisar
"""
import os
import sys
import csv
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mining.aliexpress_scraper import AliExpressScraper
from src.mining.criteria import CriteriosMineracao, validar_produto
from src.ai.claude_client import ClaudeClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Diretórios
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def salvar_produtos_csv(produtos: list, arquivo: str = None):
    """Salva produtos em CSV"""
    if not arquivo:
        data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = DATA_DIR / f"products_mined_{data_str}.csv"

    if not produtos:
        logger.warning("Nenhum produto para salvar")
        return

    fieldnames = list(produtos[0].keys())

    with open(arquivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(produtos)

    logger.info(f"✅ {len(produtos)} produtos salvos em: {arquivo}")


def salvar_produtos_aprovados(produtos: list):
    """Salva produtos aprovados no arquivo principal"""
    arquivo = DATA_DIR / "products_approved.csv"

    # Se arquivo existe, carrega existentes
    existentes = []
    if arquivo.exists():
        with open(arquivo, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existentes = list(reader)

    # Adiciona novos (evita duplicatas por product_id)
    ids_existentes = {p.get('product_id') for p in existentes}
    novos = [p for p in produtos if p.get('product_id') not in ids_existentes]

    todos = existentes + novos

    if todos:
        fieldnames = list(todos[0].keys())
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(todos)

        logger.info(f"✅ {len(novos)} novos produtos adicionados aos aprovados")


def minerar_categoria(scraper: AliExpressScraper, categoria: str, quantidade: int, analisar_ia: bool = False):
    """Minera uma categoria específica"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 Minerando: {categoria.upper()}")
    logger.info(f"{'='*60}")

    # Busca produtos
    produtos = scraper.buscar_categoria(categoria, quantidade)

    if not produtos:
        logger.warning(f"Nenhum produto encontrado em {categoria}")
        return []

    # Análise com IA (se habilitada)
    if analisar_ia:
        logger.info("🤖 Analisando com IA...")
        ai_client = ClaudeClient()

        produtos_analisados = []
        for produto in produtos:
            analise = ai_client.analisar_produto(produto)
            if analise and analise.aprovado:
                produto['ai_score'] = analise.score
                produto['ai_titulo'] = analise.titulo_otimizado
                produto['ai_descricao'] = analise.descricao_seo
                produto['ai_preco_sugerido'] = analise.preco_sugerido
                produto['ai_tags'] = ','.join(analise.tags_sugeridas)
                produtos_analisados.append(produto)
                logger.info(f"✅ Aprovado (score: {analise.score}): {produto['title'][:40]}...")
            else:
                score = analise.score if analise else 0
                logger.info(f"❌ Reprovado (score: {score}): {produto['title'][:40]}...")

        produtos = produtos_analisados

    logger.info(f"📊 Total aprovados: {len(produtos)}")
    return produtos


def main():
    parser = argparse.ArgumentParser(description="Mineração de Produtos")
    parser.add_argument("--categoria", "-c", help="Categoria específica (jewelry, watches, bags, etc)")
    parser.add_argument("--quantidade", "-q", type=int, default=20, help="Quantidade por categoria")
    parser.add_argument("--todas", "-t", action="store_true", help="Minerar todas as categorias")
    parser.add_argument("--analisar", "-a", action="store_true", help="Analisar com IA")
    parser.add_argument("--headless", action="store_true", default=True, help="Modo headless")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🔍 MINERAÇÃO DE PRODUTOS - TWP Acessórios")
    print("="*60)

    scraper = AliExpressScraper(headless=args.headless)
    criterios = CriteriosMineracao()

    todos_produtos = []

    try:
        if args.todas:
            # Minera todas as categorias
            for categoria in criterios.categorias_permitidas:
                produtos = minerar_categoria(scraper, categoria, args.quantidade, args.analisar)
                todos_produtos.extend(produtos)
        elif args.categoria:
            # Minera categoria específica
            produtos = minerar_categoria(scraper, args.categoria, args.quantidade, args.analisar)
            todos_produtos.extend(produtos)
        else:
            # Padrão: jewelry
            produtos = minerar_categoria(scraper, "jewelry", args.quantidade, args.analisar)
            todos_produtos.extend(produtos)

        # Salva resultados
        if todos_produtos:
            salvar_produtos_csv(todos_produtos)
            salvar_produtos_aprovados(todos_produtos)

        print("\n" + "="*60)
        print("✅ MINERAÇÃO CONCLUÍDA!")
        print("="*60)
        print(f"📦 Total de produtos aprovados: {len(todos_produtos)}")
        print(f"📁 Dados salvos em: {DATA_DIR}")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Mineração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise
    finally:
        scraper._close_driver()


if __name__ == "__main__":
    main()

