"""
🤖 Automação DSers
Automatiza login, adição de produtos e sincronização com Shopify
"""
import os
import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class DSersConfig:
    """Configurações do DSers"""
    email: str = ""
    password: str = ""
    base_url: str = "https://www.dsers.com"
    login_url: str = "https://www.dsers.com/login"
    import_url: str = "https://www.dsers.com/import-list"

    def __post_init__(self):
        self.email = os.getenv("DSERS_EMAIL", "")
        self.password = os.getenv("DSERS_PASSWORD", "")


class DSersAutomation:
    """Automação do DSers via Selenium"""

    def __init__(self, headless: bool = False):
        """
        Inicializa automação DSers

        Args:
            headless: True para rodar sem interface gráfica
        """
        self.config = DSersConfig()
        self.headless = headless
        self.driver = None
        self.logged_in = False

        if not self.config.email or not self.config.password:
            logger.warning("⚠️ Credenciais DSers não configuradas no .env")

    def _init_driver(self):
        """Inicializa Chrome driver"""
        if self.driver:
            return

        options = Options()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        # Evita detecção de automação
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.info("✅ Chrome driver inicializado para DSers")

    def login(self) -> bool:
        """
        Faz login no DSers

        Returns:
            True se login bem sucedido
        """
        if self.logged_in:
            return True

        if not self.config.email or not self.config.password:
            logger.error("❌ Credenciais DSers não configuradas")
            return False

        self._init_driver()

        try:
            logger.info("🔐 Fazendo login no DSers...")
            self.driver.get(self.config.login_url)
            time.sleep(3)

            # Email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.clear()
            email_input.send_keys(self.config.email)

            # Password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.config.password)

            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()

            # Aguarda dashboard carregar
            time.sleep(5)

            # Verifica se logou
            if "dashboard" in self.driver.current_url or "import" in self.driver.current_url:
                self.logged_in = True
                logger.info("✅ Login no DSers bem sucedido!")
                return True
            else:
                logger.error("❌ Falha no login - verifique credenciais")
                return False

        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            return False

    def adicionar_produto_por_url(self, aliexpress_url: str) -> bool:
        """
        Adiciona um produto do AliExpress ao DSers pela URL

        Args:
            aliexpress_url: URL do produto no AliExpress

        Returns:
            True se adicionado com sucesso
        """
        if not self.logged_in:
            if not self.login():
                return False

        try:
            logger.info(f"📦 Adicionando produto: {aliexpress_url[:50]}...")

            # Vai para página de importação
            self.driver.get(self.config.import_url)
            time.sleep(3)

            # Procura campo de URL
            url_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='AliExpress']"))
            )
            url_input.clear()
            url_input.send_keys(aliexpress_url)

            # Clica em importar
            import_btn = self.driver.find_element(By.CSS_SELECTOR, "button.import-btn")
            import_btn.click()

            time.sleep(5)

            logger.info("✅ Produto adicionado à lista de importação!")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao adicionar produto: {e}")
            return False

    def push_to_shopify(self, product_ids: List[str] = None) -> bool:
        """
        Envia produtos para a Shopify

        Args:
            product_ids: Lista de IDs ou None para todos pendentes

        Returns:
            True se enviado com sucesso
        """
        if not self.logged_in:
            if not self.login():
                return False

        try:
            logger.info("🚀 Enviando produtos para Shopify...")

            # Vai para lista de importação
            self.driver.get(self.config.import_url)
            time.sleep(3)

            # Seleciona todos os produtos pendentes
            select_all = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'].select-all")
            if not select_all.is_selected():
                select_all.click()

            time.sleep(1)

            # Clica em Push to Shopify
            push_btn = self.driver.find_element(By.CSS_SELECTOR, "button.push-to-shopify")
            push_btn.click()

            time.sleep(5)

            logger.info("✅ Produtos enviados para Shopify!")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar para Shopify: {e}")
            return False

    def adicionar_e_sincronizar(self, produtos: List[Dict]) -> Dict:
        """
        Adiciona lista de produtos e sincroniza com Shopify

        Args:
            produtos: Lista de produtos com 'product_url'

        Returns:
            Dict com estatísticas
        """
        stats = {
            "total": len(produtos),
            "adicionados": 0,
            "falhas": 0,
        }

        for produto in produtos:
            url = produto.get('product_url', '')
            if url:
                if self.adicionar_produto_por_url(url):
                    stats["adicionados"] += 1
                else:
                    stats["falhas"] += 1
                time.sleep(2)  # Delay entre produtos

        # Push para Shopify
        if stats["adicionados"] > 0:
            self.push_to_shopify()

        return stats

    def close(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False

    def __del__(self):
        self.close()

