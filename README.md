# 🤖 Shopify Automation + Product Mining

Sistema completo de automação para loja Shopify com mineração inteligente de produtos dropshipping.

## 🎯 Funcionalidades

- **Mineração de Produtos**: Busca automática no AliExpress com filtros inteligentes
- **Análise com IA (Claude)**: Avalia potencial, saturação, tendências
- **Automação DSers**: Login automático, adição de produtos, sync Shopify
- **Gestão Shopify**: CRUD produtos, coleções, health check

## 📁 Estrutura

```
src/
├── shopify/       # API Shopify
├── mining/        # Mineração AliExpress
├── ai/            # Integração Claude/GPT
├── dsers/         # Automação DSers
├── media/         # Processamento imagens/vídeos
├── collections/   # Coleções
├── enrichment/    # Enriquecimento
└── health/        # Health check

scripts/
├── mine_products.py    # Mineração
├── sync_dsers.py       # Sync DSers
└── daily_routine.py    # Rotina diária

data/
├── products_mined.csv
└── products_approved.csv
```

## 🚀 Instalação

```bash
git clone https://github.com/taffapereira/shopify-automation.git
cd shopify-automation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure suas credenciais
```

## ⚙️ Configuração (.env)

```env
SHOPIFY_STORE_URL=gpyvfv-1k.myshopify.com
SHOPIFY_ACCESS_TOKEN=seu_token
ANTHROPIC_API_KEY=sua_chave_claude
DSERS_EMAIL=seu_email
DSERS_PASSWORD=sua_senha
```

## 📋 Comandos

```bash
python scripts/mine_products.py --categoria jewelry --quantidade 20
python scripts/sync_dsers.py
python scripts/daily_routine.py
python main.py health
```

## 🎯 Critérios de Mineração

| Critério | Mínimo |
|----------|--------|
| Pedidos | > 500 |
| Rating | > 4.5 ⭐ |
| Preço | $5-30 |
| Margem | > 50% |
| Envio | < 30 dias |

## 🔄 Fluxo

```
MINERAÇÃO → ANÁLISE IA → APROVAÇÃO → DSERS → SHOPIFY
```

## 📄 Licença
MIT

