#!/usr/bin/env python3
"""
📢 Script para PUBLICAR todos os produtos na loja online
"""
import requests
import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

store = os.getenv('SHOPIFY_STORE_URL')
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
base_url = f'https://{store}/admin/api/2024-01'

def get_all_products():
    """Busca todos os produtos"""
    produtos = []
    url = f'{base_url}/products.json?limit=250'

    while url:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            produtos.extend(data.get('products', []))
            link = r.headers.get('Link', '')
            if 'rel="next"' in link:
                match = re.search(r'<([^>]+)>; rel="next"', link)
                url = match.group(1) if match else None
            else:
                url = None
        elif r.status_code == 429:
            print("⏳ Rate limit, aguardando 30s...")
            time.sleep(30)
        else:
            print(f"Erro: {r.status_code}")
            break

    return produtos

def publicar_produto(produto):
    """Publica um produto"""
    pid = produto['id']
    published_at = produto.get('published_at')

    # Se já está publicado, pula
    if published_at:
        return False, "Já publicado"

    # Publica o produto
    url = f'{base_url}/products/{pid}.json'
    data = {
        'product': {
            'id': pid,
            'published': True,
            'published_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }

    r = requests.put(url, headers=headers, json=data)

    if r.status_code == 200:
        return True, "Publicado!"
    else:
        return False, f"Erro: {r.status_code}"

def main():
    print("\n" + "="*60)
    print("📢 PUBLICANDO PRODUTOS NA LOJA")
    print("="*60)

    produtos = get_all_products()
    print(f"\n📦 Total de produtos: {len(produtos)}\n")

    publicados = 0
    pulados = 0
    erros = 0

    for i, p in enumerate(produtos, 1):
        titulo = p['title'][:40]

        ok, msg = publicar_produto(p)

        if ok:
            print(f"[{i}/{len(produtos)}] ✅ {titulo}...")
            publicados += 1
        elif "Já publicado" in msg:
            pulados += 1
        else:
            print(f"[{i}/{len(produtos)}] ❌ {titulo}... → {msg}")
            erros += 1

        time.sleep(0.3)

    print("\n" + "="*60)
    print(f"✅ CONCLUÍDO!")
    print(f"   Publicados: {publicados}")
    print(f"   Já estavam publicados: {pulados}")
    print(f"   Erros: {erros}")
    print("="*60)

if __name__ == "__main__":
    main()

