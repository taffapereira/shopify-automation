"""
🔍 AUDITORIA INSTITUCIONAL DA LOJA SHOPIFY
Verifica se todos os elementos essenciais estão configurados.
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)


def get_headers():
    return {
        "X-Shopify-Access-Token": os.getenv("SHOPIFY_ACCESS_TOKEN"),
        "Content-Type": "application/json"
    }


def get_api_url(endpoint):
    store_url = os.getenv("SHOPIFY_STORE_URL")
    api_version = os.getenv("SHOPIFY_API_VERSION", "2025-04")
    return f"https://{store_url}/admin/api/{api_version}/{endpoint}"


def api_get(endpoint):
    """Faz requisição GET na API."""
    url = get_api_url(endpoint)
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    return None


# =============================================================================
# CHECAGENS INDIVIDUAIS
# =============================================================================

def check_info_loja():
    """Verifica informações básicas da loja."""
    print("\n" + "=" * 60)
    print("🏪 INFORMAÇÕES DA LOJA")
    print("=" * 60)

    data = api_get("shop.json")
    if not data:
        return {"status": "❌ ERRO", "details": "Não foi possível acessar a API"}

    shop = data.get("shop", {})

    checks = {
        "Nome": shop.get("name"),
        "Email": shop.get("email"),
        "Domínio": shop.get("domain"),
        "Moeda": shop.get("currency"),
        "País": shop.get("country_name"),
        "Timezone": shop.get("timezone"),
        "Plano": shop.get("plan_name"),
        "Checkout API": shop.get("checkout_api_supported"),
        "Multi-moeda": shop.get("enabled_presentment_currencies"),
    }

    for key, value in checks.items():
        status = "✅" if value else "⚠️"
        print(f"  {status} {key}: {value or 'Não configurado'}")

    return {"status": "✅ OK", "data": shop}


def check_checkout():
    """Verifica configurações de checkout."""
    print("\n" + "=" * 60)
    print("💳 CHECKOUT & PAGAMENTOS")
    print("=" * 60)

    # Verificar métodos de pagamento
    data = api_get("payment_gateways.json")

    if data:
        gateways = data.get("payment_gateways", [])
        ativos = [g for g in gateways if g.get("enabled")]
        print(f"  {'✅' if ativos else '❌'} Gateways de pagamento: {len(ativos)} ativos")
        for g in ativos:
            print(f"      • {g.get('name')}")
    else:
        print("  ⚠️ Não foi possível verificar gateways (permissão necessária)")

    # Verificar shop para checkout info
    shop_data = api_get("shop.json")
    if shop_data:
        shop = shop_data.get("shop", {})
        print(f"  {'✅' if shop.get('checkout_api_supported') else '⚠️'} Checkout API suportado")
        print(f"  ℹ️ Moeda principal: {shop.get('currency')}")

    return {"status": "verificado"}


def check_shipping():
    """Verifica configurações de frete."""
    print("\n" + "=" * 60)
    print("🚚 FRETE & ENVIO")
    print("=" * 60)

    data = api_get("shipping_zones.json")

    if not data:
        print("  ⚠️ Não foi possível verificar zonas de envio")
        return {"status": "⚠️ Verificar manualmente"}

    zones = data.get("shipping_zones", [])

    if zones:
        print(f"  ✅ {len(zones)} zona(s) de envio configurada(s):")
        for zone in zones:
            print(f"\n      📦 {zone.get('name')}")
            countries = zone.get("countries", [])
            print(f"         Países: {len(countries)}")
            for c in countries[:5]:  # Mostrar até 5
                print(f"           • {c.get('name')}")
            if len(countries) > 5:
                print(f"           ... e mais {len(countries) - 5}")

            # Taxas de frete
            rates = zone.get("price_based_shipping_rates", []) + zone.get("weight_based_shipping_rates", [])
            if rates:
                print(f"         Taxas: {len(rates)} configuradas")
    else:
        print("  ❌ Nenhuma zona de envio configurada!")

    return {"status": "✅ OK" if zones else "❌ CONFIGURAR", "zones": len(zones)}


def check_policies():
    """Verifica políticas da loja."""
    print("\n" + "=" * 60)
    print("📜 POLÍTICAS DA LOJA")
    print("=" * 60)

    data = api_get("policies.json")

    required_policies = [
        "Refund policy",
        "Privacy policy",
        "Terms of service",
        "Shipping policy"
    ]

    if not data:
        print("  ⚠️ Não foi possível verificar políticas")
        return {"status": "⚠️ Verificar"}

    policies = data.get("policies", [])
    found = [p.get("title") for p in policies if p.get("body")]

    for req in required_policies:
        exists = any(req.lower() in f.lower() for f in found)
        status = "✅" if exists else "❌"
        print(f"  {status} {req}")

    missing = len(required_policies) - len([r for r in required_policies if any(r.lower() in f.lower() for f in found)])

    return {"status": "✅ OK" if missing == 0 else f"❌ {missing} faltando", "found": found}


def check_pages():
    """Verifica páginas institucionais."""
    print("\n" + "=" * 60)
    print("📄 PÁGINAS INSTITUCIONAIS")
    print("=" * 60)

    data = api_get("pages.json")

    recommended_pages = [
        "Sobre", "About",
        "Contato", "Contact",
        "FAQ", "Perguntas",
        "Rastreamento", "Tracking", "Rastreio"
    ]

    if not data:
        print("  ⚠️ Não foi possível verificar páginas")
        return {"status": "⚠️ Verificar"}

    pages = data.get("pages", [])
    page_titles = [p.get("title", "").lower() for p in pages]

    print(f"  ℹ️ {len(pages)} página(s) encontrada(s):")
    for p in pages:
        published = "✅" if p.get("published_at") else "⚠️ Rascunho"
        print(f"      {published} {p.get('title')}")

    # Verificar recomendadas
    print("\n  📋 Páginas recomendadas:")
    for rec in ["Sobre/About", "Contato/Contact", "FAQ", "Rastreamento"]:
        terms = rec.lower().split("/")
        exists = any(any(t in pt for t in terms) for pt in page_titles)
        status = "✅" if exists else "⚠️ Faltando"
        print(f"      {status} {rec}")

    return {"status": "verificado", "count": len(pages)}


def check_collections():
    """Verifica coleções/categorias."""
    print("\n" + "=" * 60)
    print("📁 COLEÇÕES / CATEGORIAS")
    print("=" * 60)

    # Coleções manuais
    custom = api_get("custom_collections.json")
    custom_cols = custom.get("custom_collections", []) if custom else []

    # Coleções automáticas
    smart = api_get("smart_collections.json")
    smart_cols = smart.get("smart_collections", []) if smart else []

    total = len(custom_cols) + len(smart_cols)

    print(f"  ℹ️ Total: {total} coleção(ões)")
    print(f"      • Manuais: {len(custom_cols)}")
    print(f"      • Automáticas: {len(smart_cols)}")

    if custom_cols:
        print("\n  📂 Coleções manuais:")
        for c in custom_cols[:10]:
            published = "✅" if c.get("published_at") else "⚠️"
            print(f"      {published} {c.get('title')}")

    if smart_cols:
        print("\n  🔄 Coleções automáticas:")
        for c in smart_cols[:10]:
            published = "✅" if c.get("published_at") else "⚠️"
            print(f"      {published} {c.get('title')}")

    if total == 0:
        print("  ❌ Nenhuma coleção criada!")

    return {"status": "✅ OK" if total > 0 else "❌ CRIAR", "total": total}


def check_products():
    """Verifica produtos."""
    print("\n" + "=" * 60)
    print("📦 PRODUTOS")
    print("=" * 60)

    data = api_get("products/count.json")

    if not data:
        print("  ⚠️ Não foi possível contar produtos")
        return {"status": "⚠️ Verificar"}

    total = data.get("count", 0)
    print(f"  ℹ️ Total de produtos: {total}")

    # Verificar produtos ativos vs rascunho
    active = api_get("products/count.json?status=active")
    draft = api_get("products/count.json?status=draft")
    archived = api_get("products/count.json?status=archived")

    active_count = active.get("count", 0) if active else 0
    draft_count = draft.get("count", 0) if draft else 0
    archived_count = archived.get("count", 0) if archived else 0

    print(f"      ✅ Ativos: {active_count}")
    print(f"      ⚠️ Rascunho: {draft_count}")
    print(f"      🗄️ Arquivados: {archived_count}")

    # Amostra de produtos
    sample = api_get("products.json?limit=5")
    if sample:
        products = sample.get("products", [])
        if products:
            print("\n  📋 Amostra de produtos:")
            for p in products:
                imgs = len(p.get("images", []))
                vars = len(p.get("variants", []))
                print(f"      • {p.get('title')[:40]} | {imgs} imgs | {vars} vars")

    return {"status": "✅ OK" if total > 0 else "⚠️ Sem produtos", "total": total}


def check_theme():
    """Verifica tema."""
    print("\n" + "=" * 60)
    print("🎨 TEMA")
    print("=" * 60)

    data = api_get("themes.json")

    if not data:
        print("  ⚠️ Não foi possível verificar temas")
        return {"status": "⚠️ Verificar"}

    themes = data.get("themes", [])

    for t in themes:
        role = t.get("role")
        if role == "main":
            print(f"  ✅ Tema ativo: {t.get('name')}")
        elif role == "unpublished":
            print(f"  ⚠️ Tema não publicado: {t.get('name')}")

    return {"status": "✅ OK", "themes": len(themes)}


def check_navigation():
    """Verifica menus de navegação."""
    print("\n" + "=" * 60)
    print("🧭 NAVEGAÇÃO / MENUS")
    print("=" * 60)

    # Menus não são acessíveis diretamente via REST API padrão
    # Precisaria de GraphQL ou verificar via tema
    print("  ℹ️ Verificação de menus requer acesso manual ou GraphQL")
    print("  📋 Verificar no admin:")
    print("      • Menu principal (header)")
    print("      • Menu rodapé (footer)")
    print("      • Links de categorias")

    return {"status": "⚠️ Verificar manualmente"}


def check_metafields():
    """Verifica metafields configurados."""
    print("\n" + "=" * 60)
    print("🏷️ METAFIELDS & METAOBJECTS")
    print("=" * 60)

    # Metafield definitions (requer GraphQL para listagem completa)
    print("  ℹ️ Metafields são configurados por recurso")
    print("  📋 Verificar no admin > Settings > Custom data:")
    print("      • Products metafields")
    print("      • Variants metafields")
    print("      • Orders metafields")
    print("      • Customers metafields")

    return {"status": "⚠️ Verificar manualmente"}


def check_apps():
    """Lista apps instalados."""
    print("\n" + "=" * 60)
    print("📱 APPS INSTALADOS")
    print("=" * 60)

    # Apps não são listáveis diretamente via API padrão
    print("  ℹ️ Lista de apps requer verificação manual")
    print("  📋 Apps recomendados para dropshipping:")
    print("      • DSers (import AliExpress + fulfillment)")
    print("      • Tracking app (rastreamento)")
    print("      • Reviews app (avaliações)")
    print("      • Email marketing (Klaviyo, etc)")

    return {"status": "⚠️ Verificar manualmente"}


def check_locations():
    """Verifica localizações de estoque."""
    print("\n" + "=" * 60)
    print("📍 LOCALIZAÇÕES DE ESTOQUE")
    print("=" * 60)

    data = api_get("locations.json")

    if not data:
        print("  ⚠️ Não foi possível verificar localizações")
        return {"status": "⚠️ Verificar"}

    locations = data.get("locations", [])

    print(f"  ℹ️ {len(locations)} localização(ões):")
    for loc in locations:
        active = "✅" if loc.get("active") else "❌"
        print(f"      {active} {loc.get('name')}")
        print(f"         {loc.get('address1', 'N/A')}, {loc.get('city', 'N/A')}")

    return {"status": "✅ OK", "count": len(locations)}


# =============================================================================
# RELATÓRIO FINAL
# =============================================================================

def gerar_relatorio_auditoria():
    """Gera relatório completo de auditoria."""

    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " 🔍 AUDITORIA INSTITUCIONAL DA LOJA SHOPIFY ".center(58) + "║")
    print("║" + f" {datetime.now().strftime('%d/%m/%Y %H:%M')} ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    resultados = {}

    # Executar todas as verificações
    resultados["loja"] = check_info_loja()
    resultados["checkout"] = check_checkout()
    resultados["frete"] = check_shipping()
    resultados["politicas"] = check_policies()
    resultados["paginas"] = check_pages()
    resultados["colecoes"] = check_collections()
    resultados["produtos"] = check_products()
    resultados["tema"] = check_theme()
    resultados["navegacao"] = check_navigation()
    resultados["metafields"] = check_metafields()
    resultados["apps"] = check_apps()
    resultados["locations"] = check_locations()

    # Resumo final
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " 📊 RESUMO DA AUDITORIA ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    print("\n  ✅ = OK | ⚠️ = Atenção | ❌ = Ação necessária\n")

    for area, resultado in resultados.items():
        status = resultado.get("status", "?")
        print(f"  {status} {area.upper()}")

    # Ações recomendadas
    print("\n" + "=" * 60)
    print("📋 AÇÕES RECOMENDADAS")
    print("=" * 60)

    acoes = []

    if resultados.get("politicas", {}).get("status", "").startswith("❌"):
        acoes.append("• Criar/completar políticas (reembolso, privacidade, termos, frete)")

    if resultados.get("colecoes", {}).get("total", 0) == 0:
        acoes.append("• Criar coleções/categorias para organizar produtos")

    if resultados.get("produtos", {}).get("total", 0) == 0:
        acoes.append("• Importar produtos via DSers")

    acoes.append("• Verificar menus de navegação (header/footer)")
    acoes.append("• Configurar página de rastreamento")
    acoes.append("• Instalar DSers para dropshipping")
    acoes.append("• Configurar email transacional")

    for acao in acoes:
        print(f"  {acao}")

    print("\n" + "=" * 60)

    return resultados


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    gerar_relatorio_auditoria()
