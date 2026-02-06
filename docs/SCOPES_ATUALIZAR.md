# 📋 Scopes Shopify - Configuração Completa

## ✅ Scopes Atuais (já ativos)
```
read_files,write_files,write_inventory,read_inventory,read_locales,write_locales,read_locations,read_markets,write_markets,read_metaobject_definitions,write_metaobject_definitions,read_metaobjects,write_metaobjects,read_online_store_navigation,write_online_store_navigation,read_product_listings,write_product_listings,read_products,write_products,read_publications,write_publications,read_reports,read_content,write_content,write_theme_code,read_themes,write_themes,read_translations,write_translations
```

---

## ⚠️ Scopes que FALTAM (adicionar dos opcionais)

Para automação completa de dropshipping, você **PRECISA** ativar:

| Scope | Motivo |
|-------|--------|
| `read_orders`, `write_orders` | **ESSENCIAL** - Gerenciar pedidos |
| `read_customers`, `write_customers` | **ESSENCIAL** - Gerenciar clientes |
| `read_fulfillments`, `write_fulfillments` | **ESSENCIAL** - Tracking/envio |
| `read_shipping`, `write_shipping` | **IMPORTANTE** - Zonas de frete |
| `read_all_orders` | Ver todos os pedidos (histórico) |
| `read_discounts`, `write_discounts` | Cupons e promoções |
| `read_price_rules`, `write_price_rules` | Regras de preço |

---

## 🔄 COPIE E SUBSTITUA ABAIXO

### Lista completa para substituir no Shopify Admin:

```
read_files,write_files,write_inventory,read_inventory,read_locales,write_locales,read_locations,read_markets,write_markets,read_metaobject_definitions,write_metaobject_definitions,read_metaobjects,write_metaobjects,read_online_store_navigation,write_online_store_navigation,read_product_listings,write_product_listings,read_products,write_products,read_publications,write_publications,read_reports,read_content,write_content,write_theme_code,read_themes,write_themes,read_translations,write_translations,read_all_orders,read_orders,write_orders,read_customers,write_customers,read_fulfillments,write_fulfillments,read_shipping,write_shipping,read_discounts,write_discounts,read_price_rules,write_price_rules,read_returns,write_returns
```

---

## 📋 Resumo das Adições

| Adicionado | Função |
|------------|--------|
| ✅ `read_all_orders` | Ver histórico completo |
| ✅ `read_orders`, `write_orders` | CRUD de pedidos |
| ✅ `read_customers`, `write_customers` | CRUD de clientes |
| ✅ `read_fulfillments`, `write_fulfillments` | Marcar enviado, tracking |
| ✅ `read_shipping`, `write_shipping` | Configurar frete |
| ✅ `read_discounts`, `write_discounts` | Cupons |
| ✅ `read_price_rules`, `write_price_rules` | Regras de preço |
| ✅ `read_returns`, `write_returns` | Devoluções |

---

> Após atualizar os scopes, será necessário **regenerar o token de acesso** e atualizar no `.env`
