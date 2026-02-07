#!/usr/bin/env python3
"""
🚀 Script Principal de Pós-Processamento de Produtos
Transforma produtos brutos em listagens profissionais

Funcionalidades:
1. Processa imagens (aesthetic clean)
2. Gera conteúdo com Gemini IA
3. Calcula preços corretos (markup 2.5)
4. Atualiza na Shopify
"""
import os
import sys
import time
import json
import logging
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.media.image_processor import AestheticImageProcessor
from src.ai.content_generator import GeminiContentGenerator
from src.pricing.advanced_calculator import AdvancedPriceCalculator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ShopifyEnhancer:
    """Melhora produtos existentes na Shopify"""

    def __init__(self, dry_run: bool = False):
        self.store = os.getenv('SHOPIFY_STORE_URL')
        self.token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.api_version = os.getenv('SHOPIFY_API_VERSION', '2024-01')
        self.base_url = f'https://{self.store}/admin/api/{self.api_version}'
        self.headers = {
            'X-Shopify-Access-Token': self.token,
            'Content-Type': 'application/json'
        }

        self.image_processor = AestheticImageProcessor()
        self.content_generator = GeminiContentGenerator()
        self.price_calculator = AdvancedPriceCalculator()

        self.dry_run = dry_run
        self.stats = {
            'processados': 0,
            'sucesso': 0,
            'erros': 0,
            'inicio': datetime.now()
        }

        # Verificar conexão
        self._verificar_conexao()

    def _verificar_conexao(self):
        """Verifica conexão com Shopify"""
        try:
            r = requests.get(f'{self.base_url}/shop.json', headers=self.headers)
            if r.status_code == 200:
                shop = r.json()['shop']
                logger.info(f"✅ Conectado: {shop['name']}")
            else:
                logger.error(f"❌ Erro de conexão: {r.status_code}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            sys.exit(1)

    def get_products(self, collection_handle: str = None, limit: int = None) -> List[Dict]:
        """Busca produtos da loja"""
        produtos = []

        if collection_handle:
            # Buscar ID da coleção
            url = f'{self.base_url}/smart_collections.json'
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                for c in r.json().get('smart_collections', []):
                    if c['handle'] == collection_handle:
                        url = f'{self.base_url}/products.json?collection_id={c["id"]}&limit=250'
                        break

            # Tentar custom collections também
            url = f'{self.base_url}/custom_collections.json'
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                for c in r.json().get('custom_collections', []):
                    if c['handle'] == collection_handle:
                        url = f'{self.base_url}/products.json?collection_id={c["id"]}&limit=250'
                        break
        else:
            url = f'{self.base_url}/products.json?limit=250'

        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            produtos = r.json().get('products', [])

        if limit:
            produtos = produtos[:limit]

        return produtos

    def process_collection(self, collection: str = None, limit: int = None):
        """Processa todos os produtos de uma coleção"""
        print("\n" + "="*60)
        print("🚀 PÓS-PROCESSAMENTO DE PRODUTOS")
        print("="*60)

        if self.dry_run:
            print("⚠️  MODO DRY-RUN: Nenhuma alteração será feita")

        print(f"📦 Buscando produtos...")
        produtos = self.get_products(collection, limit)
        print(f"   Encontrados: {len(produtos)} produtos\n")

        for idx, produto in enumerate(produtos, 1):
            print(f"\n{'─'*60}")
            print(f"[{idx}/{len(produtos)}] {produto['title'][:50]}...")
            print(f"{'─'*60}")

            try:
                resultado = self.process_single_product(produto)

                if resultado['success']:
                    self.stats['sucesso'] += 1
                    print(f"✅ Produto processado com sucesso!")
                else:
                    self.stats['erros'] += 1
                    print(f"❌ Erro: {resultado.get('error', 'Desconhecido')}")

            except Exception as e:
                self.stats['erros'] += 1
                print(f"❌ Exceção: {str(e)}")

            self.stats['processados'] += 1
            time.sleep(1)  # Rate limiting

        self._print_report()

    def process_single_product(self, produto: Dict) -> Dict:
        """Processa um produto individual"""
        pid = produto['id']

        # 1. OBTER IMAGENS
        print("📸 Etapa 1/4: Processando imagens...")
        image_urls = [img['src'] for img in produto.get('images', [])]

        if not image_urls:
            return {'success': False, 'error': 'Produto sem imagens'}

        processed_images = self.image_processor.process_product_images(image_urls)
        print(f"   ✓ {len(processed_images)} imagens processadas")

        # 2. GERAR CONTEÚDO COM GEMINI
        print("🤖 Etapa 2/4: Gerando conteúdo com IA...")

        # Extrair opções atuais
        raw_options = []
        for variant in produto.get('variants', []):
            if variant.get('option1') and variant['option1'] not in raw_options:
                raw_options.append(variant['option1'])

        # Usar primeira imagem processada
        if processed_images:
            new_content = self.content_generator.analyze_product(
                processed_images[0],
                raw_options,
                produto['title']
            )
        else:
            new_content = self.content_generator._fallback_content(raw_options, produto['title'])

        print(f"   ✓ Título: {new_content['titulo'][:50]}...")

        # 3. CALCULAR PREÇO
        print("💰 Etapa 3/4: Calculando preço (markup 2.5)...")

        # Detectar nicho pelo product_type
        product_type = produto.get('product_type', '').lower()
        nicho = 'acessorios'
        for n in ['bolsas', 'brincos', 'colares', 'pulseiras', 'aneis', 'relogios', 'oculos']:
            if n in product_type:
                nicho = n
                break

        # Estimar custo (assumindo que preço atual tem markup errado)
        preco_atual = float(produto['variants'][0].get('price', 100))

        # Se preço > 500, provavelmente está errado - estimar custo real
        if preco_atual > 500:
            custo_estimado = preco_atual / 15  # Assumindo que foi multiplicado ~15x errado
        elif preco_atual > 200:
            custo_estimado = preco_atual / 8
        else:
            custo_estimado = preco_atual / 3

        pricing = self.price_calculator.calcular_preco_final(
            custo_estimado,
            nicho=nicho
        )

        print(f"   ✓ Custo estimado: R$ {custo_estimado:.2f}")
        print(f"   ✓ Preço sugerido: R$ {pricing['preco_sugerido']:.2f}")
        print(f"   ✓ Margem: {pricing['margem_lucro_percentual']:.1f}%")

        # 4. ATUALIZAR NA SHOPIFY
        if not self.dry_run:
            print("📤 Etapa 4/4: Atualizando na Shopify...")

            # Atualizar produto
            update_data = {
                'product': {
                    'id': pid,
                    'title': new_content['titulo'],
                    'body_html': self._format_description(
                        new_content['descricao'],
                        pricing
                    ),
                    'tags': ', '.join(new_content['tags'] + ['processado', 'clean-aesthetic'])
                }
            }

            r = requests.put(
                f'{self.base_url}/products/{pid}.json',
                headers=self.headers,
                json=update_data
            )

            if r.status_code != 200:
                return {'success': False, 'error': f'API: {r.status_code}'}

            # Atualizar variantes (preço + opções traduzidas)
            for idx, variant in enumerate(produto['variants']):
                vid = variant['id']
                variant_data = {
                    'variant': {
                        'id': vid,
                        'price': f"{pricing['preco_sugerido']:.2f}",
                        'compare_at_price': f"{pricing['preco_de']:.2f}"
                    }
                }

                # Traduzir opção se existir
                if idx < len(new_content.get('opcoes_padronizadas', [])):
                    variant_data['variant']['option1'] = new_content['opcoes_padronizadas'][idx]

                r = requests.put(
                    f'{self.base_url}/variants/{vid}.json',
                    headers=self.headers,
                    json=variant_data
                )
                time.sleep(0.2)

            print("   ✓ Produto atualizado!")
        else:
            print("⚠️  Etapa 4/4: PULADA (dry-run)")

        return {'success': True}

    def _format_description(self, descricao: str, pricing: Dict) -> str:
        """Formata descrição HTML com transparência de preços"""
        html = f"""
<div style="font-family: 'Inter', sans-serif; line-height: 1.6;">
    {descricao}
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    
    <h4>🚚 Entrega e Garantia</h4>
    <ul>
        <li>✅ Frete Grátis para todo Brasil</li>
        <li>✅ Prazo de entrega: 15-25 dias úteis</li>
        <li>✅ Garantia de 30 dias</li>
        <li>✅ 7 dias para troca/devolução</li>
    </ul>
    
    <p style="font-weight: bold; color: #2e7d32;">
        💳 Parcele em até 6x de R$ {pricing['parcelamento'][6]['valor']:.2f} sem juros
    </p>
</div>
"""
        return html

    def _print_report(self):
        """Imprime relatório final"""
        duracao = datetime.now() - self.stats['inicio']

        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL")
        print("="*60)
        print(f"Total processados: {self.stats['processados']}")
        print(f"✅ Sucesso: {self.stats['sucesso']}")
        print(f"❌ Erros: {self.stats['erros']}")
        if self.stats['processados'] > 0:
            taxa = (self.stats['sucesso']/self.stats['processados']*100)
            print(f"Taxa de sucesso: {taxa:.1f}%")
        print(f"Duração: {duracao}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Pós-processamento de produtos Shopify')
    parser.add_argument('--collection', '-c', default=None, help='Handle da coleção')
    parser.add_argument('--limit', '-l', type=int, default=None, help='Limite de produtos')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Não fazer alterações')

    args = parser.parse_args()

    enhancer = ShopifyEnhancer(dry_run=args.dry_run)
    enhancer.process_collection(args.collection, args.limit)


if __name__ == '__main__':
    main()

