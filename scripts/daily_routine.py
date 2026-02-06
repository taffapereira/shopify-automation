#!/usr/bin/env python3
"""
📅 Rotina Diária de Automação
Executa mineração, análise IA, sync DSers, relatórios
Pode ser configurada para rodar 3x ao dia (manhã, tarde, noite)
"""
import os
import sys
import argparse
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mining.aliexpress_scraper import AliExpressScraper
from src.mining.criteria import CriteriosMineracao
from src.ai.claude_client import ClaudeClient
from src.dsers.automation import DSersAutomation
from src.shopify.client import ShopifyClient
from src.health.checker import HealthChecker
from src.dashboard import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/routine_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Diretórios
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("relatorios").mkdir(exist_ok=True)


class RotinaAutomatizada:
    """Gerencia rotina diária de automação"""

    def __init__(self):
        self.dashboard = Dashboard()
        self.categorias = ["jewelry", "watches", "bags", "earrings", "necklaces"]
        self.produtos_por_categoria = 5

    def executar_mineracao(self) -> list:
        """Fase 1: Mineração de produtos"""
        logger.info("="*60)
        logger.info("🔍 FASE 1: MINERAÇÃO DE PRODUTOS")
        logger.info("="*60)

        scraper = AliExpressScraper(headless=True)
        ai_client = ClaudeClient(modelo="opus")

        produtos_aprovados = []
        total_minerados = 0

        try:
            for categoria in self.categorias:
                logger.info(f"\n📁 Categoria: {categoria}")

                produtos = scraper.buscar_categoria(categoria, self.produtos_por_categoria * 2)
                total_minerados += len(produtos)

                for produto in produtos[:self.produtos_por_categoria]:
                    # Análise com IA
                    analise = ai_client.analisar_produto(produto)

                    if analise and analise.aprovado and analise.score >= 70:
                        produto['ai_score'] = analise.score
                        produto['ai_titulo'] = analise.titulo_otimizado
                        produto['ai_preco'] = analise.preco_sugerido
                        produto['viralidade_score'] = analise.viralidade.score if analise.viralidade else 0
                        produtos_aprovados.append(produto)

                        logger.info(f"✅ Aprovado (Score: {analise.score}, Viral: {produto['viralidade_score']}): {produto['title'][:40]}...")
                    else:
                        score = analise.score if analise else 0
                        logger.debug(f"❌ Reprovado (Score: {score})")

                time.sleep(2)

        finally:
            scraper._close_driver()

        # Registra métricas
        score_medio = sum(p.get('ai_score', 0) for p in produtos_aprovados) / len(produtos_aprovados) if produtos_aprovados else 0
        self.dashboard.registrar_mineracao(total_minerados, len(produtos_aprovados), score_medio)

        logger.info(f"\n📊 Mineração: {len(produtos_aprovados)}/{total_minerados} aprovados")
        return produtos_aprovados

    def executar_sincronizacao(self, produtos: list) -> dict:
        """Fase 2: Sincronização com DSers/Shopify"""
        logger.info("\n" + "="*60)
        logger.info("🔄 FASE 2: SINCRONIZAÇÃO DSERS")
        logger.info("="*60)

        if not produtos:
            logger.info("Nenhum produto para sincronizar")
            return {"adicionados": 0}

        dsers = DSersAutomation(headless=False)

        try:
            stats = dsers.adicionar_e_sincronizar(produtos)
            self.dashboard.registrar_sincronizacao(stats.get("adicionados", 0))
            logger.info(f"📊 DSers: {stats['adicionados']}/{stats['total']} sincronizados")
            return stats

        finally:
            dsers.close()

    def executar_health_check(self) -> dict:
        """Fase 3: Health check da loja"""
        logger.info("\n" + "="*60)
        logger.info("🏥 FASE 3: HEALTH CHECK")
        logger.info("="*60)

        try:
            checker = HealthChecker()
            resultado = checker.executar_verificacao_completa()

            logger.info(f"📦 Produtos: {resultado.get('total_produtos', 0)}")
            logger.info(f"📁 Coleções: {resultado.get('total_colecoes', 0)}")

            if resultado.get('alertas'):
                for alerta in resultado['alertas']:
                    logger.warning(f"⚠️ {alerta}")

            return resultado
        except Exception as e:
            logger.error(f"Erro no health check: {e}")
            return {}

    def gerar_relatorios(self):
        """Fase 4: Gera relatórios"""
        logger.info("\n" + "="*60)
        logger.info("📊 FASE 4: RELATÓRIOS")
        logger.info("="*60)

        # Dashboard
        self.dashboard.imprimir_dashboard()

        # Salva HTML
        caminho = self.dashboard.salvar_relatorio()
        logger.info(f"📄 Relatório salvo: {caminho}")

    def executar_rotina_completa(self):
        """Executa rotina completa"""
        inicio = datetime.now()
        logger.info("\n" + "="*60)
        logger.info(f"🤖 ROTINA DIÁRIA - {inicio.strftime('%d/%m/%Y %H:%M')}")
        logger.info("="*60)

        try:
            # Fase 1: Mineração
            produtos = self.executar_mineracao()

            # Fase 2: Sincronização (se tiver produtos)
            if produtos:
                self.executar_sincronizacao(produtos)

            # Fase 3: Health Check
            self.executar_health_check()

            # Fase 4: Relatórios
            self.gerar_relatorios()

            duracao = (datetime.now() - inicio).total_seconds() / 60
            logger.info(f"\n✅ ROTINA CONCLUÍDA em {duracao:.1f} minutos")

        except Exception as e:
            logger.error(f"❌ ERRO NA ROTINA: {e}")
            raise

    def executar_apenas_mineracao(self):
        """Executa apenas mineração (sem sync)"""
        produtos = self.executar_mineracao()
        self.gerar_relatorios()
        return produtos

    def agendar_execucoes(self, horarios: list = None):
        """
        Agenda execuções diárias

        Args:
            horarios: Lista de horários ["08:00", "14:00", "20:00"]
        """
        if not horarios:
            horarios = ["08:00", "14:00", "20:00"]

        for horario in horarios:
            schedule.every().day.at(horario).do(self.executar_rotina_completa)
            logger.info(f"⏰ Agendado para: {horario}")

        logger.info(f"🔄 Executando agendador... (Ctrl+C para parar)")

        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Rotina Diária")
    parser.add_argument("--completa", "-c", action="store_true", help="Executa rotina completa")
    parser.add_argument("--mineracao", "-m", action="store_true", help="Apenas mineração")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Mostra dashboard")
    parser.add_argument("--agendar", "-a", action="store_true", help="Agenda execuções 3x/dia")
    parser.add_argument("--horarios", nargs="+", default=["08:00", "14:00", "20:00"], help="Horários para agendamento")
    parser.add_argument("--categorias", nargs="+", default=["jewelry", "watches", "bags"], help="Categorias para minerar")
    parser.add_argument("--quantidade", "-q", type=int, default=5, help="Produtos por categoria")

    args = parser.parse_args()

    rotina = RotinaAutomatizada()
    rotina.categorias = args.categorias
    rotina.produtos_por_categoria = args.quantidade

    if args.dashboard:
        rotina.dashboard.imprimir_dashboard()
    elif args.mineracao:
        rotina.executar_apenas_mineracao()
    elif args.agendar:
        rotina.agendar_execucoes(args.horarios)
    else:
        rotina.executar_rotina_completa()


if __name__ == "__main__":
    main()

