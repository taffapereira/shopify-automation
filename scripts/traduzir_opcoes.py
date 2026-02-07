#!/usr/bin/env python3
"""
🌐 Script para TRADUZIR OPÇÕES dos produtos (Color → Cor, Size → Tamanho)
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

# Tradução de nomes de opções
OPCOES_PT = {
    "color": "Cor",
    "colour": "Cor",
    "size": "Tamanho",
    "material": "Material",
    "style": "Estilo",
    "type": "Tipo",
    "length": "Comprimento",
    "width": "Largura",
    "weight": "Peso",
    "pattern": "Estampa",
    "quantity": "Quantidade",
}

# Tradução de valores de opções
VALORES_PT = {
    # Cores
    "red": "Vermelho", "blue": "Azul", "green": "Verde", "black": "Preto",
    "white": "Branco", "pink": "Rosa", "purple": "Roxo", "yellow": "Amarelo",
    "orange": "Laranja", "brown": "Marrom", "gray": "Cinza", "grey": "Cinza",
    "gold": "Dourado", "silver": "Prata", "rose": "Rosé", "beige": "Bege",
    "navy": "Azul Marinho", "wine": "Vinho", "khaki": "Cáqui",
    "coffee": "Café", "apricot": "Damasco", "champagne": "Champanhe",
    "red in golden": "Vermelho Dourado", "blue in golden": "Azul Dourado",
    "gold color": "Cor Dourada", "silver color": "Cor Prata",
    "rose gold": "Rosé", "light blue": "Azul Claro", "dark blue": "Azul Escuro",
    "light green": "Verde Claro", "dark green": "Verde Escuro",
    "cream": "Creme", "ivory": "Marfim", "coral": "Coral",
    # Tamanhos
    "small": "Pequeno", "medium": "Médio", "large": "Grande",
    "s": "P", "m": "M", "l": "G", "xl": "GG", "xxl": "GGG",
    "one size": "Tamanho Único", "free size": "Tamanho Único",
    # Medidas
    "18cm": "18cm", "20cm": "20cm", "22cm": "22cm",
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

def traduzir_valor(valor):
    """Traduz um valor de opção"""
    if not valor:
        return valor

    valor_lower = valor.lower().strip()

    # Tradução direta
    if valor_lower in VALORES_PT:
        return VALORES_PT[valor_lower]

    # Tradução parcial
    resultado = valor
    for en, pt in sorted(VALORES_PT.items(), key=lambda x: -len(x[0])):
        resultado = re.sub(r'\b' + re.escape(en) + r'\b', pt, resultado, flags=re.IGNORECASE)

    return resultado.title() if resultado != valor else valor

def traduzir_opcoes(produto):
    """Traduz as opções do produto"""
    pid = produto['id']
    options = produto.get('options', [])

    if not options:
        return False, "Sem opções"

    alterado = False
    novas_opcoes = []

    for opt in options:
        nome_original = opt.get('name', '')
        nome_lower = nome_original.lower().strip()

        # Traduz nome da opção
        if nome_lower in OPCOES_PT:
            novo_nome = OPCOES_PT[nome_lower]
            if novo_nome != nome_original:
                opt['name'] = novo_nome
                alterado = True

        # Traduz valores
        valores = opt.get('values', [])
        novos_valores = []
        for v in valores:
            novo_valor = traduzir_valor(v)
            if novo_valor != v:
                alterado = True
            novos_valores.append(novo_valor)
        opt['values'] = novos_valores

        novas_opcoes.append(opt)

    if not alterado:
        return False, "Já está em português"

    # Atualiza produto
    url = f'{base_url}/products/{pid}.json'
    data = {'product': {'id': pid, 'options': novas_opcoes}}
    r = requests.put(url, headers=headers, json=data)

    if r.status_code == 200:
        return True, f"Opções traduzidas"
    else:
        return False, f"Erro: {r.status_code}"

def traduzir_variantes(produto):
    """Traduz os valores das variantes"""
    pid = produto['id']
    variants = produto.get('variants', [])

    alterado = False

    for v in variants:
        vid = v['id']
        updates = {}

        for opt_key in ['option1', 'option2', 'option3']:
            valor = v.get(opt_key)
            if valor:
                novo_valor = traduzir_valor(valor)
                if novo_valor != valor:
                    updates[opt_key] = novo_valor
                    alterado = True

        if updates:
            url = f'{base_url}/variants/{vid}.json'
            updates['id'] = vid
            r = requests.put(url, headers=headers, json={'variant': updates})
            time.sleep(0.2)

    return alterado

def main():
    print("\n" + "="*60)
    print("🌐 TRADUZINDO OPÇÕES DOS PRODUTOS")
    print("="*60)

    produtos = get_all_products()
    print(f"\n📦 Total de produtos: {len(produtos)}\n")

    traduzidos = 0
    pulados = 0
    erros = 0

    for i, p in enumerate(produtos, 1):
        titulo = p['title'][:35]
        options = p.get('options', [])

        # Mostra opções atuais
        nomes_opcoes = [o.get('name', '') for o in options]

        ok, msg = traduzir_opcoes(p)
        traduzir_variantes(p)  # Traduz também os valores nas variantes

        if ok:
            print(f"[{i}/{len(produtos)}] ✅ {titulo}... ({', '.join(nomes_opcoes)})")
            traduzidos += 1
        elif "Já está" in msg or "Sem opções" in msg:
            pulados += 1
        else:
            print(f"[{i}/{len(produtos)}] ❌ {titulo}... → {msg}")
            erros += 1

        time.sleep(0.3)

    print("\n" + "="*60)
    print(f"✅ CONCLUÍDO!")
    print(f"   Traduzidos: {traduzidos}")
    print(f"   Pulados: {pulados}")
    print(f"   Erros: {erros}")
    print("="*60)

if __name__ == "__main__":
    main()

