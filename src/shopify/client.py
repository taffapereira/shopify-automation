"""
Shopify API Client
Cliente para interagir com a Admin API da Shopify
"""
import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class ShopifyClient:
    """Cliente para a Admin API da Shopify"""

    def __init__(self):
        self.store = os.getenv("SHOPIFY_STORE_URL")
        self.token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = os.getenv("SHOPIFY_API_VERSION", "2024-01")
        self.base_url = f"https://{self.store}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.token,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> Optional[Dict[str, Any]]:
        """Faz requisição para a API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erro HTTP: {e}")
            print(f"   Response: {response.text}")
            raise
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise

    # ==================== PRODUTOS ====================

    def get_products(self, limit: int = 50, **params) -> Dict[str, Any]:
        """Lista produtos"""
        params["limit"] = limit
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self._request("GET", f"products.json?{query}")

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Obtém um produto específico"""
        return self._request("GET", f"products/{product_id}.json")

    def update_product(self, product_id: int, data: dict) -> Dict[str, Any]:
        """Atualiza um produto"""
        return self._request("PUT", f"products/{product_id}.json", {"product": data})

    def create_product(self, data: dict) -> Dict[str, Any]:
        """Cria um novo produto"""
        return self._request("POST", "products.json", {"product": data})

    def delete_product(self, product_id: int) -> None:
        """Deleta um produto"""
        self._request("DELETE", f"products/{product_id}.json")

    def get_product_count(self) -> int:
        """Retorna contagem de produtos"""
        result = self._request("GET", "products/count.json")
        return result.get("count", 0)

    # ==================== VARIANTES ====================

    def update_variant(self, variant_id: int, data: dict) -> Dict[str, Any]:
        """Atualiza uma variante"""
        return self._request("PUT", f"variants/{variant_id}.json", {"variant": data})

    # ==================== COLEÇÕES ====================

    def get_smart_collections(self) -> Dict[str, Any]:
        """Lista coleções inteligentes"""
        return self._request("GET", "smart_collections.json")

    def get_custom_collections(self) -> Dict[str, Any]:
        """Lista coleções manuais"""
        return self._request("GET", "custom_collections.json")

    def create_smart_collection(self, data: dict) -> Dict[str, Any]:
        """Cria coleção inteligente (automática)"""
        return self._request("POST", "smart_collections.json", {"smart_collection": data})

    def create_custom_collection(self, data: dict) -> Dict[str, Any]:
        """Cria coleção manual"""
        return self._request("POST", "custom_collections.json", {"custom_collection": data})

    def delete_smart_collection(self, collection_id: int) -> None:
        """Deleta coleção inteligente"""
        self._request("DELETE", f"smart_collections/{collection_id}.json")

    # ==================== PEDIDOS ====================

    def get_orders(self, status: str = "any", limit: int = 50) -> Dict[str, Any]:
        """Lista pedidos"""
        return self._request("GET", f"orders.json?status={status}&limit={limit}")

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Obtém um pedido específico"""
        return self._request("GET", f"orders/{order_id}.json")

    # ==================== INVENTORY ====================

    def get_locations(self) -> Dict[str, Any]:
        """Lista localizações de estoque"""
        return self._request("GET", "locations.json")

    def get_inventory_levels(self, location_id: int) -> Dict[str, Any]:
        """Lista níveis de estoque por localização"""
        return self._request("GET", f"inventory_levels.json?location_ids={location_id}")

    def set_inventory_level(self, location_id: int, inventory_item_id: int, available: int) -> Dict[str, Any]:
        """Define nível de estoque"""
        data = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": available
        }
        return self._request("POST", "inventory_levels/set.json", data)

    # ==================== SHOP ====================

    def get_shop(self) -> Dict[str, Any]:
        """Obtém informações da loja"""
        return self._request("GET", "shop.json")

    # ==================== TEMAS ====================

    def get_themes(self) -> Dict[str, Any]:
        """Lista temas"""
        return self._request("GET", "themes.json")

    # ==================== METAFIELDS ====================

    def get_product_metafields(self, product_id: int) -> Dict[str, Any]:
        """Lista metafields de um produto"""
        return self._request("GET", f"products/{product_id}/metafields.json")

    def create_product_metafield(self, product_id: int, namespace: str, key: str, value: str, type: str = "single_line_text_field") -> Dict[str, Any]:
        """Cria metafield em um produto"""
        data = {
            "metafield": {
                "namespace": namespace,
                "key": key,
                "value": value,
                "type": type
            }
        }
        return self._request("POST", f"products/{product_id}/metafields.json", data)

    # ==================== IMAGENS ====================

    def get_product_images(self, product_id: int) -> List[Dict]:
        """Lista imagens de um produto"""
        result = self._request("GET", f"products/{product_id}/images.json")
        return result.get("images", []) if result else []

    def delete_product_image(self, product_id: int, image_id: int) -> bool:
        """Deleta uma imagem específica de um produto"""
        try:
            self._request("DELETE", f"products/{product_id}/images/{image_id}.json")
            return True
        except Exception as e:
            print(f"      ⚠️ Erro ao deletar imagem {image_id}: {e}")
            return False

    def create_product_image(self, product_id: int, image_base64: str, position: int = 1) -> Optional[Dict]:
        """
        Cria/upload de nova imagem para um produto

        Args:
            product_id: ID do produto
            image_base64: Imagem em base64
            position: Posição da imagem (1 = principal)
        """
        data = {
            "image": {
                "position": position,
                "attachment": image_base64
            }
        }
        try:
            result = self._request("POST", f"products/{product_id}/images.json", data)
            return result.get("image") if result else None
        except Exception as e:
            print(f"      ❌ Erro ao criar imagem: {e}")
            return None

    def replace_product_images(self, product_id: int, processed_images: List[bytes]) -> bool:
        """
        Substitui TODAS as imagens de um produto

        Fluxo:
        1. Busca imagens atuais
        2. Deleta todas as imagens antigas
        3. Faz upload das novas (base64)
        4. Define primeira como principal

        Args:
            product_id: ID do produto Shopify
            processed_images: Lista de imagens em bytes (WebP/JPEG format)

        Returns:
            bool: True se sucesso, False se falha
        """
        import base64
        import time

        try:
            print(f"      🖼️  Substituindo imagens do produto {product_id}...")

            # PASSO 1: Buscar imagens atuais
            current_images = self.get_product_images(product_id)
            old_images_count = len(current_images)

            # PASSO 2: Deletar TODAS as imagens antigas
            if old_images_count > 0:
                print(f"      🗑️  Deletando {old_images_count} imagens antigas...")

                for img in current_images:
                    self.delete_product_image(product_id, img['id'])
                    time.sleep(0.5)  # Rate limiting

                print(f"      ✓ {old_images_count} imagens antigas removidas")

            # PASSO 3: Fazer upload das novas imagens
            print(f"      📤 Enviando {len(processed_images)} novas imagens...")

            uploaded = 0
            for idx, img_bytes in enumerate(processed_images, start=1):
                try:
                    # Converter bytes para base64
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                    # Criar nova imagem via API
                    result = self.create_product_image(product_id, img_base64, position=idx)

                    if result:
                        uploaded += 1
                        print(f"         ✓ Imagem {idx}/{len(processed_images)} enviada")
                    else:
                        print(f"         ❌ Falha ao enviar imagem {idx}")

                    # Rate limiting (Shopify limita a 2 req/segundo)
                    time.sleep(0.6)

                except Exception as e:
                    print(f"         ❌ Erro ao enviar imagem {idx}: {e}")

            success = uploaded == len(processed_images)

            if success:
                print(f"      ✅ {uploaded}/{len(processed_images)} imagens enviadas com sucesso")
            else:
                print(f"      ⚠️ Apenas {uploaded}/{len(processed_images)} imagens foram enviadas")

            return success

        except Exception as e:
            print(f"      ❌ Erro crítico ao substituir imagens: {e}")
            import traceback
            traceback.print_exc()
            return False


# Teste rápido
if __name__ == "__main__":
    client = ShopifyClient()
    try:
        shop = client.get_shop()
        print(f"✅ Conectado à loja: {shop['shop']['name']}")
        print(f"   Email: {shop['shop']['email']}")
        print(f"   Domínio: {shop['shop']['domain']}")
    except Exception as e:
        print(f"❌ Falha na conexão: {e}")

