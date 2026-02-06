"""
🎯 Critérios de Mineração de Produtos
Define os critérios para filtrar produtos vencedores
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class CriteriosMineracao:
    """Critérios para mineração de produtos"""

    # Métricas mínimas
    min_pedidos: int = 500
    min_rating: float = 4.5
    min_reviews: int = 100
    min_rating_fornecedor: float = 95.0

    # Faixa de preço (USD)
    preco_min: float = 5.0
    preco_max: float = 30.0

    # Margem e markup
    margem_minima: float = 0.5  # 50%
    markup_padrao: float = 2.5

    # Envio
    max_dias_envio: int = 30
    metodos_envio_preferidos: List[str] = field(default_factory=lambda: [
        "ePacket",
        "AliExpress Standard Shipping",
        "Yanwen Economic Air Mail",
    ])

    # Categorias permitidas
    categorias_permitidas: List[str] = field(default_factory=lambda: [
        "jewelry",
        "watches",
        "bags",
        "sunglasses",
        "accessories",
    ])

    # Palavras-chave a evitar (produtos problemáticos)
    keywords_evitar: List[str] = field(default_factory=lambda: [
        "replica",
        "fake",
        "copy",
        "brand",
        "nike",
        "adidas",
        "gucci",
        "louis vuitton",
        "rolex",
        "battery",
        "liquid",
        "aerosol",
    ])


@dataclass
class TabelaMarkup:
    """Tabela de markup por faixa de custo"""

    faixas: List[tuple] = field(default_factory=lambda: [
        (5.0, 4.0),     # Custo até $5 → markup 4x
        (10.0, 3.5),    # Custo até $10 → markup 3.5x
        (15.0, 3.0),    # Custo até $15 → markup 3x
        (25.0, 2.5),    # Custo até $25 → markup 2.5x
        (50.0, 2.2),    # Custo até $50 → markup 2.2x
        (float('inf'), 2.0),  # Acima → markup 2x
    ])

    def get_markup(self, custo: float) -> float:
        """Retorna markup para um custo"""
        for limite, markup in self.faixas:
            if custo <= limite:
                return markup
        return 2.0

    def calcular_preco_venda(self, custo: float, frete: float = 0) -> float:
        """Calcula preço de venda com markup"""
        custo_total = custo + frete
        markup = self.get_markup(custo_total)
        return round(custo_total * markup, 2)


def validar_produto(produto: dict, criterios: CriteriosMineracao = None) -> tuple:
    """
    Valida se um produto atende aos critérios de mineração

    Args:
        produto: Dict com dados do produto
        criterios: Critérios de validação (usa padrão se None)

    Returns:
        (aprovado: bool, motivos: list)
    """
    if criterios is None:
        criterios = CriteriosMineracao()

    motivos_reprovacao = []

    # Verifica pedidos
    pedidos = produto.get('orders', 0)
    if pedidos < criterios.min_pedidos:
        motivos_reprovacao.append(f"Pedidos insuficientes: {pedidos} < {criterios.min_pedidos}")

    # Verifica rating
    rating = produto.get('rating', 0)
    if rating < criterios.min_rating:
        motivos_reprovacao.append(f"Rating baixo: {rating} < {criterios.min_rating}")

    # Verifica reviews
    reviews = produto.get('reviews', 0)
    if reviews < criterios.min_reviews:
        motivos_reprovacao.append(f"Poucos reviews: {reviews} < {criterios.min_reviews}")

    # Verifica preço
    preco = produto.get('price', 0)
    if preco < criterios.preco_min:
        motivos_reprovacao.append(f"Preço muito baixo: ${preco}")
    if preco > criterios.preco_max:
        motivos_reprovacao.append(f"Preço muito alto: ${preco}")

    # Verifica tempo de envio
    dias_envio = produto.get('shipping_days', 99)
    if dias_envio > criterios.max_dias_envio:
        motivos_reprovacao.append(f"Envio lento: {dias_envio} dias")

    # Verifica keywords proibidas
    titulo = produto.get('title', '').lower()
    for keyword in criterios.keywords_evitar:
        if keyword in titulo:
            motivos_reprovacao.append(f"Keyword proibida: {keyword}")
            break

    aprovado = len(motivos_reprovacao) == 0
    return aprovado, motivos_reprovacao

