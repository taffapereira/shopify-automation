#!/usr/bin/env python3
"""
🔧 Script para CORRIGIR APENAS AS TAGS dos produtos
Usa o product_type existente para definir a tag cat: correta
"""
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

store = os.getenv('SHOPIFY_STORE_URL')
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
base_url = f'https://{store}/admin/api/2024-01'

# Mapeamento de product_type para tag cat:
TYPE_TO_CAT = {
    "brincos": "cat:brincos",
    "colares": "cat:colares",
    "pulseiras": "cat:pulseiras",
    "aneis": "cat:aneis",
    "anéis": "cat:aneis",
    "relogios": "cat:relogios",
    "relógios": "cat:relogios",
    "oculos": "cat:oculos",
    "óculos": "cat:oculos",
    "bolsas": "cat:bolsas",
    "carteiras": "cat:carteiras",
    "acessorios": "cat:acessorios",
    "acessórios": "cat:acessorios",
}

def get_all_products():
    """Busca todos os produtos com retry"""
    import re as regex_module
    produtos = []
    url = f'{base_url}/products.json?limit=250'

    max_retries = 3

    while url:
        for attempt in range(max_retries):
            r = requests.get(url, headers=headers)

            if r.status_code == 200:
                data = r.json()
                produtos.extend(data.get('products', []))
                link = r.headers.get('Link', '')
                if 'rel="next"' in link:
                    match = regex_module.search(r'<([^>]+)>; rel="next"', link)
                    url = match.group(1) if match else None
                else:
                    url = None
                break
            elif r.status_code == 429:
                print(f"⏳ Rate limit, aguardando 30s... (tentativa {attempt+1})")
                time.sleep(30)
            else:
                print(f"Erro na API: {r.status_code}")
                url = None
                break
        else:
            print("❌ Máximo de tentativas excedido")
            break

    return produtos

def corrigir_tags(produto):
    """Corrige as tags do produto para incluir cat:"""
    pid = produto['id']
    product_type = produto.get('product_type', '').lower().strip()
    tags_atuais = produto.get('tags', '')

    # Encontra a tag cat: correta
    cat_tag = TYPE_TO_CAT.get(product_type, 'cat:acessorios')

    # Se já tem a tag correta, pula
    if cat_tag in tags_atuais:
        return False, "Já tem tag correta"

    # Remove qualquer tag cat: antiga
    tags_lista = [t.strip() for t in tags_atuais.split(',') if t.strip() and not t.strip().startswith('cat:')]

    # Adiciona a tag cat: correta
    tags_lista.insert(0, cat_tag)

    # Junta as tags
    novas_tags = ', '.join(tags_lista)

    # Atualiza o produto
    url = f'{base_url}/products/{pid}.json'
    data = {'product': {'id': pid, 'tags': novas_tags}}
    r = requests.put(url, headers=headers, json=data)

    if r.status_code == 200:
        return True, f"{cat_tag}"
    else:
        return False, f"Erro API: {r.status_code}"

def main():
    print("\n" + "="*60)
    print("🔧 CORRIGINDO TAGS DOS PRODUTOS")
    print("="*60)

    produtos = get_all_products()
    print(f"\n📦 Total de produtos: {len(produtos)}\n")

    corrigidos = 0
    erros = 0
    pulados = 0

    for i, p in enumerate(produtos, 1):
        titulo = p['title'][:40]
        product_type = p.get('product_type', 'Sem tipo')

        ok, msg = corrigir_tags(p)

        if ok:
            print(f"[{i}/{len(produtos)}] ✅ {titulo}... → {msg}")
            corrigidos += 1
        elif "Já tem" in msg:
            pulados += 1
        else:
            print(f"[{i}/{len(produtos)}] ❌ {titulo}... → {msg}")
            erros += 1

        time.sleep(0.3)

    print("\n" + "="*60)
    print(f"✅ CONCLUÍDO!")
    print(f"   Corrigidos: {corrigidos}")
    print(f"   Pulados: {pulados}")
    print(f"   Erros: {erros}")
    print("="*60)

if __name__ == "__main__":
    main()



