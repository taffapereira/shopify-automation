"""
Módulo para gerenciamento de produtos na Shopify.
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def get_headers():
    """Retorna headers padrão para requisições."""
    return {
        "X-Shopify-Access-Token": os.getenv("SHOPIFY_ACCESS_TOKEN"),
        "Content-Type": "application/json"
    }


def get_api_url(endpoint):
    """Retorna URL completa da API."""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")
    return f"https://{store_url}/admin/api/{api_version}/{endpoint}"


# =============================================================================
# PRODUTOS - CRUD
# =============================================================================

def listar_produtos(limit=50):
    """Lista todos os produtos da loja."""
    url = get_api_url(f"products.json?limit={limit}")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        produtos = response.json().get("products", [])
        print(f"\n📦 {len(produtos)} produtos encontrados:\n")
        for p in produtos:
            print(f"  [{p['id']}] {p['title']} - {p['status']}")
        return produtos
    else:
        print(f"❌ Erro ao listar produtos: {response.text}")
        return []


def obter_produto(product_id):
    """Obtém detalhes de um produto específico."""
    url = get_api_url(f"products/{product_id}.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        produto = response.json().get("product")
        print(f"\n📦 Produto: {produto['title']}")
        print(f"   ID: {produto['id']}")
        print(f"   Status: {produto['status']}")
        print(f"   Preço: {produto['variants'][0]['price'] if produto['variants'] else 'N/A'}")
        return produto
    else:
        print(f"❌ Erro ao obter produto: {response.text}")
        return None


def criar_produto(titulo, descricao="", preco="0.00", tipo_produto="", vendor="", status="draft"):
    """
    Cria um novo produto na loja.

    Args:
        titulo: Nome do produto
        descricao: Descrição HTML do produto
        preco: Preço do produto
        tipo_produto: Tipo/categoria do produto
        vendor: Fornecedor/marca
        status: 'active', 'draft', ou 'archived'
    """
    url = get_api_url("products.json")

    payload = {
        "product": {
            "title": titulo,
            "body_html": descricao,
            "vendor": vendor,
            "product_type": tipo_produto,
            "status": status,
            "variants": [
                {
                    "price": preco,
                    "inventory_management": "shopify"
                }
            ]
        }
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        produto = response.json().get("product")
        print(f"✅ Produto criado: {produto['title']} (ID: {produto['id']})")
        return produto
    else:
        print(f"❌ Erro ao criar produto: {response.text}")
        return None


def atualizar_produto(product_id, **kwargs):
    """
    Atualiza um produto existente.

    Args:
        product_id: ID do produto
        **kwargs: Campos a atualizar (title, body_html, vendor, status, etc.)
    """
    url = get_api_url(f"products/{product_id}.json")

    payload = {"product": {"id": product_id, **kwargs}}

    response = requests.put(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        produto = response.json().get("product")
        print(f"✅ Produto atualizado: {produto['title']}")
        return produto
    else:
        print(f"❌ Erro ao atualizar produto: {response.text}")
        return None


def deletar_produto(product_id):
    """Remove um produto da loja."""
    url = get_api_url(f"products/{product_id}.json")
    response = requests.delete(url, headers=get_headers())

    if response.status_code == 200:
        print(f"✅ Produto {product_id} removido com sucesso!")
        return True
    else:
        print(f"❌ Erro ao deletar produto: {response.text}")
        return False


def atualizar_preco(product_id, novo_preco):
    """Atualiza o preço de um produto."""
    # Primeiro, obter o variant_id
    produto = obter_produto(product_id)
    if not produto or not produto.get("variants"):
        return None

    variant_id = produto["variants"][0]["id"]
    url = get_api_url(f"variants/{variant_id}.json")

    payload = {
        "variant": {
            "id": variant_id,
            "price": str(novo_preco)
        }
    }

    response = requests.put(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        print(f"✅ Preço atualizado para: R$ {novo_preco}")
        return response.json().get("variant")
    else:
        print(f"❌ Erro ao atualizar preço: {response.text}")
        return None


def atualizar_estoque(inventory_item_id, location_id, quantidade):
    """Atualiza o estoque de um item."""
    url = get_api_url("inventory_levels/set.json")

    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available": quantidade
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        print(f"✅ Estoque atualizado para: {quantidade} unidades")
        return response.json()
    else:
        print(f"❌ Erro ao atualizar estoque: {response.text}")
        return None


# =============================================================================
# EXEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🛍️  Gerenciador de Produtos Shopify")
    print("=" * 50)

    # Exemplo: Listar produtos
    # listar_produtos()

    # Exemplo: Criar produto
    # criar_produto(
    #     titulo="Camiseta Teste",
    #     descricao="<p>Uma camiseta incrível!</p>",
    #     preco="49.90",
    #     tipo_produto="Vestuário",
    #     vendor="Minha Marca",
    #     status="draft"
    # )

    # Exemplo: Atualizar produto
    # atualizar_produto(123456789, title="Novo Nome", status="active")

    # Exemplo: Deletar produto
    # deletar_produto(123456789)

    print("\n📝 Descomente os exemplos acima para testar!")
