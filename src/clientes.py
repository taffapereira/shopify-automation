"""
Módulo para gerenciamento de clientes na Shopify.
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
# CLIENTES - CRUD
# =============================================================================

def listar_clientes(limit=50):
    """Lista todos os clientes da loja."""
    url = get_api_url(f"customers.json?limit={limit}")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        clientes = response.json().get("customers", [])
        print(f"\n👥 {len(clientes)} clientes encontrados:\n")
        for c in clientes:
            nome = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or "Sem nome"
            print(f"  [{c['id']}] {nome} - {c.get('email', 'Sem email')}")
            print(f"      Pedidos: {c.get('orders_count', 0)} | Total gasto: R$ {c.get('total_spent', '0.00')}")
        return clientes
    else:
        print(f"❌ Erro ao listar clientes: {response.text}")
        return []


def obter_cliente(customer_id):
    """Obtém detalhes de um cliente específico."""
    url = get_api_url(f"customers/{customer_id}.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        cliente = response.json().get("customer")
        print(f"\n👤 Cliente: {cliente.get('first_name', '')} {cliente.get('last_name', '')}")
        print(f"   ID: {cliente['id']}")
        print(f"   Email: {cliente.get('email', 'N/A')}")
        print(f"   Telefone: {cliente.get('phone', 'N/A')}")
        print(f"   Pedidos: {cliente.get('orders_count', 0)}")
        print(f"   Total gasto: R$ {cliente.get('total_spent', '0.00')}")
        print(f"   Aceita marketing: {'Sim' if cliente.get('accepts_marketing') else 'Não'}")

        if cliente.get("default_address"):
            addr = cliente["default_address"]
            print(f"\n   📍 Endereço padrão:")
            print(f"      {addr.get('address1', '')}")
            print(f"      {addr.get('city', '')} - {addr.get('province', '')}")
            print(f"      {addr.get('zip', '')} - {addr.get('country', '')}")

        return cliente
    else:
        print(f"❌ Erro ao obter cliente: {response.text}")
        return None


def criar_cliente(email, primeiro_nome="", ultimo_nome="", telefone=None, aceita_marketing=False):
    """
    Cria um novo cliente.

    Args:
        email: Email do cliente
        primeiro_nome: Primeiro nome
        ultimo_nome: Sobrenome
        telefone: Telefone (formato: +5511999999999)
        aceita_marketing: Se aceita receber marketing
    """
    url = get_api_url("customers.json")

    payload = {
        "customer": {
            "email": email,
            "first_name": primeiro_nome,
            "last_name": ultimo_nome,
            "accepts_marketing": aceita_marketing
        }
    }

    if telefone:
        payload["customer"]["phone"] = telefone

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        cliente = response.json().get("customer")
        print(f"✅ Cliente criado: {cliente['email']} (ID: {cliente['id']})")
        return cliente
    else:
        print(f"❌ Erro ao criar cliente: {response.text}")
        return None


def atualizar_cliente(customer_id, **kwargs):
    """
    Atualiza um cliente existente.

    Args:
        customer_id: ID do cliente
        **kwargs: Campos a atualizar (email, first_name, last_name, phone, etc.)
    """
    url = get_api_url(f"customers/{customer_id}.json")

    payload = {"customer": {"id": customer_id, **kwargs}}

    response = requests.put(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        cliente = response.json().get("customer")
        print(f"✅ Cliente atualizado: {cliente['email']}")
        return cliente
    else:
        print(f"❌ Erro ao atualizar cliente: {response.text}")
        return None


def deletar_cliente(customer_id):
    """Remove um cliente da loja."""
    url = get_api_url(f"customers/{customer_id}.json")
    response = requests.delete(url, headers=get_headers())

    if response.status_code == 200:
        print(f"✅ Cliente {customer_id} removido com sucesso!")
        return True
    else:
        print(f"❌ Erro ao deletar cliente: {response.text}")
        return False


def buscar_clientes(query):
    """
    Busca clientes por email, nome ou outros critérios.

    Args:
        query: Termo de busca (email, nome, etc.)
    """
    url = get_api_url(f"customers/search.json?query={query}")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        clientes = response.json().get("customers", [])
        print(f"\n🔍 {len(clientes)} clientes encontrados para '{query}':\n")
        for c in clientes:
            nome = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or "Sem nome"
            print(f"  [{c['id']}] {nome} - {c.get('email', 'Sem email')}")
        return clientes
    else:
        print(f"❌ Erro na busca: {response.text}")
        return []


def adicionar_endereco_cliente(customer_id, endereco):
    """
    Adiciona um endereço ao cliente.

    Args:
        customer_id: ID do cliente
        endereco: Dict com address1, city, province, zip, country, etc.
    """
    url = get_api_url(f"customers/{customer_id}/addresses.json")

    payload = {"address": endereco}

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        addr = response.json().get("customer_address")
        print(f"✅ Endereço adicionado ao cliente {customer_id}")
        return addr
    else:
        print(f"❌ Erro ao adicionar endereço: {response.text}")
        return None


def pedidos_do_cliente(customer_id):
    """Lista todos os pedidos de um cliente específico."""
    url = get_api_url(f"customers/{customer_id}/orders.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        pedidos = response.json().get("orders", [])
        print(f"\n📋 {len(pedidos)} pedidos do cliente:\n")
        for p in pedidos:
            print(f"  #{p['order_number']} - R$ {p['total_price']} - {p['financial_status']}")
        return pedidos
    else:
        print(f"❌ Erro ao listar pedidos do cliente: {response.text}")
        return []


# =============================================================================
# EXEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("👥 Gerenciador de Clientes Shopify")
    print("=" * 50)

    # Exemplo: Listar clientes
    # listar_clientes()

    # Exemplo: Criar cliente
    # criar_cliente(
    #     email="cliente@exemplo.com",
    #     primeiro_nome="João",
    #     ultimo_nome="Silva",
    #     telefone="+5511999999999",
    #     aceita_marketing=True
    # )

    # Exemplo: Buscar cliente
    # buscar_clientes("joao@email.com")

    print("\n📝 Descomente os exemplos acima para testar!")
