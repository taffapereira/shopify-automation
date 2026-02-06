"""
Módulo para configurações da loja Shopify.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def get_headers():
    return {
        "X-Shopify-Access-Token": os.getenv("SHOPIFY_ACCESS_TOKEN"),
        "Content-Type": "application/json"
    }


def get_api_url(endpoint):
    store_url = os.getenv("SHOPIFY_STORE_URL")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")
    return f"https://{store_url}/admin/api/{api_version}/{endpoint}"


# =============================================================================
# INFORMAÇÕES DA LOJA
# =============================================================================

def obter_info_loja():
    """Obtém todas as informações da loja."""
    url = get_api_url("shop.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        loja = response.json().get("shop")
        print(f"\n🏪 Informações da Loja:")
        print(f"   Nome: {loja['name']}")
        print(f"   Email: {loja['email']}")
        print(f"   Domínio: {loja['domain']}")
        print(f"   Moeda: {loja['currency']}")
        print(f"   Timezone: {loja['timezone']}")
        print(f"   País: {loja['country_name']}")
        print(f"   Plano: {loja['plan_name']}")
        return loja
    else:
        print(f"❌ Erro ao obter info da loja: {response.text}")
        return None


# =============================================================================
# LOCALIZAÇÕES
# =============================================================================

def listar_localizacoes():
    """Lista todas as localizações/estoques da loja."""
    url = get_api_url("locations.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        locations = response.json().get("locations", [])
        print(f"\n📍 {len(locations)} localizações encontradas:\n")
        for loc in locations:
            print(f"  [{loc['id']}] {loc['name']}")
            print(f"      {loc['address1']}, {loc['city']} - {loc['country']}")
            print(f"      Ativo: {'Sim' if loc['active'] else 'Não'}")
        return locations
    else:
        print(f"❌ Erro ao listar localizações: {response.text}")
        return []


# =============================================================================
# POLÍTICAS DA LOJA
# =============================================================================

def listar_politicas():
    """Lista todas as políticas da loja (reembolso, privacidade, etc.)."""
    url = get_api_url("policies.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        policies = response.json().get("policies", [])
        print(f"\n📜 {len(policies)} políticas encontradas:\n")
        for pol in policies:
            print(f"  • {pol['title']}")
            print(f"    URL: {pol['url']}")
        return policies
    else:
        print(f"❌ Erro ao listar políticas: {response.text}")
        return []


# =============================================================================
# PAÍSES E FRETE
# =============================================================================

def listar_paises_envio():
    """Lista países habilitados para envio."""
    url = get_api_url("shipping_zones.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        zones = response.json().get("shipping_zones", [])
        print(f"\n🚚 {len(zones)} zonas de envio:\n")
        for zone in zones:
            print(f"  📦 {zone['name']}")
            for country in zone.get("countries", []):
                print(f"     • {country['name']}")
        return zones
    else:
        print(f"❌ Erro ao listar zonas de envio: {response.text}")
        return []


# =============================================================================
# MEIOS DE PAGAMENTO
# =============================================================================

def listar_gateways_pagamento():
    """Lista gateways de pagamento configurados."""
    # Nota: Este endpoint requer permissões especiais
    url = get_api_url("payment_gateways.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        gateways = response.json().get("payment_gateways", [])
        print(f"\n💳 {len(gateways)} gateways de pagamento:\n")
        for gw in gateways:
            status = "✅ Ativo" if gw.get("enabled") else "❌ Inativo"
            print(f"  {status} {gw['name']}")
        return gateways
    else:
        print(f"❌ Erro ao listar gateways (pode precisar de permissões especiais): {response.text}")
        return []


# =============================================================================
# TEMAS
# =============================================================================

def listar_temas():
    """Lista temas instalados na loja."""
    url = get_api_url("themes.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        themes = response.json().get("themes", [])
        print(f"\n🎨 {len(themes)} temas instalados:\n")
        for theme in themes:
            role = "🌟 ATIVO" if theme['role'] == 'main' else theme['role']
            print(f"  [{theme['id']}] {theme['name']} - {role}")
        return themes
    else:
        print(f"❌ Erro ao listar temas: {response.text}")
        return []


def obter_tema_ativo():
    """Retorna o tema atualmente ativo."""
    temas = listar_temas()
    for tema in temas:
        if tema['role'] == 'main':
            return tema
    return None


# =============================================================================
# COLEÇÕES
# =============================================================================

def listar_colecoes():
    """Lista coleções manuais (custom collections)."""
    url = get_api_url("custom_collections.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        collections = response.json().get("custom_collections", [])
        print(f"\n📁 {len(collections)} coleções manuais:\n")
        for col in collections:
            print(f"  [{col['id']}] {col['title']}")
        return collections
    else:
        print(f"❌ Erro ao listar coleções: {response.text}")
        return []


def criar_colecao(titulo, descricao="", publicada=True):
    """Cria uma nova coleção manual."""
    url = get_api_url("custom_collections.json")

    payload = {
        "custom_collection": {
            "title": titulo,
            "body_html": descricao,
            "published": publicada
        }
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        col = response.json().get("custom_collection")
        print(f"✅ Coleção criada: {col['title']} (ID: {col['id']})")
        return col
    else:
        print(f"❌ Erro ao criar coleção: {response.text}")
        return None


def adicionar_produto_colecao(collection_id, product_id):
    """Adiciona um produto a uma coleção."""
    url = get_api_url("collects.json")

    payload = {
        "collect": {
            "collection_id": collection_id,
            "product_id": product_id
        }
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        print(f"✅ Produto {product_id} adicionado à coleção {collection_id}")
        return response.json().get("collect")
    else:
        print(f"❌ Erro ao adicionar produto à coleção: {response.text}")
        return None


# =============================================================================
# EXEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("⚙️  Configurações da Loja Shopify")
    print("=" * 50)

    # Exemplo: Informações da loja
    # obter_info_loja()

    # Exemplo: Listar localizações
    # listar_localizacoes()

    # Exemplo: Listar temas
    # listar_temas()

    # Exemplo: Listar coleções
    # listar_colecoes()

    print("\n📝 Descomente os exemplos acima para testar!")
