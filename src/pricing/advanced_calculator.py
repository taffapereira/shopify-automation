"""
💰 Calculadora de Preços Avançada
Com impostos de importação, ICMS e markup configurável
"""
import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AdvancedPriceCalculator:
    """
    Calculadora de preços para dropshipping internacional

    Fórmula:
    1. Subtotal (produto)
    2. Frete internacional
    3. Imposto de Importação (II) = 15% × (1+2)
    4. ICMS = 18% × (1+2+3) [por dentro]
    5. Custo Total = 1+2+3+4
    6. Preço de Venda = 5 × Markup (2.5 padrão)
    """

    DEFAULT_CONFIG = {
        'global': {
            'markup': 2.5,
            'imposto_importacao': 0.15,
            'icms': 0.18,
            'frete_padrao': 30.0
        },
        'nichos': {
            'bolsas': {'markup': 2.5, 'frete_padrao': 35.0},
            'brincos': {'markup': 2.5, 'frete_padrao': 15.0},
            'colares': {'markup': 2.5, 'frete_padrao': 18.0},
            'pulseiras': {'markup': 2.5, 'frete_padrao': 15.0},
            'aneis': {'markup': 2.5, 'frete_padrao': 12.0},
            'relogios': {'markup': 2.5, 'frete_padrao': 25.0},
            'oculos': {'markup': 2.5, 'frete_padrao': 20.0},
            'acessorios': {'markup': 2.5, 'frete_padrao': 20.0}
        }
    }

    def __init__(self, config_path: str = 'config/taxas.json'):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuração de taxas"""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar config: {e}. Usando padrão.")

        return self.DEFAULT_CONFIG

    def calcular_preco_final(self,
                            preco_produto: float,
                            frete: float = None,
                            nicho: str = 'acessorios') -> Dict:
        """
        Calcula preço final com todos os impostos

        Args:
            preco_produto: Custo do produto em BRL
            frete: Frete internacional em BRL (usa padrão do nicho se None)
            nicho: Categoria do produto

        Returns:
            Dict com breakdown completo de custos e preço sugerido
        """
        # Obter configurações
        global_config = self.config.get('global', self.DEFAULT_CONFIG['global'])
        nicho_config = self.config.get('nichos', {}).get(nicho.lower(), {})

        markup = nicho_config.get('markup', global_config.get('markup', 2.5))
        ii_rate = global_config.get('imposto_importacao', 0.15)
        icms_rate = global_config.get('icms', 0.18)

        if frete is None:
            frete = nicho_config.get('frete_padrao', global_config.get('frete_padrao', 30.0))

        # 1. Subtotal
        subtotal = preco_produto

        # 2. Frete
        frete_int = frete

        # 3. Imposto de Importação (15% sobre produto + frete)
        base_ii = subtotal + frete_int
        ii = base_ii * ii_rate

        # 4. ICMS (cálculo por dentro: base = produto + frete + II)
        base_icms = subtotal + frete_int + ii
        icms = base_icms * icms_rate / (1 - icms_rate)

        # 5. Custo Total
        custo_total = subtotal + frete_int + ii + icms

        # 6. Preço de Venda
        preco_venda = custo_total * markup

        # 7. Arredondamento psicológico (X,90)
        preco_final = self._arredondar_psicologico(preco_venda)

        # 8. Calcular margem real
        margem_lucro = ((preco_final - custo_total) / preco_final) * 100 if preco_final > 0 else 0

        # 9. Calcular parcelamento
        parcelamento = self._calcular_parcelamento(preco_final)

        return {
            'subtotal': round(subtotal, 2),
            'frete': round(frete_int, 2),
            'imposto_importacao': round(ii, 2),
            'icms': round(icms, 2),
            'custo_total': round(custo_total, 2),
            'markup_aplicado': markup,
            'preco_calculado': round(preco_venda, 2),
            'preco_sugerido': preco_final,
            'preco_de': self._calcular_preco_de(preco_final),
            'margem_lucro_percentual': round(margem_lucro, 2),
            'parcelamento': parcelamento
        }

    def _arredondar_psicologico(self, valor: float) -> float:
        """Arredonda para R$ XX9,90 ou R$ XXX,90"""
        if valor < 50:
            # Arredondar para múltiplo de 10 - 0.10
            return max(29.90, round(valor / 10) * 10 - 0.10)
        elif valor < 200:
            # Arredondar para múltiplo de 10 - 0.10
            return round(valor / 10) * 10 - 0.10
        elif valor < 500:
            # Arredondar para múltiplo de 20 - 0.10
            return round(valor / 20) * 20 - 0.10
        else:
            # Arredondar para múltiplo de 50 - 0.10
            return round(valor / 50) * 50 - 0.10

    def _calcular_preco_de(self, preco: float) -> float:
        """Calcula preço 'de' (30% maior)"""
        preco_de = preco * 1.30
        return round(preco_de / 10) * 10 - 0.10

    def _calcular_parcelamento(self, preco: float) -> Dict:
        """
        Calcula parcelamento em até 12x

        Regras:
        - 1-6x: sem juros
        - 7-12x: juros de 1.99% a.m.
        """
        parcelas = {}
        taxa_juros = 0.0199  # 1.99% ao mês

        for i in range(1, 13):
            if i <= 6:
                # Sem juros
                parcelas[i] = {
                    'valor': round(preco / i, 2),
                    'total': preco,
                    'juros': 0,
                    'texto': f'{i}x de R$ {preco/i:.2f} sem juros'
                }
            else:
                # Com juros (Price)
                fator = (taxa_juros * (1 + taxa_juros)**i) / ((1 + taxa_juros)**i - 1)
                valor_parcela = preco * fator
                total = valor_parcela * i

                parcelas[i] = {
                    'valor': round(valor_parcela, 2),
                    'total': round(total, 2),
                    'juros': round(total - preco, 2),
                    'texto': f'{i}x de R$ {valor_parcela:.2f}'
                }

        return parcelas

    def estimar_custo_aliexpress(self, preco_atual_loja: float,
                                 markup_estimado: float = 2.5) -> float:
        """
        Estima o custo original do produto no AliExpress
        baseado no preço atual da loja

        Útil para corrigir preços de produtos já importados
        """
        # Se o preço está muito alto, provavelmente foi calculado errado
        # Estimar custo como: preco_atual / markup / (1 + impostos)
        fator_impostos = 1 + 0.15 + 0.18  # ~1.33
        custo_estimado = preco_atual_loja / markup_estimado / fator_impostos

        return round(custo_estimado, 2)

