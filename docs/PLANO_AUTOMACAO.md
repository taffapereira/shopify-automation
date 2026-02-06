# 🚀 Shopify Automation - Plano Completo

## 📋 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SHOPIFY AUTOMATION - FULL STACK                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  ALIEXPRESS │───▶│    DSERS    │───▶│   SHOPIFY   │◀───│   PYTHON    │  │
│  │  (Produtos) │    │  (Ponte)    │    │   (Loja)    │    │ (Automação) │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                  ▲                  │          │
│                            │                  │                  │          │
│                            ▼                  │                  ▼          │
│                     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│                     │  Pedidos &  │    │   Catálogo  │    │  Relatórios │  │
│                     │ Fulfillment │    │  Enriquecido│    │  & Alertas  │  │
│                     └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Módulos de Automação

### **FASE 0 - Fundamentos (Base de Dados)**

| Item | Descrição | Status |
|------|-----------|--------|
| SQLite Database | Banco local para logs, mapeamentos, auditoria | 🔲 Criar |
| Padrão de SKU | `CATEGORIA-FORNECEDOR-ID` | 🔲 Definir |
| Regras de Preço | Margem, arredondamento, frete embutido | 🔲 Configurar |
| Location Virtual | Estoque único para dropshipping | 🔲 Criar |

### **FASE 1 - Catálogo Automático (Maior ROI)**

| Automação | Entrada | Saída | Responsável |
|-----------|---------|-------|-------------|
| Importar Produtos | AliExpress | Shopify | **DSers** |
| Enriquecer Catálogo | Produto bruto | Tags, SEO, descrições | **Python** |
| Criar Coleções | Tags padronizadas | Coleções automáticas | **Python** |
| Upload Imagens | URLs | Files API | **Python** |
| Metafields | Especificações | Dados estruturados | **Python** |

### **FASE 2 - Precificação Inteligente**

| Regra | Fórmula |
|-------|---------|
| Preço Base | `(custo + frete) × markup` |
| Markup Padrão | 2.2x a 3.0x (configurável) |
| Arredondamento | `.90` ou `.99` |
| Preço Mínimo | Garantir margem mínima |

### **FASE 3 - Pedidos & Fulfillment**

| Etapa | Responsável | Automação |
|-------|-------------|-----------|
| Pedido entra | Shopify | Webhook |
| Sincroniza | DSers | Automático |
| Compra AliExpress | DSers | Semi-auto/Auto |
| Tracking | DSers → Shopify | Automático |
| Fulfillment | DSers | Automático |
| Auditoria | Python | Relatórios |

### **FASE 4 - Reviews (Metaobjects)**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| product_handle | String | Vincula ao produto |
| rating | Integer | 1-5 estrelas |
| title | String | Título do review |
| body | Text | Conteúdo |
| author | String | Nome do cliente |
| verified | Boolean | Compra verificada |
| created_at | DateTime | Data |

### **FASE 5 - Monitoramento & Qualidade**

| KPI | Frequência | Alerta |
|-----|------------|--------|
| Taxa de Conversão | Diário | < 1% |
| AOV (Ticket Médio) | Diário | Variação > 20% |
| Margem Real | Semanal | < 30% |
| Taxa de Reembolso | Semanal | > 5% |
| Prazo de Entrega | Diário | > SLA |

---

## 📁 Estrutura do Projeto Completa

```
shopify-automation/
├── config/
│   ├── settings.py          # Configurações globais
│   ├── pricing_rules.yaml   # Regras de precificação
│   └── tags_mapping.yaml    # Mapeamento de tags/categorias
│
├── data/
│   ├── suppliers.csv        # Mapeamento SKU → Fornecedor
│   ├── reviews_import.csv   # Reviews para importar
│   └── shopify.db           # SQLite (logs, cache, auditoria)
│
├── src/
│   ├── __init__.py
│   ├── produtos.py          # ✅ Existe
│   ├── pedidos.py           # ✅ Existe
│   ├── clientes.py          # ✅ Existe
│   ├── loja.py              # ✅ Existe
│   ├── utils.py             # ✅ Existe
│   ├── database.py          # 🔲 SQLite operations
│   ├── pricing.py           # 🔲 Motor de precificação
│   ├── collections.py       # 🔲 Coleções automáticas
│   ├── reviews.py           # 🔲 Metaobjects de reviews
│   └── enrichment.py        # 🔲 Enriquecimento de catálogo
│
├── scripts/
│   ├── 01_enriquecer_catalogo.py   # Tags, SEO, descrições
│   ├── 02_reprecificar.py          # Aplicar regras de preço
│   ├── 03_criar_colecoes.py        # Coleções por tag
│   ├── 04_importar_reviews.py      # Reviews via metaobjects
│   ├── 05_healthcheck.py           # Relatório de saúde
│   └── 06_sync_inventory.py        # Sincronizar estoque
│
├── pipelines/
│   ├── daily.py             # Rotina diária (30-60min)
│   ├── weekly.py            # Rotina semanal (1-2h)
│   └── monthly.py           # Rotina mensal (auditoria)
│
├── relatorios/              # Auto-limpeza: 30 dias
├── temp/                    # Auto-limpeza: 1 dia
├── testes/                  # Auto-limpeza: 7 dias
├── logs/                    # Auto-limpeza: 14 dias
│
├── main.py                  # ✅ Existe
├── requirements.txt         # ✅ Existe
├── .env                     # ✅ Existe (credenciais)
└── README.md                # ✅ Existe
```

---

## ⚡ Fluxos Automatizados

### **Fluxo 1: Importação de Produto (DSers + Python)**

