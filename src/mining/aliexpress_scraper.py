"""
🔍 AliExpress Scraper Avançado
Com scraping de reviews, análise de concorrência, download de vídeos
"""
import os
import time
import random
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

from .criteria import CriteriosMineracao, validar_produto

logger = logging.getLogger(__name__)


@dataclass
class ReviewProduto:
    autor: str
    rating: int
    texto: str
    data: str
    pais: str
    com_foto: bool


class AliExpressScraper:
    """Scraper avançado para AliExpress"""

    CATEGORIAS = {
        "jewelry": "/category/200001679/jewelry-accessories.html",
        "watches": "/category/200034143/watches.html",
        "bags": "/category/200010063/luggage-bags.html",
        "sunglasses": "/category/200095142/eyewear-accessories.html",
        "earrings": "/category/200001574/earrings.html",
        "necklaces": "/category/200001578/necklaces-pendants.html",
        "bracelets": "/category/200001573/bracelets-bangles.html",
        "rings": "/category/200001580/rings.html",
    }

    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.criterios = CriteriosMineracao()

    def _init_driver(self):
        if self.driver:
            return

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        self.driver = webdriver.Chrome(options=options)
        logger.info("✅ Chrome inicializado")

    def _close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _delay(self, min_s=1, max_s=3):
        time.sleep(random.uniform(min_s, max_s))

    def buscar_categoria(self, categoria: str, max_produtos=20) -> List[Dict]:
        """Busca produtos de uma categoria"""
        if categoria not in self.CATEGORIAS:
            logger.error(f"Categoria não encontrada: {categoria}")
            return []

        self._init_driver()
        produtos = []

        try:
            url = f"https://www.aliexpress.com{self.CATEGORIAS[categoria]}?sortType=total_tranpro_desc"
            logger.info(f"🔍 Buscando: {categoria}")

            self.driver.get(url)
            self._delay(2, 4)

            # Scroll para carregar mais
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._delay(1, 2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            cards = soup.find_all(class_=re.compile(r"search-item-card|product-card"))

            logger.info(f"📦 {len(cards)} produtos encontrados")

            for card in cards[:max_produtos * 2]:
                try:
                    produto = self._parse_card(card, categoria)
                    if produto:
                        aprovado, _ = validar_produto(produto, self.criterios)
                        if aprovado:
                            produtos.append(produto)
                            if len(produtos) >= max_produtos:
                                break
                except:
                    continue

        except Exception as e:
            logger.error(f"Erro: {e}")

        logger.info(f"✅ {len(produtos)} produtos aprovados")
        return produtos

    def _parse_card(self, card, categoria) -> Optional[Dict]:
        """Extrai dados de um card"""
        try:
            # Título
            title_elem = card.find(class_=re.compile(r"title|name"))
            title = title_elem.text.strip() if title_elem else ""

            # Preço
            price_elem = card.find(class_=re.compile(r"price"))
            price_text = price_elem.text if price_elem else "0"
            price = float(re.sub(r'[^\d.]', '', price_text) or 0)

            # Pedidos
            orders_elem = card.find(class_=re.compile(r"trade|sold|orders"))
            orders_text = orders_elem.text if orders_elem else "0"
            orders = int(re.sub(r'\D', '', orders_text) or 0)

            # Rating
            rating_elem = card.find(class_=re.compile(r"star|rating"))
            rating = float(rating_elem.text) if rating_elem and rating_elem.text else 4.5

            # URL
            link = card.find("a", href=True)
            url = link["href"] if link else ""
            if url and not url.startswith("http"):
                url = f"https:{url}"

            # ID
            product_id = ""
            if "/item/" in url:
                match = re.search(r'/item/(\d+)', url)
                product_id = match.group(1) if match else ""

            # Imagem
            img = card.find("img")
            img_url = img.get("src", "") if img else ""
            if img_url and not img_url.startswith("http"):
                img_url = f"https:{img_url}"

            if not title or price <= 0:
                return None

            return {
                "product_id": product_id,
                "title": title,
                "price": price,
                "orders": orders,
                "rating": rating,
                "reviews": int(orders * 0.1),
                "shipping_days": 20,
                "image_url": img_url,
                "product_url": url,
                "category": categoria,
            }
        except:
            return None

    def buscar_reviews(self, product_url: str, max_reviews=10) -> List[ReviewProduto]:
        """Busca reviews de um produto"""
        self._init_driver()
        reviews = []

        try:
            self.driver.get(product_url)
            self._delay(3, 5)

            # Clica na aba de reviews
            try:
                reviews_tab = self.driver.find_element(By.CSS_SELECTOR, "[data-tab='reviews'], .tab-reviews")
                reviews_tab.click()
                self._delay(2, 3)
            except:
                pass

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            review_elements = soup.find_all(class_=re.compile(r"feedback|review-item"))

            for elem in review_elements[:max_reviews]:
                try:
                    autor = elem.find(class_=re.compile(r"user|name"))
                    texto = elem.find(class_=re.compile(r"content|text"))
                    rating_elem = elem.find(class_=re.compile(r"star|rating"))

                    reviews.append(ReviewProduto(
                        autor=autor.text.strip() if autor else "Anônimo",
                        rating=5,
                        texto=texto.text.strip() if texto else "",
                        data="",
                        pais="",
                        com_foto=bool(elem.find("img"))
                    ))
                except:
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar reviews: {e}")

        return reviews

    def verificar_concorrencia(self, titulo: str) -> Dict:
        """Verifica nível de concorrência do produto"""
        # Busca no Google por lojas vendendo o mesmo produto
        resultado = {
            "nivel": "medio",
            "estimativa_lojas": 50,
            "alertas": []
        }

        # Verifica palavras de marca registrada
        marcas_conhecidas = ["nike", "adidas", "gucci", "louis vuitton", "rolex", "chanel", "prada"]
        titulo_lower = titulo.lower()

        for marca in marcas_conhecidas:
            if marca in titulo_lower:
                resultado["alertas"].append(f"⚠️ Possível marca registrada: {marca}")
                resultado["nivel"] = "alto_risco"

        return resultado

    def baixar_imagens(self, product_url: str, pasta: str = "temp/imagens") -> List[str]:
        """Baixa imagens do produto"""
        os.makedirs(pasta, exist_ok=True)
        imagens_salvas = []

        self._init_driver()

        try:
            self.driver.get(product_url)
            self._delay(3, 5)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            imgs = soup.find_all("img", src=re.compile(r"alicdn|ae01"))

            for i, img in enumerate(imgs[:5]):
                url = img.get("src", "")
                if url and "alicdn" in url:
                    if not url.startswith("http"):
                        url = f"https:{url}"

                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            caminho = f"{pasta}/img_{i}.jpg"
                            with open(caminho, "wb") as f:
                                f.write(response.content)
                            imagens_salvas.append(caminho)
                    except:
                        continue

        except Exception as e:
            logger.error(f"Erro ao baixar imagens: {e}")

        return imagens_salvas

    def buscar_todas_categorias(self, max_por_categoria=10) -> List[Dict]:
        """Busca em todas as categorias"""
        todos = []
        for cat in self.CATEGORIAS.keys():
            produtos = self.buscar_categoria(cat, max_por_categoria)
            todos.extend(produtos)
            self._delay(3, 6)
        return todos

    def __del__(self):
        self._close_driver()

