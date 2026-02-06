#!/usr/bin/env python3
"""
🤖 Automação Completa DSers + Claude Opus
Busca produtos no DSers, analisa com IA e envia para Shopify automaticamente
"""
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dsers.automation import DSersAutomation
from src.dashboard import Dashboard
from anthropic import Anthropic
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DSersFullAutomation:
    """Automação completa: DSers + Claude + Shopify"""

    # Categorias para busca
    CATEGORIAS = {
        "jewelry": "joias",
        "earrings": "brincos",
        "necklace": "colares",
        "bracelet": "pulseiras",
        "ring": "aneis",
        "watch": "relogios",
        "sunglasses": "oculos",
        "bag": "bolsas",
    }

    def __init__(self):
        self.dsers = DSersAutomation(headless=False)
        self.dashboard = Dashboard()

        # Claude API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada no .env")

        self.claude = Anthropic(api_key=api_key)
        logger.info("✅ Claude Opus inicializado")

    def analyze_product_with_claude(self, product_data: dict) -> int:
        """Analisa produto com Claude Opus e retorna score 0-100"""
        prompt = f"""Analise este produto de dropshipping para uma loja de acessórios femininos no Brasil.
Dê um score de 0-100 baseado nos critérios abaixo.

PRODUTO:
- Título: {product_data.get('title', 'N/A')}
- Preço: {product_data.get('price', 'N/A')}
- Pedidos: {product_data.get('orders', 'N/A')}
- Rating: {product_data.get('rating', 'N/A')}

CRITÉRIOS:
1. Potencial viral (TikTok/Instagram)
2. Margem de lucro (vender por 2-3x)
3. Qualidade percebida
4. Apelo visual/emocional
5. Não ser produto muito saturado

RESPONDA APENAS com um número inteiro de 0 a 100. Nada mais."""

        try:
            message = self.claude.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()
            # Extrai apenas números
            score = int(''.join(filter(str.isdigit, response[:3])))
            return min(max(score, 0), 100)  # Garante 0-100

        except Exception as e:
            logger.error(f"Erro ao analisar com Claude: {e}")
            return 50  # Score neutro em caso de erro

    def search_and_add_products(self, category: str = "jewelry", min_score: int = 70, quantity: int = 10):
        """
        Busca produtos no DSers, analisa com Claude e adiciona os aprovados

        Args:
            category: Categoria para buscar (jewelry, earrings, watch, etc)
            min_score: Score mínimo para aprovar (0-100)
            quantity: Quantidade de produtos para adicionar
        """
        print("\n" + "="*60)
        print(f"🔍 BUSCANDO {quantity} PRODUTOS: {category.upper()}")
        print(f"📊 Score mínimo: {min_score}/100")
        print("="*60)

        # Login
        if not self.dsers.login():
            print("❌ Falha no login DSers")
            return

        print("✅ Login OK!\n")

        # Vai para Find Supplier
        print("📌 Navegando para Find Supplier...")
        self.dsers.driver.get('https://www.dsers.com/app/find-supplier')
        time.sleep(5)

        # Busca pela categoria
        try:
            search_selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                "input.search-input",
                "input[type='text']"
            ]

            search_box = None
            for selector in search_selectors:
                try:
                    search_box = WebDriverWait(self.dsers.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue

            if search_box:
                search_box.clear()
                search_box.send_keys(category)
                search_box.send_keys(Keys.RETURN)
                print(f"🔍 Buscando: {category}")
                time.sleep(5)
            else:
                print("⚠️ Campo de busca não encontrado, continuando...")

        except Exception as e:
            print(f"⚠️ Erro na busca: {e}")

        added_count = 0
        analyzed_count = 0
        total_minerados = 0

        # Loop principal - busca e analisa produtos
        max_iterations = 20  # Limite de iterações para evitar loop infinito
        iteration = 0

        while added_count < quantity and iteration < max_iterations:
            iteration += 1

            # Pega produtos na tela
            product_selectors = [
                ".product-item",
                "[class*='product-card']",
                "[class*='ProductCard']",
                ".supplier-product",
                "[class*='goods-item']"
            ]

            products = []
            for selector in product_selectors:
                try:
                    products = self.dsers.driver.find_elements(By.CSS_SELECTOR, selector)
                    if products:
                        break
                except:
                    continue

            if not products:
                print("⚠️ Nenhum produto encontrado na página")
                # Tenta rolar para carregar mais
                self.dsers.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(3)
                continue

            # Analisa produtos ainda não vistos
            for product in products[analyzed_count:]:
                try:
                    analyzed_count += 1
                    total_minerados += 1

                    # Extrai dados do produto
                    title = "N/A"
                    price = "N/A"
                    orders = "N/A"
                    rating = "N/A"

                    # Título
                    title_selectors = ["[class*='title']", "h3", "h4", ".name", "[class*='name']"]
                    for sel in title_selectors:
                        try:
                            title = product.find_element(By.CSS_SELECTOR, sel).text.strip()
                            if title:
                                break
                        except:
                            continue

                    # Preço
                    price_selectors = ["[class*='price']", ".price", "span[class*='price']"]
                    for sel in price_selectors:
                        try:
                            price = product.find_element(By.CSS_SELECTOR, sel).text.strip()
                            if price:
                                break
                        except:
                            continue

                    # Pedidos
                    order_selectors = ["[class*='order']", "[class*='sold']", "[class*='sale']"]
                    for sel in order_selectors:
                        try:
                            orders = product.find_element(By.CSS_SELECTOR, sel).text.strip()
                            if orders:
                                break
                        except:
                            continue

                    # Rating
                    rating_selectors = ["[class*='rating']", "[class*='star']", "[class*='score']"]
                    for sel in rating_selectors:
                        try:
                            rating = product.find_element(By.CSS_SELECTOR, sel).text.strip()
                            if rating:
                                break
                        except:
                            continue

                    if title == "N/A" or not title:
                        continue

                    product_data = {
                        'title': title,
                        'price': price,
                        'orders': orders,
                        'rating': rating
                    }

                    print(f"\n📦 [{analyzed_count}] {title[:50]}...")
                    print(f"   💰 {price} | 📊 {orders} | ⭐ {rating}")

                    # Analisa com Claude
                    print(f"   🤖 Analisando com Claude...")
                    score = self.analyze_product_with_claude(product_data)
                    print(f"   📊 Score: {score}/100")

                    if score >= min_score:
                        # Tenta clicar em "Add to Import List"
                        add_selectors = [
                            "button[class*='add']",
                            "[class*='add-btn']",
                            "button[class*='import']",
                            ".add-to-import"
                        ]

                        added = False
                        for sel in add_selectors:
                            try:
                                add_button = product.find_element(By.CSS_SELECTOR, sel)
                                add_button.click()
                                time.sleep(2)
                                added = True
                                break
                            except:
                                continue

                        if added:
                            added_count += 1
                            print(f"   ✅ ADICIONADO! ({added_count}/{quantity})")

                            if added_count >= quantity:
                                break
                        else:
                            print(f"   ⚠️ Botão Add não encontrado")
                    else:
                        print(f"   ⏭️ Ignorado (score < {min_score})")

                except Exception as e:
                    logger.debug(f"Erro ao processar produto: {e}")
                    continue

            # Rola para carregar mais produtos
            self.dsers.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)

        # Registra métricas
        self.dashboard.registrar_mineracao(total_minerados, added_count, min_score)

        print(f"\n{'='*60}")
        print(f"📊 RESULTADO: {added_count} produtos adicionados de {total_minerados} analisados")
        print(f"{'='*60}")

        if added_count > 0:
            self._push_to_shopify()

    def _push_to_shopify(self):
        """Envia produtos da Import List para Shopify"""
        print("\n📋 Navegando para Import List...")
        self.dsers.driver.get('https://www.dsers.com/app/import-list')
        time.sleep(5)

        try:
            # Tenta encontrar e clicar no botão Push
            push_selectors = [
                "//button[contains(text(), 'Push')]",
                "//button[contains(text(), 'Shopify')]",
                "//button[contains(@class, 'push')]",
            ]

            for xpath in push_selectors:
                try:
                    push_button = WebDriverWait(self.dsers.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    push_button.click()
                    print("✅ Push to Shopify iniciado!")
                    time.sleep(3)

                    # Tenta confirmar (se houver modal)
                    confirm_xpaths = [
                        "//button[contains(text(), 'Confirm')]",
                        "//button[contains(text(), 'OK')]",
                        "//button[contains(text(), 'Yes')]"
                    ]

                    for confirm_xpath in confirm_xpaths:
                        try:
                            confirm = self.dsers.driver.find_element(By.XPATH, confirm_xpath)
                            confirm.click()
                            print("✅ Push confirmado!")
                            break
                        except:
                            continue

                    self.dashboard.registrar_sincronizacao(1)
                    break

                except:
                    continue

        except Exception as e:
            print(f"⚠️ Erro ao fazer push: {e}")
            print("   Faça manualmente: Import List > Push to Shopify")

        print("\n⏳ Aguardando 15s para sincronização...")
        time.sleep(15)

    def run_full_cycle(self, categorias: list = None, produtos_por_categoria: int = 3, min_score: int = 70):
        """
        Executa ciclo completo para múltiplas categorias

        Args:
            categorias: Lista de categorias ou None para todas
            produtos_por_categoria: Quantidade por categoria
            min_score: Score mínimo para aprovar
        """
        if not categorias:
            categorias = list(self.CATEGORIAS.keys())

        print("\n" + "="*60)
        print("🚀 CICLO COMPLETO DE AUTOMAÇÃO")
        print("="*60)
        print(f"📁 Categorias: {', '.join(categorias)}")
        print(f"📦 Produtos por categoria: {produtos_por_categoria}")
        print(f"📊 Score mínimo: {min_score}")
        print("="*60)

        for categoria in categorias:
            try:
                self.search_and_add_products(
                    category=categoria,
                    min_score=min_score,
                    quantity=produtos_por_categoria
                )
            except Exception as e:
                print(f"❌ Erro na categoria {categoria}: {e}")
                continue

            time.sleep(5)

        print("\n" + "="*60)
        print("✅ CICLO COMPLETO FINALIZADO!")
        print("="*60)

        self.dashboard.imprimir_dashboard()

    def close(self):
        """Fecha recursos"""
        try:
            self.dsers.close()
        except:
            pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Automação DSers + Claude")
    parser.add_argument("--categoria", "-c", default="jewelry", help="Categoria para buscar")
    parser.add_argument("--quantidade", "-q", type=int, default=5, help="Quantidade de produtos")
    parser.add_argument("--score", "-s", type=int, default=70, help="Score mínimo (0-100)")
    parser.add_argument("--todas", "-t", action="store_true", help="Buscar em todas categorias")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🤖 AUTOMAÇÃO COMPLETA DSERS + CLAUDE OPUS")
    print("="*60)

    bot = DSersFullAutomation()

    try:
        if args.todas:
            bot.run_full_cycle(
                produtos_por_categoria=args.quantidade,
                min_score=args.score
            )
        else:
            bot.search_and_add_products(
                category=args.categoria,
                min_score=args.score,
                quantity=args.quantidade
            )
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        bot.close()
        print("\n✅ Finalizado!")


if __name__ == "__main__":
    main()