```
AliExpress → DSers (import) → Shopify (produto bruto)
                                    ↓
                              Python detecta tag "src:dsers"
                                    ↓
                              Enriquece: tags, SEO, preço
                                    ↓
                              Cria coleção automática
                                    ↓
                              Ativa produto (draft → active)
```

### **Fluxo 2: Pedido (DSers automático)**

```
Cliente compra → Shopify (pedido pago)
                      ↓
                DSers sincroniza
                      ↓
                DSers → AliExpress (pedido)
                      ↓
                Tracking → DSers → Shopify
                      ↓
                Fulfillment automático
                      ↓
                Python: auditoria + relatório
```

### **Fluxo 3: Pipeline Diário (Python)**

```
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE DIÁRIO (Rodar 1x/dia - 30min)                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Enriquecer produtos novos (importados via DSers)            │
│  2. Verificar/ajustar preços                                    │
│  3. Atualizar coleções automáticas                              │
│  4. Healthcheck (produtos sem imagem, preço, etc.)              │
│  5. Alertas (estoque baixo, pedidos atrasados)                  │
│  6. Gerar relatório diário                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Comandos de Execução

```bash
# Rotina diária completa
python pipelines/daily.py

# Ou scripts individuais:
python scripts/01_enriquecer_catalogo.py
python scripts/02_reprecificar.py
python scripts/03_criar_colecoes.py
python scripts/05_healthcheck.py

# Importar reviews
python scripts/04_importar_reviews.py --file data/reviews_import.csv

# Limpeza de arquivos antigos
python -c "from src import limpar_tudo; limpar_tudo(dry_run=False)"
```

---

## 📊 Banco de Dados (SQLite)

```sql
-- Tabela de produtos mapeados
CREATE TABLE products_map (
    id INTEGER PRIMARY KEY,
    shopify_product_id TEXT,
    shopify_variant_id TEXT,
    sku TEXT UNIQUE,
    supplier TEXT DEFAULT 'aliexpress',
    supplier_url TEXT,
    cost REAL,
    shipping_cost REAL,
    margin REAL,
    status TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- Tabela de execuções (auditoria)
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    script TEXT,
    started_at DATETIME,
    finished_at DATETIME,
    status TEXT,
    items_processed INTEGER,
    errors INTEGER,
    log TEXT
);

-- Tabela de alertas
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    type TEXT,
    severity TEXT,
    message TEXT,
    product_id TEXT,
    order_id TEXT,
    created_at DATETIME,
    resolved_at DATETIME
);
```

---

## 💰 Regras de Precificação (YAML)

```yaml
# config/pricing_rules.yaml
default:
  markup: 2.5
  min_margin: 0.30
  rounding: 0.90
  
categories:
  eletronicos:
    markup: 2.2
    min_price: 49.90
  
  acessorios:
    markup: 3.0
    min_price: 29.90
  
  vestuario:
    markup: 2.8
    min_price: 39.90

shipping:
  included: true
  default_estimate: 15.00
```

---

## 🏷️ Padrão de Tags

| Prefixo | Uso | Exemplo |
|---------|-----|---------|
| `cat:` | Categoria | `cat:smartwatch` |
| `brand:` | Marca | `brand:xiaomi` |
| `ship:` | Tipo envio | `ship:aliexpress` |
| `src:` | Origem | `src:dsers` |
| `status:` | Status interno | `status:enriched` |
| `promo:` | Promoções | `promo:blackfriday` |

---

## ✅ Checklist de Implementação

### Fase 0 - Fundamentos
- [ ] Criar `config/settings.py`
- [ ] Criar `config/pricing_rules.yaml`
- [ ] Criar `src/database.py` (SQLite)
- [ ] Definir padrão de SKU
- [ ] Configurar DSers (plano pago)

### Fase 1 - Catálogo
- [ ] Criar `src/enrichment.py`
- [ ] Criar `scripts/01_enriquecer_catalogo.py`
- [ ] Criar `src/collections.py`
- [ ] Criar `scripts/03_criar_colecoes.py`

### Fase 2 - Precificação
- [ ] Criar `src/pricing.py`
- [ ] Criar `scripts/02_reprecificar.py`

### Fase 3 - Reviews
- [ ] Criar `src/reviews.py`
- [ ] Criar metaobject definition na Shopify
- [ ] Criar `scripts/04_importar_reviews.py`

### Fase 4 - Monitoramento
- [ ] Criar `scripts/05_healthcheck.py`
- [ ] Criar `pipelines/daily.py`
- [ ] Configurar alertas

---

## 🎯 Resultado Esperado

| Tarefa | Antes | Depois |
|--------|-------|--------|
| Importar produto | Manual | DSers (1 clique) |
| Enriquecer catálogo | 10-15min/produto | **Automático** |
| Precificar | Manual | **Automático** |
| Criar coleções | Manual | **Automático** |
| Processar pedido | Manual | DSers (automático) |
| Tracking | Manual | DSers (automático) |
| Reviews | Não tinha | **Automático** |
| Relatórios | Não tinha | **Automático** |
| Limpeza arquivos | Manual | **Automático** |

**Tempo economizado: ~3-4 horas/dia** 🚀

---

## 📌 Próximos Passos

1. **Começar pela Fase 0** - Criar database e configs
2. **Configurar DSers** - Plano pago para máxima automação
3. **Implementar scripts** - Um por vez, testando
4. **Criar pipelines** - Automatizar rotinas diárias

---

> 📄 **Nota:** Este arquivo será removido após uso. Salvo em `docs/PLANO_AUTOMACAO.md`
