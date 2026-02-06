"""
Módulo para gerenciamento de pedidos na Shopify.
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
# PEDIDOS
# =============================================================================

def listar_pedidos(status="any", limit=50):
    """
    Lista pedidos da loja.

    Args:
        status: 'open', 'closed', 'cancelled', 'any'
        limit: Número máximo de pedidos
    """
    url = get_api_url(f"orders.json?status={status}&limit={limit}")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        pedidos = response.json().get("orders", [])
        print(f"\n📋 {len(pedidos)} pedidos encontrados:\n")
        for p in pedidos:
            print(f"  #{p['order_number']} - {p['customer']['first_name'] if p.get('customer') else 'N/A'} - R$ {p['total_price']} - {p['financial_status']}")
        return pedidos
    else:
        print(f"❌ Erro ao listar pedidos: {response.text}")
        return []


def obter_pedido(order_id):
    """Obtém detalhes de um pedido específico."""
    url = get_api_url(f"orders/{order_id}.json")
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        pedido = response.json().get("order")
        print(f"\n📋 Pedido #{pedido['order_number']}")
        print(f"   Cliente: {pedido['customer']['first_name'] if pedido.get('customer') else 'N/A'}")
        print(f"   Total: R$ {pedido['total_price']}")
        print(f"   Status Financeiro: {pedido['financial_status']}")
        print(f"   Status Fulfillment: {pedido['fulfillment_status'] or 'Não enviado'}")
        print(f"\n   Itens:")
        for item in pedido.get("line_items", []):
            print(f"     • {item['quantity']}x {item['title']} - R$ {item['price']}")
        return pedido
    else:
        print(f"❌ Erro ao obter pedido: {response.text}")
        return None


def cancelar_pedido(order_id, motivo="customer", restock=True):
    """
    Cancela um pedido.

    Args:
        order_id: ID do pedido
        motivo: 'customer', 'fraud', 'inventory', 'declined', 'other'
        restock: Se deve retornar itens ao estoque
    """
    url = get_api_url(f"orders/{order_id}/cancel.json")

    payload = {
        "reason": motivo,
        "restock": restock
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        print(f"✅ Pedido {order_id} cancelado!")
        return response.json().get("order")
    else:
        print(f"❌ Erro ao cancelar pedido: {response.text}")
        return None


def fechar_pedido(order_id):
    """Fecha um pedido (marca como completo)."""
    url = get_api_url(f"orders/{order_id}/close.json")
    response = requests.post(url, headers=get_headers())

    if response.status_code == 200:
        print(f"✅ Pedido {order_id} fechado!")
        return response.json().get("order")
    else:
        print(f"❌ Erro ao fechar pedido: {response.text}")
        return None


def reabrir_pedido(order_id):
    """Reabre um pedido fechado."""
    url = get_api_url(f"orders/{order_id}/open.json")
    response = requests.post(url, headers=get_headers())

    if response.status_code == 200:
        print(f"✅ Pedido {order_id} reaberto!")
        return response.json().get("order")
    else:
        print(f"❌ Erro ao reabrir pedido: {response.text}")
        return None


def adicionar_nota_pedido(order_id, nota):
    """Adiciona uma nota interna ao pedido."""
    url = get_api_url(f"orders/{order_id}.json")

    payload = {
        "order": {
            "id": order_id,
            "note": nota
        }
    }

    response = requests.put(url, headers=get_headers(), json=payload)

    if response.status_code == 200:
        print(f"✅ Nota adicionada ao pedido {order_id}")
        return response.json().get("order")
    else:
        print(f"❌ Erro ao adicionar nota: {response.text}")
        return None


# =============================================================================
# FULFILLMENT (ENVIO)
# =============================================================================

def criar_fulfillment(order_id, tracking_number=None, tracking_company=None, notify_customer=True):
    """
    Cria um fulfillment (marca como enviado).

    Args:
        order_id: ID do pedido
        tracking_number: Código de rastreio
        tracking_company: Transportadora
        notify_customer: Se deve notificar o cliente
    """
    # Primeiro, obter fulfillment_order_id
    url_fo = get_api_url(f"orders/{order_id}/fulfillment_orders.json")
    response_fo = requests.get(url_fo, headers=get_headers())

    if response_fo.status_code != 200:
        print(f"❌ Erro ao obter fulfillment orders: {response_fo.text}")
        return None

    fulfillment_orders = response_fo.json().get("fulfillment_orders", [])
    if not fulfillment_orders:
        print("❌ Nenhum fulfillment order encontrado")
        return None

    fo_id = fulfillment_orders[0]["id"]
    line_items = [{"fulfillment_order_id": fo_id}]

    url = get_api_url("fulfillments.json")

    payload = {
        "fulfillment": {
            "line_items_by_fulfillment_order": line_items,
            "notify_customer": notify_customer
        }
    }

    if tracking_number:
        payload["fulfillment"]["tracking_info"] = {
            "number": tracking_number,
            "company": tracking_company or "Outro"
        }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        print(f"✅ Pedido {order_id} marcado como enviado!")
        if tracking_number:
            print(f"   Rastreio: {tracking_number}")
        return response.json().get("fulfillment")
    else:
        print(f"❌ Erro ao criar fulfillment: {response.text}")
        return None


# =============================================================================
# EXEMPLOS DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("📋 Gerenciador de Pedidos Shopify")
    print("=" * 50)

    # Exemplo: Listar pedidos
    # listar_pedidos(status="open")

    # Exemplo: Obter detalhes de um pedido
    # obter_pedido(123456789)

    # Exemplo: Marcar como enviado
    # criar_fulfillment(123456789, tracking_number="BR123456789", tracking_company="Correios")

    print("\n📝 Descomente os exemplos acima para testar!")
