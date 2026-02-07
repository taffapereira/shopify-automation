#!/usr/bin/env python3
"""Verifica coleções e produtos na loja"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

store = os.getenv('SHOPIFY_STORE_URL')
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
headers = {'X-Shopify-Access-Token': token}
base_url = f'https://{store}/admin/api/2024-01'

print('📁 COLEÇÕES NA LOJA:')
print('='*50)

# Custom collections
r = requests.get(f'{base_url}/custom_collections.json', headers=headers)
if r.status_code == 200:
    for c in r.json().get('custom_collections', []):
        print(f"  CUSTOM: {c['title']} (handle: {c['handle']}) - ID: {c['id']}")

# Smart collections
r = requests.get(f'{base_url}/smart_collections.json', headers=headers)
if r.status_code == 200:
    for c in r.json().get('smart_collections', []):
        print(f"  SMART: {c['title']} (handle: {c['handle']}) - ID: {c['id']}")

print()
print('📦 PRODUTOS (primeiros 3):')
print('='*50)
r = requests.get(f'{base_url}/products.json?limit=3', headers=headers)
if r.status_code == 200:
    for p in r.json().get('products', []):
        print(f"  Título: {p['title'][:50]}")
        print(f"  Tags: {p.get('tags', 'Sem tags')[:50]}")
        print(f"  Type: {p.get('product_type', 'Sem tipo')}")
        print()

