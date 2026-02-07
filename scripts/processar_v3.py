#!/usr/bin/env python3
"""
🛍️ Processador de Produtos Shopify v4
- Títulos 100% em português
- Concordância correta
- Produtos nas coleções certas
- Salva progresso para não repetir
- Variações em português
"""
import sys
import os
import time
import logging
import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# Arquivo para salvar progresso
PROGRESSO_FILE = Path(__file__).parent.parent / "data" / "produtos_processados.json"


class SmartTranslator:
    """Tradutor inteligente EN→PT para produtos"""

    # Títulos prontos por categoria (100% português, concordância correta)
    TITULOS_BASE = {
        "brincos": [
            "Brinco Feminino Elegante",
            "Brinco de Argola Dourado",
            "Brinco Ponto de Luz Cristal",
            "Brinco Pendente Delicado",
            "Brinco Fashion Moderno",
        ],
        "colares": [
            "Colar Feminino Elegante",
            "Colar com Pingente Cristal",
            "Colar Corrente Dourada",
            "Colar Delicado Prata",
            "Colar Fashion Moderno",
        ],
        "pulseiras": [
            "Pulseira Feminina Elegante",
            "Pulseira Bracelete Dourada",
            "Pulseira de Pérolas",
            "Pulseira Aço Inox",
            "Pulseira Fashion Moderna",
        ],
        "aneis": [
            "Anel Feminino Elegante",
            "Anel Solitário Cristal",
            "Anel Dourado Delicado",
            "Anel Prata Fashion",
            "Anel com Pedra Zircônia",
        ],
        "relogios": [
            "Relógio Feminino Elegante",
            "Relógio Dourado Fashion",
            "Relógio Prata Delicado",
            "Relógio Moderno Casual",
            "Relógio Luxo Feminino",
        ],
        "oculos": [
            "Óculos de Sol Feminino",
            "Óculos Fashion Moderno",
            "Óculos Estilo Vintage",
            "Óculos Elegante UV400",
            "Óculos de Sol Luxo",
        ],
        "bolsas": [
            "Bolsa Feminina Elegante",
            "Bolsa de Couro Legítimo",
            "Bolsa Tote Grande",
            "Bolsa Transversal Compacta",
            "Bolsa Bucket Fashion",
        ],
        "carteiras": [
            "Carteira Feminina Compacta",
            "Carteira de Couro",
            "Porta-Cartões Elegante",
            "Carteira Fashion Moderna",
            "Carteira Pequena Delicada",
        ],
    }

    # Adjetivos para complementar (todos femininos/masculinos corretos)
    ADJETIVOS = {
        "brincos": ["Delicado", "Sofisticado", "Luxuoso", "Moderno", "Clássico"],
        "colares": ["Delicado", "Sofisticado", "Luxuoso", "Moderno", "Clássico"],
        "pulseiras": ["Delicada", "Sofisticada", "Luxuosa", "Moderna", "Clássica"],
        "aneis": ["Delicado", "Sofisticado", "Luxuoso", "Moderno", "Clássico"],
        "relogios": ["Delicado", "Sofisticado", "Luxuoso", "Moderno", "Clássico"],
        "oculos": ["Elegante", "Sofisticado", "Luxuoso", "Moderno", "Clássico"],
        "bolsas": ["Elegante", "Sofisticada", "Luxuosa", "Moderna", "Clássica"],
        "carteiras": ["Elegante", "Sofisticada", "Compacta", "Moderna", "Clássica"],
    }

    # Materiais traduzidos
    MATERIAIS = {
        "gold": "Dourado", "golden": "Dourado", "18k": "Banhado Ouro",
        "silver": "Prata", "platinum": "Platinado",
        "crystal": "Cristal", "zirconia": "Zircônia",
        "pearl": "Pérola", "pearls": "Pérolas",
        "leather": "Couro", "genuine leather": "Couro Legítimo",
        "suede": "Camurça", "steel": "Aço Inox",
        "rhinestone": "Strass", "stone": "Pedra",
    }

    # Emojis por categoria
    EMOJIS = {
        "brincos": "✨", "colares": "📿", "pulseiras": "💎",
        "aneis": "💍", "relogios": "⌚", "oculos": "👓",
        "bolsas": "👜", "carteiras": "👛", "acessorios": "🎀"
    }

    def extrair_caracteristicas(self, titulo: str) -> Dict:
        """Extrai características do título original"""
        titulo_lower = titulo.lower()

        caracteristicas = {
            "material": None,
            "cor": None,
            "formato": None,
        }

        # Detecta material
        for en, pt in self.MATERIAIS.items():
            if en in titulo_lower:
                caracteristicas["material"] = pt
                break

        # Detecta cor
        if any(x in titulo_lower for x in ["gold", "golden", "dourad"]):
            caracteristicas["cor"] = "Dourado"
        elif any(x in titulo_lower for x in ["silver", "prata"]):
            caracteristicas["cor"] = "Prata"
        elif any(x in titulo_lower for x in ["rose"]):
            caracteristicas["cor"] = "Rosé"

        # Detecta formato
        if any(x in titulo_lower for x in ["heart", "coração"]):
            caracteristicas["formato"] = "Coração"
        elif any(x in titulo_lower for x in ["flower", "flor"]):
            caracteristicas["formato"] = "Flor"
        elif any(x in titulo_lower for x in ["star", "estrela"]):
            caracteristicas["formato"] = "Estrela"
        elif any(x in titulo_lower for x in ["round", "redond"]):
            caracteristicas["formato"] = "Redondo"
        elif any(x in titulo_lower for x in ["square", "quadrad"]):
            caracteristicas["formato"] = "Quadrado"

        return caracteristicas

    def gerar_titulo(self, titulo_original: str, categoria: str, indice: int = 0) -> str:
        """Gera título 100% em português com concordância correta"""

        # Extrai características do original
        caract = self.extrair_caracteristicas(titulo_original)

        # Pega um título base da categoria
        titulos_base = self.TITULOS_BASE.get(categoria, self.TITULOS_BASE["bolsas"])
        titulo_base = titulos_base[indice % len(titulos_base)]

        # Constrói título com características
        partes = [titulo_base]

        if caract["cor"] and caract["cor"] not in titulo_base:
            partes.append(caract["cor"])

        if caract["material"] and caract["material"] not in titulo_base:
            partes.append(caract["material"])

        if caract["formato"]:
            partes.append(f"Formato {caract['formato']}")

        titulo = " ".join(partes)

        # Adiciona emoji
        emoji = self.EMOJIS.get(categoria, "✨")
        titulo_final = f"{emoji} {titulo}"

        # Limita tamanho
        if len(titulo_final) > 60:
            titulo_final = titulo_final[:57] + "..."

        return titulo_final


