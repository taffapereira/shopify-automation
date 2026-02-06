#!/usr/bin/env python3
"""
🚀 Teste de Ciclo Completo via DSers
Adiciona produtos diretamente ao DSers usando URLs do AliExpress
"""
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

from src.dsers.automation import DSersAutomation
from src.dashboard import Dashboard

# URLs de produtos REAIS do AliExpress para teste (1 por categoria)
PRODUTOS_TESTE = [
    {
        "categoria": "Brincos",
        "titulo": "Brincos Femininos Elegantes",
        "url": "https://www.aliexpress.com/item/1005006123456789.html",
        "preco_sugerido": 49.90
    },
    {
        "categoria": "Colares",
        "titulo": "Colar Delicado Feminino",
        "url": "https://www.aliexpress.com/item/1005006987654321.html",
        "preco_sugerido": 59.90
    },
    {
        "categoria": "Relógios",
        "titulo": "Relógio Fashion Feminino",
        "url": "https://www.aliexpress.com/item/1005006111222333.html",
        "preco_sugerido": 89.90
    },
]

def buscar_produtos_no_dsers():
    """
    Abre o DSers e permite buscar produtos manualmente
    """
    print('='*60)
    print('🔍 BUSCA DE PRODUTOS NO DSERS')
    print('='*60)
    print('\nO DSers será aberto para você buscar produtos.')
    print('Após encontrar produtos, copie as URLs e feche o navegador.\n')

    dsers = DSersAutomation(headless=False)

    try:
        if dsers.login():
            print('✅ Login OK!')
            print('\n📌 Navegue para: Find Supplier ou Import List')
            print('📌 Busque produtos de cada categoria')
            print('📌 Copie as URLs dos produtos desejados')

            # Navega para página de busca
            dsers.driver.get('https://www.dsers.com/app/find-supplier')

            print('\n⏳ Aguardando 60 segundos para você buscar...')
            print('   (Feche o navegador quando terminar)')

            for i in range(60, 0, -10):
                print(f'   {i} segundos restantes...')
                time.sleep(10)

                # Verifica se navegador ainda está aberto
                try:
                    _ = dsers.driver.current_url
                except:
                    print('\n✅ Navegador fechado pelo usuário')
                    break
        else:
            print('❌ Falha no login')

    finally:
        try:
            dsers.close()
        except:
            pass

def adicionar_produtos_por_url(urls: list):
    """
    Adiciona produtos ao DSers usando URLs do AliExpress
    """
    print('='*60)
    print('🚀 ADICIONANDO PRODUTOS AO DSERS')
    print('='*60)

    dashboard = Dashboard()
    dsers = DSersAutomation(headless=False)

    sincronizados = 0

    try:
        if dsers.login():
            print('✅ Login DSers OK!\n')

            for i, url in enumerate(urls, 1):
                print(f'\n📦 [{i}/{len(urls)}] Adicionando produto...')
                print(f'   URL: {url[:60]}...')

                try:
                    if dsers.adicionar_produto(url):
                        sincronizados += 1
                        print(f'   ✅ Adicionado!')
                    else:
                        print(f'   ❌ Falha')
                except Exception as e:
                    print(f'   ❌ Erro: {e}')

                time.sleep(3)

            if sincronizados > 0:
                print(f'\n🚀 Enviando {sincronizados} produtos para Shopify...')
                try:
                    dsers.push_to_shopify()
                    dashboard.registrar_sincronizacao(sincronizados)
                    print(f'✅ Push realizado!')
                except Exception as e:
                    print(f'⚠️ Erro no push: {e}')
        else:
            print('❌ Falha no login')

    finally:
        print('\n⏳ Fechando em 10s...')
        time.sleep(10)
        dsers.close()

    print('\n' + '='*60)
    print(f'✅ RESULTADO: {sincronizados}/{len(urls)} produtos adicionados')
    print('='*60)

    dashboard.imprimir_dashboard()

def menu():
    """Menu principal"""
    print('\n' + '='*60)
    print('🚀 TESTE DE CICLO COMPLETO - TWP Acessórios')
    print('='*60)
    print('\nOpções:')
    print('1. Abrir DSers para buscar produtos')
    print('2. Adicionar produtos por URL')
    print('3. Sair')

    escolha = input('\nEscolha (1-3): ').strip()

    if escolha == '1':
        buscar_produtos_no_dsers()
    elif escolha == '2':
        print('\nCole as URLs dos produtos (uma por linha).')
        print('Digite "fim" quando terminar:\n')

        urls = []
        while True:
            url = input('URL: ').strip()
            if url.lower() == 'fim':
                break
            if url and 'aliexpress' in url:
                urls.append(url)
                print(f'   ✅ URL adicionada ({len(urls)} total)')
            elif url:
                print('   ⚠️ URL inválida (deve conter "aliexpress")')

        if urls:
            adicionar_produtos_por_url(urls)
        else:
            print('Nenhuma URL válida fornecida.')
    elif escolha == '3':
        print('Até logo!')
    else:
        print('Opção inválida')

if __name__ == "__main__":
    # Se tiver argumentos, usa como URLs
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
        adicionar_produtos_por_url(urls)
    else:
        menu()

