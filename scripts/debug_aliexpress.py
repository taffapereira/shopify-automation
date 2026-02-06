#!/usr/bin/env python3
"""
🔍 Diagnóstico do AliExpress - Verifica estrutura da página
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re

options = Options()
options.add_argument('--window-size=1920,1080')

print('🔍 Abrindo AliExpress...')
driver = webdriver.Chrome(options=options)
driver.get('https://www.aliexpress.com/category/200001679/jewelry-accessories.html?sortType=total_tranpro_desc')
time.sleep(10)

# Scroll para carregar produtos
print('📜 Fazendo scroll...')
for i in range(5):
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    print(f'   Scroll {i+1}/5')

soup = BeautifulSoup(driver.page_source, 'html.parser')

print(f'\n📄 Título: {driver.title}')
print(f'📄 URL: {driver.current_url}')

# Tenta diferentes seletores
print('\n🔍 Procurando produtos...')
seletores = [
    'div[class*="search-item"]',
    'div[class*="product-card"]',
    'div[class*="card-out-wrapper"]',
    'a[class*="search-card"]',
    '[class*="SnowProductCard"]',
    '[class*="productCard"]',
    'div.search-item-card-wrapper-gallery',
    'div[data-widget-cid]',
]

for sel in seletores:
    try:
        elementos = soup.select(sel)
        if elementos:
            print(f'\n✅ ENCONTRADO: {sel}')
            print(f'   Total: {len(elementos)}')
            if elementos:
                classes = elementos[0].get('class', [])
                print(f'   Classes: {classes[:3]}...' if len(classes) > 3 else f'   Classes: {classes}')
    except Exception as e:
        print(f'❌ Erro com {sel}: {e}')

# Procura por links de produtos
links = soup.find_all('a', href=re.compile(r'/item/\d+'))
print(f'\n🔗 Links de produtos encontrados: {len(links)}')

if links:
    print('\n📦 Primeiros 3 produtos:')
    for i, link in enumerate(links[:3]):
        href = link.get('href', '')
        title_elem = link.find(class_=re.compile(r'title|name'))
        title = title_elem.text.strip() if title_elem else 'N/A'
        print(f'   {i+1}. {title[:50]}...')
        print(f'      URL: {href[:60]}...')

# Salva HTML
with open('temp/aliexpress_debug.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)
print('\n📄 HTML salvo em temp/aliexpress_debug.html')

print('\n⏳ Fechando em 15s... Verifique a tela!')
time.sleep(15)
driver.quit()
print('✅ Finalizado')

