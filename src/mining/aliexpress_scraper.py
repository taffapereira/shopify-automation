"""
🔍 AliExpress Scraper
Busca e coleta produtos do AliExpress para mineração
"""
import os
import time
import random
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import requests

from .criteria import CriteriosMineracao, validar_produto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProdutoAliExpress:
    """Dados de um produto do AliExpress"""
    product_id: str
    title: str
    price: float
    original_price: float
    orders: int
    rating: float
    reviews: int
    store_name: str
    store_rating: float
    shipping_days: int
    shipping_cost: float
    image_url: str
    product_url: str
    category: str


class AliExpressScraper:
    """Scraper para mineração de produtos no AliExpress"""

    BASE_URL = "https://www.aliexpress.com"
    DS_CENTER_URL = "https://dropshipping.aliexpress.com"

    # Mapeamento de categorias para URLs
    CATEGORIAS = {
        "jewelry": "/category/200001679/jewelry-accessories.html",
        "watches": "/category/200034143/watches.html",
        "bags": "/category/200010063/luggage-bags.html",
        "sunglasses": "/category/200095142/eyewear-accessories.html",
        "accessories": "/category/200001616/fashion-accessories.html",
        "earrings": "/category/200001574/earrings.html",
        "necklaces": "/category/200001578/necklaces-pendants.html",
        "bracelets": "/category/200001573/bracelets-bangles.html",
        "rings": "/category/200001580/rings.html",
    }

    def __init__(self, headless: bool = True):
        """
        Inicializa o scraper

        Args:
            headless: Rodar Chrome em modo headless (sem interface)
        """
        self.headless = headless
        self.driver = None
        self.criterios = CriteriosMineracao()

    def _init_driver(self):
        """Inicializa o driver do Chrome"""
        if self.driver is not None:
            return

        options = Options()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Desabilita detecção de automação
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.info("✅ Chrome driver inicializado")

    def _close_driver(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _random_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Delay aleatório para parecer mais humano"""
        time.sleep(random.uniform(min_sec, max_sec))

    def buscar_categoria(self, categoria: str, max_produtos: int = 20) -> List[Dict]:
        """
        Busca produtos de uma categoria

        Args:
            categoria: Nome da categoria (ex: "jewelry")
            max_produtos: Máximo de produtos a retornar

        Returns:
            Lista de produtos encontrados
        """
        if categoria not in self.CATEGORIAS:
            logger.error(f"❌ Categoria não encontrada: {categoria}")
            return []

        self._init_driver()
        produtos = []

        try:
            url = f"{self.BASE_URL}{self.CATEGORIAS[categoria]}?sortType=total_tranpro_desc"
            logger.info(f"🔍 Buscando: {url}")

            self.driver.get(url)
            self._random_delay(2, 4)

            # Aguarda carregamento
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-item-card-wrapper-gallery"))
            )

            # Scroll para carregar mais produtos
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_delay(1, 2)

            # Parse do HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            cards = soup.find_all(class_="search-item-card-wrapper-gallery")

            logger.info(f"📦 Encontrados {len(cards)} produtos")

            for card in cards[:max_produtos * 2]:  # Busca mais para filtrar depois
                try:
                    produto = self._parse_product_card(card, categoria)
                    if produto:
                        # Valida contra critérios
                        aprovado, motivos = validar_produto(produto, self.criterios)
                        if aprovado:
                            produtos.append(produto)
                            logger.info(f"✅ Aprovado: {produto['title'][:50]}...")
                        else:
                            logger.debug(f"❌ Reprovado: {motivos[0]}")

                        if len(produtos) >= max_produtos:
                            break

                except Exception as e:
                    logger.debug(f"Erro ao parsear produto: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Erro ao buscar categoria: {e}")

        logger.info(f"✅ {len(produtos)} produtos aprovados de {categoria}")
        return produtos

    def _parse_product_card(self, card, categoria: str) -> Optional[Dict]:
        """Extrai dados de um card de produto"""
        try:
            # Título
            title_elem = card.find(class_="multi--titleText--nXeOvyr")
            title = title_elem.text.strip() if title_elem else "Sem título"

            # Preço
            price_elem = card.find(class_="multi--price-sale--U-S0jtj")
            price_text = price_elem.text if price_elem else "0"
            price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)) or 0)

            # Pedidos
            orders_elem = card.find(class_="multi--trade--Ktbl2jB")
            orders_text = orders_elem.text if orders_elem else "0"
            orders = int(''.join(filter(str.isdigit, orders_text)) or 0)

            # Rating
            rating_elem = card.find(class_="multi--starValue--3bDWCw3")
            rating = float(rating_elem.text) if rating_elem else 0

            # URL
            link_elem = card.find("a")
            product_url = link_elem.get("href", "") if link_elem else ""
            if product_url and not product_url.startswith("http"):
                product_url = f"https:{product_url}"

            # Extrai product_id da URL
            product_id = ""
            if "/item/" in product_url:
                product_id = product_url.split("/item/")[1].split(".")[0]

            # Imagem
            img_elem = card.find("img")
            image_url = img_elem.get("src", "") if img_elem else ""
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}"

            return {
                "product_id": product_id,
                "title": title,
                "price": price,
                "original_price": price * 1.2,  # Estimativa
                "orders": orders,
                "rating": rating,
                "reviews": int(orders * 0.1),  # Estimativa
                "store_name": "AliExpress Seller",
                "store_rating": 96.0,  # Estimativa
                "shipping_days": 20,  # Estimativa padrão
                "shipping_cost": 0,
                "image_url": image_url,
                "product_url": product_url,
                "category": categoria,
            }

        except Exception as e:
            logger.debug(f"Erro no parse: {e}")
            return None

    def buscar_produto_detalhes(self, product_url: str) -> Optional[Dict]:
        """
        Busca detalhes completos de um produto

        Args:
            product_url: URL do produto no AliExpress

        Returns:
            Dict com detalhes ou None
        """
        self._init_driver()

        try:
            logger.info(f"🔍 Buscando detalhes: {product_url[:60]}...")
            self.driver.get(product_url)
            self._random_delay(2, 4)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extrai informações detalhadas
            # ... (implementação específica)

            return None  # TODO: Implementar extração detalhada

        except Exception as e:
            logger.error(f"❌ Erro ao buscar detalhes: {e}")
            return None

    def buscar_todas_categorias(self, max_por_categoria: int = 10) -> List[Dict]:
        """
        Busca produtos de todas as categorias permitidas

        Args:
            max_por_categoria: Máximo de produtos por categoria

        Returns:
            Lista de todos os produtos encontrados
        """
        todos_produtos = []

        for categoria in self.criterios.categorias_permitidas:
            if categoria in self.CATEGORIAS:
                produtos = self.buscar_categoria(categoria, max_por_categoria)
                todos_produtos.extend(produtos)
                self._random_delay(3, 6)  # Delay entre categorias

        return todos_produtos

    def __del__(self):
        """Cleanup ao destruir objeto"""
        self._close_driver()

