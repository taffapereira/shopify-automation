"""
🤖 Automação DSers Avançada
Com retry automático, suporte a variantes, logs detalhados
"""
import os
import time
import logging
import json
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def retry(max_attempts=3, delay=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Tentativa {attempt}/{max_attempts}: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
                    else:
                        raise
        return wrapper
    return decorator


@dataclass
class DSersLog:
    timestamp: str
    operacao: str
    url: str
    status: str
    msg: str


class DSersAutomation:
    # URLs corretas do DSers
    LOGIN_URL = "https://accounts.dsers.com/accounts/login?redirect_url=https%3A%2F%2Fwww.dsers.com%2Fapplication%2F"
    IMPORT_URL = "https://www.dsers.com/app/import-list"

    def __init__(self, headless=False):
        self.email = os.getenv("DSERS_EMAIL", "")
        self.password = os.getenv("DSERS_PASSWORD", "")
        self.headless = headless
        self.driver = None
        self.logged_in = False
        self.logs: List[DSersLog] = []

    def _log(self, op, url, status, msg):
        self.logs.append(DSersLog(datetime.now().isoformat(), op, url[:50], status, msg))
        emoji = "✅" if status == "ok" else "❌"
        logger.info(f"{emoji} [{op}] {msg}")

    def _init_driver(self):
        if self.driver:
            return
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=options)
        logger.info("✅ Chrome inicializado")

    @retry(max_attempts=3)
    def login(self) -> bool:
        if self.logged_in:
            return True
        if not self.email:
            logger.error("Email não configurado")
            return False

        self._init_driver()
        logger.info(f"🔗 Acessando DSers...")
        self.driver.get(self.LOGIN_URL)
        time.sleep(6)

        # DSers usa Ant Design - espera input carregar
        try:
            # Espera primeiro input aparecer
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.ant-input"))
            )
            logger.info("✅ Página carregada")

            # Pega todos os inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input.ant-input")

            if len(inputs) >= 2:
                # Primeiro input = email
                inputs[0].clear()
                inputs[0].send_keys(self.email)
                logger.info(f"✅ Email preenchido")
                time.sleep(0.5)

                # Segundo input = senha
                inputs[1].clear()
                inputs[1].send_keys(self.password)
                logger.info(f"✅ Senha preenchida")
                time.sleep(0.5)
            else:
                logger.error(f"❌ Apenas {len(inputs)} inputs encontrados")
                return False

            # Clica no botão LOG IN
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.ant-btn")
            login_btn.click()
            logger.info(f"✅ Botão LOGIN clicado")

        except Exception as e:
            logger.error(f"❌ Erro ao preencher formulário: {e}")
            raise

        time.sleep(10)

        # Verifica se logou
        current_url = self.driver.current_url.lower()
        if any(x in current_url for x in ["dashboard", "import", "application", "app", "my-products"]):
            self.logged_in = True
            self._log("login", "", "ok", "Login OK")
            logger.info("✅ LOGIN DSERS SUCESSO!")
            return True

        logger.warning(f"❌ URL atual não indica login: {current_url[:50]}")
        return False

    @retry(max_attempts=3)
    def adicionar_produto(self, url: str) -> bool:
        if not self.logged_in and not self.login():
            return False

        self.driver.get(self.IMPORT_URL)
        time.sleep(3)

        url_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='AliExpress'], input[type='text']"))
        )
        url_input.clear()
        url_input.send_keys(url)
        time.sleep(1)

        self.driver.find_element(By.CSS_SELECTOR, "button.import-btn, button[type='submit']").click()
        time.sleep(5)

        self._log("add", url, "ok", "Produto adicionado")
        return True

    @retry(max_attempts=2)
    def push_to_shopify(self) -> bool:
        if not self.logged_in and not self.login():
            return False

        self.driver.get(self.IMPORT_URL)
        time.sleep(3)

        try:
            select_all = self.driver.find_element(By.CSS_SELECTOR, "input.select-all")
            if not select_all.is_selected():
                select_all.click()
        except:
            pass

        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, "button.push-to-shopify, .push-btn").click()
        time.sleep(5)

        self._log("push", "", "ok", "Push Shopify OK")
        return True

    def adicionar_e_sincronizar(self, produtos: List[Dict]) -> Dict:
        stats = {"total": len(produtos), "adicionados": 0, "falhas": 0}

        for p in produtos:
            url = p.get("product_url", "")
            if url:
                try:
                    if self.adicionar_produto(url):
                        stats["adicionados"] += 1
                    else:
                        stats["falhas"] += 1
                except:
                    stats["falhas"] += 1
                time.sleep(2)

        if stats["adicionados"] > 0:
            self.push_to_shopify()

        return stats

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False

    def __del__(self):
        self.close()

