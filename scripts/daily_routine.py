#!/usr/bin/env python3
"""
📅 Rotina Diária de Automação
Executa: mineração → análise IA → DSers → health check

USO:
    python scripts/daily_routine.py
    python scripts/daily_routine.py --skip-mining
    python scripts/daily_routine.py --categorias jewelry,watches
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mining.aliexpress_scraper import AliExpressScraper
from src.mining.criteria import CriteriosMineracao
from src.ai.claude_client import ClaudeClient
from src.dsers.automation import DSersAutomation
from src.shopify.client import ShopifyClient
from src.health.checker import HealthChecker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_header(titulo: str):
    """Imprime header de seção"""
    print("\n" + "="*60)
    print(f"📌 {titulo}")
    print("="*60)


def rotina_mineracao(categorias: list, quantidade: int = 10) -> list:
    """Executa mineração de produtos"""
    print_header("FASE 1: MINERAÇÃO DE PRODUTOS")

    scraper = AliExpressScraper(headless=True)
    ai_client = ClaudeClient()

    produtos_aprovados = []

    try:
        for categoria in categorias:
            logger.info(f"\n🔍 Minerando: {categoria}")

            # Busca produtos
            produtos = scraper.buscar_categoria(categoria, quantidade * 2)  # Busca mais para filtrar

            # Analisa com IA
            for produto in produtos[:quantidade]:
                analise = ai_client.analisar_produto(produto)

                if analise and analise.aprovado and analise.score >= 70:
                    produto['ai_score'] = analise.score
                    produto['ai_titulo'] = analise.titulo_otimizado
                    produto['ai_preco'] = analise.preco_sugerido
                    produtos_aprovados.append(produto)
                    logger.info(f"✅ Aprovado ({analise.score}): {produto['title'][:40]}...")
                else:
                    score = analise.score if analise else 0
                    logger.debug(f"❌ Reprovado ({score})")

            if len(produtos_aprovados) >= quantidade:
                break

    finally:
        scraper._close_driver()

    logger.info(f"\n📊 Total aprovados: {len(produtos_aprovados)}")
    return produtos_aprovados


def rotina_dsers(produtos: list) -> dict:
    """Sincroniza produtos com DSers"""
    print_header("FASE 2: SINCRONIZAÇÃO DSERS")

    if not produtos:
        logger.info("Nenhum produto para sincronizar")
        return {"total": 0, "adicionados": 0, "falhas": 0}

    dsers = DSersAutomation(headless=False)  # Precisa de interface para login

    try:
        if not dsers.login():
            logger.error("❌ Falha no login DSers")
            return {"total": len(produtos), "adicionados": 0, "falhas": len(produtos)}

        stats = dsers.adicionar_e_sincronizar(produtos)
        return stats

    finally:
        dsers.close()


def rotina_health_check():
    """Executa health check da loja"""
    print_header("FASE 3: HEALTH CHECK")

    try:
        checker = HealthChecker()
        resultado = checker.executar_verificacao_completa()

        print(f"\n📊 Status: {resultado.get('status', 'N/A')}")
        print(f"📦 Produtos: {resultado.get('total_produtos', 0)}")
        print(f"📁 Coleções: {resultado.get('total_colecoes', 0)}")

        if resultado.get('alertas'):
            print("\n⚠️ Alertas:")
            for alerta in resultado['alertas']:
                print(f"   - {alerta}")

        return resultado

    except Exception as e:
        logger.error(f"❌ Erro no health check: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Rotina Diária")
    parser.add_argument("--skip-mining", action="store_true", help="Pular mineração")
    parser.add_argument("--skip-dsers", action="store_true", help="Pular DSers")
    parser.add_argument("--categorias", "-c", default="jewelry,watches,bags", help="Categorias (separadas por vírgula)")
    parser.add_argument("--quantidade", "-q", type=int, default=5, help="Produtos por categoria")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🤖 ROTINA DIÁRIA DE AUTOMAÇÃO")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*60)

    categorias = [c.strip() for c in args.categorias.split(",")]
    produtos_aprovados = []

    try:
        # FASE 1: Mineração
        if not args.skip_mining:
            produtos_aprovados = rotina_mineracao(categorias, args.quantidade)
        else:
            logger.info("⏭️ Mineração pulada")

        # FASE 2: DSers
        if not args.skip_dsers and produtos_aprovados:
            stats = rotina_dsers(produtos_aprovados)
            logger.info(f"📊 DSers: {stats['adicionados']}/{stats['total']} sincronizados")
        else:
            logger.info("⏭️ DSers pulado")

        # FASE 3: Health Check
        rotina_health_check()

        print("\n" + "="*60)
        print("✅ ROTINA DIÁRIA CONCLUÍDA!")
        print("="*60)
        print(f"📦 Produtos minerados: {len(produtos_aprovados)}")
        print(f"📅 Próxima execução: amanhã")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Rotina interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro na rotina: {e}")
        raise


if __name__ == "__main__":
    main()

