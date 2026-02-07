#!/usr/bin/env python3
"""
💰 Script para CORRIGIR PREÇOS dos produtos
Preços FIXOS por categoria baseados em custo real + markup 2x
"""
import requests
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

store = os.getenv('SHOPIFY_STORE_URL')
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
base_url = f'https://{store}/admin/api/2024-01'

# Preços FIXOS por categoria (venda, de)
# Baseado em: Custo AliExpress + Frete + Impostos (~R$70-150) x Markup 2x
PRECOS = {
    "brincos": (89.90, 129.90),
    "colares": (119.90, 169.90),
    "pulseiras": (99.90, 139.90),
    "aneis": (79.90, 109.90),
    "anéis": (79.90, 109.90),
    "relogios": (189.90, 269.90),
    "relógios": (189.90, 269.90),
    "oculos": (129.90, 179.90),
    "óculos": (129.90, 179.90),
    "bolsas": (199.90, 279.90),
    "carteiras": (89.90, 129.90),
    "acessorios": (99.90, 139.90),
    "acessórios": (99.90, 139.90),
}

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

def obter_preco_categoria(product_type):
    """Retorna preço baseado na categoria"""
    pt_lower = product_type.lower() if product_type else ""

    for cat, precos in PRECOS.items():
        if cat in pt_lower:
            return precos

    # Fallback
    return (99.90, 139.90)

def corrigir_precos(produto):
    """Corrige os preços de um produto"""
    pid = produto['id']
    product_type = produto.get('product_type', '')
    variants = produto.get('variants', [])

    if not variants:
        return False, "Sem variantes"

    preco_atual = float(variants[0].get('price', 0))
    preco_novo, preco_de = obter_preco_categoria(product_type)

    # Se já está no preço correto (tolerância de R$5), pula
    if abs(preco_novo - preco_atual) < 5:
        return False, "OK"

    # Atualiza todas as variantes
    for v in variants:
        vid = v['id']
        url = f'{base_url}/variants/{vid}.json'
        data = {
            'variant': {
                'id': vid,
                'price': f'{preco_novo:.2f}',
                'compare_at_price': f'{preco_de:.2f}'
            }
        }
        r = requests.put(url, headers=headers, json=data)
        if r.status_code != 200:
            return False, f"Erro: {r.status_code}"
        time.sleep(0.2)

    return True, f"R$ {preco_atual:.2f} → R$ {preco_novo:.2f}"

def main():
    print("\n" + "="*60)
    print("💰 CORRIGINDO PREÇOS DOS PRODUTOS")
    print("="*60)
    print("\n📋 Tabela de preços por categoria:")
    for cat, (venda, de) in sorted(PRECOS.items()):
        if cat in ["anéis", "relógios", "óculos", "acessórios"]:
            continue
        print(f"   {cat.capitalize()}: R$ {venda:.2f} (de R$ {de:.2f})")
    print("="*60)

    produtos = get_all_products()
    print(f"\n📦 Total: {len(produtos)} produtos\n")

    corrigidos = erros = pulados = 0

    for i, p in enumerate(produtos, 1):
        titulo = p['title'][:35]
        cat = p.get('product_type', 'N/A')

        ok, msg = corrigir_precos(p)

        if ok:
            print(f"[{i}/{len(produtos)}] ✅ [{cat}] {titulo}... {msg}")
            corrigidos += 1
        elif "OK" in msg:
            pulados += 1
        else:
            print(f"[{i}/{len(produtos)}] ❌ {titulo}... {msg}")
            erros += 1

        time.sleep(0.3)

    print("\n" + "="*60)
    print(f"✅ CONCLUÍDO!")
    print(f"   Corrigidos: {corrigidos}")
    print(f"   Já estavam OK: {pulados}")
    print(f"   Erros: {erros}")
    print("="*60)

if __name__ == "__main__":
    main()

