import os
import json
from dotenv import load_dotenv
import shopify
import requests

load_dotenv(override=True)


# =============================================================================
# CONFIGURAÇÕES E CONEXÃO
# =============================================================================

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


def testar_conexao_direta():
    """Testa conexão direta com a API para debug."""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")

    url = f"https://{store_url}/admin/api/{api_version}/shop.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    print(f"\n🔍 Debug - URL: {url}")

    response = requests.get(url, headers=headers)
    print(f"🔍 Debug - Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Conexão com API funcionando!")
        return True
    elif response.status_code == 404:
        print("⚠️  Status 404 - Loja ainda não publicada ou API indisponível")
        print("   Isso é normal para lojas em desenvolvimento.")
        return False
    elif response.status_code == 401:
        print("❌ Status 401 - Token de acesso inválido ou sem permissões")
        return False
    else:
        print(f"❌ Erro: {response.text[:200]}")
        return False


def conectar_shopify():
    """Estabelece conexão com a API da Shopify."""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")

    if not store_url or not access_token:
        print("❌ Erro: Configure SHOPIFY_STORE_URL e SHOPIFY_ACCESS_TOKEN no arquivo .env")
        return False

    shop_url = f"https://{store_url}/admin/api/{api_version}"
    shopify.ShopifyResource.set_site(shop_url)
    shopify.ShopifyResource.set_headers({
        "X-Shopify-Access-Token": access_token
    })

    return True


def listar_produtos():
    """Lista os produtos da loja."""
    try:
        produtos = shopify.Product.find()
        print(f"\n📦 Total de produtos encontrados: {len(produtos)}\n")
        for produto in produtos:
            print(f"  • {produto.title}")
        return produtos
    except Exception as e:
        print(f"❌ Erro ao listar produtos: {e}")
        return []


def obter_info_loja():
    """Obtém informações da loja."""
    try:
        loja = shopify.Shop.current()
        print(f"\n🏪 Informações da Loja:")
        print(f"  • Nome: {loja.name}")
        print(f"  • Email: {loja.email}")
        print(f"  • Domínio: {loja.domain}")
        return loja
    except Exception as e:
        print(f"❌ Erro ao obter informações da loja: {e}")
        return None


def main():
    print("=" * 50)
    print("🚀 Shopify Automation")
    print("=" * 50)

    # Teste de conexão direta para debug
    api_disponivel = testar_conexao_direta()

    if not api_disponivel:
        print("\n" + "=" * 50)
        print("📋 Próximos passos:")
        print("   1. Publique sua loja no Shopify Admin")
        print("   2. Verifique se o token tem permissões de leitura")
        print("   3. Execute novamente este script")
        print("=" * 50)
        return

    if conectar_shopify():
        print("✅ Conectado à Shopify com sucesso!")

        # Obtém informações da loja
        obter_info_loja()

        # Lista produtos
        listar_produtos()
    else:
        print("❌ Falha na conexão com a Shopify")


if __name__ == "__main__":
    main()