class ShopifyProcessorV4:
    """Processador de produtos otimizado v4"""

    CATEGORIAS_MAP = {
        "earring": "brincos", "brinco": "brincos", "hoop": "brincos", "stud": "brincos",
        "necklace": "colares", "colar": "colares", "pendant": "colares", "chain": "colares",
        "bracelet": "pulseiras", "pulseira": "pulseiras", "bangle": "pulseiras", "cuff": "pulseiras",
        "ring": "aneis", "anel": "aneis",
        "watch": "relogios", "relógio": "relogios",
        "sunglasses": "oculos", "glasses": "oculos", "óculos": "oculos",
        "bag": "bolsas", "handbag": "bolsas", "purse": "bolsas", "tote": "bolsas", "bucket": "bolsas",
        "wallet": "carteiras", "card holder": "carteiras",
    }

    # Mapeamento categoria → coleção (handle na Shopify)
    COLECOES = {
        "brincos": "brincos",
        "colares": "colares",
        "pulseiras": "pulseiras",
        "aneis": "aneis",
        "relogios": "relogios",
        "oculos": "oculos",
        "bolsas": "bolsas",
        "carteiras": "carteiras",
    }

    # Tradução de variações
    VARIACOES_PT = {
        # Cores
        "red": "Vermelho", "blue": "Azul", "green": "Verde", "black": "Preto",
        "white": "Branco", "pink": "Rosa", "purple": "Roxo", "yellow": "Amarelo",
        "orange": "Laranja", "brown": "Marrom", "gray": "Cinza", "grey": "Cinza",
        "gold": "Dourado", "silver": "Prata", "rose": "Rosé", "beige": "Bege",
        "navy": "Azul Marinho", "wine": "Vinho", "khaki": "Cáqui",
        "coffee": "Café", "apricot": "Damasco", "champagne": "Champanhe",
        # Tamanhos
        "small": "Pequeno", "medium": "Médio", "large": "Grande",
        "s": "P", "m": "M", "l": "G", "xl": "GG",
        "one size": "Tamanho Único", "free size": "Tamanho Único",
        # Outros
        "gold color": "Cor Dourada", "silver color": "Cor Prata",
        "in golden": "Dourado", "in silver": "Prata",
    }

    def __init__(self):
        self.store_url = os.getenv("SHOPIFY_STORE_URL")
        self.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = os.getenv("SHOPIFY_API_VERSION", "2024-01")

        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        self.translator = SmartTranslator()
        self.markup = float(os.getenv("DEFAULT_MARKUP", "2.5"))
        self.taxa_cambio = 5.5

        # Carrega progresso
        self.processados = self._carregar_progresso()

        # Cache de coleções
        self.colecoes_ids = {}

        logger.info(f"✅ Shopify: {self.store_url}")
        logger.info(f"✅ Já processados: {len(self.processados)} produtos")

    def _carregar_progresso(self) -> set:
        """Carrega IDs de produtos já processados"""
        if PROGRESSO_FILE.exists():
            try:
                with open(PROGRESSO_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get("processados", []))
            except:
                pass
        return set()

    def _salvar_progresso(self, product_id: str):
        """Salva produto como processado"""
        self.processados.add(str(product_id))

        # Garante que o diretório existe
        PROGRESSO_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(PROGRESSO_FILE, 'w') as f:
            json.dump({
                "processados": list(self.processados),
                "ultima_atualizacao": datetime.now().isoformat()
            }, f, indent=2)

    def traduzir_variacao(self, valor: str) -> str:
        """Traduz valor de variação para português"""
        valor_lower = valor.lower().strip()

        # Tenta tradução direta
        if valor_lower in self.VARIACOES_PT:
            return self.VARIACOES_PT[valor_lower]

        # Tenta tradução parcial
        resultado = valor
        for en, pt in self.VARIACOES_PT.items():
            resultado = re.sub(r'\b' + re.escape(en) + r'\b', pt, resultado, flags=re.IGNORECASE)

        # Capitaliza
        return resultado.title()

    def get_products(self) -> List[Dict]:
        """Busca todos produtos"""
        produtos = []
        url = f"{self.base_url}/products.json?limit=250"

        while url:
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                produtos.extend(data.get("products", []))
                link = r.headers.get("Link", "")
                match = re.search(r'<([^>]+)>; rel="next"', link)
                url = match.group(1) if match else None
            else:
                break

        return produtos

    def get_colecoes(self) -> Dict[str, str]:
        """Busca coleções e retorna mapeamento handle → id"""
        if self.colecoes_ids:
            return self.colecoes_ids

        # Smart collections
        url = f"{self.base_url}/smart_collections.json"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            for c in r.json().get("smart_collections", []):
                self.colecoes_ids[c["handle"]] = c["id"]

        # Custom collections
        url = f"{self.base_url}/custom_collections.json"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            for c in r.json().get("custom_collections", []):
                self.colecoes_ids[c["handle"]] = c["id"]

        return self.colecoes_ids

    def adicionar_produto_colecao(self, product_id: str, collection_handle: str) -> bool:
        """Adiciona produto a uma coleção"""
        colecoes = self.get_colecoes()
        collection_id = colecoes.get(collection_handle)

        if not collection_id:
            return False

        url = f"{self.base_url}/collects.json"
        data = {
            "collect": {
                "product_id": product_id,
                "collection_id": collection_id
            }
        }
        r = requests.post(url, headers=self.headers, json=data)
        return r.status_code in [200, 201]

    def update_product(self, product_id: str, data: Dict) -> bool:
        """Atualiza produto"""
        url = f"{self.base_url}/products/{product_id}.json"
        r = requests.put(url, headers=self.headers, json={"product": data})
        return r.status_code == 200

    def update_variant(self, variant_id: str, data: Dict) -> bool:
        """Atualiza variante"""
        url = f"{self.base_url}/variants/{variant_id}.json"
        r = requests.put(url, headers=self.headers, json={"variant": data})
        return r.status_code == 200

    def detectar_categoria(self, titulo: str) -> str:
        """Detecta categoria"""
        titulo_lower = titulo.lower()
        for kw, cat in self.CATEGORIAS_MAP.items():
            if kw in titulo_lower:
                return cat
        return "acessorios"

    def calcular_preco(self, preco_original: float) -> Tuple[float, float]:
        """Calcula preços"""
        if preco_original < 100:
            preco_brl = preco_original * self.taxa_cambio
        else:
            preco_brl = preco_original

        preco_venda = preco_brl * self.markup

        if preco_venda < 50:
            preco_venda = max(29.90, round(preco_venda / 5) * 5 - 0.10)
        elif preco_venda < 200:
            preco_venda = round(preco_venda / 10) * 10 - 0.10
        else:
            preco_venda = round(preco_venda / 50) * 50 - 0.10

        preco_comp = round(preco_venda * 1.4, -1) - 0.10

        return preco_venda, preco_comp

    def gerar_tags(self, titulo: str, categoria: str) -> str:
        """Gera tags - usa formato cat:categoria para Smart Collections"""
        # Tag principal da categoria (formato esperado pelas Smart Collections)
        tags = [f"cat:{categoria}", "feminino", "moda", "twp", "processado"]
        titulo_lower = titulo.lower()

        if any(x in titulo_lower for x in ["gold", "dourad", "ouro", "18k"]):
            tags.append("dourado")
        if any(x in titulo_lower for x in ["silver", "prata"]):
            tags.append("prata")
        if any(x in titulo_lower for x in ["crystal", "cristal", "zirconia"]):
            tags.append("cristal")
        if any(x in titulo_lower for x in ["pearl", "perola"]):
            tags.append("perola")
        if any(x in titulo_lower for x in ["leather", "couro"]):
            tags.append("couro")
        if any(x in titulo_lower for x in ["steel", "aço", "inox"]):
            tags.append("aco-inox")

        return ", ".join(list(set(tags)))

    def gerar_descricao(self, titulo: str, categoria: str) -> str:
        """Gera descrição HTML"""
        # Concordância correta
        cat_descricao = {
            "brincos": ("Este brinco", "brincos"),
            "colares": ("Este colar", "colares"),
            "pulseiras": ("Esta pulseira", "pulseiras"),
            "aneis": ("Este anel", "anéis"),
            "relogios": ("Este relógio", "relógios"),
            "oculos": ("Este óculos", "óculos"),
            "bolsas": ("Esta bolsa", "bolsas"),
            "carteiras": ("Esta carteira", "carteiras"),
            "acessorios": ("Este acessório", "acessórios"),
        }

        artigo, cat_nome = cat_descricao.get(categoria, ("Este produto", "acessórios"))

        return f"""
<h3>✨ {titulo}</h3>

<p>{artigo} foi selecionado especialmente para mulheres que valorizam estilo e elegância. 
Design moderno e sofisticado que combina perfeitamente com qualquer ocasião!</p>

<h4>🎁 Por que você vai amar:</h4>
<ul>
<li>✅ Material de alta qualidade e durabilidade</li>
<li>✅ Acabamento premium com atenção aos detalhes</li>
<li>✅ Design exclusivo que destaca sua beleza</li>
<li>✅ Perfeito para usar no dia a dia ou em ocasiões especiais</li>
<li>✅ Ótima opção de presente para alguém especial</li>
</ul>

<h4>📦 Informações:</h4>
<ul>
<li>Categoria: {cat_nome.capitalize()}</li>
<li>Estilo: Fashion / Elegante</li>
<li>Ocasião: Versátil - Casual, Trabalho, Festa</li>
</ul>

<p>🚚 <strong>Frete Grátis</strong> para todo o Brasil!</p>
<p>🔒 <strong>Compra 100% Segura</strong> - Site protegido</p>
<p>↩️ <strong>7 dias</strong> para troca ou devolução sem complicação</p>
<p>💬 <strong>Suporte</strong> via WhatsApp para tirar suas dúvidas</p>
"""

    def processar_produto(self, produto: Dict, indice: int) -> bool:
        """Processa um produto"""
        pid = str(produto["id"])
        titulo_original = produto.get("title", "")

        # Verifica se já foi processado
        if pid in self.processados:
            print(f"   ⏭️ Já processado, pulando...")
            return True

        # Categoria
        categoria = self.detectar_categoria(titulo_original)

        # Título 100% português
        titulo_novo = self.translator.gerar_titulo(titulo_original, categoria, indice)

        # Descrição com concordância
        descricao = self.gerar_descricao(titulo_novo, categoria)

        # Preço
        variants = produto.get("variants", [])
        preco_original = float(variants[0].get("price", 0)) if variants else 0
        preco_venda, preco_comp = self.calcular_preco(preco_original)

        # Tags
        tags = self.gerar_tags(titulo_original, categoria)

        print(f"\n📦 [{categoria.upper()}] {titulo_original[:35]}...")
        print(f"   → {titulo_novo}")
        print(f"   💰 R$ {preco_venda:.2f} (de R$ {preco_comp:.2f})")

        # Atualiza produto
        update_data = {
            "title": titulo_novo,
            "body_html": descricao,
            "tags": tags,
            "vendor": "TWP Acessórios",
            "product_type": categoria.capitalize(),
        }

        if self.update_product(pid, update_data):
            # Atualiza variantes (preço + tradução)
            for v in variants:
                variant_data = {
                    "id": v["id"],
                    "price": f"{preco_venda:.2f}",
                    "compare_at_price": f"{preco_comp:.2f}"
                }

                # Traduz opções
                if v.get("option1"):
                    variant_data["option1"] = self.traduzir_variacao(v["option1"])
                if v.get("option2"):
                    variant_data["option2"] = self.traduzir_variacao(v["option2"])
                if v.get("option3"):
                    variant_data["option3"] = self.traduzir_variacao(v["option3"])

                self.update_variant(v["id"], variant_data)

            # Smart Collections são automáticas por tag (cat:categoria)
            print(f"   📁 Tag: cat:{categoria} (Smart Collection automática)")

            # Salva progresso
            self._salvar_progresso(pid)

            print(f"   ✅ OK")
            return True
        else:
            print(f"   ❌ ERRO na API")
            return False

    def processar_todos(self, limite: int = None, reprocessar: bool = False):
        """Processa todos os produtos"""
        print("\n" + "="*60)
        print("🛍️ PROCESSANDO PRODUTOS - TWP ACESSÓRIOS v4")
        print("="*60)

        if reprocessar:
            self.processados = set()
            print("⚠️ Modo reprocessar: ignorando progresso anterior")

        produtos = self.get_products()

        # Filtra já processados
        if not reprocessar:
            produtos = [p for p in produtos if str(p["id"]) not in self.processados]

        if limite:
            produtos = produtos[:limite]

        print(f"\n📦 Total: {len(produtos)} produtos para processar")
        print(f"⏭️ Já processados anteriormente: {len(self.processados)}\n")

        if not produtos:
            print("✅ Todos os produtos já foram processados!")
            return

        ok = erro = 0

        for i, p in enumerate(produtos, 1):
            print(f"[{i}/{len(produtos)}]", end="")
            try:
                if self.processar_produto(p, i):
                    ok += 1
                else:
                    erro += 1
                time.sleep(0.5)
            except Exception as e:
                print(f" ❌ Erro: {e}")
                erro += 1

        print("\n" + "="*60)
        print(f"✅ CONCLUÍDO: {ok} atualizados | {erro} erros")
        print(f"📊 Total processados: {len(self.processados)}")
        print("="*60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", "-l", type=int, help="Limite de produtos")
    parser.add_argument("--reprocessar", "-r", action="store_true", help="Reprocessar todos (ignora progresso)")
    args = parser.parse_args()

    proc = ShopifyProcessorV4()
    proc.processar_todos(args.limite, args.reprocessar)



