"""
Health Checker
Verifica problemas nos produtos e gera relatórios de saúde da loja
"""
import os
from datetime import datetime
from typing import Dict, Any, List

try:
    from ..shopify.client import ShopifyClient
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shopify.client import ShopifyClient


class HealthChecker:
    """Verificador de saúde dos produtos da loja"""

    def __init__(self):
        self.client = ShopifyClient()

    def check_all_products(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Verifica todos os produtos e retorna problemas encontrados
        """
        issues = {
            "no_images": [],
            "no_price": [],
            "zero_price": [],
            "no_description": [],
            "short_description": [],
            "no_tags": [],
            "needs_review": [],
            "no_inventory": [],
            "draft_status": [],
        }

        products = self.client.get_products(limit=250)

        for product in products.get("products", []):
            pid = product["id"]
            title = product["title"]
            product_info = {"id": pid, "title": title}

            # Sem imagens
            if not product.get("images"):
                issues["no_images"].append(product_info.copy())

            # Verificação de variantes e preços
            variants = product.get("variants", [])
            if not variants:
                issues["no_price"].append(product_info.copy())
            else:
                prices = [float(v.get("price", 0)) for v in variants]
                if all(p == 0 for p in prices):
                    issues["zero_price"].append(product_info.copy())

            # Verificação de descrição
            body = product.get("body_html", "") or ""
            if not body:
                issues["no_description"].append(product_info.copy())
            elif len(body) < 100:
                issues["short_description"].append(product_info.copy())

            # Sem tags
            if not product.get("tags"):
                issues["no_tags"].append(product_info.copy())

            # Precisa revisão
            tags = product.get("tags", "")
            if "status:needs-review" in tags:
                issues["needs_review"].append(product_info.copy())

            # Status draft
            if product.get("status") == "draft":
                issues["draft_status"].append(product_info.copy())

        return issues

    def generate_report(self, save_to_file: bool = True) -> str:
        """
        Gera relatório de saúde em formato Markdown

        Args:
            save_to_file: Se True, salva em relatorios/
        """
        issues = self.check_all_products()

        # Contagem de produtos
        products = self.client.get_products(limit=1)
        total_count = self.client.get_product_count()

        # Monta relatório
        report_lines = [
            "# 🏥 Health Check Report",
            f"\n**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"**Total de Produtos:** {total_count}",
            "\n---\n",
            "## 📊 Resumo\n",
        ]

        # Resumo
        issue_labels = {
            "no_images": "❌ Sem imagens",
            "no_price": "❌ Sem preço definido",
            "zero_price": "⚠️ Preço zerado",
            "no_description": "❌ Sem descrição",
            "short_description": "⚠️ Descrição curta (<100 chars)",
            "no_tags": "⚠️ Sem tags",
            "needs_review": "🔍 Precisa revisão",
            "draft_status": "📝 Em rascunho",
            "no_inventory": "📦 Sem estoque",
        }

        total_issues = sum(len(v) for v in issues.values())

        report_lines.append(f"| Problema | Quantidade |")
        report_lines.append(f"|----------|------------|")

        for key, label in issue_labels.items():
            count = len(issues.get(key, []))
            if count > 0:
                report_lines.append(f"| {label} | {count} |")

        report_lines.append(f"\n**Total de problemas:** {total_issues}")

        # Detalhes por categoria
        report_lines.append("\n---\n")
        report_lines.append("## 📋 Detalhes\n")

        for key, label in issue_labels.items():
            products_with_issue = issues.get(key, [])
            if products_with_issue:
                report_lines.append(f"\n### {label} ({len(products_with_issue)})\n")

                # Mostra até 15 produtos
                for p in products_with_issue[:15]:
                    report_lines.append(f"- `{p['id']}` - {p['title'][:60]}")

                if len(products_with_issue) > 15:
                    report_lines.append(f"- _...e mais {len(products_with_issue) - 15} produtos_")

        # Score de saúde
        report_lines.append("\n---\n")
        report_lines.append("## 🎯 Score de Saúde\n")

        if total_count > 0:
            health_score = max(0.0, 100.0 - (total_issues / total_count * 20))
        else:
            health_score = 100

        if health_score >= 80:
            emoji = "🟢"
            status = "Excelente"
        elif health_score >= 60:
            emoji = "🟡"
            status = "Bom"
        elif health_score >= 40:
            emoji = "🟠"
            status = "Regular"
        else:
            emoji = "🔴"
            status = "Precisa Atenção"

        report_lines.append(f"{emoji} **{health_score:.0f}/100** - {status}")

        # Recomendações
        report_lines.append("\n---\n")
        report_lines.append("## 💡 Recomendações\n")

        if issues["no_images"]:
            report_lines.append("1. **Adicione imagens** aos produtos sem foto - produtos sem imagem têm taxa de conversão muito baixa")

        if issues["zero_price"]:
            report_lines.append("2. **Defina preços** para produtos com preço zerado - use o comando `python main.py enrich`")

        if issues["no_description"]:
            report_lines.append("3. **Escreva descrições** para os produtos - isso melhora SEO e conversão")

        if issues["no_tags"]:
            report_lines.append("4. **Adicione tags** para organizar produtos em coleções automáticas")

        if issues["needs_review"]:
            report_lines.append("5. **Revise produtos** marcados como 'needs-review' e marque como processados")

        report = "\n".join(report_lines)

        # Salva arquivo
        if save_to_file:
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "relatorios")
            os.makedirs(reports_dir, exist_ok=True)

            filename = f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"\n📄 Relatório salvo em: {filepath}")

        return report

    def get_quick_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas rápidas da loja"""
        try:
            shop = self.client.get_shop()
            products = self.client.get_products(limit=5)
            product_count = self.client.get_product_count()

            return {
                "shop_name": shop.get("shop", {}).get("name"),
                "shop_email": shop.get("shop", {}).get("email"),
                "total_products": product_count,
                "recent_products": [p["title"] for p in products.get("products", [])[:5]],
                "status": "online"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Teste direto
if __name__ == "__main__":
    checker = HealthChecker()

    print("=== Quick Stats ===")
    stats = checker.get_quick_stats()

    if stats["status"] == "online":
        print(f"🏪 Loja: {stats['shop_name']}")
        print(f"📧 Email: {stats['shop_email']}")
        print(f"📦 Produtos: {stats['total_products']}")
    else:
        print(f"❌ Erro: {stats['error']}")


