#!/usr/bin/env python3
"""
🚀 Teste de Ciclo Completo
Minera 1 produto de cada coleção, analisa com IA e sincroniza com DSers
"""
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.mining.aliexpress_scraper import AliExpressScraper
from src.ai.claude_client import ClaudeClient
from src.dsers.automation import DSersAutomation
from src.dashboard import Dashboard

# Categorias da loja
CATEGORIAS = ['jewelry', 'watches', 'bags', 'earrings', 'necklaces', 'bracelets', 'rings']

def main():
    print('='*60)
    print('🚀 CICLO COMPLETO DE TESTE - 1 PRODUTO POR COLEÇÃO')
    print('='*60)

    dashboard = Dashboard()
    scraper = AliExpressScraper(headless=True)
    ai_client = ClaudeClient(modelo='opus')

    produtos_aprovados = []
    total_minerados = 0

    print('\n📦 FASE 1: MINERAÇÃO')
    print('-'*60)

    try:
        for categoria in CATEGORIAS[:3]:  # Teste com 3 categorias
            print(f'\n🔍 Minerando: {categoria}')

            produtos = scraper.buscar_categoria(categoria, 3)
            total_minerados += len(produtos)

            if produtos:
                # Pega o melhor produto
                melhor = max(produtos, key=lambda x: x.get('orders', 0))

                print(f'   📦 Encontrado: {melhor["title"][:50]}...')
                print(f'   💰 Preço: ${melhor["price"]:.2f}')
                print(f'   📊 Pedidos: {melhor["orders"]}')

                img_url = melhor.get("image_url", "N/A")
                if img_url and img_url != "N/A":
                    print(f'   🖼️  Imagem: {img_url[:60]}...')

                # Análise com IA
                print(f'   🤖 Analisando com Claude...')
                analise = ai_client.analisar_produto(melhor)

                if analise:
                    print(f'   ✅ Score: {analise.score}')
                    if analise.titulo_otimizado:
                        print(f'   📝 Título PT: {analise.titulo_otimizado[:40]}...')

                    if analise.aprovado and analise.score >= 50:
                        melhor['ai_score'] = analise.score
                        melhor['ai_titulo'] = analise.titulo_otimizado
                        melhor['ai_preco'] = analise.preco_sugerido
                        produtos_aprovados.append(melhor)
                        print(f'   ✅ APROVADO!')
                    else:
                        print(f'   ❌ Reprovado (score baixo)')
                        # Adiciona mesmo assim para teste
                        produtos_aprovados.append(melhor)
                        print(f'   ⚠️ Adicionado para teste')
                else:
                    print(f'   ⚠️ Análise falhou, adicionando para teste')
                    produtos_aprovados.append(melhor)
            else:
                print(f'   ⚠️ Nenhum produto encontrado')

            time.sleep(2)

    finally:
        scraper._close_driver()

    print(f'\n📊 Mineração: {len(produtos_aprovados)} aprovados de {total_minerados} minerados')

    # Registra no dashboard
    if produtos_aprovados:
        score_medio = sum(p.get('ai_score', 70) for p in produtos_aprovados) / len(produtos_aprovados)
        dashboard.registrar_mineracao(total_minerados, len(produtos_aprovados), score_medio)

    if produtos_aprovados:
        print('\n🔄 FASE 2: SINCRONIZAÇÃO DSERS')
        print('-'*60)

        dsers = DSersAutomation(headless=False)

        try:
            if dsers.login():
                print('✅ Login DSers OK')

                sincronizados = 0
                for produto in produtos_aprovados:
                    url = produto.get('product_url', '')
                    if url:
                        titulo = produto.get("title", "")[:40]
                        print(f'\n📦 Adicionando: {titulo}...')
                        print(f'   URL: {url[:60]}...')

                        try:
                            if dsers.adicionar_produto(url):
                                sincronizados += 1
                                print(f'   ✅ Adicionado!')
                            else:
                                print(f'   ❌ Falha ao adicionar')
                        except Exception as e:
                            print(f'   ❌ Erro: {e}')

                        time.sleep(3)

                if sincronizados > 0:
                    print(f'\n🚀 Enviando para Shopify...')
                    try:
                        dsers.push_to_shopify()
                        dashboard.registrar_sincronizacao(sincronizados)
                        print(f'✅ {sincronizados} produtos sincronizados!')
                    except Exception as e:
                        print(f'⚠️ Erro no push: {e}')
            else:
                print('❌ Falha no login DSers')

        finally:
            print('\nFechando DSers em 10s...')
            time.sleep(10)
            dsers.close()

    print('\n' + '='*60)
    print('✅ CICLO COMPLETO FINALIZADO!')
    print('='*60)
    dashboard.imprimir_dashboard()


if __name__ == "__main__":
    main()

